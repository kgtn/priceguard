"""
Main entry point for the PriceGuard Telegram bot.
File: src/main.py
"""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import load_config
from core.database import init_db
from core.logging import setup_logging, get_logger
from bot.handlers import register_all_handlers
from bot.middlewares import setup_middlewares
from bot.services import PromotionMonitor, NotificationService, MarketplaceClientFactory
from bot.routers import admin_router, user_router, payment_router

# Initialize logging
setup_logging()
logger = get_logger(__name__)

async def main():
    """Initialize and start the bot."""
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()

        # Initialize bot and dispatcher
        logger.info("Initializing bot...")
        bot = Bot(token=config.telegram.token, parse_mode=ParseMode.HTML)
        dp = Dispatcher(storage=MemoryStorage())

        # Initialize database
        logger.info("Initializing database...")
        db = await init_db(config.database.path)

        # Initialize marketplace client factory
        client_factory = MarketplaceClientFactory()

        # Initialize monitoring services
        monitor = PromotionMonitor(db, client_factory)
        notifications = NotificationService(bot, db)

        # Setup middlewares
        logger.info("Setting up middlewares...")
        setup_middlewares(dp, config)

        # Register all handlers
        logger.info("Registering handlers...")
        register_all_handlers(dp, config, db)
        dp.include_router(admin_router)
        dp.include_router(user_router)
        dp.include_router(payment_router)

        # Add bot instance to dispatcher data
        dp["bot"] = bot

        # Start monitoring
        await monitor.start()

        # Start polling
        logger.info("Starting bot...")
        try:
            await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        finally:
            await monitor.stop()
            await bot.session.close()
            logger.info("Closing database connection...")
            await db.close()

    except Exception as e:
        logger.critical(f"Failed to start bot: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical("Unexpected error occurred", exc_info=True)
