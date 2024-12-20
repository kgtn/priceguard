"""
Notification service for the PriceGuard bot.
File: src/services/monitoring/notifications.py
"""

import logging
from typing import Dict, List
from datetime import datetime

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
        changes: Dict[str, List[Dict]]
    ) -> None:
        """
        Отправляет уведомление об акциях.
        
        Args:
            user_id: ID пользователя
            changes: Словарь с активными акциями для каждого маркетплейса
        """
        try:
            messages = []
            
            # Форматируем сообщения для каждого маркетплейса
            if "ozon" in changes and changes["ozon"]:
                messages.append(self._format_ozon_changes(changes["ozon"]))
            
            if "wildberries" in changes and changes["wildberries"]:
                messages.append(self._format_wb_changes(changes["wildberries"]))
            
            # Отправляем сообщения
            for message in messages:
                if message:  # Отправляем только непустые сообщения
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

    def _format_ozon_changes(self, promotions: List[Dict]) -> str:
        """Форматирует сообщение об акциях Ozon."""
        message = "🔵 *Активные акции OZON*\n\n"
        
        if not promotions:
            message += "❌ Активных акций с вашими товарами не найдено\n"
            return message.strip()
            
        # Функция для форматирования даты
        def format_date(date_str: str) -> str:
            if not date_str:
                return "не указана"
            try:
                if 'T' in date_str:  # ISO format with timezone
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:  # Simple date format
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                return date.strftime("%d.%m.%Y")
            except Exception as e:
                logger.error(f"Error formatting date {date_str}: {str(e)}")
                return "не указана"

        for promo in promotions:
            title = promo.get('title', promo.get('name', 'Hot Sale'))
            message += (
                f"🔸 *{title}*\n"
                f"   └ 📦 Товаров: {promo.get('products_count', 0)}\n"
                f"   └ 📅 Период: {format_date(promo.get('date_start'))} - {format_date(promo.get('date_end'))}\n\n"
            )

        return message.strip()

    def _format_wb_changes(self, promotions: List[Dict]) -> str:
        """Форматирует сообщение об акциях Wildberries."""
        message = "🟣 *Активные акции Wildberries*\n\n"
        
        if not promotions:
            message += "❌ Активных акций с вашими товарами не найдено\n"
            return message.strip()
            
        # Функция для форматирования даты
        def format_date(date_str: str) -> str:
            if not date_str:
                return "не указана"
            try:
                if 'T' in date_str:  # ISO format with timezone
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:  # Simple date format
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                return date.strftime("%d.%m.%Y")
            except Exception as e:
                logger.error(f"Error formatting date {date_str}: {str(e)}")
                return "не указана"

        for promo in promotions:
            message += (
                f"🔸 *{promo['name']}*\n"
                f"   └ 📦 Товаров: {promo.get('products_count', 0)}\n"
                f"   └ 📅 Период: {format_date(promo.get('date_start'))} - {format_date(promo.get('date_end'))}\n\n"
            )

        return message.strip()

    def _format_ozon_promo(self, promo: Dict) -> str:
        """Format single Ozon promotion."""
        return f"📦 Количество товаров: {promo['products_count']}"

    def _format_wb_promo(self, promo: Dict) -> str:
        """Format single Wildberries promotion."""
        return f"• {promo['name']}\n  📦 Товаров: {promo['products_count']}"
