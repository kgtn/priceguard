"""
Promotion monitoring service for the PriceGuard bot.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from core.database import Database
from services.marketplaces.ozon import OzonClient
from services.marketplaces.wildberries import WildberriesClient
from services.marketplaces.factory import MarketplaceFactory
from services.marketplaces.queue import QueueManager
from services.monitoring.notifications import NotificationService

logger = logging.getLogger(__name__)

class PromotionMonitor:
    """Service for monitoring promotions on marketplaces."""

    def __init__(
        self,
        db: Database,
        marketplace_factory: MarketplaceFactory,
        notification_service: NotificationService,
        check_interval: int = 14400  # 4 hours
    ):
        """Initialize monitor."""
        self.db = db
        self.marketplace_factory = marketplace_factory
        self.notification_service = notification_service
        self.check_interval = check_interval
        self._task: Optional[asyncio.Task] = None
        self._last_check: Dict[int, Dict[str, datetime]] = {}  # Changed to store per-marketplace timestamps
        self._cached_promotions: Dict[int, Dict] = {}
        self._check_queue: Dict[str, asyncio.Queue] = {
            'ozon': asyncio.Queue(),
            'wildberries': asyncio.Queue()
        }
        self._processing_tasks: Dict[str, asyncio.Task] = {}

    async def start(self) -> None:
        """Start monitoring task."""
        if self._task is None or self._task.done():
            # Start queue processors
            for marketplace in self._check_queue:
                self._processing_tasks[marketplace] = asyncio.create_task(
                    self._process_queue(marketplace)
                )
            
            # Start main monitoring task
            self._task = asyncio.create_task(self._monitor_loop())
            logger.info("Started promotion monitoring task")

    async def stop(self) -> None:
        """Stop monitoring task."""
        # Stop main monitoring task
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        # Stop queue processors
        for task in self._processing_tasks.values():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        logger.info("Stopped promotion monitoring task")

    async def force_check(self, user_id: int) -> Dict:
        """
        Force check promotions for specific user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Dict with changes found
        """
        # Add high-priority check to queues
        user = await self.db.get_user(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return self._empty_changes()
        
        changes = self._empty_changes()  # Initialize with empty structure for both marketplaces
        
        if user.get("ozon_api_key"):
            await self._check_queue['ozon'].put((user_id, True))
            changes['ozon'] = await self._check_ozon_promotions(user_id, user)
        
        if user.get("wildberries_api_key"):
            await self._check_queue['wildberries'].put((user_id, True))
            changes['wildberries'] = await self._check_wb_promotions(user_id, user)
        
        return changes

    def _empty_changes(self) -> Dict:
        """Get empty changes structure."""
        return {
            "ozon": {
                "new": [],
                "ended": [],
                "changed": []
            },
            "wildberries": {
                "new": [],
                "ended": [],
                "changed": []
            }
        }

    async def _process_queue(self, marketplace: str) -> None:
        """
        Process marketplace check queue.
        
        Args:
            marketplace: Marketplace name
        """
        while True:
            try:
                # Get next check from queue
                user_id, priority = await self._check_queue[marketplace].get()
                
                # Get user data
                user = await self.db.get_user(user_id)
                if not user:
                    logger.warning(f"User {user_id} not found")
                    continue
                
                logger.info(
                    f"Processing {marketplace} check for user {user_id}\n"
                    f"Priority: {priority}"
                )
                
                # Skip if checked recently
                if user_id not in self._last_check:
                    self._last_check[user_id] = {}
                
                last_check = self._last_check[user_id].get(marketplace)
                check_interval = user.get('check_interval', self.check_interval)
                
                if not priority and last_check:
                    seconds_since_check = (datetime.now() - last_check).total_seconds()
                    time_left = check_interval - seconds_since_check
                    
                    if time_left > 0:
                        logger.info(
                            f"Skipping {marketplace} check for user {user_id}:\n"
                            f"Last check: {int(seconds_since_check)} seconds ago\n"
                            f"Check interval: {check_interval} seconds\n"
                            f"Next check in: {int(time_left)} seconds"
                        )
                        continue
                
                # Perform check
                if marketplace == 'ozon':
                    changes = await self._check_ozon_promotions(user_id, user)
                    if any(changes):  # Проверяем, есть ли какие-либо изменения
                        marketplace_changes = {'ozon': changes, 'wildberries': []}
                        await self._notify_user(user_id, marketplace_changes)
                elif marketplace == 'wildberries':
                    changes = await self._check_wb_promotions(user_id, user)
                    if any(changes):  # Проверяем, есть ли какие-либо изменения
                        marketplace_changes = {'ozon': [], 'wildberries': changes}
                        await self._notify_user(user_id, marketplace_changes)
                else:
                    logger.warning(f"Unknown marketplace: {marketplace}")
                    continue
                
                # Update last check time only for successful non-priority checks
                if not priority:
                    if user_id not in self._last_check:
                        self._last_check[user_id] = {}
                    self._last_check[user_id][marketplace] = datetime.now()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing {marketplace} check: {str(e)}")
                await asyncio.sleep(5)

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        MONITOR_INTERVAL = 900  # 15 минут в секундах
        
        while True:
            try:
                # Получаем список активных подписок
                subscriptions = await self.db.get_active_subscriptions()
                logger.info(f"Found {len(subscriptions)} active subscriptions")
                
                # Обрабатываем каждую подписку
                for user in subscriptions:
                    user_id = user['user_id']
                    interval = user.get('check_interval', self.check_interval)
                    
                    # Проверяем время последней проверки
                    if user_id not in self._last_check:
                        self._last_check[user_id] = {}
                    
                    last_check_ozon = self._last_check[user_id].get('ozon')
                    last_check_wb = self._last_check[user_id].get('wildberries')
                    
                    # Если нет записи о последней проверке или интервал истек
                    should_check_ozon = not last_check_ozon or (datetime.now() - last_check_ozon).total_seconds() >= interval
                    should_check_wb = not last_check_wb or (datetime.now() - last_check_wb).total_seconds() >= interval
                    
                    if should_check_ozon or should_check_wb:
                        # Проверяем наличие API ключей
                        has_ozon = bool(user.get('ozon_api_key'))
                        has_wb = bool(user.get('wildberries_api_key'))
                        
                        # Логируем только если есть хотя бы один ключ
                        if has_ozon or has_wb:
                            logger.info(
                                f"Adding checks for user {user_id} "
                                f"(interval: {interval} seconds, APIs: "
                                f"{'Ozon ' if has_ozon else ''}"
                                f"{'WB' if has_wb else ''})"
                            )
                            
                            # Добавляем проверки в очереди
                            if has_ozon and should_check_ozon:
                                await self._check_queue['ozon'].put((user_id, False))
                            if has_wb and should_check_wb:
                                await self._check_queue['wildberries'].put((user_id, False))
                    else:
                        time_left_ozon = interval - (datetime.now() - last_check_ozon).total_seconds()
                        time_left_wb = interval - (datetime.now() - last_check_wb).total_seconds()
                        logger.info(
                            f"Skipping checks for user {user_id}:\n"
                            f"Last check Ozon: {int((datetime.now() - last_check_ozon).total_seconds())} seconds ago\n"
                            f"Last check WB: {int((datetime.now() - last_check_wb).total_seconds())} seconds ago\n"
                            f"Check interval: {interval} seconds\n"
                            f"Next check Ozon in: {int(time_left_ozon)} seconds\n"
                            f"Next check WB in: {int(time_left_wb)} seconds"
                        )
                
                # Ждем 15 минут перед следующей итерацией
                await asyncio.sleep(MONITOR_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(MONITOR_INTERVAL)

    async def _check_ozon_promotions(self, user_id: int, user: Dict) -> List[Dict]:
        """
        Проверяет акции Ozon.
        
        Args:
            user_id: ID пользователя
            user: Данные пользователя
            
        Returns:
            Список акций с ненулевым количеством товаров
        """
        try:
            ozon_client = await self.marketplace_factory.get_ozon_client(
                user["ozon_api_key"],
                user["ozon_client_id"]
            )
            async with ozon_client:
                active_promotions = []
                promotions = await ozon_client.get_promo_products()
                
                for promo in promotions:
                    if promo.get('products_count', 0) > 0:
                        active_promotions.append({
                            "name": promo.get("title", promo.get("name", "Hot Sale")),
                            "products_count": promo.get("products_count", 0),
                            "date_start": promo.get("start_date"),
                            "date_end": promo.get("end_date")
                        })
                
                return active_promotions
                
        except Exception as e:
            logger.error(f"Error checking Ozon promotions for user {user_id}: {str(e)}")
            return []

    async def _check_wb_promotions(self, user_id: int, user: Dict) -> List[Dict]:
        """
        Проверяет акции Wildberries.
        
        Args:
            user_id: ID пользователя
            user: Данные пользователя
            
        Returns:
            Список акций с ненулевым количеством товаров
        """
        try:
            wb_client = await self.marketplace_factory.get_wildberries_client(
                user["wildberries_api_key"]
            )
            async with wb_client:
                active_promotions = []
                promotions = await wb_client.get_promo_products()
                
                for promo in promotions:
                    if promo.get('products_count', 0) > 0:
                        active_promotions.append(promo)
                
                return active_promotions
                
        except Exception as e:
            logger.error(f"Error checking Wildberries promotions for user {user_id}: {str(e)}")
            return []

    async def _notify_user(self, user_id: int, changes: Dict) -> None:
        """
        Send notification to user about promotion changes.
        
        Args:
            user_id: User to notify
            changes: Changes found in promotions for each marketplace
        """
        if any(changes.values()):
            # Добавляем задержку между уведомлениями
            await asyncio.sleep(2)  # 2 секунды между уведомлениями
            
            try:
                await self.notification_service.notify_promotion_changes(user_id, changes)
                logger.info(f"Sent notification about changes to user {user_id}")
            except TelegramForbiddenError:
                logger.warning(f"User {user_id} blocked the bot")
                # Можно добавить логику для обработки блокировки
            except TelegramBadRequest as e:
                if "Flood control exceeded" in str(e):
                    # При превышении лимита ждем и пробуем снова
                    retry_after = int(str(e).split('retry after ')[1].split()[0])
                    logger.warning(f"Rate limit exceeded, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)
                    try:
                        await self.notification_service.notify_promotion_changes(user_id, changes)
                    except Exception as retry_e:
                        logger.error(f"Failed to send notification after retry: {retry_e}")
                else:
                    logger.error(f"Error sending notification: {e}")
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
