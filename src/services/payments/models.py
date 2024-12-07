"""
Payment and subscription models.
"""

from enum import Enum
from typing import Optional
from datetime import datetime

class PaymentStatus(str, Enum):
    """Payment status enum."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class SubscriptionPlan(str, Enum):
    """Subscription plan enum."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

    @property
    def price(self) -> int:
        """Get plan price in kopeks."""
        prices = {
            self.MONTHLY: 49900,    # 499 RUB
            self.QUARTERLY: 129900,  # 1299 RUB
            self.YEARLY: 399900     # 3999 RUB
        }
        return prices[self]

    @property
    def duration_days(self) -> int:
        """Get plan duration in days."""
        durations = {
            self.MONTHLY: 30,
            self.QUARTERLY: 90,
            self.YEARLY: 365
        }
        return durations[self]

    @property
    def title(self) -> str:
        """Get plan title."""
        titles = {
            self.MONTHLY: "Месячная подписка",
            self.QUARTERLY: "Квартальная подписка",
            self.YEARLY: "Годовая подписка"
        }
        return titles[self]

    @property
    def description(self) -> str:
        """Get plan description."""
        descriptions = {
            self.MONTHLY: "Доступ ко всем функциям на 1 месяц",
            self.QUARTERLY: "Доступ ко всем функциям на 3 месяца",
            self.YEARLY: "Доступ ко всем функциям на 1 год"
        }
        return descriptions[self]

class Subscription:
    """User subscription model."""
    
    def __init__(
        self,
        user_id: int,
        plan: SubscriptionPlan,
        start_date: datetime,
        end_date: datetime,
        status: str = "active",
        payment_id: Optional[int] = None
    ):
        self.user_id = user_id
        self.plan = plan
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.payment_id = payment_id

    @property
    def is_active(self) -> bool:
        """Check if subscription is active."""
        return (
            self.status == "active" and
            self.end_date > datetime.now()
        )

    @property
    def days_left(self) -> int:
        """Get days left in subscription."""
        if not self.is_active:
            return 0
        delta = self.end_date - datetime.now()
        return max(0, delta.days)

class Payment:
    """Payment model."""
    
    def __init__(
        self,
        user_id: int,
        amount: int,
        currency: str,
        provider_payment_id: str,
        status: PaymentStatus = PaymentStatus.PENDING,
        payment_id: Optional[int] = None,
        created_at: Optional[datetime] = None
    ):
        self.payment_id = payment_id
        self.user_id = user_id
        self.amount = amount
        self.currency = currency
        self.provider_payment_id = provider_payment_id
        self.status = status
        self.created_at = created_at or datetime.now()
