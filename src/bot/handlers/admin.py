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
    get_subscriptions_keyboard,
    get_users_pagination_keyboard
)
from bot.utils.messages import format_user_info, format_subscription_info
from services.monitoring.monitor import PromotionMonitor  # noqa: F401

router = Router()

class AdminStates(StatesGroup):
    """Admin FSM states."""
    waiting_for_broadcast = State()
    waiting_for_force_check = State()

async def is_admin(user_id: int, settings: Settings) -> bool:
    """Check if user is admin."""
    return str(user_id) == str(settings.telegram.admin_user_id)

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

@router.callback_query(F.data == "admin_users")
async def on_admin_users(callback: types.CallbackQuery, db: Database, settings: Settings):
    """Handle admin_users callback."""
    users_data = await db.get_all_users(page=1)
    users = users_data["users"]
    
    message = "👥 Список пользователей:\n\n"
    message += "\n\n".join([format_user_info(user) for user in users])
    message += f"\n\nВсего пользователей: {users_data['total_users']}"
    
    keyboard = get_users_pagination_keyboard(
        current_page=users_data["current_page"],
        total_pages=users_data["total_pages"]
    )
    
    await callback.message.edit_text(
        text=message,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("users_page:"))
async def handle_users_page(callback: types.CallbackQuery, db: Database):
    """Handle users page navigation."""
    page = int(callback.data.split(":")[1])
    
    users_data = await db.get_all_users(page=page)
    users = users_data["users"]
    
    message = "👥 Список пользователей:\n\n"
    message += "\n\n".join([format_user_info(user) for user in users])
    message += f"\n\nВсего пользователей: {users_data['total_users']}"
    
    keyboard = get_users_pagination_keyboard(
        current_page=users_data["current_page"],
        total_pages=users_data["total_pages"]
    )
    
    await callback.message.edit_text(
        text=message,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(Command("users"))
async def cmd_users(message: types.Message, db: Database, settings: Settings):
    """Show list of users."""
    if not await is_admin(message.from_user.id, settings):
        await message.answer("❌ У вас нет прав администратора")
        return

    users_data = await db.get_all_users(page=1)
    users = users_data["users"]
    
    message_text = "👥 Список пользователей:\n\n"
    message_text += "\n\n".join([format_user_info(user) for user in users])
    message_text += f"\n\nВсего пользователей: {users_data['total_users']}"
    
    keyboard = get_users_pagination_keyboard(
        current_page=users_data["current_page"],
        total_pages=users_data["total_pages"]
    )
    
    await message.answer(
        text=message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
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
        reply_markup=get_subscriptions_keyboard(),
        parse_mode="Markdown"
    )

@router.message(Command("logs"))
async def cmd_logs(message: types.Message, settings: Settings):
    """Send bot logs."""
    try:
        # Отправляем оба файла логов
        for log_file in ["logs/errors.log", "logs/priceguard.log"]:
            try:
                with open(log_file, "r") as f:
                    logs = f.read()[-4000:]  # Last 4000 chars
                await message.answer_document(
                    types.BufferedInputFile(
                        logs.encode(),
                        filename=f"{log_file.split('/')[-1]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    )
                )
            except Exception as e:
                await message.answer(f"❌ Ошибка при чтении {log_file}: {str(e)}")
    except Exception as e:
        await message.answer("❌ Произошла общая ошибка при обработке логов")

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
    users_data = await db.get_all_users()
    users = users_data["users"]  # Получаем список пользователей из словаря
    sent_count = 0
    failed_count = 0
    error_details = []

    for user in users:
        try:
            # Проверяем, что у пользователя есть валидный ID в словаре
            user_id = user.get('user_id')  # Используем 'user_id' вместо 'id'
            if not user_id:
                raise ValueError(f"Missing user_id in user data: {user}")
                
            # Пробуем отправить сообщение
            await message.copy_to(chat_id=user_id)
            sent_count += 1
            
        except Exception as e:
            failed_count += 1
            error_details.append(f"User {user.get('user_id', 'Unknown')}: {str(e)}")
            print(f"Broadcast error for user {user.get('user_id', 'Unknown')}: {str(e)}")  # Для отладки

    # Формируем детальный отчет
    report = f"📢 Рассылка завершена\n✅ Успешно: {sent_count}\n❌ Ошибок: {failed_count}"
    
    # Если были ошибки, добавляем детали в отдельном сообщении
    if error_details:
        error_report = "Детали ошибок:\n" + "\n".join(error_details[:10])  # Первые 10 ошибок
        if len(error_details) > 10:
            error_report += f"\n... и еще {len(error_details) - 10} ошибок"
        await message.answer(error_report)

    await state.clear()
    await message.answer(report)

@router.message(AdminStates.waiting_for_force_check)
async def process_force_check(
    message: types.Message,
    state: FSMContext,
    db: Database,
    monitor: PromotionMonitor = None
):
    """Process force check request."""
    try:
        user_id = int(message.text)
        user = await db.get_user(user_id)
        if not user:
            await message.answer("❌ Пользователь не найден")
            return

        await message.answer(f"🔄 Запускаю проверку акций для пользователя {user_id}")
        changes = await monitor.force_check(user_id)
        
        # Проверяем есть ли реальные изменения
        has_changes = False
        for marketplace, marketplace_changes in changes.items():
            if any(marketplace_changes.values()):  # Проверяем есть ли что-то в new, ended или changed
                has_changes = True
                break
        
        if has_changes:
            await message.answer("✅ Проверка завершена. Найдены изменения в акциях.")
        else:
            await message.answer("✅ Проверка завершена. Изменений в акциях не найдено.")
            
    except ValueError:
        await message.answer("❌ Некорректный ID пользователя")
    except Exception as e:
        await message.answer(f"❌ Ошибка при проверке акций: {str(e)}")
    finally:
        await state.clear()

# Callback handlers
@router.callback_query(F.data == "admin_subscriptions")
async def on_admin_subscriptions(callback: types.CallbackQuery, settings: Settings):
    """Handle admin_subscriptions callback."""
    await callback.message.edit_text(
        "💳 Управление подписками",
        reply_markup=get_subscriptions_keyboard()
    )

@router.callback_query(F.data == "admin_broadcast")
async def on_admin_broadcast(callback: types.CallbackQuery, state: FSMContext, settings: Settings):
    """Handle admin_broadcast callback."""
    await state.set_state(AdminStates.waiting_for_broadcast)
    await callback.message.edit_text(
        "📢 Введите текст для рассылки:",
        reply_markup=None
    )

@router.callback_query(F.data == "admin_stats")
async def on_admin_stats(callback: types.CallbackQuery, db: Database, settings: Settings):
    """Handle admin_stats callback."""
    # TODO: Implement statistics gathering
    await callback.answer("🚧 Функция в разработке", show_alert=True)

@router.callback_query(F.data == "admin_logs")
async def on_admin_logs(callback: types.CallbackQuery, settings: Settings):
    """Handle admin_logs callback."""
    await callback.message.delete()
    await cmd_logs(callback.message, settings)

@router.callback_query(F.data == "admin_force_check")
async def on_admin_force_check(callback: types.CallbackQuery, state: FSMContext, settings: Settings):
    """Handle admin_force_check callback."""
    await state.set_state(AdminStates.waiting_for_force_check)
    await callback.message.edit_text(
        "🔄 Введите ID пользователя для проверки акций:",
        reply_markup=None
    )

@router.callback_query(F.data == "admin_active_subs")
async def on_admin_active_subs(callback: types.CallbackQuery, db: Database, settings: Settings):
    """Handle admin_active_subs callback."""
    subscriptions = await db.get_active_subscriptions()
    if not subscriptions:
        text = "❌ Активных подписок не найдено"
    else:
        text = "✅ Активные подписки:\n\n"
        for sub in subscriptions:
            user = await db.get_user(sub["user_id"])
            if user:
                text += f"👤 ID: {user['user_id']}\n"
                text += f"📅 До: {datetime.fromisoformat(sub['end_date']).strftime('%d.%m.%Y')}\n"
                text += f"⏱ Интервал проверки: {sub['check_interval']} ч.\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_subscriptions_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_inactive_subs")
async def on_admin_inactive_subs(callback: types.CallbackQuery, db: Database, settings: Settings):
    """Handle admin_inactive_subs callback."""
    async with db.db.execute(
        """
        SELECT s.*, u.check_interval
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        WHERE u.subscription_status = 'inactive'
        OR s.end_date <= CURRENT_TIMESTAMP
        """
    ) as cursor:
        rows = await cursor.fetchall()
        subscriptions = [
            {
                "user_id": row[1],
                "payment_id": row[2],
                "start_date": row[3],
                "end_date": row[4],
                "check_interval": row[5]
            }
            for row in rows
        ]

    if not subscriptions:
        text = "✅ Неактивных подписок не найдено"
    else:
        text = "❌ Неактивные подписки:\n\n"
        for sub in subscriptions:
            user = await db.get_user(sub["user_id"])
            if user:
                text += f"👤 ID: {user['user_id']}\n"
                text += f"📅 Истекла: {datetime.fromisoformat(sub['end_date']).strftime('%d.%m.%Y')}\n"
                text += f"⏱ Интервал проверки: {sub['check_interval']} ч.\n\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_subscriptions_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_back")
async def on_admin_back(callback: types.CallbackQuery, settings: Settings):
    """Handle admin_back callback."""
    await callback.message.edit_text(
        "🤖 Панель администратора",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()
