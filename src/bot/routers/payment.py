"""
Payment router for the PriceGuard bot.
"""

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="payment")

@router.message(Command("subscribe"))
async def handle_subscribe(message: Message):
    """Handle /subscribe command."""
    await message.answer("Subscription feature is not implemented yet.")
