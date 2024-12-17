"""
Promotion monitoring service for the PriceGuard bot.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

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
        logger.info(f"Started {marketplace} queue processor")
        
        while True:
            try:
                user_id, is_priority = await self._check_queue[marketplace].get()
                logger.info(f"Processing {marketplace} check for user {user_id} (priority: {is_priority})")
                
                try:
                    # Get user data and check interval
                    user = await self.db.get_user(user_id)
                    if not user:
                        logger.warning(f"User {user_id} not found")
                        continue
                    
                    user_interval = user.get("check_interval", self.check_interval)
                    
                    # Skip if checked recently and not priority
                    if not is_priority:
                        last_check = self._last_check.get(user_id)
                        if last_check:
                            time_since_last_check = (datetime.now() - last_check).seconds
                            if time_since_last_check < user_interval:  
                                logger.info(
                                    f"Skipping {marketplace} check for user {user_id}: "
                                    f"last check was {time_since_last_check} seconds ago "
                                    f"(interval: {user_interval} seconds)"
                                )
                                continue
                    
                    # Check promotions
                    changes = {}
                    if marketplace == 'ozon' and user.get("ozon_api_key"):
                        logger.info(f"Checking Ozon promotions for user {user_id}")
                        changes = await self._check_ozon_promotions(user_id, user)
                    elif marketplace == 'wildberries' and user.get("wildberries_api_key"):
                        logger.info(f"Checking Wildberries promotions for user {user_id}")
                        changes = await self._check_wb_promotions(user_id, user)
                    
                    # Update last check time
                    self._last_check[user_id] = datetime.now()
                    
                    # Log check results
                    if changes:
                        total_changes = sum(len(items) for items in changes.values())
                        logger.info(
                            f"Found {total_changes} changes in {marketplace} "
                            f"promotions for user {user_id}"
                        )
                    else:
                        logger.info(f"No changes found in {marketplace} promotions for user {user_id}")
                    
                    # Send notifications if changes found
                    if changes and any(changes.values()):
                        marketplace_changes = {marketplace: changes}
                        await self._notify_user(user_id, marketplace_changes)
                        logger.info(f"Sent notification about {marketplace} changes to user {user_id}")
                
                finally:
                    # Mark task as done only if not cancelled
                    self._check_queue[marketplace].task_done()
                    logger.debug(f"Finished processing {marketplace} check for user {user_id}")
                
            except asyncio.CancelledError:
                logger.info(f"Stopping {marketplace} queue processor")
                break
            except Exception as e:
                logger.error(f"Error processing {marketplace} queue for user {user_id}: {str(e)}")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        logger.info("Started main monitoring loop")
        
        while True:
            try:
                # Get all active subscriptions
                subscriptions = await self.db.get_active_subscriptions()
                logger.info(f"Found {len(subscriptions)} active subscriptions")
                
                # Add checks to queues
                processed_users = set()  
                for sub in subscriptions:
                    user_id = sub["user_id"]
                    
                    # Пропускаем повторные подписки одного пользователя
                    if user_id in processed_users:
                        logger.debug(f"Skipping duplicate subscription for user {user_id}")
                        continue
                    processed_users.add(user_id)
                    
                    # Получаем данные пользователя для проверки ключей
                    user = await self.db.get_user(user_id)
                    if not user:
                        logger.warning(f"User {user_id} not found despite having active subscription")
                        continue

                    # Проверяем наличие хотя бы одного ключа API
                    has_ozon = bool(user.get("ozon_api_key") and user.get("ozon_client_id"))
                    has_wb = bool(user.get("wildberries_api_key"))
                    
                    if not (has_ozon or has_wb):
                        logger.debug(f"Skipping user {user_id}: no API keys configured")
                        continue
                        
                    # Получаем интервал проверки
                    user_interval = user.get("check_interval", self.check_interval)
                    logger.info(
                        f"Adding checks for user {user_id} "
                        f"(interval: {user_interval} seconds, "
                        f"APIs: {'Ozon ' if has_ozon else ''}{'WB' if has_wb else ''})"
                    )
                    
                    # Добавляем в очереди только если есть соответствующие ключи
                    if has_ozon:
                        await self._check_queue['ozon'].put((user_id, False))
                    
                    if has_wb:
                        await self._check_queue['wildberries'].put((user_id, False))

            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")

            logger.debug(f"Monitoring loop sleeping for {self.check_interval} seconds")
            await asyncio.sleep(self.check_interval)

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
        old_ids = {p["id"] for p in old_promotions}
        new_ids = {p["id"] for p in new_promotions}
        
        # Find new and ended promotions
        new_promos = [p for p in new_promotions if p["id"] not in old_ids]
        ended_promos = [p for p in old_promotions if p["id"] not in new_ids]
        
        # Find changed promotions
        changed_promos = []
        for old_promo in old_promotions:
            if old_promo["id"] in new_ids:
                new_promo = next(
                    p for p in new_promotions if p["id"] == old_promo["id"]
                )
                if self._has_changes(old_promo, new_promo):
                    changed_promos.append(new_promo)
        
        return {
            "new": new_promos,
            "ended": ended_promos,
            "changed": changed_promos
        }

    def _has_changes(self, old_promo: Dict, new_promo: Dict) -> bool:
        """
        Check if promotion has significant changes.
        
        Args:
            old_promo: Old promotion data
            new_promo: New promotion data
            
        Returns:
            True if changes found
        """
        significant_fields = ["products_count", "date_end"]
        return any(
            old_promo.get(field) != new_promo.get(field)
            for field in significant_fields
        )

    async def _notify_user(self, user_id: int, changes: Dict) -> None:
        """
        Send notification to user about promotion changes.
        
        Args:
            user_id: User to notify
            changes: Changes found in promotions for each marketplace
        """
        try:
            await self.notification_service.notify_promotion_changes(user_id, changes)
        except Exception as e:
            logger.error(f"Failed to notify user {user_id} about changes: {str(e)}")
