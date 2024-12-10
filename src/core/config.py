"""
Configuration management for the PriceGuard bot.
File: src/core/config.py
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

@dataclass
class DatabaseConfig:
    path: str

@dataclass
class TelegramConfig:
    token: str
    admin_user_id: int
    payment_provider_token: str  # Добавляем токен провайдера платежей

@dataclass
class Config:
    database: DatabaseConfig
    telegram: TelegramConfig
    encryption_key: str
    subscription_price: int

class Settings:
    """Application settings."""

    def __init__(self):
        """Initialize settings from environment variables."""
        self.bot_token = os.getenv("BOT_TOKEN")
        self.admin_user_id = int(os.getenv("ADMIN_USER_ID"))
        self.database_path = os.getenv("DATABASE_PATH", "bot.db")
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        
        # Payment settings
        self.payment_provider_token = os.getenv("PAYMENT_PROVIDER_TOKEN")
        self.subscription_price = int(os.getenv("SUBSCRIPTION_PRICE", "100"))  # Default 100 RUB

def load_config() -> Config:
    """Load configuration from environment variables."""
    # Load .env file from the correct path
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(env_path)
    
    settings = Settings()
    
    if not all([settings.bot_token, settings.admin_user_id, settings.payment_provider_token]):
        raise ValueError("Missing required environment variables")
    
    return Config(
        database=DatabaseConfig(
            path=settings.database_path
        ),
        telegram=TelegramConfig(
            token=settings.bot_token,
            admin_user_id=settings.admin_user_id,
            payment_provider_token=settings.payment_provider_token
        ),
        encryption_key=settings.encryption_key,
        subscription_price=settings.subscription_price
    )

# Initialize config
config = load_config()

# Export constants
BOT_TOKEN = config.telegram.token
ADMIN_USER_ID = config.telegram.admin_user_id
DATABASE_PATH = config.database.path
ENCRYPTION_KEY = config.encryption_key
SUBSCRIPTION_PRICE = config.subscription_price
PAYMENT_PROVIDER_TOKEN = config.telegram.payment_provider_token
