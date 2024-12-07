"""
Admin command handlers for the PriceGuard bot.
File: src/bot/handlers/admin.py
"""

from datetime import datetime
from typing import List

from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.config import Settings
from core.database import Database
from bot.keyboards.admin import (
    get_admin_keyboard,
    get_users_keyboard,
    get_subscriptions_keyboard
)
from bot.utils.messages import format_user_info, format_subscription_info

router = Router()

class AdminStates(StatesGroup):
    """Admin FSM states."""
    waiting_for_broadcast = State()
    waiting_for_force_check = State()

async def is_admin(user_id: int, settings: Settings) -> bool:
    """Check if user is admin."""
    return str(user_id) == settings.admin_user_id

@router.message(Command("admin"))
async def cmd_admin(message: types.Message, settings: Settings):
    """Admin menu handler."""
    if not await is_admin(message.from_user.id, settings):
        await message.answer("❌ У вас нет прав администратора")
        return

    await message.answer(
        "👨‍💼 Панель администратора",
        reply_markup=get_admin_keyboard()
    )

@router.message(Command("users"))
async def cmd_users(message: types.Message, db: Database, settings: Settings):
    """Users list handler."""
    if not await is_admin(message.from_user.id, settings):
        await message.answer("❌ У вас нет прав администратора")
        return

    users = await db.get_all_users()
    if not users:
        await message.answer("👥 Пользователей пока нет")
        return

    text = "👥 Список пользователей:\n\n"
    for user in users:
        text += format_user_info(user) + "\n"

    await message.answer(
        text,
        reply_markup=get_users_keyboard()
    )

@router.message(Command("subscriptions"))
async def cmd_subscriptions(
    message: types.Message,
    db: Database,
    settings: Settings
):
    """Subscriptions list handler."""
    if not await is_admin(message.from_user.id, settings):
        await message.answer("❌ У вас нет прав администратора")
        return

    subscriptions = await db.get_all_subscriptions()
    if not subscriptions:
        await message.answer("💳 Подписок пока нет")
        return

    text = "💳 Список подписок:\n\n"
    for sub in subscriptions:
        text += format_subscription_info(sub) + "\n"

    await message.answer(
        text,
        reply_markup=get_subscriptions_keyboard()
    )

@router.message(Command("logs"))
async def cmd_logs(message: types.Message, settings: Settings):
    """Send bot logs."""
    if not await is_admin(message.from_user.id, settings):
        await message.answer("❌ У вас нет прав администратора")
        return

    try:
        with open("bot.log", "r") as f:
            logs = f.read()[-4000:]  # Last 4000 chars
        await message.answer_document(
            types.BufferedInputFile(
                logs.encode(),
                filename=f"bot_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при чтении логов: {str(e)}")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, state: FSMContext, settings: Settings):
    """Start broadcast message handler."""
    if not await is_admin(message.from_user.id, settings):
        await message.answer("❌ У вас нет прав администратора")
        return

    await state.set_state(AdminStates.waiting_for_broadcast)
    await message.answer(
        "📢 Отправьте сообщение для рассылки всем пользователям\n"
        "Для отмены используйте /cancel"
    )

@router.message(Command("force_check"))
async def cmd_force_check(
    message: types.Message,
    state: FSMContext,
    settings: Settings
):
    """Force check promotions handler."""
    if not await is_admin(message.from_user.id, settings):
        await message.answer("❌ У вас нет прав администратора")
        return

    await state.set_state(AdminStates.waiting_for_force_check)
    await message.answer(
        "🔄 Отправьте ID пользователя для принудительной проверки акций\n"
        "Для отмены используйте /cancel"
    )

@router.message(AdminStates.waiting_for_broadcast)
async def process_broadcast(
    message: types.Message,
    state: FSMContext,
    db: Database
):
    """Process broadcast message."""
    users = await db.get_all_users()
    sent_count = 0
    failed_count = 0

    for user in users:
        try:
            await message.copy_to(user.id)
            sent_count += 1
        except Exception:
            failed_count += 1

    await state.clear()
    await message.answer(
        f"📢 Рассылка завершена\n"
        f"✅ Успешно: {sent_count}\n"
        f"❌ Ошибок: {failed_count}"
    )

@router.message(AdminStates.waiting_for_force_check)
async def process_force_check(
    message: types.Message,
    state: FSMContext,
    db: Database
):
    """Process force check request."""
    try:
        user_id = int(message.text)
        user = await db.get_user(user_id)
        if not user:
            await message.answer("❌ Пользователь не найден")
            return

        # TODO: Implement force check logic
        await message.answer(
            f"✅ Запущена проверка акций для пользователя {user_id}"
        )
    except ValueError:
        await message.answer("❌ Некорректный ID пользователя")
    finally:
        await state.clear()
