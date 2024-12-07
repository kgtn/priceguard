"""
Tests for promotion monitoring system.
"""

import pytest
from unittest.mock import AsyncMock, patch

from services.monitoring.monitor import PromotionMonitor
from services.monitoring.notifications import NotificationService

@pytest.mark.asyncio
async def test_monitor_start_stop(monitor: PromotionMonitor):
    """Test monitor start and stop."""
    await monitor.start()
    assert monitor.is_running
    await monitor.stop()
    assert not monitor.is_running

@pytest.mark.asyncio
async def test_promotion_check(monitor: PromotionMonitor, database):
    """Test promotion check functionality."""
    with patch("services.marketplaces.ozon.OzonClient.get_hot_sales") as mock_ozon:
        mock_ozon.return_value = AsyncMock(return_value=[
            {
                "id": "123",
                "name": "Test Product",
                "price": 1000,
                "action_price": 800,
                "stock": 10
            }
        ])
        
        # Add test user with Ozon marketplace
        await database.add_user(123, "test")
        await database.add_marketplace(123, "ozon", "test_key")
        
        # Run check
        changes = await monitor.check_promotions()
        assert len(changes) > 0
        assert changes[0].marketplace == "ozon"

@pytest.mark.asyncio
async def test_notification_sending(notification_service: NotificationService, bot):
    """Test notification sending."""
    with patch("aiogram.Bot.send_message") as mock_send:
        mock_send.return_value = AsyncMock()
        
        await notification_service.notify_user(
            user_id=123,
            message="Test notification"
        )
        
        mock_send.assert_called_once()
        assert mock_send.call_args[1]["chat_id"] == 123
        assert "Test notification" in mock_send.call_args[1]["text"]

@pytest.mark.asyncio
async def test_promotion_comparison(monitor: PromotionMonitor):
    """Test promotion comparison logic."""
    old_promotions = [
        {
            "id": "123",
            "price": 1000,
            "action_price": 800
        }
    ]
    new_promotions = [
        {
            "id": "123",
            "price": 1000,
            "action_price": 700
        },
        {
            "id": "456",
            "price": 500,
            "action_price": 400
        }
    ]
    
    changes = monitor.compare_promotions(old_promotions, new_promotions)
    
    assert len(changes.changed) == 1  # Price changed for id 123
    assert len(changes.new) == 1      # New promotion with id 456
    assert len(changes.ended) == 0    # No ended promotions
