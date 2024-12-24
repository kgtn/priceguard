"""
Service for managing user reminders.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from core.database import Database
from services.marketplaces.factory import MarketplaceFactory

logger = logging.getLogger(__name__)

REMINDER_MESSAGES = {
    "no_api_keys": (
        "🔑 Привет! Замечу, что вы еще не добавили API ключи.\n\n"
        "Без них бот не сможет мониторить акции на маркетплейсах. "
        "Давайте я помогу вам с настройкой?"
    ),
    "invalid_api_keys": (
        "⚠️ Кажется, возникли проблемы с вашими API ключами.\n\n"
        "Это может быть связано с:\n"
        "• Неверным форматом ключа\n"
        "• Недостаточными правами доступа\n"
        "• Истекшим сроком действия\n\n"
        "Хотите, помогу разобраться?"
    )
}

REMINDER_INTERVALS = [
    timedelta(hours=24),  # Первое напоминание через 24 часа
    timedelta(days=2),    # Второе через 2 дня
    timedelta(days=4),    # Третье через 4 дня
    timedelta(days=7)     # Последнее через неделю
]

class ReminderService:
    """Service for managing user reminders."""

    def __init__(self, bot: Bot, db: Database, marketplace_factory: MarketplaceFactory):
        """Initialize reminder service."""
        self.bot = bot
        self.db = db
        self.marketplace_factory = marketplace_factory

    async def check_and_send_reminders(self):
        """Check users and send reminders if needed."""
        logger.info("Starting reminder check...")
        
        # Получаем всех пользователей, которым можно отправить напоминание
        users = await self._get_users_for_reminder()
        
        for user in users:
            try:
                await self._process_user_reminder(user)
            except Exception as e:
                logger.error(f"Error processing reminder for user {user['user_id']}: {e}")

    async def _get_users_for_reminder(self) -> List[Dict]:
        """Get users who need reminders."""
        # Получаем пользователей, у которых:
        # 1. Нет API ключей или они невалидны (setup_status != 'api_validated')
        # 2. Прошло достаточно времени с момента регистрации или последнего напоминания
        # 3. Отправлено менее 4 напоминаний
        
        query = """
            SELECT * FROM users 
            WHERE setup_status != 'api_validated'
            AND (
                (last_reminder_sent IS NULL AND created_at < datetime('now', '-1 day'))
                OR 
                (last_reminder_sent < datetime('now', '-1 day'))
            )
            AND (
                (SELECT COUNT(*) FROM user_notifications 
                WHERE user_id = users.user_id 
                AND type = 'reminder') < 4
            );
        """
        
        return await self.db.fetch_all(query)

    async def _process_user_reminder(self, user: Dict):
        """Process reminder for specific user."""
        user_id = user['user_id']
        setup_status = user['setup_status']
        
        # Определяем тип напоминания
        if setup_status == 'started':
            message = REMINDER_MESSAGES['no_api_keys']
            keyboard = self._get_reminder_keyboard('add_api')
        else:  # 'api_added'
            message = REMINDER_MESSAGES['invalid_api_keys']
            keyboard = self._get_reminder_keyboard('check_api')

        # Отправляем напоминание
        try:
            await self.bot.send_message(
                user_id,
                message,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
            # Обновляем информацию о напоминании
            await self.db.update_reminder_info(user_id)
            
            logger.info(f"Sent reminder to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send reminder to user {user_id}: {e}")

    def _get_reminder_keyboard(self, action: str) -> InlineKeyboardMarkup:
        """Get keyboard for reminder message."""
        if action == 'add_api':
            keyboard = [
                [InlineKeyboardButton(
                    text="🔑 Добавить API ключи",
                    callback_data="add_api"
                )],
                [InlineKeyboardButton(
                    text="📝 Инструкция",
                    callback_data="show_api_instructions"
                )],
                [InlineKeyboardButton(
                    text="👨‍💻 Тех. поддержка",
                    url="https://t.me/plmkr78"
                )],
                [InlineKeyboardButton(
                    text="🔕 Больше не напоминать",
                    callback_data="disable_reminders"
                )]
            ]
        else:  # check_api
            keyboard = [
                [InlineKeyboardButton(
                    text="🔑 Изменить ключи",
                    callback_data="change_api_keys"
                )],
                [InlineKeyboardButton(
                    text="📝 Как получить ключи",
                    callback_data="show_api_instructions"
                )],
                [InlineKeyboardButton(
                    text="👨‍💻 Тех. поддержка",
                    url="https://t.me/plmkr78"
                )],
                [InlineKeyboardButton(
                    text="🔕 Больше не напоминать",
                    callback_data="disable_reminders"
                )]
            ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    async def disable_reminders(self, user_id: int):
        """Disable reminders for user."""
        await self.db.disable_reminders(user_id)
