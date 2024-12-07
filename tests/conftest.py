"""
Pytest configuration file.
"""

import asyncio
import base64
import os
from typing import AsyncGenerator, Generator

import pytest
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from cryptography.fernet import Fernet

from core.config import Settings
from core.database import Database, init_db
from services.marketplaces.factory import MarketplaceFactory
from services.monitoring.monitor import PromotionMonitor
from services.monitoring.notifications import NotificationService

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    os.environ["BOT_TOKEN"] = "test_token"
    os.environ["ADMIN_USER_ID"] = "123456789"
    os.environ["DATABASE_PATH"] = ":memory:"
    os.environ["PAYMENT_PROVIDER_TOKEN"] = "test_payment_token"
    # Generate a valid Fernet key
    encryption_key = Fernet.generate_key().decode()
    os.environ["ENCRYPTION_KEY"] = encryption_key
    return Settings()

@pytest.fixture
async def bot() -> AsyncGenerator[Bot, None]:
    """Create test bot."""
    bot = Bot(token="123456789:ABCdefGHIjklMNOpqrsTUVwxyz")  # Test token in correct format
    yield bot
    await bot.session.close()

@pytest.fixture
async def dispatcher() -> AsyncGenerator[Dispatcher, None]:
    """Create test dispatcher instance."""
    dp = Dispatcher(storage=MemoryStorage())
    yield dp
    await dp.storage.close()

@pytest.fixture
async def marketplace_factory(settings: Settings) -> MarketplaceFactory:
    """Create test marketplace factory."""
    return MarketplaceFactory(settings.encryption_key)

@pytest.fixture
async def database() -> AsyncGenerator[Database, None]:
    """Create test database."""
    db = Database(":memory:")
    await db.connect()
    yield db
    await db.disconnect()

@pytest.fixture
async def notification_service(bot: Bot) -> AsyncGenerator[NotificationService, None]:
    """Create test notification service."""
    service = NotificationService(bot)
    yield service

@pytest.fixture
async def monitor(marketplace_factory: MarketplaceFactory, notification_service: NotificationService, database: Database) -> AsyncGenerator[PromotionMonitor, None]:
    """Create test promotion monitor."""
    monitor = PromotionMonitor(marketplace_factory, notification_service, database)
    await monitor.start()
    yield monitor
    await monitor.stop()
