"""
Middleware initialization for the PriceGuard bot.
File: src/bot/middlewares/__init__.py
"""

from aiogram import Dispatcher
from core.config import Config
from .auth import AuthMiddleware
from .error import ErrorMiddleware
from .admin import AdminMiddleware

def setup_middlewares(dp: Dispatcher, config: Config) -> None:
    """
    Setup all middlewares for the bot.
    
    Args:
        dp: Dispatcher instance
        config: Bot configuration
    """
    # Add authentication middleware
    dp.message.middleware(AuthMiddleware(config.telegram.admin_user_id))
    dp.callback_query.middleware(AuthMiddleware(config.telegram.admin_user_id))

    # Add admin middleware
    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(AdminMiddleware())

    # Add error handling middleware
    dp.message.middleware(ErrorMiddleware())
    dp.callback_query.middleware(ErrorMiddleware())
    dp.errors.middleware(ErrorMiddleware())
