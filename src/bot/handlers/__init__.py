"""
Handler registration for the PriceGuard bot.
File: src/bot/handlers/__init__.py
"""

from aiogram import Dispatcher
from core.config import Config
from core.database import Database
from .user import router as user_router
from .admin import router as admin_router

def register_all_handlers(dp: Dispatcher, config: Config, db: Database) -> None:
    """
    Register all handlers for the bot.
    
    Args:
        dp: Dispatcher instance
        config: Bot configuration
        db: Database instance
    """
    # Include routers
    dp.include_router(admin_router)  # Admin handlers first
    dp.include_router(user_router)   # User handlers second

    # Inject dependencies
    dp["config"] = config
    dp["db"] = db
