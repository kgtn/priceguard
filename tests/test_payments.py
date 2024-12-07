"""
Tests for payment processing system.
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from services.payments.telegram import TelegramPaymentService
from services.payments.models import Payment, PaymentStatus, SubscriptionPlan

@pytest.mark.asyncio
async def test_create_invoice(bot):
    """Test invoice creation."""
    payment_service = TelegramPaymentService(bot, "test_provider_token")
    
    with patch.object(bot, "create_invoice") as mock_create:
        mock_create.return_value = "test_invoice"
        
        invoice = await payment_service.create_invoice(
            user_id=123,
            plan=SubscriptionPlan.MONTHLY
        )
        
        assert invoice == "test_invoice"
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_process_successful_payment(database):
    """Test successful payment processing."""
    payment_data = Payment(
        user_id=123,
        amount=1000,
        currency="RUB",
        provider_payment_id="test_provider_charge",
        status=PaymentStatus.COMPLETED
    )
    
    # Add test user
    await database.add_user(payment_data.user_id, "test")
    
    # Process payment
    await database.add_payment(payment_data)
    
    # Check subscription status
    subscription = await database.get_subscription(payment_data.user_id)
    assert subscription is not None
    assert subscription.is_active is True

@pytest.mark.asyncio
async def test_subscription_expiration(database):
    """Test subscription expiration handling."""
    user_id = 456
    await database.add_user(user_id, "test")
    
    # Add expired subscription
    expired_date = datetime.now() - timedelta(days=1)
    await database.update_subscription(
        user_id=user_id,
        expiry_date=expired_date,
        is_active=True
    )
    
    # Check subscription status
    subscription = await database.get_subscription(user_id)
    assert subscription is not None
    assert subscription.is_active is False
