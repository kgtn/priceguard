"""
Authentication middleware for the PriceGuard bot.
File: src/bot/middlewares/auth.py
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from core.database import Database
from core.logging import get_logger
from bot.utils.messages import SUBSCRIPTION_REQUIRED
from datetime import datetime

logger = get_logger(__name__)

# Commands allowed without active subscription
ALLOWED_COMMANDS = {
    '/start',
    '/help',
    '/status',
    '/support'
}

class AuthMiddleware(BaseMiddleware):
    def __init__(self, admin_id: int):
        self.admin_id = admin_id
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        try:
            start_time = datetime.now()
            # Get user from event
            user = event.from_user
            if not user:
                logger.warning("Event without user received")
                return

            # Get database instance from data
            db: Database = data.get("db")
            if not db:
                logger.error("Database instance not found in middleware data")
                return

            # Check if user exists in database
            user_data = await db.get_user(user.id)
            if not user_data:
                # Add new user if not exists
                try:
                    full_name = user.first_name
                    if user.last_name:
                        full_name += f" {user.last_name}"
                        
                    await db.add_user(
                        user_id=user.id,
                        username=user.username,
                        full_name=full_name
                    )
                    logger.info(f"New user registered: {user.id} (@{user.username})")
                except Exception as e:
                    logger.error(f"Failed to register new user {user.id}: {e}")
                    return

            # Add user info to handler data
            data["user"] = user_data
            data["is_admin"] = user.id == self.admin_id

            # Get fresh user data if it was just created
            if not user_data:
                user_data = await db.get_user(user.id)
                data["user"] = user_data

            # Check subscription status for non-admin users
            if not data["is_admin"]:
                status = user_data.get("subscription_status", "inactive")
                if status not in ["active", "trial"]:
                    # Allow only specific commands for users without active subscription
                    if isinstance(event, Message) and event.text:
                        command = event.text.split()[0].lower()
                        if command not in ALLOWED_COMMANDS:
                            await event.answer(
                                SUBSCRIPTION_REQUIRED,
                                parse_mode="HTML"
                            )
                            return
                    elif isinstance(event, CallbackQuery):
                        # Block callback queries for inactive users except specific ones
                        if not any(cmd in event.data for cmd in ["subscribe", "support", "help"]):
                            await event.answer(
                                "Требуется активная подписка",
                                show_alert=True
                            )
                            return

            result = await handler(event, data)
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log event processing
            event_type = "message" if isinstance(event, Message) else "callback"
            event_id = event.message_id if isinstance(event, Message) else event.id
            logger.info(
                f"Update id={event_id} handled in {duration:.0f} ms\n"
                f"Type: {event_type}"
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error processing event:\n"
                f"Type: {type(event).__name__}\n"
                f"Error: {str(e)}"
            )
            raise
