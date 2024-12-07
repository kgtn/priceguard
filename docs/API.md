# API Documentation

## Marketplaces API

### Ozon Client

#### `get_hot_sales()`
Получает список активных акций на Ozon.

**Параметры:**
- Нет

**Возвращает:**
```python
List[Dict[str, Any]]
```
Пример:
```python
[
    {
        "id": "123456",
        "name": "Product Name",
        "price": 1000,
        "action_price": 800,
        "stock": 10,
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-01-31T23:59:59Z"
    }
]
```

### Wildberries Client

#### `get_auto_promotions()`
Получает список автоматических акций на Wildberries.

**Параметры:**
- Нет

**Возвращает:**
```python
List[Dict[str, Any]]
```
Пример:
```python
[
    {
        "id": "789012",
        "name": "Auto Promotion",
        "discount": 20,
        "products_count": 5,
        "start_date": "2024-01-01T00:00:00Z",
        "end_date": "2024-01-31T23:59:59Z"
    }
]
```

## Payment API

### Telegram Payment Service

#### `create_invoice(chat_id: int, plan: SubscriptionPlan, title: str, description: str)`
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
Пример:
```python
{
    "invoice_id": "inv_123456",
    "total_amount": 1000,
    "currency": "RUB"
}
```

## Monitoring API

### Promotion Monitor

#### `check_promotions()`
Проверяет изменения в акциях для всех активных пользователей.

**Параметры:**
- Нет

**Возвращает:**
```python
List[PromotionChange]
```
Пример:
```python
[
    {
        "marketplace": "ozon",
        "user_id": 123456,
        "changes": {
            "new": [...],
            "changed": [...],
            "ended": [...]
        }
    }
]
```

### Notification Service

#### `notify_user(user_id: int, message: str)`
Отправляет уведомление пользователю.

**Параметры:**
- `user_id`: ID пользователя
- `message`: Текст уведомления

**Возвращает:**
```python
bool
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
