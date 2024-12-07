"""
Pytest configuration file.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage

from core.config import Settings
from core.database import Database, init_db
from services.marketplaces.factory import MarketplaceClientFactory
from services.monitoring.monitor import PromotionMonitor
from services.monitoring.notifications import NotificationService

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def settings() -> Settings:
    """Get test settings."""
    os.environ["BOT_TOKEN"] = "test_token"
    os.environ["ADMIN_USER_ID"] = "123456789"
    os.environ["DATABASE_PATH"] = ":memory:"
    os.environ["PAYMENT_PROVIDER_TOKEN"] = "test_payment_token"
    os.environ["ENCRYPTION_KEY"] = "test_key"
    return Settings()

@pytest.fixture(scope="session")
async def database(settings: Settings) -> AsyncGenerator[Database, None]:
    """Create test database."""
    db = await init_db(settings.database_path)
    yield db
    await db.close()

@pytest.fixture(scope="session")
async def bot(settings: Settings) -> AsyncGenerator[Bot, None]:
    """Create test bot instance."""
    session = AiohttpSession()
    bot = Bot(settings.bot_token, session=session)
    yield bot
    await bot.session.close()

@pytest.fixture(scope="function")
async def dispatcher() -> AsyncGenerator[Dispatcher, None]:
    """Create test dispatcher instance."""
    dp = Dispatcher(storage=MemoryStorage())
    yield dp
    await dp.storage.close()

@pytest.fixture(scope="session")
def client_factory() -> MarketplaceClientFactory:
    """Create test marketplace client factory."""
    return MarketplaceClientFactory()

@pytest.fixture(scope="function")
async def monitor(
    database: Database,
    client_factory: MarketplaceClientFactory
) -> AsyncGenerator[PromotionMonitor, None]:
    """Create test promotion monitor."""
    monitor = PromotionMonitor(database, client_factory, check_interval=1)
    yield monitor
    await monitor.stop()

@pytest.fixture(scope="function")
def notification_service(
    bot: Bot,
    database: Database
) -> NotificationService:
    """Create test notification service."""
    return NotificationService(bot, database)
