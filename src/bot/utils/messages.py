"""
Message templates for the PriceGuard bot.
File: src/bot/utils/messages.py
"""

from typing import List, Dict, Optional
from datetime import datetime
from core.logging import get_logger
from services.marketplaces.factory import MarketplaceFactory

logger = get_logger(__name__)

# Инструкции по API ключам
OZON_API_KEY_INSTRUCTION = """
🔑 Добавление API ключа Ozon

Для получения API ключа:
1. Нажмите 👤 в правом верхнем углу личного кабинета
2. Выберите Настройки
3. Перейдите в раздел Seller API (https://seller.ozon.ru/app/settings/api-keys)
4. Нажмите "Сгенерировать ключ"
5. Укажите название и выберите роль "Admin read only"
6. Нажмите "Сгенерировать"

Отправьте ключ в формате:
CLIENT_ID:API_KEY

Пример:
12345:a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6

❗️ Важно: Отправляйте ключ ровно в таком формате, иначе бот не сможет его обработать
"""

WILDBERRIES_API_KEY_INSTRUCTION = """
🔑 Добавление API ключа Wildberries

Для получения API ключа:
1. В личном кабинете нажмите на имя профиля
2. Выберите Настройки → Доступ к API (https://seller.wildberries.ru/supplier-settings/access-to-api)
3. Выберите опцию "Только на чтение"
4. Выберите категории API:
   - Цены и скидки
   - Календарь акций
5. Создайте токен

Отправьте токен в следующем сообщении.

❗️ Важно: Отправляйте только сам токен, без дополнительных символов
"""

START_MESSAGE = """
👋 Привет! Это PriceGuard - сервис мониторинга автоматических акций для продавцов Ozon и Wildberries.

🔍 Мы поможем вам отслеживать, когда товары автоматически попадают в горячие акции.

✨ Первые 14 дней - бесплатно, до 100 товаров.
"""

HOW_IT_WORKS_MESSAGE = """
PriceGuard автоматически:

✅ Проверяет ваши товары на Ozon и Wildberries
✅ Считает количество товаров, попавших в автоматические акции
✅ Присылает уведомления об изменениях

Вам больше не нужно вручную отслеживать акции!
"""

START_SETUP_MESSAGE = """
Для работы сервиса нужны API-ключи Ozon и Wildberries.

🔐 Это полностью безопасно:

- Ключи шифруются
- Вы в любой момент можете их отозвать
- Используются только для чтения
"""

SETUP_COMPLETE_MESSAGE = """

🎉 Отлично! Ваши ключи добавлены.

Сервис будет проверять акции автоматически 4 раза в сутки.
Уведомления придут в этот чат.

Пробный период активирован:
⏰ Осталось дней: 14
📦 Лимит товаров: 100
"""

MENU_MESSAGE = """
🤖 Главное меню PriceGuard

Выберите нужное действие:
"""

def format_start_message(is_registered: bool = False) -> str:
    """Format start command message."""
    if is_registered:
        return (
            "👋 С возвращением в PriceGuard!\n\n"
            "PriceGuard - ваш надежный помощник для отслеживания цен на Ozon и Wildberries. "
            "Бот автоматически мониторит цены ваших товаров и уведомляет об изменениях.\n\n"
            "Выберите действие из меню ниже:"
        )
    else:
        return (
            START_MESSAGE + "\n\n" +
            HOW_IT_WORKS_MESSAGE + "\n\n" +
            START_SETUP_MESSAGE
        )

def format_help_message() -> str:
    """Format help command message."""
    return (
        "ℹ️ Доступные команды:\n\n"
        "/start - Запустить бота\n"
        "/help - Показать эту справку\n"
        "/menu - Открыть главное меню\n"
        "/settings - Настройки бота\n"
        "/status - Проверить статус подписки\n"
        "/add_api - Добавить API ключи\n"
        "/delete_data - Удалить все API ключи\n\n"
        "По всем вопросам обращайтесь к @kagitin"
    )

