"""
Notification service for the PriceGuard bot.
File: src/services/monitoring/notifications.py
"""

import logging
from typing import Dict, List

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from core.database import Database

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications to users."""

    def __init__(self, bot: Bot, db: Database):
        """Initialize service."""
        self.bot = bot
        self.db = db

    async def notify_promotion_changes(
        self,
        user_id: int,
        changes: Dict
    ) -> None:
        """
        Send notification about promotion changes.
        
        Args:
            user_id: User to notify
            changes: Changes found in promotions
        """
        try:
            # Format messages for each marketplace
            messages = []
            
            # Ozon changes
            if any(changes["ozon"].values()):
                messages.append(self._format_ozon_changes(changes["ozon"]))
            
            # Wildberries changes
            if any(changes["wildberries"].values()):
                messages.append(self._format_wb_changes(changes["wildberries"]))
            
            # Send messages
            for message in messages:
                try:
                    await self.bot.send_message(
                        user_id,
                        message,
                        parse_mode="Markdown"
                    )
                except TelegramAPIError as e:
                    logger.error(
                        f"Error sending notification to user {user_id}: {str(e)}"
                    )

        except Exception as e:
            logger.error(
                f"Error formatting notification for user {user_id}: {str(e)}"
            )

    def _format_ozon_changes(self, changes: Dict) -> str:
        """Format Ozon changes message."""
        message = "🔵 *Изменения в акциях Ozon*\n\n"
        
        # New promotions
        if changes["new"]:
            message += "✨ *Новые акции:*\n"
            for promo in changes["new"]:
                message += self._format_ozon_promo(promo) + "\n"
        
        # Changed promotions
        if changes["changed"]:
            message += "\n📊 *Изменения в акциях:*\n"
            for promo in changes["changed"]:
                message += self._format_ozon_promo(promo) + "\n"
        
        # Ended promotions
        if changes["ended"]:
            message += "\n❌ *Завершенные акции:*\n"
            for promo in changes["ended"]:
                message += f"• {promo.get('name', 'Без названия')}\n"
        
        return message.strip()

    def _format_wb_changes(self, changes: Dict) -> str:
        """Format Wildberries changes message."""
        message = "⚪️ *Изменения в акциях Wildberries*\n\n"
        
        # New promotions
        if changes["new"]:
            message += "✨ *Новые акции:*\n"
            for promo in changes["new"]:
                message += self._format_wb_promo(promo) + "\n"
        
        # Changed promotions
        if changes["changed"]:
            message += "\n📊 *Изменения в акциях:*\n"
            for promo in changes["changed"]:
                message += self._format_wb_promo(promo) + "\n"
        
        # Ended promotions
        if changes["ended"]:
            message += "\n❌ *Завершенные акции:*\n"
            for promo in changes["ended"]:
                message += f"• {promo.get('name', 'Без названия')}\n"
        
        return message.strip()

    def _format_ozon_promo(self, promo: Dict) -> str:
        """Format single Ozon promotion."""
        return (
            f"• *{promo.get('name', 'Без названия')}*\n"
            f"  💰 Цена: {promo.get('price')} ₽\n"
            f"  🏷 Цена по акции: {promo.get('action_price')} ₽\n"
            f"  📦 Остаток: {promo.get('stock')} шт.\n"
            f"  📅 {promo.get('date_start')} - {promo.get('date_end')}"
        )

    def _format_wb_promo(self, promo: Dict) -> str:
        """Format single Wildberries promotion."""
        return (
            f"• *{promo.get('name', 'Без названия')}*\n"
            f"  💰 Скидка: {promo.get('discount')}%\n"
            f"  📦 Товаров: {promo.get('products_count')} шт.\n"
            f"  📅 {promo.get('date_start')} - {promo.get('date_end')}"
        )
