"""
Admin keyboard utilities for the PriceGuard bot.
File: src/bot/keyboards/admin.py
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Get admin panel keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text="👥 Пользователи",
                callback_data="admin_users"
            ),
            InlineKeyboardButton(
                text="💳 Подписки",
                callback_data="admin_subscriptions"
            )
        ],
        [
            InlineKeyboardButton(
                text="📢 Рассылка",
                callback_data="admin_broadcast"
            ),
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 Логи",
                callback_data="admin_logs"
            ),
            InlineKeyboardButton(
                text="🔄 Проверка",
                callback_data="admin_force_check"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_users_keyboard() -> InlineKeyboardMarkup:
    """Get users management keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text="🔍 Поиск",
                callback_data="admin_search_user"
            ),
            InlineKeyboardButton(
                text="⚠️ Заблокировать",
                callback_data="admin_block_user"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="admin_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_subscriptions_keyboard() -> InlineKeyboardMarkup:
    """Get subscriptions management keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Активные",
                callback_data="admin_active_subs"
            ),
            InlineKeyboardButton(
                text="❌ Неактивные",
                callback_data="admin_inactive_subs"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад",
                callback_data="admin_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
