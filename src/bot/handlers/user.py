"""
User command handlers for the PriceGuard bot.
File: src/bot/handlers/user.py
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from aiogram import Router, F, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, BotCommand, BotCommandScopeDefault, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest

from core.database import Database
from core.logging import get_logger
from services.marketplaces.factory import MarketplaceFactory
from services.monitoring.monitor import PromotionMonitor
from bot.utils.messages import (
    format_help_message,
    format_subscription_status,
    format_api_keys_message
)
from ..utils.messages import (
    format_start_message,
    START_MESSAGE,
    HOW_IT_WORKS_MESSAGE,
    START_SETUP_MESSAGE,
    OZON_API_KEY_INSTRUCTION,
    WILDBERRIES_API_KEY_INSTRUCTION,
    SETUP_COMPLETE_MESSAGE,
    MENU_MESSAGE
)
from ..keyboards.user import (
    get_start_keyboard,
    get_settings_keyboard,
    get_api_key_keyboard,
    get_confirmation_keyboard,
    get_main_menu_keyboard
)
from ..keyboards.payment import (
    get_subscription_keyboard,
    get_subscription_plans_keyboard
)

router = Router()
logger = get_logger(__name__)

class UserStates(StatesGroup):
    """User state machine for conversation handling."""
    waiting_for_ozon_api = State()
    waiting_for_wb_api = State()
    waiting_for_interval = State()
    waiting_for_confirmation = State()

async def setup_bot_commands(bot: Bot):
    """Setup bot commands."""
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота"),
        BotCommand(command="my_promotions", description="📊 Акции"),
        BotCommand(command="settings", description="⚙️ Настройки"),
        BotCommand(command="add_api", description="🔑 API ключи"),
        BotCommand(command="status", description="💳 Статус подписки"),
        BotCommand(command="help", description="❓ Помощь")
    ]
    await bot.set_my_commands(commands)

@router.message(Command("start"))
async def cmd_start(message: Message, db: Database):
    """Handle /start command."""
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.add_user(message.from_user.id)
    
    await message.answer(
        text=format_start_message(is_registered=bool(user)),
        reply_markup=get_start_keyboard()
    )

@router.callback_query(F.data == "how_it_works")
async def process_how_it_works(callback: CallbackQuery):
    """Handle 'How it works' button press."""
    try:
        await callback.message.edit_text(
            text=HOW_IT_WORKS_MESSAGE + "\u200b",
            reply_markup=get_start_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.callback_query(F.data == "start_setup")
async def process_start_setup(callback: CallbackQuery):
    """Handle 'Start setup' button press."""
    try:
        await callback.message.edit_text(
            text=START_SETUP_MESSAGE + "\u200b",
            reply_markup=get_api_key_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.callback_query(F.data == "add_ozon_key")
async def process_add_ozon_key(callback: CallbackQuery, state: FSMContext):
    """Handle Ozon API key addition."""
    try:
        await state.set_state(UserStates.waiting_for_ozon_api)
        await callback.message.edit_text(
            text=OZON_API_KEY_INSTRUCTION + "\u200b",
            reply_markup=get_api_key_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.callback_query(F.data == "add_wb_key")
async def process_add_wb_key(callback: CallbackQuery, state: FSMContext):
    """Handle Wildberries API key addition."""
    await state.set_state(UserStates.waiting_for_wb_api)
    await callback.message.edit_text(
        text=WILDBERRIES_API_KEY_INSTRUCTION + "\u200b",
        reply_markup=get_api_key_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback: CallbackQuery):
    """Handle back to main menu button press."""
    try:
        await callback.message.edit_text(
            text=START_MESSAGE + "\u200b",
            reply_markup=get_start_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    await message.answer(
        format_help_message(),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🤔 Как это работает?",
                        callback_data="how_it_works"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="👨‍💻 Тех. поддержка",
                        url="https://t.me/kagitin"
                    )
                ]
            ]
        )
    )

@router.message(Command("status"))
async def cmd_status(message: Message, db: Database) -> None:
    """Handle /status command."""
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return
        
    await message.answer(
        await format_subscription_status(user_data),
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
        api_key = message.text.strip()
        if not api_key:
            await message.answer("❌ API ключ не может быть пустым")
            return
            
        parts = api_key.split(':')
        if len(parts) != 2:
            await message.answer(
                "❌ Неверный формат. Отправьте ключ в формате CLIENT_ID:API_KEY"
            )
            return
            
        client_id, api_key = parts
        logger.info(f"Parsed API key - Client ID: {client_id}, Key length: {len(api_key)}")
        
        await message.answer("🔄 Проверяю API ключ...")
        
        # Создаем клиента с незашифрованным ключом для проверки
        logger.info("Creating Ozon client for validation")
        client = await marketplace_factory.create_client(
            'ozon', api_key, client_id=client_id, is_encrypted=False
        )
        
        # Проверяем валидность ключа
        logger.info("Starting API key validation")
        async with client:
            is_valid = await client.validate_api_key()
            logger.info(f"API key validation result: {is_valid}")
            if not is_valid:
                await message.answer("❌ Неверный API ключ")
                return
        
        # Если ключ валидный, шифруем и сохраняем
        logger.info("Encrypting API key")
        encrypted_key = marketplace_factory.encrypt_api_key(api_key)
        
        # Сохраняем API ключ и client_id в одной транзакции
        logger.info("Saving API credentials to database")
        async with db.db.execute(
            """
            UPDATE users 
            SET ozon_api_key = ?,
                ozon_client_id = ?
            WHERE user_id = ?
            """,
            (encrypted_key, client_id, message.from_user.id)
        ):
            await db.db.commit()
            
        await message.answer(
            "✅ API ключ Ozon успешно добавлен!\n\n"
            "Теперь вы можете:\n"
            "1️⃣ Настроить интервал проверки в разделе ⚙️ Настройки\n"
            "2️⃣ Начать отслеживать акции в разделе 📊 Мои акции",
            reply_markup=get_main_menu_keyboard()
        )
        await show_api_keys_message(message, db)
        
    except ValueError as e:
        await message.answer(f"❌ Ошибка валидации: {str(e)}")
    except Exception as e:
        logger.error(f"Error adding Ozon API key: {str(e)}")
        await message.answer("❌ Произошла ошибка при добавлении API ключа")
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
        if not api_key:
            await message.answer("❌ API ключ не может быть пустым")
            return
        
        await message.answer("🔄 Проверяю API ключ...")
        
        # Создаем клиента с незашифрованным ключом для проверки
        client = await marketplace_factory.create_client(
            'wildberries', api_key, is_encrypted=False
        )
        
        # Проверяем валидность ключа
        async with client:
            is_valid = await client.validate_api_key()
            if not is_valid:
                await message.answer("❌ Неверный API ключ")
                return
        
        # Если ключ валидный, шифруем и сохраняем
        encrypted_key = marketplace_factory.encrypt_api_key(api_key)
        await db.update_api_keys(
            message.from_user.id,
            wildberries_key=encrypted_key
        )
        
        await message.answer(
            "✅ API ключ Wildberries успешно добавлен!\n\n"
            "Теперь вы можете:\n"
            "1️⃣ Настроить интервал проверки в разделе ⚙️ Настройки\n"
            "2️⃣ Начать отслеживать акции в разделе 📊 Мои акции",
            reply_markup=get_main_menu_keyboard()
        )
        await show_api_keys_message(message, db)
        
    except Exception as e:
        logger.error(f"Error processing Wildberries API key: {str(e)}")
        await message.answer(
            "❌ Произошла ошибка при проверке API ключа\n\n"
            "Пожалуйста, убедитесь что:\n"
            "1. У вас есть доступ к API Wildberries\n"
            "2. API ключ активен и это не тестовый ключ\n"
            "3. API ключ имеет права для доступа к Цены и скидки\n"
            "4. Ключ не содержит лишних символов",
            reply_markup=get_main_menu_keyboard()
        )
    finally:
        await state.clear()

async def show_api_keys_message(message: Message, db: Database) -> None:
    """Show API keys for message."""
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await message.answer("❌ Вы не зарегистрированы. Используйте /start")
        return

    await message.answer(
        await format_api_keys_message(user_data),
        reply_markup=get_api_key_keyboard()
    )

@router.callback_query(F.data == "settings")
async def process_settings(callback: CallbackQuery):
    """Handle settings button press."""
    try:
        await callback.message.edit_text(
            "⚙️ Настройки\n\n" + "\u200b"
            "Выберите интервал проверки акций:",
            reply_markup=get_settings_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.callback_query(F.data.startswith("interval:"))
async def process_interval_change(callback: CallbackQuery, db: Database):
    """Handle interval change."""
    hours = int(callback.data.split(":")[1])
    
    try:
        await db.update_check_interval(callback.from_user.id, hours)
        await callback.message.edit_text(
            f"✅ Интервал проверки обновлен: каждые {hours} {'час' if hours == 1 else 'часа' if 2 <= hours <= 4 else 'часов'}" + "\u200b",
            reply_markup=get_main_menu_keyboard()
        )
    except Exception as e:
        await callback.message.edit_text(
            "❌ Не удалось обновить интервал проверки. Попробуйте позже." + "\u200b",
            reply_markup=get_main_menu_keyboard()
        )
    
    await callback.answer()

@router.callback_query(F.data == "back_to_main")
async def process_back_to_main(callback: CallbackQuery) -> None:
    """Handle back to main menu."""
    try:
        await callback.message.edit_text(
            format_start_message(True) + "\u200b",
            reply_markup=get_start_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
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
@router.callback_query(F.data == "delete_data")
async def cmd_delete_data(event: Union[Message, CallbackQuery], state: FSMContext):
    """Handle /delete_data command and delete_data button."""
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(
            "❗️ Вы уверены, что хотите удалить все сохранённые API ключи?\n" + "\u200b"
            "Это действие нельзя отменить.",
            reply_markup=get_confirmation_keyboard()
        )
    else:
        await event.answer(
            "❗️ Вы уверены, что хотите удалить все сохранённые API ключи?\n" + "\u200b"
            "Это действие нельзя отменить.",
            reply_markup=get_confirmation_keyboard()
        )
    await state.set_state(UserStates.waiting_for_confirmation)
    await state.update_data(action="delete_keys")

@router.callback_query(F.data == "subscribe")
async def process_subscribe(callback: CallbackQuery) -> None:
    """Handle subscription request."""
    try:
        await callback.message.edit_text(
            "💳 Выберите действие:" + "\u200b",
            reply_markup=get_subscription_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.callback_query(F.data == "pay_subscription")
async def process_payment(callback: CallbackQuery, db: Database) -> None:
    """Handle payment request."""
    try:
        await callback.message.edit_text(
            "💳 Выберите план подписки:\n\n"
            "1️⃣ Месяц - 299₽\n"
            "3️⃣ Месяца - 799₽\n"
            "6️⃣ Месяцев - 1499₽\n"
            "1️⃣2️⃣ Месяцев - 2699₽",
            reply_markup=get_subscription_plans_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

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
        
        if action == "delete_keys":
            try:
                await db.clear_api_keys(callback.from_user.id)
                await callback.message.edit_text(
                    "✅ Все API ключи успешно удалены"
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
    try:
        await callback.message.edit_text("❌ Действие отменено" + "\u200b")
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "my_promotions")
async def show_promotions(callback: CallbackQuery, db: Database):
    """Show user's promotions."""
    # Проверяем наличие API ключей
    user_data = await db.get_user(callback.from_user.id)
    if not user_data:
        await callback.answer("❌ Сначала добавьте API ключи", show_alert=True)
        return

    # Формируем сообщение в зависимости от наличия ключей
    has_wb = bool(user_data.get("wildberries_api_key"))
    has_ozon = bool(user_data.get("ozon_api_key") and user_data.get("ozon_client_id"))
    
    if not (has_wb or has_ozon):
        text = (
            "📊 *Ваши акции*\n\n"
            "❌ У вас не добавлены API ключи маркетплейсов\n\n"
            "Добавьте ключи в разделе 🔑 API ключи, чтобы отслеживать акции"
        )
    else:
        # Получаем интервал проверки пользователя (в секундах) или используем значение по умолчанию
        check_interval = user_data.get("check_interval", 14400)  # 4 часа по умолчанию
        interval_hours = check_interval // 3600  # переводим секунды в часы
        
        text = "📊 *Ваши акции*\n\n"
        
        if has_wb:
            text += "🟣 *Wildberries*: Подключен\n"
            text += f"└ Бот проверяет акции каждые {interval_hours} часа\n"
            text += "└ Вы получите уведомление при изменениях\n\n"
            
        if has_ozon:
            text += "🔵 *OZON*: Подключен\n"
            text += f"└ Бот проверяет акции каждые {interval_hours} часа\n"
            text += "└ Вы получите уведомление при изменениях\n"

    try:
        await callback.message.edit_text(
            text + "\u200b",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()

@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery):
    """Show settings menu."""
    try:
        await callback.message.edit_text(
            "⚙️ Настройки\n\n"
            "Выберите параметр для настройки:",
            reply_markup=get_settings_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.callback_query(F.data == "subscription")
async def show_subscription(callback: CallbackQuery, db: Database):
    """Show subscription info."""
    user_data = await db.get_user(callback.from_user.id)
    if not user_data:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return
    
    status_text = await format_subscription_status(user_data)
    try:
        await callback.message.edit_text(
            status_text + "\u200b",
            reply_markup=get_subscription_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.callback_query(F.data == "api_keys")
async def show_api_keys(callback: CallbackQuery, db: Database):
    """Show API keys management."""
    user_data = await db.get_user(callback.from_user.id)
    if not user_data:
        await callback.message.edit_text(
            "❌ Вы не зарегистрированы. Используйте /start",
            reply_markup=get_start_keyboard()
        )
        return
        
    try:
        await callback.message.edit_text(
            await format_api_keys_message(user_data) + "\u200b",
            reply_markup=get_api_key_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.callback_query(F.data == "check_interval")
async def show_check_interval(callback: CallbackQuery):
    """Show check interval settings."""
    try:
        await callback.message.edit_text(
            "⏰ Интервал проверки акций\n\n" + "\u200b"
            "Выберите, как часто проверять акции:",
            reply_markup=get_settings_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Show help message."""
    help_text = format_help_message()
    try:
        await callback.message.edit_text(
            help_text + "\u200b",
            reply_markup=get_main_menu_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.callback_query(F.data == "check_api_status")
async def check_api_status(
    callback: CallbackQuery,
    db: Database,
    marketplace_factory: MarketplaceFactory
):
    """Handle API status check."""
    user_data = await db.get_user(callback.from_user.id)
    if not user_data:
        await callback.answer("❌ Сначала добавьте API ключи", show_alert=True)
        return
        
    # Check if any keys are present
    if not (user_data.get('ozon_api_key') or user_data.get('wildberries_api_key')):
        await callback.answer("❌ Добавьте хотя бы один API ключ", show_alert=True)
        return
    
    try:
        await callback.message.edit_text(
            "🔄 Проверяю статус API ключей..." + "\u200b",
            reply_markup=None
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    # Get status message with validation
    status_message = await format_api_keys_message(user_data, marketplace_factory, validate=True)
    
    try:
        await callback.message.edit_text(
            status_message + "\u200b",
            reply_markup=get_api_key_keyboard()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()

@router.message(Command("my_promotions"))
async def cmd_my_promotions(message: Message, db: Database, monitor: PromotionMonitor):
    """Handle /my_promotions command."""
    # Проверяем наличие API ключей
    user_data = await db.get_user(message.from_user.id)
    if not user_data:
        await message.answer("❌ Сначала добавьте API ключи")
        return

    # Формируем сообщение в зависимости от наличия ключей
    has_wb = bool(user_data.get("wildberries_api_key"))
    has_ozon = bool(user_data.get("ozon_api_key") and user_data.get("ozon_client_id"))
    
    if not (has_wb or has_ozon):
        text = (
            "📊 *Ваши акции*\n\n"
            "❌ У вас не добавлены API ключи маркетплейсов\n\n"
            "Добавьте ключи в разделе 🔑 API ключи, чтобы отслеживать акции"
        )
    else:
        # Получаем интервал проверки пользователя (в секундах) или используем значение по умолчанию
        check_interval = user_data.get("check_interval", 14400)  # 4 часа по умолчанию
        interval_hours = check_interval // 3600  # переводим секунды в часы
        
        # Получаем времена последних проверок
        user_last_checks = monitor._last_check.get(message.from_user.id, {})
        last_check_ozon = user_last_checks.get('ozon')
        last_check_wb = user_last_checks.get('wildberries')
        
        # Получаем кэшированные данные о промо-акциях
        cached_promotions = monitor._cached_promotions.get(message.from_user.id, {})
        
        text = "📊 *Ваши акции*\n\n"
        
        if has_ozon:
            text += "🔵 *OZON*: Подключен\n"
            # Получаем количество активных акций из кэша
            ozon_promotions = cached_promotions.get('ozon', [])
            text += f"└ Акций: {len(ozon_promotions)}\n"
            if last_check_ozon:
                minutes_ago = int((datetime.now() - last_check_ozon).total_seconds() / 60)
                text += f"└ Проверено: {minutes_ago} мин. назад\n\n"
            else:
                text += "└ Ещё не проверялось\n\n"
            
        if has_wb:
            text += "🟣 *Wildberries*: Подключен\n"
            # Получаем количество активных акций из кэша
            wb_promotions = cached_promotions.get('wildberries', [])
            text += f"└ Акций: {len(wb_promotions)}\n"
            if last_check_wb:
                minutes_ago = int((datetime.now() - last_check_wb).total_seconds() / 60)
                text += f"└ Проверено: {minutes_ago} мин. назад\n\n"
            else:
                text += "└ Ещё не проверялось\n\n"
            
        text += f"Интервал проверки: {interval_hours} ч."

    await message.answer(
        text,
        parse_mode="Markdown"
    )