async def format_subscription_status(user_data: Dict) -> str:
    """Format subscription status message."""
    subscription_status = user_data.get('subscription_status', 'inactive')
    subscription_end_date = user_data.get('subscription_end_date')
    created_at = user_data.get('created_at')
    
    if subscription_status == 'active' and subscription_end_date:
        status = "✅ Активна"
        try:
            end_date = datetime.fromisoformat(subscription_end_date)
            created = datetime.fromisoformat(created_at)
            days_left = (end_date - datetime.now()).days
            
            created_text = f"Дата активации: {created.strftime('%d.%m.%Y %H:%M')}\n"
            expires_text = f"Действует до: {end_date.strftime('%d.%m.%Y %H:%M')}\n"
            days_text = f"Осталось дней: {days_left}"
        except (ValueError, TypeError):
            created_text = ""
            expires_text = ""
            days_text = ""
    elif subscription_status == 'trial':
        status = "🎁 Пробный период"
        created_text = ""
        expires_text = ""
        days_text = ""
    else:
        status = "❌ Неактивна"
        created_text = ""
        expires_text = ""
        days_text = ""
    
    return (
        f"📊 Статус подписки\n\n"
        f"Статус: {status}\n"
        f"{created_text}"
        f"{expires_text}"
        f"{days_text}"
    )

def format_promo_update(
    marketplace: str,
    old_count: int,
    new_count: int,
    details: List[Dict]
) -> str:
    """Format promotion update message."""
    diff = new_count - old_count
    if diff == 0:
        return f"ℹ️ {marketplace}: изменений в акциях нет"
        
    emoji = "🔺" if diff > 0 else "🔻"
    msg = [f"{emoji} {marketplace}: {abs(diff)} товар(ов) {diff > 0 and 'добавлено в' or 'убрано из'} акций"]
    
    if details:
        msg.append("\nПодробности:")
        for item in details:
            if marketplace == "Ozon":
                msg.append(
                    f"• {item['name']}\n"
                    f"  Цена по акции: {item['action_price']}₽\n"
                    f"  Дата акции: {item['date_promo']}"
                )
            else:  # Wildberries
                msg.append(
                    f"• {item['name']}\n"
                    f"  Акция: {item['promotion_name']}\n"
                    f"  Период: {item['start_date']} - {item['end_date']}"
                )
                
    return "\n".join(msg)

def format_api_instructions(marketplace: str) -> str:
    """Format API key instructions message."""
    if marketplace.lower() == "ozon":
        return OZON_API_KEY_INSTRUCTION
    return WILDBERRIES_API_KEY_INSTRUCTION

def format_user_info(user: Dict) -> str:
    """Format user info message."""
    ozon_key = "✅" if user.get("ozon_api_key") and user.get("ozon_client_id") else "❌"
    wb_key = "✅" if user.get("wildberries_api_key") else "❌"
    
    status = user.get("subscription_status", "trial")
    if status == "active":
        status = "✅ Активна"
    elif status == "trial":
        status = "🎁 Пробный период"
    else:
        status = "❌ Неактивна"
    
    created_at = user.get("created_at")
    if created_at:
        try:
            created_at = datetime.fromisoformat(created_at).strftime("%d.%m.%Y %H:%M")
        except (ValueError, TypeError):
            created_at = "Неизвестно"
    
    end_date = user.get("subscription_end_date")
    if end_date:
        try:
            end_date = datetime.fromisoformat(end_date).strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            end_date = "Неизвестно"
    else:
        end_date = "Нет"
    
    interval = user.get("check_interval", 14400)
    interval_min = interval // 360
    
    return (
        f"👤 ID: `{user.get('user_id')}`\n"
        f"├ API Ozon: {ozon_key}\n"
        f"├ API WB: {wb_key}\n"
        f"├ Подписка: {status}\n"
        f"├ Дата окончания: {end_date}\n"
        f"├ Дата регистрации: {created_at}\n"
        f"└ Интервал проверки: {interval_min} мин"
    )

