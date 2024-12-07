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
/add_marketplace - Add a marketplace (Ozon or Wildberries)
/list_marketplaces - List your connected marketplaces
/add_product - Add a product to monitor
/list_products - List your monitored products
/remove_product - Remove a product from monitoring
"""
    await message.answer(help_text)
