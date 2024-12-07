"""
Admin router for the PriceGuard bot.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="admin")

@router.message(Command("stats"))
async def handle_stats(message: Message):
    """Handle /stats command."""
    await message.answer("Stats command is not implemented yet.")
