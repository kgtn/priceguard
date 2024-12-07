"""
Main entry point for the PriceGuard bot.
"""

import asyncio
import logging
import os
from typing import Dict, Optional

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from dotenv import load_dotenv

from core.config import load_config
from core.database import Database
from core.logging import setup_logging, get_logger
from services.monitoring.monitor import PromotionMonitor
from services.monitoring.notifications import NotificationService
from services.marketplaces.factory import MarketplaceFactory
from bot.handlers import register_all_handlers
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
        bot = Bot(token=config.telegram.token, parse_mode="HTML")
        dp = Dispatcher(storage=MemoryStorage())

        # Initialize database
        logger.info("Initializing database...")
        db = await Database(config.database.path)

        # Initialize marketplace factory
        marketplace_factory = MarketplaceFactory(encryption_key=config.encryption.key)

        # Initialize notification service
        notification_service = NotificationService(bot=bot, database=db)

        # Initialize promotion monitor
        monitor = PromotionMonitor(
            database=db,
            notification_service=notification_service,
            client_factory=marketplace_factory
        )

        # Setup middlewares
        setup_middlewares(dp, db)

        # Register routers
        dp.include_router(admin_router)
        dp.include_router(payment_router)
        dp.include_router(user_router)

        # Register handlers
        register_all_handlers(dp)

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
