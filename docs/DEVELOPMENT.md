# Development Guide

## Архитектура проекта

### Основные компоненты

1. **Bot Layer**
   - Обработчики команд
   - Клавиатуры
   - Middleware для аутентификации и логирования

2. **Core Layer**
   - Конфигурация
   - База данных
   - Логирование

3. **Services Layer**
   - Маркетплейсы (Ozon, Wildberries)
   - Платежи (Telegram Payments)
   - Мониторинг и уведомления

### Диаграмма компонентов

```
[Telegram Bot] <-> [Bot Layer] <-> [Services Layer] <-> [Core Layer]
                                         ^
                                         |
                            [External APIs (Ozon, WB)]
```

## Добавление нового функционала

### Новый маркетплейс

1. Создайте новый класс в `src/services/marketplaces/`:
```python
from .base import MarketplaceClient

class NewMarketplaceClient(MarketplaceClient):
    async def get_promotions(self):
        # Implementation
        pass
```

2. Добавьте фабрику:
```python
def get_new_marketplace_client(api_key: str):
    return NewMarketplaceClient(api_key)
```

3. Обновите обработчики команд в `src/bot/handlers/`

### Новый тип подписки

1. Обновите модель в `src/services/payments/models.py`:
```python
class SubscriptionPlan(str, Enum):
    NEW_PLAN = "new_plan"
```

2. Добавьте цены в конфигурацию
3. Обновите обработчики платежей

## Тестирование

### Unit Tests

```bash
pytest tests/test_unit/
```

### Integration Tests

```bash
pytest tests/test_integration/
```

### End-to-End Tests

```bash
pytest tests/test_e2e/
```

## Деплой

### Подготовка

1. Обновите версию в `pyproject.toml`
2. Обновите CHANGELOG.md
3. Создайте тег версии

### Процесс

1. Остановите текущий инстанс бота
2. Обновите код
3. Примените миграции БД
4. Запустите новую версию

## Мониторинг

### Логи

- `logs/bot.log` - основной лог
- `logs/errors.log` - ошибки
- `logs/payments.log` - платежи

### Метрики

- Активные пользователи
- Успешные платежи
- Количество акций
- Время ответа API

## Безопасность

### API ключи

- Храните в переменных окружения
- Используйте шифрование в БД
- Регулярно обновляйте

### Пользовательские данные

- Храните только необходимое
- Шифруйте чувствительные данные
- Удаляйте по запросу

## Оптимизация

### База данных

- Используйте индексы
- Очищайте старые данные
- Мониторьте размер

### API запросы

- Кэшируйте ответы
- Используйте rate limiting
- Обрабатывайте ошибки

## Известные проблемы

1. Rate limiting на API маркетплейсов
   - Решение: Очередь запросов

2. Большие уведомления
   - Решение: Пагинация

## Roadmap

1. Новые маркетплейсы
2. Аналитика для продавцов
3. API для внешних интеграций
