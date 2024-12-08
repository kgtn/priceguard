"""
Database management and models for the PriceGuard bot.
File: src/core/database.py
"""

import aiosqlite
from typing import Optional, List, Dict
from datetime import datetime
import json

CREATE_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        email TEXT,
        ozon_api_key TEXT,
        ozon_client_id TEXT,
        wildberries_api_key TEXT,
        subscription_status TEXT CHECK(subscription_status IN ('active', 'inactive', 'trial')) NOT NULL DEFAULT 'trial',
        subscription_end_date TIMESTAMP,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        check_interval INTEGER NOT NULL DEFAULT 3600
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS promo_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        marketplace TEXT NOT NULL CHECK(marketplace IN ('ozon', 'wildberries')),
        base_count INTEGER NOT NULL,
        last_checked_count INTEGER NOT NULL,
        last_checked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS payments (
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        status TEXT NOT NULL,
        months INTEGER NOT NULL,
        created_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        payment_id TEXT NOT NULL,
        start_date TIMESTAMP NOT NULL,
        end_date TIMESTAMP NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (payment_id) REFERENCES payments(id)
    );
    """
]

class Database:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.db: Optional[aiosqlite.Connection] = None

    async def init(self):
        """Initialize database connection and create tables."""
        self.db = await aiosqlite.connect(self.database_path)
        await self.db.execute("PRAGMA foreign_keys = ON")
        
        for table_query in CREATE_TABLES:
            await self.db.execute(table_query)
        await self.db.commit()

    async def close(self):
        """Close database connection."""
        if self.db:
            await self.db.close()
            self.db = None

    async def add_user(self, user_id: int, email: Optional[str] = None) -> bool:
        """Add new user to the database."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        try:
            await self.db.execute(
                "INSERT OR IGNORE INTO users (user_id, email) VALUES (?, ?)",
                (user_id, email)
            )
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise

    async def update_api_keys(self, user_id: int, ozon_key: Optional[str] = None, 
                            wildberries_key: Optional[str] = None) -> bool:
        """Update marketplace API keys for user."""
        if not self.db:
            raise RuntimeError("Database not initialized")

        update_fields = []
        params = []
        if ozon_key is not None:
            update_fields.append("ozon_api_key = ?")
            params.append(ozon_key)
        if wildberries_key is not None:
            update_fields.append("wildberries_api_key = ?")
            params.append(wildberries_key)
        
        if not update_fields:
            return False

        params.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = ?"
        
        try:
            await self.db.execute(query, params)
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise

    async def update_subscription(self, user_id: int, status: str, 
                                end_date: datetime) -> bool:
        """Update user subscription status and end date."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        try:
            await self.db.execute(
                """
                UPDATE users 
                SET subscription_status = ?, subscription_end_date = ?
                WHERE user_id = ?
                """,
                (status, end_date.isoformat(), user_id)
            )
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user information."""
        if not self.db:
            raise RuntimeError("Database not initialized")

        async with self.db.execute(
            "SELECT * FROM users WHERE user_id = ?", 
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))

    async def get_all_users(self) -> List[Dict]:
        """Get all users from database."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        users = []
        async with self.db.execute("SELECT * FROM users") as cursor:
            async for row in cursor:
                users.append({
                    "user_id": row[0],
                    "email": row[1],
                    "ozon_api_key": row[2],
                    "ozon_client_id": row[3],
                    "wildberries_api_key": row[4],
                    "subscription_status": row[5],
                    "subscription_end_date": row[6],
                    "created_at": row[7],
                    "check_interval": row[8]
                })
        return users

    async def update_promo_check(self, user_id: int, marketplace: str,
                               base_count: int, current_count: int) -> bool:
        """Update or create promo check record."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        try:
            await self.db.execute(
                """
                INSERT INTO promo_checks (user_id, marketplace, base_count, last_checked_count)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (user_id, marketplace) DO UPDATE SET
                    last_checked_count = ?,
                    last_checked_at = CURRENT_TIMESTAMP
                """,
                (user_id, marketplace, base_count, current_count, current_count)
            )
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise

    async def create_payment(self, payment_data: Dict) -> None:
        """Create payment record."""
        await self.db.execute(
            "INSERT INTO payments (id, user_id, amount, status, months, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                payment_data["id"],
                payment_data["user_id"],
                payment_data["amount"],
                payment_data["status"],
                payment_data["months"],
                payment_data["created_at"]
            )
        )
        await self.db.commit()

    async def update_payment(self, payment_id: str, payment_data: Dict) -> None:
        """Update payment record."""
        set_clause = ", ".join(f"{k} = ?" for k in payment_data.keys())
        query = f"UPDATE payments SET {set_clause} WHERE id = ?"
        await self.db.execute(query, (*payment_data.values(), payment_id))
        await self.db.commit()

    async def get_payment(self, payment_id: str) -> Optional[Dict]:
        """Get payment by ID."""
        async with self.db.execute(
            "SELECT * FROM payments WHERE id = ?",
            (payment_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))

    async def create_subscription(self, subscription_data: Dict) -> None:
        """Create subscription record."""
        await self.db.execute(
            "INSERT INTO subscriptions "
            "(user_id, payment_id, start_date, end_date, is_active) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                subscription_data["user_id"],
                subscription_data["payment_id"],
                subscription_data["start_date"],
                subscription_data["end_date"],
                subscription_data["is_active"]
            )
        )
        await self.db.commit()

    async def get_subscription(self, user_id: int) -> Optional[Dict]:
        """Get active subscription for user."""
        async with self.db.execute(
            "SELECT * FROM subscriptions "
            "WHERE user_id = ? AND is_active = 1 "
            "ORDER BY end_date DESC LIMIT 1",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))

    async def get_subscription_by_payment(self, payment_id: str) -> Optional[Dict]:
        """Get subscription by payment ID."""
        async with self.db.execute(
            "SELECT * FROM subscriptions WHERE payment_id = ?",
            (payment_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))

    async def get_all_subscriptions(self) -> List[Dict]:
        """Get all subscriptions."""
        async with self.db.execute("SELECT * FROM subscriptions") as cursor:
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    async def create_tables(self):
        """Create necessary tables if they don't exist."""
        async with aiosqlite.connect(self.database_path) as db:
            # Create users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    is_admin INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 0,
                    subscription_active INTEGER DEFAULT 0,
                    subscription_expires TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create api_keys table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    user_id INTEGER,
                    marketplace TEXT,
                    api_key TEXT,
                    client_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, marketplace),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            await db.commit()

    async def update_user_subscription(self, user_id: int, is_active: bool):
        """Update user subscription status."""
        async with aiosqlite.connect(self.database_path) as db:
            expires_at = (datetime.now() + datetime.timedelta(days=30)).isoformat() if is_active else None
            await db.execute(
                '''
                UPDATE users 
                SET subscription_active = ?, subscription_expires = ?
                WHERE user_id = ?
                ''',
                (1 if is_active else 0, expires_at, user_id)
            )
            await db.commit()

    async def check_subscription(self, user_id: int) -> bool:
        """Check if user has active subscription."""
        async with aiosqlite.connect(self.database_path) as db:
            async with db.execute(
                '''
                SELECT subscription_active, subscription_expires 
                FROM users 
                WHERE user_id = ?
                ''',
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return False
                
                is_active, expires_at = row
                if not is_active:
                    return False
                
                if expires_at:
                    expires = datetime.fromisoformat(expires_at)
                    if expires < datetime.now():
                        await self.update_user_subscription(user_id, False)
                        return False
                
                return True

    async def update_check_interval(self, user_id: int, interval_hours: int) -> bool:
        """Update user check interval in hours."""
        if not self.db:
            raise RuntimeError("Database not initialized")
        
        try:
            await self.db.execute(
                """
                UPDATE users 
                SET check_interval = ?
                WHERE user_id = ?
                """,
                (interval_hours * 3600, user_id)  # Convert hours to seconds
            )
            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise

    async def get_active_subscriptions(self) -> List[Dict]:
        """Get all active subscriptions."""
        async with self.db.execute(
            """
            SELECT s.*, u.check_interval
            FROM subscriptions s
            JOIN users u ON s.user_id = u.user_id
            WHERE u.subscription_status = 'active'
            AND s.start_date <= CURRENT_TIMESTAMP
            AND s.end_date > CURRENT_TIMESTAMP
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "user_id": row[1],
                    "payment_id": row[2],
                    "start_date": row[3],
                    "end_date": row[4],
                    "check_interval": row[5]
                }
                for row in rows
            ]

async def init_db(database_path: str) -> Database:
    """Initialize and return database instance."""
    db = Database(database_path)
    await db.init()
    return db
