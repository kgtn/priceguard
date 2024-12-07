"""
Tests for notification service.
"""

import pytest
from unittest.mock import AsyncMock, patch
from src.services.monitoring.notifications import NotificationService
from src.core.database import Database

@pytest.mark.asyncio
async def test_notification_service_init(notification_service: NotificationService):
    """Test notification service initialization."""
    assert notification_service.bot is not None
    assert notification_service.database is not None

@pytest.mark.asyncio
async def test_send_notification(notification_service: NotificationService, bot):
    """Test sending notification to user."""
    with patch.object(bot, "send_message", AsyncMock(return_value=True)) as mock_send:
        result = await notification_service.notify_user(
            user_id=123,
            message="Test notification"
        )
        
        assert result is True
        mock_send.assert_called_once_with(
            chat_id=123,
            text="Test notification"
        )

@pytest.mark.asyncio
async def test_format_promotion_message(notification_service: NotificationService):
    """Test promotion message formatting."""
    promotion = {
        "id": "test_promo",
        "name": "Test Product",
        "price": 1000,
        "action_price": 800,
        "marketplace": "ozon",
        "url": "https://example.com/product"
    }
    
    message = notification_service.format_promotion_message(promotion)
    assert "Test Product" in message
    assert "1000" in message
    assert "800" in message
    assert "ozon" in message
    assert "https://example.com/product" in message

@pytest.mark.asyncio
async def test_notify_price_changes(notification_service: NotificationService, database: Database):
    """Test notifying about price changes."""
    # Setup test user
    await database.add_user(123, "test_user")
    
    changes = {
        "new": [{
            "id": "new_promo",
            "name": "New Product",
            "price": 500,
            "action_price": 400,
            "marketplace": "ozon"
        }],
        "changed": [{
            "id": "changed_promo",
            "name": "Changed Product",
            "old_price": 1000,
            "new_price": 800,
            "marketplace": "ozon"
        }],
        "ended": [{
            "id": "ended_promo",
            "name": "Ended Product",
            "marketplace": "ozon"
        }]
    }
    
    with patch.object(notification_service, "notify_user", AsyncMock(return_value=True)) as mock_notify:
        await notification_service.notify_price_changes(123, changes)
        assert mock_notify.call_count == 3  # One call for each type of change
