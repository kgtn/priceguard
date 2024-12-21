# Метода API Ozon 

## Ozon API:  Список акций

### **Описание**
Метод для получения списка акций, в которых можуг участвовать товары клиента

### **GET** `/v1/actions`
---

### Ответы

#### **200** Список акций  
**Response Schema:** `application/json`  

- **`result`**: `Array of objects`  
  Результаты запроса.  

##### **Array of Objects:**
- **`id`**: `number <double>`  
  Идентификатор акции.  

- **`title`**: `string`  
  Название акции.  

- **`action_type`**: `string`  
  Тип акции.  

- **`description`**: `string`  
  Описание акции.  

- **`date_start`**: `string`  
  Дата начала акции.  

- **`date_end`**: `string`  
  Дата окончания акции.  

- **`freeze_date`**: `string`  
  Дата приостановки акции.  
  - Если поле заполнено, продавец **не может** повышать цены, изменять список товаров и уменьшать количество единиц товаров в акции.  
  - Продавец **может** понижать цены и увеличивать количество единиц товара в акции.  

- **`potential_products_count`**: `number <double>`  
  Количество товаров, доступных для акции.  

- **`participating_products_count`**: `number <double>`  
  Количество товаров, которые участвуют в акции.  

- **`is_participating`**: `boolean`  
  Участвуете вы в этой акции или нет.  

- **`is_voucher_action`**: `boolean`  
  Признак, что для участия в акции покупателям нужен промокод.  

- **`banned_products_count`**: `number <double>`  
  Количество заблокированных товаров.  

- **`with_targeting`**: `boolean`  
  Признак, что акция с целевой аудиторией.  

- **`order_amount`**: `number <double>`  
  Сумма заказа.  

- **`discount_type`**: `string`  
  Тип скидки.  

- **`discount_value`**: `number <double>`  
  Размер скидки.  
---

## Список участвующих в акции товаров

Метод для получения списка товаров, участвующих в акции, по её идентификатору.

### **POST** `/v1/actions/products`


#### **200** Список товаров  
**Response Schema:** `application/json`  

- **`result`**: `object`  
  Результаты запроса.  

  - **`products`**: `Array of objects`  
    Список товаров.  

##### **Array of Objects:**
- **`id`**: `number <double>`  
  Идентификатор товара.  

- **`price`**: `number <double>`  
  Текущая цена товара без скидки.  

- **`action_price`**: `number <double>`  
  Цена товара по акции.  

- **`max_action_price`**: `number <double>`  
  Максимально возможная цена товара по акции.  

- **`add_mode`**: `string`  
  Тип добавления товара в акцию:  
  - автоматически  
  - вручную продавцом  

- **`min_stock`**: `number <double>`  
  Минимальное число единиц товара в акции типа «Скидка на сток».  

- **`stock`**: `number <double>`  
  Число единиц товара в акции типа «Скидка на сток».  

- **`total`**: `number <double>`  
  Общее количество товаров, которое доступно для акции.  
##### Пример
```
{
  "result": {
    "products": [
      {
        "id": 1383,
        "price": 5503,
        "action_price": 621,
        "max_action_price": 3712.1,
        "add_mode": "AUTO",
        "stock": 0,
        "min_stock": 0
      }
    ],
    "total": 1
  }
}
```
## Список доступных акций Hot Sale

### Endpoint
**POST** `/v1/actions/hotsales/list`

Метод для получения списка доступных акций Hot Sale.


## Список товаров, которые участвуют в акции Hot Sale

### Endpoint
**POST**  
`/v1/actions/hotsales/products`

---

#### Пример ответа
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

### метода валидации ключа ozon (рабочий):
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

# Метод Wildberries API:
## Детали акций, чтобы узнать какие товары в акциях

### Endpoint
**GET**  
`https://dp-calendar-api.wildberries.ru/api/v1/calendar/promotions`

### Query Parameters

#### `startDateTime` (required)
- **Type:** `string <RFC3339>`  
- **Example:** `startDateTime=2023-09-01T00:00:00Z`  
- **Description:** Начало периода, формат `YYYY-MM-DDTHH:MM:SSZ`.

#### `endDateTime` (required)
- **Type:** `string <RFC3339>`  
- **Example:** `endDateTime=2024-08-01T23:59:59Z`  
- **Description:** Конец периода, формат `YYYY-MM-DDTHH:MM:SSZ`.

#### `allPromo` (required)
- **Type:** `boolean`  
- **Default:** `false`  
- **Description:** Показать акции:  
  - `false` — доступные для участия  
  - `true` — все акции  

#### `limit` 
- **Type:** `integer <uint>` `[ 1 .. 1000 ]`  
- **Example:** `limit=10`  
- **Description:** Количество запрашиваемых акций.  

#### `offset` 
- **Type:** `integer <uint>` `>= 0`  
- **Example:** `offset=0`  
- **Description:** После какого элемента выдавать данные.  

---

#### Пример ответа
```json
{
"data": {
"promotions": []
}

```


promotions	
Array of objects
Array 
id	
integer
ID акции

name	
string
Название акции

startDateTime	
string <RFC3339>
Начало акции

endDateTime	
string <RFC3339>
Конец акции

type	
string
Enum: "regular" "auto"
Тип акции:

regular — акция
auto — автоакция

"regular" — обычная акция.
"auto" — автоакция.
exceptionProductsCount (integer <uint>)
Количество товаров, исключённых из автоакции до её старта. (Только для "type": "auto")
Эти товары автоматически будут без скидки при старте акции.
.

## Детальная информация по акциям WB

get
https://dp-calendar-api.wildberries.ru/api/v1/calendar/promotions/details

### Authorizations

#### HeaderApiKey
- **API Key:** `HeaderApiKey`  
- **Header parameter name:** `Authorization`  

---

### Query Parameters

#### `promotionIDs` (required)
- **Type:** `string` `[ 1 .. 100 ] items unique`  
- **Example:** `promotionIDs=1&promotionIDs=3&promotionIDs=64`  
- **Description:** ID акций, по которым нужно вернуть информацию.  

---

### Ответы

#### `200` Успешно

##### Response Schema: `application/json`
- **`data`**: `object`  
  - **`promotions`**: `Array of objects`  
    Список акций  

###### Array of Objects:
- **`id`**: `integer`  
  ID акции  

- **`name`**: `string`  
  Название акции  

- **`description`**: `string`  
  Описание акции  

- **`advantages`**: `Array of strings`  
  Преимущества акции  

- **`startDateTime`**: `string`  
  Начало акции  

- **`endDateTime`**: `string`  
  Конец акции  

- **`inPromoActionLeftovers`**: `integer`  
  Количество товаров с остатками, участвующих в акции  

- **`inPromoActionTotal`**: `integer`  
  Общее количество товаров, участвующих в акции  

- **`notInPromoActionLeftovers`**: `integer`  
  Количество товаров с остатками, не участвующих в акции  

- **`notInPromoActionTotal`**: `integer`  
  Общее количество товаров, не участвующих в акции  

- **`participationPercentage`**: `integer`  
  Уже участвующие в акции товары, %. Рассчитывается по товарам в акции и с остатком  

- **`type`**: `string`  
  Тип акции:  
  - Enum: `"regular"` `"auto"`  
  - `regular` — акция  
  - `auto` — автоакция  

- **`exceptionProductsCount`**: `integer <uint>`  
  Количество товаров, исключенных из автоакции до её старта.  
  - Только при `"type": "auto"`.  
  - В момент старта акции эти товары автоматически будут без скидки.  

- **`ranging`**: `Array of objects`  
  Ранжирование (если подключено).  


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
