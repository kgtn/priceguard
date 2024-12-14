# API Documentation

## Marketplaces API

### Base Client Interface

#### `async def validate_api_key() -> bool`
Проверяет валидность API ключа.

**Возвращает:**
```python
bool  # True если ключ валидный
```

**Исключения:**
- `ValueError`: Если API ключ невалидный
- `ConnectionError`: При ошибке соединения

### Ozon Client

#### `__init__(api_key: str, client_id: str)`
Инициализация клиента Ozon.

**Параметры:**
- `api_key`: API ключ продавца
- `client_id`: ID клиента в Ozon

#### `async def get_promo_products() -> List[Dict]`
Получает список активных акций Hot Sale на Ozon.

**Возвращает:**
```python
List[Dict[str, Any]]
```

**Пример ответа:**
```python
[
    {
        "id": "123456",
        "name": "Hot Sale",
        "products_count": 10,
        "date_start": "2024-01-01T00:00:00Z",
        "date_end": "2024-01-31T23:59:59Z"
    }
]
```

**Исключения:**
- `ValueError`: Если API ключ или Client ID невалидны
- `ConnectionError`: При ошибке соединения

### Wildberries Client

#### `__init__(api_key: str)`
Инициализация клиента Wildberries.

**Параметры:**
- `api_key`: API ключ продавца

#### `async def get_promo_products() -> List[Dict]`
Получает список автоматических акций на Wildberries.

**Возвращает:**
```python
List[Dict[str, Any]]
```

**Пример ответа:**
```python
[
    {
        "id": "789012",
        "name": "Auto Promotion",
        "products_count": 5,
        "date_start": "2024-01-01T00:00:00Z",
        "date_end": "2024-01-31T23:59:59Z"
    }
]
```

**Исключения:**
- `ValueError`: Если API ключ невалидный
- `ConnectionError`: При ошибке соединения

## MarketplaceFactory

### `__init__(encryption_key: str)`
Инициализация фабрики клиентов маркетплейсов.

**Параметры:**
- `encryption_key`: Ключ для шифрования/дешифрования API ключей

### `async def create_client(marketplace: str, api_key: str, client_id: Optional[str] = None, is_encrypted: bool = False) -> Union[OzonClient, WildberriesClient]`
Создает и валидирует клиент маркетплейса.

**Параметры:**
- `marketplace`: Название маркетплейса ('ozon' или 'wildberries')
- `api_key`: API ключ (зашифрованный или нет)
- `client_id`: ID клиента Ozon (обязателен для Ozon)
- `is_encrypted`: Флаг, указывающий зашифрован ли API ключ

**Возвращает:**
```python
Union[OzonClient, WildberriesClient]  # Экземпляр клиента маркетплейса
```

### `def encrypt_api_key(api_key: str) -> str`
Шифрует API ключ для хранения.

**Параметры:**
- `api_key`: API ключ для шифрования

**Возвращает:**
```python
str  # Зашифрованный API ключ
```

### `def decrypt_api_key(encrypted_key: str) -> str`
Расшифровывает хранимый API ключ.

**Параметры:**
- `encrypted_key`: Зашифрованный API ключ

**Возвращает:**
```python
str  # Расшифрованный API ключ
```

## Queue Management

### QueueManager

#### `__init__()`
Инициализация менеджера очередей.

#### `async def add_request(marketplace: str, request: Callable, priority: int = 0) -> Any`
Добавляет запрос в очередь соответствующего маркетплейса.

**Параметры:**
- `marketplace`: Название маркетплейса ('ozon' или 'wildberries')
- `request`: Асинхронная функция для выполнения запроса
- `priority`: Приоритет запроса (больше = выше приоритет)

**Возвращает:**
```python
Any  # Результат выполнения запроса
```

### RateLimiter

#### `__init__(requests_per_minute: int = 30, min_interval: float = 2.0)`
Инициализация ограничителя частоты запросов.

**Параметры:**
- `requests_per_minute`: Максимальное количество запросов в минуту
- `min_interval`: Минимальный интервал между запросами в секундах

#### `async def acquire()`
Ожидает возможности выполнить запрос.

## Notification Service

### NotificationService

#### `__init__(bot: Bot, db: Database)`
Инициализация сервиса уведомлений.

**Параметры:**
- `bot`: Экземпляр Telegram бота
- `db`: Экземпляр базы данных

#### `async def notify_promotion_changes(user_id: int, changes: Dict) -> None`
Отправляет уведомление о изменениях в акциях.

**Параметры:**
- `user_id`: ID пользователя в Telegram
- `changes`: Словарь с изменениями в акциях

**Формат changes:**
```python
{
    "ozon": {
        "new": List[Dict],      # Новые акции
        "changed": List[Dict],  # Измененные акции
        "ended": List[Dict]     # Завершенные акции
    },
    "wildberries": {
        "new": List[Dict],
        "changed": List[Dict],
        "ended": List[Dict]
    }
}
```

## Payment API

### Telegram Payment Service

#### `create_invoice(chat_id: int, plan: SubscriptionPlan, title: str, description: str) -> Dict[str, Any]`
Создает счет для оплаты подписки.

**Параметры:**
- `chat_id`: ID чата пользователя
- `plan`: План подписки (MONTHLY, QUARTERLY, YEARLY)
- `title`: Название подписки
- `description`: Описание подписки

**Возвращает:**
```python
Dict[str, Any]
```

**Пример ответа:**
```python
{
    "invoice_id": "inv_123456",
    "total_amount": 1000,
    "currency": "RUB"
}
```

## Monitoring API

### Promotion Monitor

#### `async def check_promotions() -> List[PromotionChange]`
Проверяет изменения в акциях для всех активных пользователей.

**Возвращает:**
```python
List[PromotionChange]
```

**Пример ответа:**
```python
[
    {
        "user_id": 123456789,
        "marketplace": "ozon",
        "promotion_id": "789012",
        "change_type": "new",
        "old_value": None,
        "new_value": {
            "products_count": 5,
            "name": "Hot Sale"
        }
    }
]
```

## Database API

### User Operations

#### `add_user(user_id: int, username: str)`
Добавляет нового пользователя.

#### `get_user(user_id: int)`
Получает информацию о пользователе.

### Subscription Operations

#### `add_subscription(user_id: int, plan: SubscriptionPlan, end_date: datetime)`
Добавляет подписку пользователю.

#### `get_user_subscription(user_id: int)`
Получает информацию о подписке пользователя.

### Payment Operations

#### `add_payment(user_id: int, amount: int, currency: str, provider_payment_id: str, status: PaymentStatus)`
Записывает информацию о платеже.

#### `update_payment_status(payment_id: int, status: PaymentStatus)`
Обновляет статус платежа.
