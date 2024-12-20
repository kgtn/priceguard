"""
Telegram payment service.
"""

from typing import Dict, Optional
from aiogram import Bot
from aiogram.types import LabeledPrice

from .models import SubscriptionPlan

class TelegramPaymentService:
    """Service for handling Telegram payments."""
    
    def __init__(self, bot: Bot, provider_token: str):
        """
        Initialize payment service.
        
        Args:
            bot: Telegram bot instance
            provider_token: Payment provider token
        """
        self.bot = bot
        self.provider_token = provider_token

    async def create_invoice(
        self,
        chat_id: int,
        plan: SubscriptionPlan,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict:
        """
        Create payment invoice.
        
        Args:
            chat_id: User's chat ID
            plan: Subscription plan
            title: Optional custom title
            description: Optional custom description
            
        Returns:
            Dict with invoice details
        """
        prices = [
            LabeledPrice(
                label=title or plan.title,
                amount=plan.price
            )
        ]
        
        invoice = await self.bot.create_invoice(
            chat_id=chat_id,
            title=title or plan.title,
            description=description or plan.description,
            payload=plan.value,
            provider_token=self.provider_token,
            currency="RUB",
            prices=prices,
            start_parameter=f"sub_{plan.value}",
            need_name=True,
            need_email=True,
            provider_data={
                "receipt": {
                    "items": [
                        {
                            "description": title or plan.title,
                            "quantity": "1.00",
                            "amount": plan.price,
                            "vat_code": 1,
                        }
                    ]
                }
            }
        )
        
        return {
            "invoice_id": invoice.invoice_link.split("/")[-1],
            "total_amount": plan.price,
            "currency": "RUB"
        }

    async def validate_pre_checkout(
        self,
        pre_checkout_query_id: str,
        ok: bool,
        error_message: Optional[str] = None
    ) -> None:
        """
        Answer pre-checkout query.
        
        Args:
            pre_checkout_query_id: Query ID
            ok: Whether to accept payment
            error_message: Error message if not accepting
        """
        await self.bot.answer_pre_checkout_query(
            pre_checkout_query_id=pre_checkout_query_id,
            ok=ok,
            error_message=error_message
        )
