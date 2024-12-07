"""
Message templates for the PriceGuard bot.
File: src/bot/utils/messages.py
"""

from typing import List, Dict
from datetime import datetime

OZON_API_KEY_INSTRUCTION = """
🔑 Добавление API ключа Ozon

Для получения API ключа:
1️⃣ Войдите в личный кабинет Ozon
2️⃣ Перейдите в раздел API
3️⃣ Создайте новый ключ, если его нет

Отправьте ключ в формате:
CLIENT_ID:API_KEY

Пример:
12345:a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6

❗️ Важно: Отправляйте ключ ровно в таком формате, иначе бот не сможет его обработать
"""

WILDBERRIES_API_KEY_INSTRUCTION = """
🔑 Добавление API ключа Wildberries

Для получения API ключа:
1️⃣ Войдите в личный кабинет Wildberries
2️⃣ Перейдите в раздел "Настройки" -> "Доступ к API"
3️⃣ Создайте новый ключ, если его нет

Отправьте ключ в следующем сообщении.

❗️ Важно: Отправляйте только сам ключ, без дополнительных символов
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
            "🎉 Добро пожаловать в PriceGuard!\n\n"
            "PriceGuard - ваш надежный помощник для отслеживания цен на Ozon и Wildberries. "
            "Бот автоматически мониторит цены ваших товаров и уведомляет об изменениях.\n\n"
            "Чтобы начать работу:\n"
            "1️⃣ Добавьте API ключи маркетплейсов в разделе 🔑 API ключи\n"
            "2️⃣ Настройте интервал проверки в разделе ⏰ Интервал проверки\n"
            "3️⃣ Следите за акциями в разделе 📊 Мои акции\n\n"
            "Выберите действие из меню ниже:"
        )

def format_help_message() -> str:
    """Format help command message."""
    return (
        "ℹ️ Доступные команды:\n\n"
        "/start - Начать работу с ботом\n"
        "/add_api - Добавить API ключи\n"
        "/status - Проверить статус подписки\n"
        "/settings - Изменить частоту проверок\n"
        "/unsubscribe - Отменить подписку\n"
        "/delete_data - Удалить свои данные\n\n"
        "По всем вопросам обращайтесь к @admin"
    )

async def format_subscription_status(user_data: Dict) -> str:
    """Format subscription status message."""
    subscription_active = user_data.get('subscription_active', False)
    subscription_expires = user_data.get('subscription_expires')
    check_interval = user_data.get('check_interval', 60)  # default 60 minutes
    
    if subscription_active and subscription_expires:
        expires = datetime.fromisoformat(subscription_expires)
        days_left = (expires - datetime.now()).days
        status = "✅ Активна"
        expires_text = f"Действует до: {expires.strftime('%d.%m.%Y')}\n"
        days_text = f"Осталось дней: {days_left}\n"
    else:
        status = "❌ Неактивна"
        expires_text = ""
        days_text = ""
    
    return (
        f"📊 Статус подписки\n\n"
        f"Статус: {status}\n"
        f"{expires_text}"
        f"{days_text}"
        f"Интервал проверки: {check_interval} мин."
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
    ozon_key = "✅" if user.get("ozon_api_key") else "❌"
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
    
    interval = user.get("check_interval", 3600)
    interval_min = interval // 60
    
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
        f"├ *Тариф:* {tariff}\n"
        f"├ *Статус:* {status}\n"
        f"├ *Начало:* {start_date}\n"
        f"└ *Окончание:* {end_date}"
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
        f"├ *Статус:* {status_map.get(payment.get('status'), 'Неизвестно')}\n"
        f"├ *Сумма:* {payment.get('amount')} {payment.get('currency')}\n"
        f"└ *Дата:* {payment.get('created_at')}"
    )
