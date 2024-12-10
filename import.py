import sqlite3
import json

# Путь к вашей базе данных
DB_PATH = "sqlite copy.db"

# Путь к вашему JSON-файлу
JSON_PATH = "waitlist.json"

# Подключение к базе данных
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Убедитесь, что таблица существует
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    email TEXT,
    ozon_api_key TEXT,
    wildberries_api_key TEXT,
    subscription_status TEXT CHECK(subscription_status IN ('active', 'inactive', 'trial')) NOT NULL DEFAULT 'trial',
    subscription_end_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    check_interval INTEGER NOT NULL DEFAULT 3600,
    ozon_client_id TEXT
);
""")

# Чтение данных из JSON
with open(JSON_PATH, "r") as file:
    data = json.load(file)

# Перенос данных в базу
for user in data:
    cursor.execute("""
    INSERT OR IGNORE INTO users (
        user_id, email, ozon_api_key, wildberries_api_key, 
        subscription_status, subscription_end_date, created_at, 
        check_interval, ozon_client_id
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user["user_id"],
        user["email"],
        user["ozon_api_key"],
        user["wildberries_api_key"],
        user["subscription_status"],
        user["subscription_end_date"],
        user["created_at"],
        user["check_interval"],
        user["ozon_client_id"]
    ))

# Сохранение изменений и закрытие подключения
conn.commit()
conn.close()

print("Данные успешно импортированы!")
