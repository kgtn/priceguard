"""
Payment-related keyboards.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Get subscription management keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="💳 Оплатить подписку",
                callback_data="pay_subscription"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Отменить подписку",
                callback_data="cancel_subscription"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_subscription_plans_keyboard() -> InlineKeyboardMarkup:
    """Get subscription plans keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="1 месяц - 299₽",
                callback_data="subscribe_1"
            )
        ],
        [
            InlineKeyboardButton(
                text="3 месяца - 799₽",
                callback_data="subscribe_3"
            )
        ],
        [
            InlineKeyboardButton(
                text="6 месяцев - 1499₽",
                callback_data="subscribe_6"
            )
        ],
        [
            InlineKeyboardButton(
                text="12 месяцев - 2699₽",
                callback_data="subscribe_12"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
