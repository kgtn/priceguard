# PriceGuard Bot

Telegram бот для мониторинга акций на Ozon и Wildberries.

## Возможности

- 🔍 Мониторинг акций на Ozon и Wildberries
- 📊 Отслеживание изменений цен и остатков
- 🔔 Мгновенные уведомления об изменениях
- 💳 Удобная оплата через Telegram Payments
- 📱 Простой и понятный интерфейс

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/priceguard.git
cd priceguard
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/macOS
# или
.\venv\Scripts\activate  # для Windows
pip install -r requirements.txt
```

3. Создайте файл `.env` на основе `.env.example` и заполните необходимые переменные:
```
BOT_TOKEN=your_telegram_bot_token
PAYMENT_PROVIDER_TOKEN=your_payment_provider_token
ADMIN_USER_ID=your_admin_user_id
DATABASE_PATH=your_database_path
ENCRYPTION_KEY=your_encryption_key
```

## Запуск

```bash
python src/main.py
```

## Тестирование

```bash
./run_tests.sh
```

## Структура проекта

```
priceguard/
├── src/
│   ├── bot/              # Обработчики команд бота
│   ├── core/             # Ядро приложения
│   ├── services/         # Сервисы (маркетплейсы, оплата, мониторинг)
│   └── utils/            # Вспомогательные функции
├── tests/                # Тесты
├── .env.example          # Пример конфигурации
├── requirements.txt      # Зависимости
└── README.md            # Документация
```

## API Маркетплейсов

### Ozon

- `get_hot_sales()` - получение активных акций
- `get_product_info()` - информация о товаре
- `get_stocks()` - остатки товаров

### Wildberries

- `get_auto_promotions()` - получение автоматических акций
- `get_product_details()` - детали товара
- `get_stocks()` - остатки товаров

## Система мониторинга

Бот периодически проверяет:
- Новые акции
- Изменения цен
- Изменения остатков
- Окончание акций

При обнаружении изменений пользователи получают уведомления с подробной информацией.

## Подписки

Доступны следующие планы подписки:
- Месячный
- Квартальный
- Годовой

Оплата производится через встроенную систему Telegram Payments.

## Разработка

### Добавление нового маркетплейса

1. Создайте новый класс в `src/services/marketplaces/`
2. Реализуйте интерфейс `MarketplaceClient`
3. Добавьте фабрику в `MarketplaceClientFactory`
4. Обновите обработчики команд

### Добавление новых команд

1. Создайте обработчик в `src/bot/handlers/`
2. Зарегистрируйте команду в диспетчере
3. Добавьте необходимые клавиатуры
4. Обновите справку

## Лицензия

MIT
