"""
Authentication middleware for the PriceGuard bot.
File: src/bot/middlewares/auth.py
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from core.database import Database
from core.logging import get_logger

logger = get_logger(__name__)

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

        # Continue processing
        return await handler(event, data)
