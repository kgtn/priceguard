"""
Main entry point for the PriceGuard bot.
"""

import asyncio
import logging
import os
from typing import Dict, Optional

from aiogram import Bot, Dispatcher, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from dotenv import load_dotenv

from core.config import load_config
from core.database import Database
from core.logging import setup_logging, get_logger
from services.monitoring.monitor import PromotionMonitor
from services.monitoring.notifications import NotificationService
from services.marketplaces.factory import MarketplaceFactory
from bot.handlers import admin, user, payment
from bot.middlewares import setup_middlewares
from bot.routers import admin_router, user_router, payment_router

# Initialize logging
setup_logging()
logger = get_logger(__name__)

async def main():
    """Main function."""
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()

        # Initialize bot and dispatcher
        logger.info("Initializing bot...")
        bot = Bot(token=config.telegram.token)
        dp = Dispatcher(storage=MemoryStorage())
        
        # Inject dependencies
        dp["settings"] = config
        dp["db"] = Database(config.database.path)
        await dp["db"].init()
        dp["marketplace_factory"] = MarketplaceFactory(encryption_key=config.encryption_key)

        # Initialize notification service
        notification_service = NotificationService(bot=bot, db=dp["db"])

        # Initialize promotion monitor
        monitor = PromotionMonitor(
            db=dp["db"],
            marketplace_factory=dp["marketplace_factory"]
        )

        # Setup middlewares
        setup_middlewares(dp, config)

        # Register routers
        dp.include_router(admin.router)
        dp.include_router(user.router)
        dp.include_router(payment.router)

        # Setup commands
        await user.setup_bot_commands(bot)

        # Start promotion monitor
        await monitor.start()

        # Start polling
        logger.info("Starting bot...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.exception("Error in main function: %s", str(e))
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
