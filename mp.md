# Ozon API: Список товаров, которые участвуют в акции Hot Sale

## Endpoint
**POST**  
`/v1/actions/hotsales/products`

---

## Пример ответа
```json
{
  "result": {
    "products": [
      {
        "action_price": 0,
        "date_day_promo": "string",
        "id": 0,
        "is_active": true,
        "max_action_price": 0,
        "min_stock": 0,
        "stock": 0
      }
    ],
    "total": 0
  }
}
```
Response Schema: application/json
result (object)
Результат работы метода.

products (Array of objects)
Список товаров.

action_price (number <double>)
Цена товара по акции.

date_day_promo (string)
Дата участия товара в акции в формате YYYY-MM-DD.

id (number <double>)
Идентификатор товара.

is_active (boolean)
Признак участия товара в акции.

max_action_price (number <double>)
Максимально возможная цена товара по акции.

min_stock (number <double>)
Минимальное число единиц товара в акции типа «Скидка на сток».

stock (number <double>)
Число единиц товара в акции типа «Скидка на сток»

total (number <double>)
Общее количество товаров, которое доступно для акции.
## метода валидации ключа ozon (рабочий):
```python
async def validate_api_key(self) -> bool:
        """
        Validate Ozon API key by making a test request.
        
        Returns:
            bool: True if API key is valid
            
        Raises:
            ValueError: If API key is invalid
        """
        try:
            # Use seller info endpoint for validation
            await self._make_request(
                method="POST",
                url=f"{self.base_url}/v3/product/info/stocks",
                headers=self._get_headers(),
                json={
                    "filter": {
                            "offer_id": [
                                "136834"
                            ],
                            "product_id": [
                                "214887921"
                            ],
                            "visibility": "ALL"
                        },
                        "last_id": "",
                        "limit": 100
                }
            )
            return True
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False
```

*******

## Метод Wildberries API: Детали акций, чтобы узнать какие товары в акциях

## Endpoint
**GET**  
`https://dp-calendar-api.wildberries.ru/api/v1/calendar/promotions/details`

---

## Пример ответа
```json
{
  "data": {
    "promotions": [
      {
        "id": 123,
        "name": "ХИТЫ ГОДА",
        "description": "В акции принимают участие самые популярные товары 2023 года. Карточки товаров будут выделены плашкой «ХИТ ГОДА», чтобы покупатели замечали эти товары среди других. Также они будут размещены под баннерами на главной странице и примут участие в PUSH-уведомлениях. С ценами для вступления в акцию вы можете ознакомиться ниже.",
        "advantages": [
          "Плашка",
          "Баннер",
          "Топ выдачи товаров"
        ],
        "startDateTime": "2023-06-05T21:00:00Z",
        "endDateTime": "2023-06-05T21:00:00Z",
        "inPromoActionLeftovers": 45,
        "inPromoActionTotal": 123,
        "notInPromoActionLeftovers": 3,
        "notInPromoActionTotal": 10,
        "participationPercentage": 10,
        "type": "auto",
        "exceptionProductsCount": 10
      }
    ]
  }
}
```
Response Schema: application/json
data (object)
Корневой объект данных.

promotions (Array of objects)
Список акций.

id (integer)
ID акции.

name (string)
Название акции.

description (string)
Описание акции.

advantages (Array of strings)
Преимущества акции. Например:

"Плашка"
"Баннер"
"Топ выдачи товаров"
startDateTime (string)
Дата и время начала акции в формате YYYY-MM-DDTHH:MM:SSZ.

endDateTime (string)
Дата и время завершения акции в формате YYYY-MM-DDTHH:MM:SSZ.

inPromoActionLeftovers (integer)
Количество товаров с остатками, участвующих в акции.

inPromoActionTotal (integer)
Общее количество товаров, участвующих в акции.

notInPromoActionLeftovers (integer)
Количество товаров с остатками, не участвующих в акции.

notInPromoActionTotal (integer)
Общее количество товаров, не участвующих в акции.

participationPercentage (integer)
Процент товаров, уже участвующих в акции. Рассчитывается по товарам в акции и с остатком.

type (string)
Тип акции. Возможные значения:

"regular" — обычная акция.
"auto" — автоакция.
exceptionProductsCount (integer <uint>)
Количество товаров, исключённых из автоакции до её старта. (Только для "type": "auto")
Эти товары автоматически будут без скидки при старте акции.

Использование
С помощью данного метода можно получить информацию о том, сколько товаров клиента участвуют в автоакциях Wildberries ("type": "auto").

## Метод валидации ключа WB
```python
self.common_url = "https://common-api.wildberries.ru"
async def validate_api_key(self) -> bool:
        """
        Validate Wildberries API key by making a test request to /ping endpoint.
        
        Returns:
            bool: True if API key is valid
            
        Raises:
            ValueError: If API key is invalid
        """
        try:
            # Use ping endpoint for validation
            await self._make_request(
                method="GET",
                url=f"{self.common_url}/ping",
                headers=self._get_headers()
            )
            return True
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False
```



### Как получить API-ключ Ozon
После регистрации в Ozon Seller создайте свой уникальный API-ключ. Для этого:
Нажмите 123/ в правом верхнем углу личного кабинета. Выберите Настройки.
Перейдите в раздел Seller API (https://seller.ozon.ru/app/settings/api-keys).
Нажмите Сгенерировать ключ.
В открывшемся окне:
- укажите название для одного  API-ключа и укажите их в настройках;
- выберите роль Admin read only (в самом конце).
Нажмите Сгенерировать.


### Как создать токен Wildberries
В личном кабинете нажмите на имя профиля и выберите Настройки → Доступ к API (https://seller.wildberries.ru/supplier-settings/access-to-api).
Выберите опцию:

Только на чтение: с токеном нельзя ничего изменять, только получать данные. 
Выберите, с какими категориями API вы будете работать с этим токеном - Цены и скидки,
Календарь акций
