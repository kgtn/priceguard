"""
Payment keyboard utilities for the PriceGuard bot.
File: src/bot/keyboards/payment.py
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_subscription_plans_keyboard() -> InlineKeyboardMarkup:
    """Get subscription plans keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text="1 месяц",
                callback_data="subscribe_1"
            ),
            InlineKeyboardButton(
                text="3 месяца",
                callback_data="subscribe_3"
            )
        ],
        [
            InlineKeyboardButton(
                text="6 месяцев",
                callback_data="subscribe_6"
            ),
            InlineKeyboardButton(
                text="12 месяцев",
                callback_data="subscribe_12"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_start"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
