"""
Keyboard layouts for the PriceGuard bot.
File: src/bot/keyboards/user.py
"""

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_start_keyboard() -> InlineKeyboardMarkup:
    """Get start menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🤔 Как это работает?",
                callback_data="how_it_works"
            )
        ],
        [
            InlineKeyboardButton(
                text="🚀 Начать использование",
                callback_data="start_setup"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for settings command."""
    builder = InlineKeyboardBuilder()
    
    intervals = [
        ("1 час", "interval:1"),
        ("2 часа", "interval:2"),
        ("4 часа", "interval:4"),
        ("12 часов", "interval:12"),
        ("1 раз в сутки", "interval:24")
    ]
    for text, callback_data in intervals:
        builder.button(text=text, callback_data=callback_data)
    
    builder.button(text="◀️ Назад", callback_data="back_to_main")
    builder.adjust(2, 2, 1, 1)  # 2 кнопки в ряд для интервалов, 1 для кнопки "Назад"
    return builder.as_markup()

def get_api_key_keyboard() -> InlineKeyboardMarkup:
    """Get API key menu keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔑 Добавить ключ Ozon",
                callback_data="add_ozon_key"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔑 Добавить ключ Wildberries",
                callback_data="add_wb_key"
            )
        ],
        [
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="back_to_main"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Get subscription management keyboard."""
    buttons = [
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
                callback_data="back_to_start"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm")
    builder.button(text="❌ Отменить", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Get main menu keyboard."""
    builder = InlineKeyboardBuilder()
    
    # Main actions
    builder.button(text="📊 Мои акции", callback_data="my_promotions")
    builder.button(text="⚙️ Настройки", callback_data="settings")
    
    # Account management
    builder.button(text="🔑 API ключи", callback_data="api_keys")
    builder.button(text="💳 Подписка", callback_data="subscription")
    
    # Help
    builder.button(text="ℹ️ Помощь", callback_data="help")
    
    builder.adjust(2, 2, 1)  # 2 кнопки в первых двух рядах, 1 в последнем
    return builder.as_markup()
