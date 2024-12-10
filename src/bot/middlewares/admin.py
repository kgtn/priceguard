"""
Admin middleware for the PriceGuard bot.
File: src/bot/middlewares/admin.py
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from core.config import Settings
from bot.handlers.admin import is_admin

class AdminMiddleware(BaseMiddleware):
    """Middleware for checking admin rights."""
    
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Проверяем, что обработчик находится в модуле admin
        if not handler.__module__.endswith('admin'):
            return await handler(event, data)
            
        # Получаем настройки
        settings: Settings = data.get("settings")
        if not settings:
            return await handler(event, data)
            
        # Проверяем права администратора
        user_id = event.from_user.id if event.from_user else None
        if not user_id or not await is_admin(user_id, settings):
            if isinstance(event, CallbackQuery):
                await event.answer("❌ У вас нет прав администратора", show_alert=True)
            else:
                await event.answer("❌ У вас нет прав администратора")
            return
            
        return await handler(event, data)
