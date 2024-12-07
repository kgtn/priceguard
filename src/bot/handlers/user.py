"""
User command handlers for the PriceGuard bot.
File: src/bot/handlers/user.py
"""

from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core.database import Database
from services.marketplaces.factory import MarketplaceFactory
from ..utils.messages import (
    format_start_message,
    format_help_message,
    format_subscription_status,
    format_api_instructions
)
from ..keyboards.user import (
    get_start_keyboard,
    get_settings_keyboard,
    get_api_key_keyboard,
    get_subscription_keyboard,
    get_confirmation_keyboard,
    get_main_menu_keyboard
)

router = Router()

class UserStates(StatesGroup):
    """User state machine for conversation handling."""
    waiting_for_ozon_api = State()
    waiting_for_wb_api = State()
    waiting_for_interval = State()
    waiting_for_confirmation = State()

@router.message(Command("start"))
async def cmd_start(message: Message, db: Database) -> None:
    """Handle /start command."""
    user_data = await db.get_user(message.from_user.id)
    is_registered = user_data is not None
    
    if not is_registered:
        await db.add_user(message.from_user.id)
    
    await message.answer(
        format_start_message(is_registered),
        reply_markup=get_start_keyboard()
    )
    
    # Show main menu after welcome message
    await message.answer(
        "🤖 Главное меню PriceGuard\n\n"
        "Выберите нужное действие:",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    await message.answer(format_help_message())

@router.message(Command("status"))
async def cmd_status(message: Message, db: Database) -> None:
    """Handle /status command."""
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
        
    await message.answer(
        format_subscription_status(
            status=user_data["subscription_status"],
            end_date=user_data["subscription_end_date"],
            check_interval=user_data["check_interval"]
        ),
        reply_markup=get_subscription_keyboard()
    )

@router.message(Command("settings"))
async def cmd_settings(message: Message, db: Database) -> None:
    """Handle /settings command."""
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
        
    await message.answer(
        "⚙️ Выберите интервал проверки акций:",
        reply_markup=get_settings_keyboard()
    )

@router.message(Command("add_api"))
async def cmd_add_api(message: Message, db: Database) -> None:
    """Handle /add_api command."""
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
        
    await message.answer(
        "🔑 Выберите маркетплейс для добавления API ключа:",
        reply_markup=get_api_key_keyboard()
    )

@router.callback_query(F.data == "add_ozon_api")
async def process_add_ozon_api(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle Ozon API key addition."""
    await callback.message.edit_text(
        format_api_instructions("ozon"),
        reply_markup=None
    )
    await state.set_state(UserStates.waiting_for_ozon_api)
    await callback.answer()

@router.callback_query(F.data == "add_wb_api")
async def process_add_wb_api(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle Wildberries API key addition."""
    await callback.message.edit_text(
        format_api_instructions("wildberries"),
        reply_markup=None
    )
    await state.set_state(UserStates.waiting_for_wb_api)
    await callback.answer()

@router.message(UserStates.waiting_for_ozon_api)
async def process_ozon_api_key(
    message: Message,
    state: FSMContext,
    db: Database,
    marketplace_factory: MarketplaceFactory
) -> None:
    """Process Ozon API key submission."""
    try:
        # Parse client_id and api_key
        client_id, api_key = message.text.strip().split(":")
        
        await message.answer("🔄 Проверяю API ключ...")
        
        # Encrypt API key first
        encrypted_key = marketplace_factory.encrypt_api_key(api_key)
        
        # Validate API key
        async with await marketplace_factory.create_client(
            "ozon", encrypted_key, client_id
        ) as client:
            is_valid = await client.validate_api_key()
            
        if is_valid:
            # Save encrypted API key
            await db.update_api_keys(
                message.from_user.id,
                ozon_key=encrypted_key
            )
            
            await message.answer(
                "✅ API ключ Ozon успешно добавлен!\n\n"
                "Теперь вы можете:\n"
                "1️⃣ Добавить API ключ Wildberries в разделе 🔑 API ключи\n"
                "2️⃣ Настроить интервал проверки в разделе ⏰ Интервал проверки\n"
                "3️⃣ Начать отслеживать акции в разделе 📊 Мои акции",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await message.answer(
                "❌ Неверный API ключ\n\n"
                "Пожалуйста, проверьте правильность введенных данных и попробуйте снова.\n"
                "Формат: CLIENT_ID:API_KEY",
                reply_markup=get_main_menu_keyboard()
            )
    except ValueError:
        await message.answer(
            "❌ Неверный формат. Отправьте в формате: CLIENT_ID:API_KEY",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu_keyboard()
        )
        
    finally:
        await state.clear()

@router.message(UserStates.waiting_for_wb_api)
async def process_wb_api_key(
    message: Message,
    state: FSMContext,
    db: Database,
    marketplace_factory: MarketplaceFactory
) -> None:
    """Process Wildberries API key submission."""
    try:
        api_key = message.text.strip()
        
        # Validate API key
        async with await marketplace_factory.create_client(
            "wildberries",
            api_key
        ) as client:
            is_valid = await client.validate_api_key()
            
        if is_valid:
            # Encrypt and save API key
            encrypted_key = marketplace_factory.encrypt_api_key(api_key)
            await db.update_api_keys(
                message.from_user.id,
                wildberries_key=encrypted_key
            )
            
            await message.answer("✅ API ключ Wildberries успешно добавлен!")
        else:
            await message.answer("❌ Неверный API ключ")
            
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
        
    finally:
        await state.clear()

@router.callback_query(F.data.startswith("interval:"))
async def process_interval_change(
    callback: CallbackQuery,
    db: Database
) -> None:
    """Handle check interval change."""
    hours = int(callback.data.split(":")[1])
    
    try:
        # Update user's check interval
        await db.update_check_interval(callback.from_user.id, hours * 3600)
        await callback.message.edit_text(
            f"✅ Интервал проверки изменен на {hours} час(ов)"
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
        
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback: CallbackQuery) -> None:
    """Handle back to main menu."""
    await callback.message.edit_text(
        format_start_message(True),
        reply_markup=get_start_keyboard()
    )
    await callback.answer()

@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message, db: Database) -> None:
    """Handle /unsubscribe command."""
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
        
    await message.answer(
        "❗️ Вы уверены, что хотите отменить подписку?\n"
        "Это действие нельзя отменить.",
        reply_markup=get_confirmation_keyboard()
    )

@router.message(Command("delete_data"))
async def cmd_delete_data(message: Message, state: FSMContext) -> None:
    """Handle /delete_data command."""
    await message.answer(
        "❗️ Вы уверены, что хотите удалить все свои данные?\n"
        "Это действие нельзя отменить.",
        reply_markup=get_confirmation_keyboard()
    )
    await state.set_state(UserStates.waiting_for_confirmation)
    await state.update_data(action="delete_data")

@router.callback_query(F.data == "subscribe")
async def process_subscribe(callback: CallbackQuery) -> None:
    """Handle subscription request."""
    await callback.message.edit_text(
        "💳 Выберите действие:",
        reply_markup=get_subscription_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "pay_subscription")
async def process_payment(callback: CallbackQuery, db: Database) -> None:
    """Handle payment request."""
    # TODO: Implement payment processing with YooKassa
    await callback.answer("🔄 Платежная система в разработке")

@router.callback_query(F.data == "cancel_subscription")
async def process_cancel_subscription(
    callback: CallbackQuery,
    db: Database
) -> None:
    """Handle subscription cancellation."""
    try:
        await db.update_subscription(
            callback.from_user.id,
            status="inactive",
            end_date=datetime.now()
        )
        await callback.message.edit_text("✅ Подписка успешно отменена")
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
    await callback.answer()

@router.callback_query(F.data == "confirm")
async def process_confirmation(
    callback: CallbackQuery,
    state: FSMContext,
    db: Database
) -> None:
    """Handle confirmation of dangerous actions."""
    current_state = await state.get_state()
    if current_state == UserStates.waiting_for_confirmation:
        state_data = await state.get_data()
        action = state_data.get("action")
        
        if action == "delete_data":
            try:
                await db.delete_user(callback.from_user.id)
                await callback.message.edit_text(
                    "✅ Все ваши данные успешно удалены"
                )
            except Exception as e:
                await callback.message.edit_text(f"❌ Ошибка: {str(e)}")
        
        await state.clear()
    await callback.answer()

@router.callback_query(F.data == "cancel")
async def process_cancellation(
    callback: CallbackQuery,
    state: FSMContext
) -> None:
    """Handle cancellation of dangerous actions."""
    await callback.message.edit_text("❌ Действие отменено")
    await state.clear()
    await callback.answer()

@router.message(Command("menu"))
async def cmd_menu(message: Message, db: Database):
    """Show main menu."""
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await db.add_user(message.from_user.id)
    
    await message.answer(
        "🤖 Главное меню PriceGuard\n\n"
        "Выберите нужное действие:",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "my_promotions")
async def show_promotions(callback: CallbackQuery, db: Database):
    """Show user's promotions."""
    user_data = await db.get_user(callback.from_user.id)
    if not user_data:
        await callback.answer("❌ Сначала добавьте API ключи", show_alert=True)
        return
    
    # TODO: Implement promotions display
    await callback.message.edit_text(
        "📊 Ваши акции\n\n"
        "🚧 Функция в разработке",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    """Show settings menu."""
    await callback.message.edit_text(
        "⚙️ Настройки\n\n"
        "Выберите параметр для настройки:",
        reply_markup=get_settings_keyboard()
    )

@router.callback_query(F.data == "subscription")
async def show_subscription(callback: CallbackQuery, db: Database):
    """Show subscription info."""
    user_data = await db.get_user(callback.from_user.id)
    if not user_data:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    status_text = await format_subscription_status(user_data)
    await callback.message.edit_text(
        status_text,
        reply_markup=get_subscription_keyboard()
    )

@router.callback_query(F.data == "api_keys")
async def show_api_keys(callback: CallbackQuery):
    """Show API keys management."""
    await callback.message.edit_text(
        "🔑 Управление API ключами\n\n"
        "Выберите маркетплейс для настройки:",
        reply_markup=get_api_key_keyboard()
    )

@router.callback_query(F.data == "check_interval")
async def show_check_interval(callback: CallbackQuery):
    """Show check interval settings."""
    await callback.message.edit_text(
        "⏰ Интервал проверки акций\n\n"
        "Выберите, как часто проверять акции:",
        reply_markup=get_settings_keyboard()
    )

@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Show help message."""
    help_text = format_help_message()
    await callback.message.edit_text(
        help_text,
        reply_markup=get_main_menu_keyboard()
    )
