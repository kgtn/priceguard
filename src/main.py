"""
Main entry point for the PriceGuard bot.
"""

import asyncio
import logging
import os
import signal
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
from services.reminder import ReminderService
from bot.handlers import admin, user, payment, reminders
from bot.middlewares import setup_middlewares
from bot.routers import admin_router, user_router, payment_router
from services.payments.trial_checker import start_trial_checker
from services.payments.subscription_checker import start_subscription_checker

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Global variables for cleanup
monitor: Optional[PromotionMonitor] = None
reminder_service: Optional[ReminderService] = None
dp: Optional[Dispatcher] = None
bot: Optional[Bot] = None

async def shutdown(signal_type=None):
    """Cleanup resources on shutdown."""
    global monitor, dp, bot, reminder_service
    
    logger.info(f"Received signal: {signal_type}. Starting graceful shutdown...")
    
    # Stop the monitor if it's running
    if monitor:
        logger.info("Stopping promotion monitor...")
        await monitor.stop()
    
    # Close bot session
    if bot:
        logger.info("Closing bot session...")
        await bot.session.close()
    
    # Close dispatcher and storage
    if dp:
        logger.info("Closing dispatcher...")
        await dp.storage.close()
    
    logger.info("Shutdown complete.")

async def start_reminder_checker(reminder_service: ReminderService):
    """Start periodic reminder checks."""
    while True:
        try:
            await reminder_service.check_and_send_reminders()
        except Exception as e:
            logger.error(f"Error in reminder checker: {e}")
        
        # Проверяем каждые 6 часов
        await asyncio.sleep(6 * 60 * 60)

async def main():
    """Main function."""
    global monitor, dp, bot, reminder_service
    
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
            marketplace_factory=dp["marketplace_factory"],
            notification_service=notification_service
        )
        dp["monitor"] = monitor

        # Initialize reminder service
        reminder_service = ReminderService(
            bot=bot,
            db=dp["db"],
            marketplace_factory=dp["marketplace_factory"]
        )
        dp["reminder_service"] = reminder_service

        # Setup middlewares
        setup_middlewares(dp, config)

        # Register routers
        dp.include_router(admin.router)
        dp.include_router(user.router)
        dp.include_router(payment.router)
        dp.include_router(reminders.router)

        # Setup commands
        await user.setup_bot_commands(bot)

        # Start background tasks
        logger.info("Starting background tasks...")
        asyncio.create_task(monitor.start())
        asyncio.create_task(start_trial_checker(bot=bot, db=dp["db"], settings=dp["settings"]))
        asyncio.create_task(start_subscription_checker(bot=bot, db=dp["db"], settings=dp["settings"]))
        asyncio.create_task(start_reminder_checker(reminder_service))

        # Register signal handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            asyncio.get_event_loop().add_signal_handler(sig, lambda: asyncio.create_task(shutdown(sig)))

        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise
    finally:
        await shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
