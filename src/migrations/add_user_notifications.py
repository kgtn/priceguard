"""
Migration script to add user_notifications table.
"""

import asyncio
import aiosqlite
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, src_dir)

from core.config import load_config

async def migrate(database_path: str):
    """Run migration."""
    print("Starting migration...")
    
    async with aiosqlite.connect(database_path) as db:
        # Create user_notifications table
        try:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """)
            print("Created user_notifications table")
            
            # Create index for faster lookups
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_notifications 
                ON user_notifications(user_id, type);
            """)
            print("Created index on user_notifications")
            
            await db.commit()
            print("Migration completed successfully!")
        except Exception as e:
            print(f"Error during migration: {e}")

async def main():
    """Main function."""
    config = load_config()
    database_path = config.database.path
    
    await migrate(database_path)

if __name__ == "__main__":
    asyncio.run(main())
