"""
Adds last_subscription_notification_sent field to users table.
"""

import sqlite3
from datetime import datetime

DATABASE_PATH = "sqlite.db"

def migrate():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        ALTER TABLE users
        ADD COLUMN last_subscription_notification_sent TEXT;
        """
    )
    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()