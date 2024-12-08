"""
Promotion monitoring service for the PriceGuard bot.
File: src/services/monitoring/monitor.py
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from core.database import Database
from services.marketplaces.ozon import OzonClient
from services.marketplaces.wildberries import WildberriesClient
from services.marketplaces.factory import MarketplaceFactory

logger = logging.getLogger(__name__)

class PromotionMonitor:
    """Service for monitoring promotions on marketplaces."""

    def __init__(
        self,
        db: Database,
        marketplace_factory: MarketplaceFactory,
        check_interval: int = 3600  # 1 hour
    ):
        """Initialize monitor."""
        self.db = db
        self.marketplace_factory = marketplace_factory
        self.check_interval = check_interval
        self._task: Optional[asyncio.Task] = None
        self._last_check: Dict[int, datetime] = {}
        self._cached_promotions: Dict[int, Dict] = {}

    async def start(self) -> None:
        """Start monitoring task."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._monitor_loop())
            logger.info("Started promotion monitoring task")

    async def stop(self) -> None:
        """Stop monitoring task."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
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
        return await self._check_user_promotions(user_id)

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while True:
            try:
                # Get all active subscriptions
                subscriptions = await self.db.get_active_subscriptions()
                
                for sub in subscriptions:
                    user_id = sub["user_id"]
                    
                    # Skip if checked recently
                    last_check = self._last_check.get(user_id)
                    if last_check and (datetime.now() - last_check).seconds < self.check_interval:
                        continue

                    # Check promotions
                    changes = await self._check_user_promotions(user_id)
                    
                    # Update last check time
                    self._last_check[user_id] = datetime.now()
                    
                    # Send notifications if changes found
                    if changes:
                        await self._notify_user(user_id, changes)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")

            await asyncio.sleep(self.check_interval)

    async def _check_user_promotions(self, user_id: int) -> Dict:
        """
        Check promotions for specific user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            Dict with changes found
        """
        changes = {
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

        try:
            # Get user API keys
            user = await self.db.get_user(user_id)
            if not user:
                logger.warning(f"User {user_id} not found")
                return changes

            # Check Ozon promotions
            if user.get("ozon_api_key") and user.get("ozon_client_id"):
                ozon_client = await self.marketplace_factory.get_ozon_client(
                    user["ozon_api_key"],
                    user["ozon_client_id"]
                )
                current_ozon = await ozon_client.get_hot_sales()
                cached_ozon = self._cached_promotions.get(user_id, {}).get("ozon", [])
                
                changes["ozon"] = self._compare_promotions(
                    cached_ozon,
                    current_ozon
                )
                
                # Update cache
                if not self._cached_promotions.get(user_id):
                    self._cached_promotions[user_id] = {}
                self._cached_promotions[user_id]["ozon"] = current_ozon

            # Check Wildberries promotions
            if user.get("wb_api_key"):
                wb_client = await self.marketplace_factory.get_wildberries_client(
                    user["wb_api_key"]
                )
                current_wb = await wb_client.get_auto_promotions()
                cached_wb = self._cached_promotions.get(user_id, {}).get("wb", [])
                
                changes["wildberries"] = self._compare_promotions(
                    cached_wb,
                    current_wb
                )
                
                # Update cache
                if not self._cached_promotions.get(user_id):
                    self._cached_promotions[user_id] = {}
                self._cached_promotions[user_id]["wb"] = current_wb

        except Exception as e:
            logger.error(f"Error checking promotions for user {user_id}: {str(e)}")

        return changes

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
        return old_promo.get("products_count") != new_promo.get("products_count")

    async def _notify_user(self, user_id: int, changes: Dict) -> None:
        """
        Send notification to user about promotion changes.
        
        Args:
            user_id: User to notify
            changes: Changes found
        """
        # This will be implemented in the notification service
        pass
