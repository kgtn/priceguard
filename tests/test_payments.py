"""
Tests for payment system.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from services.payments.models import PaymentStatus, SubscriptionPlan
from services.payments.telegram import TelegramPaymentService

@pytest.mark.asyncio
async def test_create_invoice(bot):
    """Test invoice creation."""
    payment_service = TelegramPaymentService(bot, "test_provider_token")
    
    with patch("aiogram.Bot.create_invoice") as mock_create:
        mock_create.return_value = AsyncMock(return_value={
            "invoice_id": "test_invoice"
        })
        
        invoice = await payment_service.create_invoice(
            chat_id=123,
            plan=SubscriptionPlan.MONTHLY,
            title="Monthly Subscription",
            description="Access to all features for 1 month"
        )
        
        mock_create.assert_called_once()
        assert invoice["invoice_id"] == "test_invoice"

@pytest.mark.asyncio
async def test_process_successful_payment(database):
    """Test successful payment processing."""
    payment_data = {
        "telegram_payment_charge_id": "test_charge",
        "provider_payment_charge_id": "test_provider_charge",
        "total_amount": 1000,
        "currency": "RUB"
    }
    
    user_id = 123
    await database.add_user(user_id, "test")
    
    # Record payment
    payment_id = await database.add_payment(
        user_id=user_id,
        amount=payment_data["total_amount"],
        currency=payment_data["currency"],
        provider_payment_id=payment_data["provider_payment_charge_id"],
        status=PaymentStatus.PENDING
    )
    
    # Update payment status
    await database.update_payment_status(
        payment_id=payment_id,
        status=PaymentStatus.COMPLETED
    )
    
    # Check subscription
    subscription = await database.get_user_subscription(user_id)
    assert subscription is not None
    assert subscription.status == "active"
    assert subscription.end_date > datetime.now()

@pytest.mark.asyncio
async def test_subscription_expiration(database):
    """Test subscription expiration handling."""
    user_id = 456
    await database.add_user(user_id, "test")
    
    # Add expired subscription
    expired_date = datetime.now() - timedelta(days=1)
    await database.add_subscription(
        user_id=user_id,
        plan=SubscriptionPlan.MONTHLY,
        end_date=expired_date
    )
    
    # Check subscription status
    subscription = await database.get_user_subscription(user_id)
    assert subscription is not None
    assert subscription.status == "expired"
