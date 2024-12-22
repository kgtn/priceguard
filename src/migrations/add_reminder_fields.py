"""
Migration script to add reminder-related fields to users table.
"""

import asyncio
import aiosqlite
import os
import sys
from pathlib import Path
from datetime import datetime

# Add src directory to Python path
src_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, src_dir)

from core.config import load_config

async def migrate(database_path: str):
    """Run migration."""
    print("Starting migration...")
    
    async with aiosqlite.connect(database_path) as db:
        # Add new columns if they don't exist
        print("Adding new columns...")
        
        # Add last_reminder_sent column
        try:
            await db.execute("""
                ALTER TABLE users ADD COLUMN last_reminder_sent TIMESTAMP;
            """)
            print("Added last_reminder_sent column")
        except Exception as e:
            print(f"last_reminder_sent column might already exist: {e}")
            
        # Add setup_status column with enum check
        try:
            await db.execute("""
                ALTER TABLE users ADD COLUMN setup_status TEXT 
                CHECK (setup_status IN ('started', 'api_added', 'api_validated'))
                DEFAULT 'started';
            """)
            print("Added setup_status column")
        except Exception as e:
            print(f"setup_status column might already exist: {e}")
        
        # Update setup_status based on existing data
        await db.execute("""
            UPDATE users 
            SET setup_status = CASE
                WHEN (ozon_api_key IS NOT NULL OR wildberries_api_key IS NOT NULL) THEN 'api_added'
                ELSE 'started'
            END
            WHERE setup_status = 'started';
        """)
        print("Updated setup_status for existing users")
        
        await db.commit()
        print("Migration completed successfully!")

async def main():
    """Main function."""
    config = load_config()
    database_path = config.database.path
    
    await migrate(database_path)

if __name__ == "__main__":
    asyncio.run(main())