def format_subscription_info(sub: Dict) -> str:
    """Format subscription info message."""
    status = "✅ Активна" if sub.get("is_active") else "❌ Неактивна"
    
    # Конвертируем даты в нужный формат
    try:
        start_date = datetime.fromisoformat(sub.get('start_date')).strftime("%d.%m.%Y")
        end_date = datetime.fromisoformat(sub.get('end_date')).strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        start_date = "Неизвестно"
        end_date = "Неизвестно"

    # Определяем название тарифа по длительности
    months = (datetime.fromisoformat(sub.get('end_date')) - 
              datetime.fromisoformat(sub.get('start_date'))).days // 30
    tariff_names = {
        1: "Базовый (1 месяц)",
        3: "Стандарт (3 месяца)",
        6: "Премиум (6 месяцев)",
        12: "VIP (12 месяцев)"
    }
    tariff = tariff_names.get(months, f"Подписка на {months} мес.")
    
    return (
        "💳 *Оплата:*\n"
        f"*Тариф:* {tariff}\n"
        f"*Статус:* {status}\n"
        f"*Начало:* {start_date}\n"
        f"*Окончание:* {end_date}"
    )

def format_payment_info(payment: Dict) -> str:
    """Format payment info message."""
    status_map = {
        "pending": "🕒 Ожидает оплаты",
        "waiting_for_capture": "🔄 Обрабатывается",
        "succeeded": "✅ Оплачен",
        "canceled": "❌ Отменен"
    }
    
    return (
        f"💳 *Платеж #{payment.get('id')}*\n"
        f"*Статус:* {status_map.get(payment.get('status'), 'Неизвестно')}\n"
        f"*Сумма:* {payment.get('amount')} {payment.get('currency')}\n"
        f"*Дата:* {payment.get('created_at')}"
    )

async def validate_marketplace_keys(user_data: Dict, marketplace_factory: MarketplaceFactory) -> Dict[str, bool]:
    """Validate marketplace API keys.
    
    Returns:
        Dict with validation status for each marketplace
    """
    results = {
        "ozon": False,
        "wildberries": False
    }
    
    # Check Ozon keys
    if user_data.get('ozon_api_key') and user_data.get('ozon_client_id'):
        try:
            # Передаем зашифрованный ключ напрямую
            ozon_client = await marketplace_factory.create_client(
                'ozon',
                user_data['ozon_api_key'],
                client_id=user_data['ozon_client_id'],
                is_encrypted=True
            )
            async with ozon_client:
                results["ozon"] = await ozon_client.validate_api_key()
        except Exception as e:
            logger.error(f"Ozon validation error: {str(e)}")
    
    # Check Wildberries key
    if user_data.get('wildberries_api_key'):
        try:
            # Передаем зашифрованный ключ напрямую
            wb_client = await marketplace_factory.create_client(
                'wildberries',
                user_data['wildberries_api_key'],
                is_encrypted=True
            )
            async with wb_client:
                results["wildberries"] = await wb_client.validate_api_key()
        except Exception as e:
            logger.error(f"Wildberries validation error: {str(e)}")
    
    return results

async def format_api_keys_message(user_data: Dict, marketplace_factory: Optional[MarketplaceFactory] = None, validate: bool = False) -> str:
    """Format API keys message."""
    ozon_key = user_data.get('ozon_api_key', '')
    ozon_client_id = user_data.get('ozon_client_id', '')
    wb_key = user_data.get('wildberries_api_key', '')
    
    if validate and marketplace_factory:
        validation_results = await validate_marketplace_keys(user_data, marketplace_factory)
        ozon_status = "✅" if validation_results["ozon"] else "❌"
        wb_status = "✅" if validation_results["wildberries"] else "❌"
    else:
        # Basic presence check
        ozon_status = "✅" if ozon_key and ozon_client_id else "❌"
        wb_status = "✅" if wb_key else "❌"
    
    return (
        "🔑 Управление API ключами\n\n"
        f"OZON API: {ozon_status}\n"
        f"Wildberries API: {wb_status}\n\n"
        "Выберите маркетплейс для настройки:"
    )
