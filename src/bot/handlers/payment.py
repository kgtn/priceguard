"""
Payment handlers for the PriceGuard bot.
File: src/bot/handlers/payment.py
"""

from datetime import datetime, timedelta
from typing import Dict

from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import LabeledPrice, PreCheckoutQuery

from core.config import Settings
from core.database import Database
from bot.keyboards.payment import get_subscription_plans_keyboard
from bot.utils.messages import format_subscription_info

router = Router()

SUBSCRIPTION_PRICES = {
    1: 299,   # 1 month
    3: 799,   # 3 months
    6: 1499,  # 6 months
    12: 2699  # 12 months
}

class PaymentStates(StatesGroup):
    """Payment FSM states."""
    selecting_plan = State()

@router.callback_query(F.data == "subscribe")
async def process_subscribe(callback: types.CallbackQuery, state: FSMContext):
    """Handle subscription request."""
    await state.set_state(PaymentStates.selecting_plan)
    await callback.message.edit_text(
        "💳 Выберите план подписки:",
        reply_markup=get_subscription_plans_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("subscribe_"))
async def process_plan_selection(
    callback: types.CallbackQuery,
    settings: Settings
):
    """Handle subscription plan selection."""
    months = int(callback.data.split("_")[1])
    amount = SUBSCRIPTION_PRICES[months]
    
    await callback.bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Подписка на {months} мес.",
        description=(
            f"Доступ ко всем функциям бота на {months} месяцев\n"
            "• Мониторинг акций\n"
            "• Уведомления об изменениях"
        ),
        payload=f"sub_{months}",
        provider_token=settings.telegram.payment_provider_token,
        currency="RUB",
        prices=[
            LabeledPrice(
                label=f"Подписка на {months} мес.",
                amount=amount * 100  # Amount in kopecks
            )
        ],
        start_parameter="subscribe",
        need_name=True,
        need_phone_number=False,
        need_email=True,
        need_shipping_address=False,
        is_flexible=False
    )
    await callback.answer()

@router.pre_checkout_query()
async def process_pre_checkout(
    pre_checkout_query: PreCheckoutQuery,
    db: Database
):
    """Handle pre-checkout query."""
    try:
        # Check if user exists
        user = await db.get_user(pre_checkout_query.from_user.id)
        if not user:
            await pre_checkout_query.answer(
                ok=False,
                error_message="Пользователь не найден. Используйте /start"
            )
            return

        await pre_checkout_query.answer(ok=True)
    except Exception as e:
        await pre_checkout_query.answer(
            ok=False,
            error_message="Произошла ошибка. Попробуйте позже."
        )

@router.message(F.successful_payment)
async def process_successful_payment(
    message: types.Message,
    db: Database
):
    """Handle successful payment."""
    try:
        payload = message.successful_payment.invoice_payload
        months = int(payload.split("_")[1])
        
        # Get current subscription if exists
        current_subscription = await db.get_subscription(message.from_user.id)
        
        # Calculate subscription dates
        start_date = datetime.now()
        if current_subscription and current_subscription.get("is_active"):
            # If user has active subscription, extend it
            current_end = datetime.fromisoformat(current_subscription.get("end_date"))
            if current_end > start_date:
                # If current subscription hasn't expired, start from its end date
                start_date = current_end
        
        # Add new period to start date
        end_date = start_date + timedelta(days=30 * months)
        
        # Create payment record first
        payment_id = str(message.successful_payment.provider_payment_charge_id)
        await db.create_payment({
            "id": payment_id,
            "user_id": message.from_user.id,
            "amount": float(message.successful_payment.total_amount) / 100,  # Convert from kopeks to rubles
            "status": "completed",
            "months": months,
            "created_at": datetime.now().isoformat()
        })

        # Create subscription
        await db.create_subscription({
            "user_id": message.from_user.id,
            "payment_id": payment_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "is_active": True
        })

        # Update user's subscription status
        await db.update_subscription(
            user_id=message.from_user.id,
            status="active",
            end_date=end_date
        )

        subscription = await db.get_subscription(message.from_user.id)
        await message.answer(
            "✅ Оплата прошла успешно!\n\n"
            f"{format_subscription_info(subscription)}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при активации подписки.\n"
            "Пожалуйста, обратитесь в поддержку."
        )
