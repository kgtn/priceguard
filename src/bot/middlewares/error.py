"""
Error handling middleware for the PriceGuard bot.
File: src/bot/middlewares/error.py
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, ErrorEvent
from core.logging import get_logger
from datetime import datetime

logger = get_logger(__name__)

class ErrorMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery | ErrorEvent,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            # Get user info
            user_id = event.from_user.id if hasattr(event, 'from_user') else 'Unknown'
            username = f"@{event.from_user.username}" if hasattr(event, 'from_user') and event.from_user.username else "нет username"
            
            # Get context info
            context = "неизвестный контекст"
            if isinstance(event, Message):
                context = f"команда: {event.text}" if event.text else "сообщение без текста"
            elif isinstance(event, CallbackQuery):
                context = f"кнопка: {event.data}" if event.data else "callback без данных"
            
            # Format error message
            error_text = (
                f"❗️ Ошибка в боте:\n\n"
                f"👤 Пользователь: {username}\n"
                f"ID: {user_id}\n\n"
                f"📝 Контекст: {context}\n\n"
                f"⚠️ Ошибка: {str(e)}\n"
                f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Log the error
            logger.error(
                f"Error processing event from user {user_id} ({username}): {str(e)}",
                exc_info=True
            )

            # Send error message to user
            if isinstance(event, (Message, CallbackQuery)):
                try:
                    error_message = (
                        "Произошла ошибка при обработке вашего запроса. "
                        "Пожалуйста, попробуйте позже или обратитесь к администратору @kagitin"
                    )
                    if isinstance(event, Message):
                        await event.answer(error_message)
                    else:
                        await event.message.answer(error_message)
                except Exception as notify_error:
                    logger.error(
                        f"Failed to send error notification to user {user_id}: {notify_error}"
                    )

            # Notify admin
            try:
                settings = data.get("settings")  
                if settings and hasattr(settings, "telegram"):
                    admin_id = settings.telegram.admin_user_id
                    bot = data.get("bot")
                    if bot and admin_id:
                        await bot.send_message(
                            admin_id,
                            error_text,
                            parse_mode="HTML"
                        )
            except Exception as admin_notify_error:
                logger.error(
                    f"Failed to notify admin about error: {admin_notify_error}"
                )
