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
        self._last_check: Dict[int, datetime] = {}
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
                last_check = self._last_check.get(user_id)
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
                    if changes:
                        await self._notify_user(user_id, {'ozon': changes, 'wildberries': self._empty_changes()})
                else:
                    changes = await self._check_wb_promotions(user_id, user)
                    if changes:
                        await self._notify_user(user_id, {'ozon': self._empty_changes(), 'wildberries': changes})
                
                # Update last check time only for successful non-priority checks
                if not priority:
                    self._last_check[user_id] = datetime.now()
                
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
                    last_check = self._last_check.get(user_id)
                    current_time = datetime.now()
                    
                    # Если нет записи о последней проверке или интервал истек
                    should_check = (
                        not last_check or 
                        (current_time - last_check).total_seconds() >= interval
                    )
                    
                    if should_check:
                        logger.info(
                            f"Adding checks for user {user_id} "
                            f"(interval: {interval} seconds, APIs: "
                            f"{'Ozon ' if user.get('ozon_api_key') else ''}"
                            f"{'WB' if user.get('wildberries_api_key') else ''})"
                        )
                        
                        # Добавляем проверки в очереди
                        if user.get('ozon_api_key'):
                            await self._check_queue['ozon'].put((user_id, False))
                        if user.get('wildberries_api_key'):
                            await self._check_queue['wildberries'].put((user_id, False))
                    else:
                        time_left = interval - (current_time - last_check).total_seconds()
                        logger.info(
                            f"Skipping checks for user {user_id}:\n"
                            f"Last check: {int((current_time - last_check).total_seconds())} seconds ago\n"
                            f"Check interval: {interval} seconds\n"
                            f"Next check in: {int(time_left)} seconds"
                        )
                
                # Ждем 15 минут перед следующей итерацией
                await asyncio.sleep(MONITOR_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(MONITOR_INTERVAL)

    async def _check_ozon_promotions(self, user_id: int, user: Dict) -> Dict:
        """Check Ozon promotions for user."""
        try:
            ozon_client = await self.marketplace_factory.get_ozon_client(
                user["ozon_api_key"],
                user["ozon_client_id"]
            )
            async with ozon_client:
                current_ozon = await ozon_client.get_promo_products()
                cached_ozon = self._cached_promotions.get(user_id, {}).get("ozon", [])
                
                changes = self._compare_promotions(cached_ozon, current_ozon)
                
                # Update cache
                if not self._cached_promotions.get(user_id):
                    self._cached_promotions[user_id] = {}
                self._cached_promotions[user_id]["ozon"] = current_ozon
                
                return changes
                
        except Exception as e:
            logger.error(f"Error checking Ozon promotions for user {user_id}: {str(e)}")
            return {"new": [], "ended": [], "changed": []}

    async def _check_wb_promotions(self, user_id: int, user: Dict) -> Dict:
        """Check Wildberries promotions for user."""
        try:
            wb_client = await self.marketplace_factory.get_wildberries_client(
                user["wildberries_api_key"]
            )
            async with wb_client:
                current_wb = await wb_client.get_promo_products()
                cached_wb = self._cached_promotions.get(user_id, {}).get("wb", [])
                
                changes = self._compare_promotions(cached_wb, current_wb)
                
                # Update cache
                if not self._cached_promotions.get(user_id):
                    self._cached_promotions[user_id] = {}
                self._cached_promotions[user_id]["wb"] = current_wb
                
                return changes
                
        except Exception as e:
            logger.error(f"Error checking Wildberries promotions for user {user_id}: {str(e)}")
            return {"new": [], "ended": [], "changed": []}

    def _compare_promotions(
        self,
        old_promotions: List[Dict],
        new_promotions: List[Dict]
    ) -> Dict:
        """
        Compare old and new promotions to find changes.
        
        Args:
            old_promotions: Previously cached promotions
            new_promotions: Current promotions
            
        Returns:
            Dict with changes found
        """
        old_by_type = {}
        new_by_type = {}
        
        # Группируем акции по типам
        for promo in old_promotions:
            promo_type = promo.get("type", "unknown")
            if promo_type not in old_by_type:
                old_by_type[promo_type] = []
            old_by_type[promo_type].append(promo)
            
        for promo in new_promotions:
            promo_type = promo.get("type", "unknown")
            if promo_type not in new_by_type:
                new_by_type[promo_type] = []
            new_by_type[promo_type].append(promo)
        
        all_types = set(old_by_type.keys()) | set(new_by_type.keys())
        changes = {
            "new": [],
            "ended": [],
            "changed": []
        }
        
        # Сравниваем акции по каждому типу
        for promo_type in all_types:
            old_promos = old_by_type.get(promo_type, [])
            new_promos = new_by_type.get(promo_type, [])
            
            old_ids = {str(p["id"]) for p in old_promos}
            new_ids = {str(p["id"]) for p in new_promos}
            
            # Новые акции
            changes["new"].extend([
                p for p in new_promos 
                if str(p["id"]) not in old_ids
            ])
            
            # Завершенные акции
            changes["ended"].extend([
                p for p in old_promos 
                if str(p["id"]) not in new_ids
            ])
            
            # Измененные акции
            for old_promo in old_promos:
                old_id = str(old_promo["id"])
                if old_id in new_ids:
                    new_promo = next(
                        p for p in new_promos 
                        if str(p["id"]) == old_id
                    )
                    if self._has_changes(old_promo, new_promo):
                        changes["changed"].append(new_promo)
        
        logger.info(
            f"Found changes in promotions:\n"
            f"New: {len(changes['new'])}\n"
            f"Ended: {len(changes['ended'])}\n"
            f"Changed: {len(changes['changed'])}"
        )
        
        return changes

    def _has_changes(self, old_promo: Dict, new_promo: Dict) -> bool:
        """
        Check if promotion has significant changes.
        
        Args:
            old_promo: Old promotion data
            new_promo: New promotion data
            
        Returns:
            True if changes found
        """
        # Основные поля для сравнения
        base_fields = ["title", "type", "products_count"]
        if any(old_promo.get(field) != new_promo.get(field) for field in base_fields):
            return True
            
        # Проверяем даты, если они есть
        date_fields = ["date_start", "date_end", "start_date", "end_date"]
        old_dates = {
            field: old_promo.get(field) 
            for field in date_fields 
            if old_promo.get(field)
        }
        new_dates = {
            field: new_promo.get(field) 
            for field in date_fields 
            if new_promo.get(field)
        }
        if old_dates != new_dates:
            return True
            
        # Проверяем только количество товаров
        old_products = old_promo.get("products", [])
        new_products = new_promo.get("products", [])
        
        return len(old_products) != len(new_products)

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
