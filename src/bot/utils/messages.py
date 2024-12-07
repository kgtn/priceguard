"""
Message templates for the PriceGuard bot.
File: src/bot/utils/messages.py
"""

from typing import List, Dict

OZON_API_KEY_INSTRUCTION = """
🔑 *Как получить API-ключ Ozon*

После регистрации в Ozon Seller создайте свой уникальный API-ключ:

1. Нажмите 123/ в правом верхнем углу личного кабинета
2. Выберите "Настройки"
3. Перейдите в раздел [Seller API](https://seller.ozon.ru/app/settings/api-keys)
4. Нажмите "Сгенерировать ключ"
5. В открывшемся окне:
   • Укажите название для API-ключа
   • Выберите роль "Admin read only" (в самом конце)
6. Нажмите "Сгенерировать"

Пожалуйста, отправьте полученный API-ключ в следующем сообщении.
"""

WB_API_KEY_INSTRUCTION = """
🔑 *Как создать токен Wildberries*

1. В личном кабинете нажмите на имя профиля
2. Выберите "Настройки" → [Доступ к API](https://seller.wildberries.ru/supplier-settings/access-to-api)
3. Выберите опцию "Только на чтение"
4. В категориях API выберите:
   • Цены и скидки
   • Календарь акций
5. Нажмите "Создать токен"

Пожалуйста, отправьте полученный токен в следующем сообщении.
"""

def format_start_message(is_registered: bool = False) -> str:
    """Format start command message."""
    if is_registered:
        return (
            "👋 С возвращением в PriceGuard!\n\n"
            "Выберите действие из меню ниже:"
        )
    else:
        return (
            "👋 Добро пожаловать в PriceGuard!\n\n"
            "Я помогу вам отслеживать товары, которые автоматически участвуют "
            "в акциях на Ozon и Wildberries.\n\n"
            "🔑 Для начала работы добавьте API ключи маркетплейсов\n"
            "💳 Первые 14 дней бесплатно, затем 400₽/месяц\n\n"
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

def format_subscription_status(
    status: str,
    end_date: str,
    check_interval: int
) -> str:
    """Format subscription status message."""
    status_emoji = {
        "trial": "🎁",
        "active": "✅",
        "inactive": "❌"
    }
    status_text = {
        "trial": "Пробный период",
        "active": "Активна",
        "inactive": "Неактивна"
    }
    
    return (
        f"Статус подписки: {status_emoji.get(status, '❓')} {status_text.get(status, 'Неизвестно')}\n"
        f"Действует до: {end_date}\n"
        f"Интервал проверок: {check_interval} час(ов)"
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
    else:
        return WB_API_KEY_INSTRUCTION

def format_user_info(user: Dict) -> str:
    """Format user info message."""
    status = "✅ Активен" if user.get("is_active") else "❌ Неактивен"
    subscription = "💳 Есть подписка" if user.get("has_subscription") else "🚫 Нет подписки"
    
    return (
        f"👤 *ID:* `{user.get('id')}`\n"
        f"├ *Статус:* {status}\n"
        f"├ *Подписка:* {subscription}\n"
        f"└ *Дата регистрации:* {user.get('created_at')}"
    )

def format_subscription_info(sub: Dict) -> str:
    """Format subscription info message."""
    status = "✅ Активна" if sub.get("is_active") else "❌ Неактивна"
    
    return (
        f"💳 *ID:* `{sub.get('id')}`\n"
        f"├ *Пользователь:* `{sub.get('user_id')}`\n"
        f"├ *Статус:* {status}\n"
        f"├ *Начало:* {sub.get('start_date')}\n"
        f"└ *Окончание:* {sub.get('end_date')}"
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
