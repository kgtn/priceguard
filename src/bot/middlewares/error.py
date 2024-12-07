"""
Error handling middleware for the PriceGuard bot.
File: src/bot/middlewares/error.py
"""

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, ErrorEvent
from core.logging import get_logger

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
            # Log the error
            user_id = event.from_user.id if hasattr(event, 'from_user') else 'Unknown'
            logger.error(
                f"Error processing event from user {user_id}: {str(e)}",
                exc_info=True
            )

            # Send error message to user
            if isinstance(event, (Message, CallbackQuery)):
                try:
                    error_message = (
                        "Произошла ошибка при обработке вашего запроса. "
                        "Пожалуйста, попробуйте позже или обратитесь к администратору."
                    )
                    if isinstance(event, Message):
                        await event.answer(error_message)
                    else:
                        await event.message.answer(error_message)
                except Exception as notify_error:
                    logger.error(
                        f"Failed to send error notification to user {user_id}: {notify_error}"
                    )

            # Notify admin if critical error
            try:
                admin_id = data["config"].telegram.admin_user_id
                bot = data["bot"]
                await bot.send_message(
                    admin_id,
                    f"❗️ Critical Error:\nUser: {user_id}\nError: {str(e)}"
                )
            except Exception as admin_notify_error:
                logger.error(
                    f"Failed to notify admin about error: {admin_notify_error}"
                )
