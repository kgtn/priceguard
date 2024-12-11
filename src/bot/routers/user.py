"""
User router for the PriceGuard bot.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="user")

@router.message(Command("start"))
async def handle_start(message: Message):
    """Handle /start command."""
    await message.answer("Welcome to PriceGuard bot! Use /help to see available commands.")

@router.message(Command("help"))
async def handle_help(message: Message):
    """Handle /help command."""
    help_text = """
Available commands:
/start - Start the bot
/help - Show this help message
/menu - Open main menu
/settings - Configure check interval and other settings
/status - Check your subscription status
/subscribe - Get or manage subscription
/unsubscribe - Cancel your subscription
/add_api - Add marketplace API key
/delete_data - Delete all saved API keys
"""
    await message.answer(help_text)
