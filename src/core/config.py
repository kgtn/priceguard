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

@dataclass
class TelegramPaymentsConfig:
    provider_token: str

@dataclass
class Config:
    database: DatabaseConfig
    telegram: TelegramConfig
    telegram_payments: TelegramPaymentsConfig
    encryption_key: str

class Settings:
    """Application settings."""

    def __init__(self):
        """Initialize settings from environment variables."""
        self.bot_token = os.getenv("BOT_TOKEN")
        self.admin_user_id = os.getenv("ADMIN_USER_ID")
        self.database_path = os.getenv("DATABASE_PATH", "bot.db")
        
        # Payment settings
        self.payment_provider_token = os.getenv("PAYMENT_PROVIDER_TOKEN")

def load_config() -> Config:
    """Load configuration from environment variables."""
    load_dotenv()

    # Required environment variables
    required_vars = [
        'BOT_TOKEN',
        'ADMIN_USER_ID',
        'DATABASE_PATH',
        'PAYMENT_PROVIDER_TOKEN',
        'ENCRYPTION_KEY'
    ]

    # Check for missing environment variables
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    try:
        admin_user_id = int(os.getenv('ADMIN_USER_ID'))
    except ValueError:
        raise ValueError("ADMIN_USER_ID must be a valid integer")

    return Config(
        database=DatabaseConfig(
            path=os.getenv('DATABASE_PATH', 'bot.db')
        ),
        telegram=TelegramConfig(
            token=os.getenv('BOT_TOKEN'),
            admin_user_id=admin_user_id
        ),
        telegram_payments=TelegramPaymentsConfig(
            provider_token=os.getenv('PAYMENT_PROVIDER_TOKEN')
        ),
        encryption_key=os.getenv('ENCRYPTION_KEY')
    )
