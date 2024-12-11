"""
Trial period checker service.
File: src/services/payments/trial_checker.py
"""

from datetime import datetime, timedelta
from typing import List, Dict
import asyncio

from aiogram import Bot
from core.database import Database
from core.config import Settings
from core.logging import get_logger
from bot.utils.messages import TRIAL_EXPIRING_SOON, TRIAL_EXPIRED
from bot.keyboards.payment import get_subscription_keyboard

logger = get_logger(__name__)

class TrialChecker:
    """Service for checking trial period status."""
    
    def __init__(self, bot: Bot, db: Database, settings: Settings):
        self.bot = bot
        self.db = db
        self.settings = settings
        self.notification_days = 3  # Notify users 3 days before trial expires
    
    async def check_trials(self):
        """Check trial periods for all users."""
        while True:
            try:
                # Get all trial users
                users = await self.db.get_all_users()
                trial_users = [
                    user for user in users["users"]
                    if user.get("subscription_status") == "trial"
                ]
                
                for user in trial_users:
                    await self._check_user_trial(user)
                
                # Check once per hour
                await asyncio.sleep(3600)
            
            except Exception as e:
                logger.error(f"Error in trial checker: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def _check_user_trial(self, user: Dict):
        """Check trial period for specific user."""
        try:
            user_id = user.get("user_id")
            end_date = user.get("subscription_end_date")
            
            if not end_date:
                return
            
            end_date = datetime.fromisoformat(end_date)
            now = datetime.now()
            
            # Trial expired
            if now >= end_date:
                await self.db.update_subscription(
                    user_id=user_id,
                    status="inactive",
                    end_date=end_date
                )
                await self.bot.send_message(
                    chat_id=user_id,
                    text=TRIAL_EXPIRED,
                    reply_markup=get_subscription_keyboard()
                )
                return
            
            # Trial expiring soon
            days_left = (end_date - now).days
            if days_left <= self.notification_days:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=TRIAL_EXPIRING_SOON.format(days_left),
                    reply_markup=get_subscription_keyboard()
                )
        
        except Exception as e:
            logger.error(f"Error checking trial for user {user.get('user_id')}: {e}")

async def start_trial_checker(bot: Bot, db: Database, settings: Settings):
    """Start trial checker service."""
    checker = TrialChecker(bot, db, settings)
    asyncio.create_task(checker.check_trials())
