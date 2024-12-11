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
    
    async def check_subscriptions(self):
        """Check subscriptions for all users."""
        while True:
            try:
                # Get all active subscriptions
                users = await self.db.get_all_users()
                active_users = [
                    user for user in users["users"]
                    if user.get("subscription_status") == "active"
                ]
                
                for user in active_users:
                    await self._check_user_subscription(user)
                
                # Check once per hour
                await asyncio.sleep(3600)
            
            except Exception as e:
                logger.error(f"Error in subscription checker: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
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
                await self.db.update_subscription(
                    user_id=user_id,
                    status="inactive",
                    end_date=end_date
                )
                await self.bot.send_message(
                    chat_id=user_id,
                    text=SUBSCRIPTION_EXPIRED,
                    reply_markup=get_subscription_keyboard()
                )
                return
            
            # Subscription expiring soon
            days_left = (end_date - now).days
            if days_left <= self.notification_days:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=SUBSCRIPTION_EXPIRING_SOON.format(days_left),
                    reply_markup=get_subscription_keyboard()
                )
        
        except Exception as e:
            logger.error(f"Error checking subscription for user {user.get('user_id')}: {e}")

async def start_subscription_checker(bot: Bot, db: Database, settings: Settings):
    """Start subscription checker service."""
    checker = SubscriptionChecker(bot, db, settings)
    asyncio.create_task(checker.check_subscriptions())
