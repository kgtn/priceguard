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

    async def notify_user(self, user_id: int, message: str) -> bool:
        """
        Send notification to user.
        
        Args:
            user_id: User's Telegram ID
            message: Message text
            
        Returns:
            bool: True if sent successfully
        """
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message
            )
            return True
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            return False

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
            if "ozon" in changes and any(changes["ozon"].values()):
                messages.append(self._format_ozon_changes(changes["ozon"]))
            
            # Wildberries changes
            if "wildberries" in changes and any(changes["wildberries"].values()):
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
        message = "🔵 *OZON Hot Sale*\n\n"
        
        # New promotions
        if changes["new"]:
            promo = changes["new"][0]  # Only one Hot Sale promotion
            message += f"✨ Ваши товары участвуют в Hot Sale!\n"
            message += f"📦 Количество товаров: {promo['products_count']}\n"
        
        # Changed promotions
        if changes["changed"]:
            promo = changes["changed"][0]
            message += f"\n📊 Изменения в Hot Sale\n"
            message += f"📦 Количество товаров: {promo['products_count']}\n"
        
        # Ended promotions
        if changes["ended"]:
            message += "\n❌ Hot Sale завершена"
        
        return message.strip()

    def _format_wb_changes(self, changes: Dict) -> str:
        """Format Wildberries changes message."""
        message = "⚪️ *Автоакции Wildberries*\n\n"
        
        # New promotions
        if changes["new"]:
            message += "✨ *Новые автоакции:*\n"
            for promo in changes["new"]:
                message += f"• {promo['name']}\n"
                message += f"  📦 Товаров: {promo['products_count']}\n"
        
        # Changed promotions
        if changes["changed"]:
            message += "\n📊 *Изменения в автоакциях:*\n"
            for promo in changes["changed"]:
                message += f"• {promo['name']}\n"
                message += f"  📦 Товаров: {promo['products_count']}\n"
        
        # Ended promotions
        if changes["ended"]:
            message += "\n❌ *Завершенные автоакции:*\n"
            for promo in changes["ended"]:
                message += f"• {promo['name']}\n"
        
        return message.strip()

    def _format_ozon_promo(self, promo: Dict) -> str:
        """Format single Ozon promotion."""
        return f"📦 Количество товаров: {promo['products_count']}"

    def _format_wb_promo(self, promo: Dict) -> str:
        """Format single Wildberries promotion."""
        return f"• {promo['name']}\n  📦 Товаров: {promo['products_count']}"
