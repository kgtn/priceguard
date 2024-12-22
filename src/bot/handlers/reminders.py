"""
Handlers for reminder-related callbacks.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from core.database import Database
from bot.utils.messages import format_api_instructions
from services.reminder import ReminderService
from services.marketplaces.factory import MarketplaceFactory

router = Router(name="reminders")

@router.callback_query(F.data == "disable_reminders")
async def process_disable_reminders(callback: CallbackQuery, reminder_service: ReminderService):
    """Handle disable reminders button press."""
    await reminder_service.disable_reminders(callback.from_user.id)
    
    await callback.message.edit_text(
        "🔕 Напоминания отключены. Вы всегда можете вернуться к настройке через команду /help",
        parse_mode="HTML"
    )
    await callback.answer("Напоминания отключены")

@router.callback_query(F.data == "check_api")
async def process_check_api(
    callback: CallbackQuery,
    db: Database,
    marketplace_factory: MarketplaceFactory
):
    """Handle check API keys button press."""
    user_id = callback.from_user.id
    user_data = await db.get_user(user_id)
    
    # Проверяем ключи
    validation_result = await marketplace_factory.validate_api_keys(user_data)
    
    if validation_result.get('ozon', False) and validation_result.get('wildberries', False):
        # Оба ключа валидны
        await db.execute(
            "UPDATE users SET setup_status = 'api_validated' WHERE user_id = ?",
            (user_id,)
        )
        message = (
            "✅ Отлично! Все API ключи работают корректно.\n\n"
            "Теперь бот будет мониторить акции и уведомлять вас об изменениях."
        )
    else:
        # Есть проблемы с ключами
        problems = []
        if not validation_result.get('ozon', False) and user_data.get('ozon_api_key'):
            problems.append(
                "• OZON: Убедитесь, что указали ключ в формате Client_id:Api_key "
                "и установили роль Admin Read Only"
            )
        if not validation_result.get('wildberries', False) and user_data.get('wildberries_api_key'):
            problems.append(
                "• Wildberries: Проверьте, что указали правильный ключ "
                "и установили разрешение на Цены и скидки"
            )
        
        message = (
            "⚠️ Обнаружены проблемы с API ключами:\n\n" +
            "\n".join(problems) +
            "\n\nИспользуйте команду /add_api чтобы обновить ключи"
        )
    
    try:
        await callback.message.edit_text(
            message,
            parse_mode="HTML",
            reply_markup=callback.message.reply_markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()

@router.callback_query(F.data == "show_api_instructions")
async def process_show_api_instructions(callback: CallbackQuery):
    """Handle show API instructions button press."""
    instructions = (
        "📝 <b>Как получить API ключи</b>\n\n"
        "<b>OZON</b>\n"
        "1. Войдите в личный кабинет продавца\n"
        "2. Перейдите в раздел Настройки → API\n"
        "3. Создайте новый ключ с ролью Admin Read Only\n"
        "4. Скопируйте Client Id и Api Key\n"
        "5. Отправьте боту в формате: Client_id:Api_key\n\n"
        "<b>Wildberries</b>\n"
        "1. Войдите в личный кабинет продавца\n"
        "2. Перейдите в раздел Настройки → Доступ к API\n"
        "3. Создайте новый ключ с разрешением на Цены и скидки\n"
        "4. Скопируйте и отправьте ключ боту\n\n"
        "Используйте команду /add_api для добавления ключей"
    )
    
    try:
        await callback.message.edit_text(
            instructions,
            parse_mode="HTML",
            reply_markup=callback.message.reply_markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()
