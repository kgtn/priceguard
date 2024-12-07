"""
Tests for database operations.
"""

import pytest
from src.core.database import Database

@pytest.mark.asyncio
async def test_user_operations(database: Database):
    """Test user CRUD operations."""
    # Test adding user
    await database.add_user(123, "test_user")
    user = await database.get_user(123)
    assert user is not None
    assert user["telegram_id"] == 123
    assert user["username"] == "test_user"
    
    # Test updating user
    await database.update_user(123, "new_test_user")
    user = await database.get_user(123)
    assert user["username"] == "new_test_user"
    
    # Test deleting user
    await database.delete_user(123)
    user = await database.get_user(123)
    assert user is None

@pytest.mark.asyncio
async def test_marketplace_operations(database: Database):
    """Test marketplace operations."""
    # Setup test user
    await database.add_user(123, "test_user")
    
    # Test adding marketplace
    await database.add_marketplace(123, "ozon", "test_key")
    marketplaces = await database.get_user_marketplaces(123)
    assert len(marketplaces) == 1
    assert marketplaces[0]["name"] == "ozon"
    assert marketplaces[0]["api_key"] == "test_key"
    
    # Test updating marketplace
    await database.update_marketplace(123, "ozon", "new_test_key")
    marketplaces = await database.get_user_marketplaces(123)
    assert marketplaces[0]["api_key"] == "new_test_key"
    
    # Test deleting marketplace
    await database.delete_marketplace(123, "ozon")
    marketplaces = await database.get_user_marketplaces(123)
    assert len(marketplaces) == 0

@pytest.mark.asyncio
async def test_promotion_operations(database: Database):
    """Test promotion tracking operations."""
    # Setup test user and marketplace
    await database.add_user(123, "test_user")
    await database.add_marketplace(123, "ozon", "test_key")
    
    # Test adding promotion
    promotion = {
        "id": "test_promo",
        "name": "Test Product",
        "price": 1000,
        "action_price": 800,
        "marketplace": "ozon"
    }
    await database.add_promotion(123, promotion)
    
    # Test getting promotions
    promotions = await database.get_user_promotions(123)
    assert len(promotions) == 1
    assert promotions[0]["id"] == "test_promo"
    assert promotions[0]["price"] == 1000
    
    # Test updating promotion
    promotion["action_price"] = 700
    await database.update_promotion(123, promotion)
    promotions = await database.get_user_promotions(123)
    assert promotions[0]["action_price"] == 700
    
    # Test deleting promotion
    await database.delete_promotion(123, "test_promo")
    promotions = await database.get_user_promotions(123)
    assert len(promotions) == 0
