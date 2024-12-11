"""
Migration script to add username and full_name columns to users table
and update existing users' data.
"""

import asyncio
import aiosqlite
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, src_dir)

from aiogram import Bot
from core.config import load_config

async def migrate(database_path: str, bot: Bot):
    """Run migration."""
    print("Starting migration...")
    
    async with aiosqlite.connect(database_path) as db:
        # Add new columns if they don't exist
        print("Adding new columns...")
        try:
            await db.execute("""
                ALTER TABLE users ADD COLUMN username TEXT;
            """)
            print("Added username column")
        except Exception as e:
            print(f"Username column might already exist: {e}")
            
        try:
            await db.execute("""
                ALTER TABLE users ADD COLUMN full_name TEXT;
            """)
            print("Added full_name column")
        except Exception as e:
            print(f"Full_name column might already exist: {e}")
            
        await db.commit()
        
        # Get all existing users
        print("Fetching existing users...")
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()
        
        # Update user info for each user
        print(f"Updating info for {len(users)} users...")
        for (user_id,) in users:
            try:
                # Get user info from Telegram
                user = await bot.get_chat(user_id)
                
                # Prepare user's full name
                full_name = user.first_name
                if user.last_name:
                    full_name += f" {user.last_name}"
                
                # Update user info
                await db.execute(
                    """
                    UPDATE users 
                    SET username = ?, full_name = ?
                    WHERE user_id = ?
                    """,
                    (user.username, full_name, user_id)
                )
                print(f"Updated user {user_id} (@{user.username if user.username else 'no username'})")
                
            except Exception as e:
                print(f"Failed to update user {user_id}: {e}")
                continue
        
        await db.commit()
    
    print("Migration completed!")

async def main():
    """Main function."""
    config = load_config()
    bot = Bot(token=config.telegram.token)
    
    try:
        await migrate(config.database.path, bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
