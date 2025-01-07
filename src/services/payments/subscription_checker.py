"""
Subscription checker service.
File: src/services/payments/subscription_checker.py
"""

from datetime import datetime, timedelta
from typing import List, Dict
import asyncio

from aiogram import Bot
from core.database import Database
from core.config import Settings
from core.logging import get_logger
from bot.utils.messages import format_subscription_status
from bot.keyboards.payment import get_subscription_keyboard

logger = get_logger(__name__)

SUBSCRIPTION_EXPIRING_SOON = """
⚠️ Ваша подписка скоро закончится!

До конца подписки осталось: {} дней.
Чтобы продолжить пользоваться сервисом без ограничений, продлите подписку.

Нажмите /status для продления подписки.
"""

SUBSCRIPTION_EXPIRED = """
❌ Ваша подписка закончилась!

Чтобы продолжить пользоваться сервисом, продлите подписку.
Нажмите /status для продления подписки.
"""

class SubscriptionChecker:
    """Service for checking subscription status."""
    
    def __init__(self, bot: Bot, db: Database, settings: Settings):
        self.bot = bot
        self.db = db
        self.settings = settings
        self.notification_days = 3  # Notify users 3 days before subscription expires
    
    async def is_bot_active_for_user(self, user_id: int) -> bool:
        """Проверяет, активен ли бот для конкретного пользователя."""
        try:
            chat_member = await self.bot.get_chat_member(chat_id=user_id, user_id=self.bot.id)
            return chat_member.status in ["member", "administrator"]
        except Exception as e:
            logger.error(f"Error checking bot status for user {user_id}: {e}")
            return False

    async def check_subscriptions(self):
        """Проверяет подписки для всех пользователей."""
        while True:
            try:
                # Получить всех активных пользователей
                users = await self.db.get_all_users()
                active_users = [
                    user for user in users["users"]
                    if user.get("subscription_status") == "active"
                ]
                
                for user in active_users:
                    if await self.is_bot_active_for_user(user["user_id"]):
                        await self._check_user_subscription(user)
                    else:
                        logger.info(f"Bot is not active for user {user['user_id']}, skipping.")

                # Проверять раз в час
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"Error in subscription checker: {e}")
                await asyncio.sleep(60)  # Подождите минуту перед повторной попыткой
    
    async def _check_user_subscription(self, user: Dict):
        """Check subscription for specific user."""
        try:
            user_id = user.get("user_id")
            end_date = user.get("subscription_end_date")
            
            if not end_date:
                return
            
            end_date = datetime.fromisoformat(end_date)
            now = datetime.now()
            
            # Subscription expired
            if now >= end_date:
                last_notification_sent = user.get("last_subscription_notification_sent")
                if not last_notification_sent or (datetime.fromisoformat(last_notification_sent).date() < now.date()):
                    await self.db.update_subscription(
                        user_id=user_id,
                        status="inactive",
                        end_date=end_date
                    )
                    logger.info(f"Subscription expired for user {user_id}")
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=SUBSCRIPTION_EXPIRED,
                        reply_markup=get_subscription_keyboard()
                    )
                    await self.db.update_user(
                        user_id=user_id,
                        last_subscription_notification_sent=now.isoformat()
                    )
                return
            
            # Subscription expiring soon
            days_left = (end_date - now).days
            if days_left <= self.notification_days:
                last_notification_sent = user.get("last_subscription_notification_sent")
                if not last_notification_sent or (datetime.fromisoformat(last_notification_sent).date() < now.date()):
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=SUBSCRIPTION_EXPIRING_SOON.format(days_left),
                        reply_markup=get_subscription_keyboard()
                    )
                    await self.db.update_user(
                        user_id=user_id,
                        last_subscription_notification_sent=now.isoformat()
                    )

        except Exception as e:
            logger.error(f"Error checking subscription for user {user.get('user_id')}: {e}")

async def start_subscription_checker(bot: Bot, db: Database, settings: Settings):
    """Start subscription checker service."""
    checker = SubscriptionChecker(bot, db, settings)
    asyncio.create_task(checker.check_subscriptions())
