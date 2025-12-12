"""Payment handlers for LiqPay and Telegram payments."""

from aiogram import Router, F, html
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, SuccessfulPayment
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import get_payment_method_keyboard, get_liqpay_payment_keyboard, get_payment_retry_keyboard, get_main_menu
from filters import IsUserFilter, IsUserCallbackFilter
from config import LIQPAY_CALLBACK_URL, PRIMARY_PAYMENT_METHOD, SHOW_PAYMENT_METHOD_CHOICE
from logger_config import get_logger
from handlers.payment_states import PaymentStates
from handlers.order_states import OrderStates
from payments import LiqPayService
from utils.payment_helpers import (
    validate_order_id,
    get_and_validate_order,
    get_order_summary_text,
    handle_payment_error,
    validate_payment_state
)

logger = get_logger("aiogram.handlers.payments")
router = Router()

liqpay_service = LiqPayService()


# ═════════════════════════════════════════════════════════════════════════════
# PAYMENT METHOD SELECTION
# ═════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "proceed_to_payment", IsUserCallbackFilter())
async def proceed_to_payment(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle proceed to payment - show payment method selection."""
    try:
        # Validate order_id from state
        order_id, is_valid = await validate_order_id(state)
        if not is_valid:
            await handle_payment_error(callback, "❌ Замовлення не знайдено")
            return
        
        # Validate order exists and belongs to user
        order_data, is_valid = await get_and_validate_order(order_id, callback.from_user.id)
        if not is_valid:
            await handle_payment_error(callback, "❌ Замовлення не знайдено")
            return
        
        # Get formatted order summary
        payment_text = get_order_summary_text(order_data) + "\n\nВиберіть спосіб оплати:"
        
        await state.set_state(PaymentStates.waiting_for_payment_method)
        
        await callback.message.edit_text(
            payment_text,
            reply_markup=get_payment_method_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in proceed_to_payment: {e}", exc_info=True)
        await handle_payment_error(callback, "❌ Помилка при обробці платежу")


@router.callback_query(F.data.startswith("payment_method:"), PaymentStates.waiting_for_payment_method, IsUserCallbackFilter())
async def select_payment_method(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle payment method selection."""
    try:
        payment_method = callback.data.split(":")[1]  # 'liqpay' or 'telegram'
        
        # Validate order_id from state
        order_id, is_valid = await validate_order_id(state)
        if not await validate_payment_state(callback, order_id):
            return
        
        # Validate order exists and belongs to user
        order_data, is_valid = await get_and_validate_order(order_id, callback.from_user.id)
        if not is_valid:
            await handle_payment_error(callback, "❌ Замовлення не знайдено")
            return
        
        await state.update_data(payment_method=payment_method)
        
        if payment_method == "liqpay":
            await handle_liqpay_payment(callback, state, order_id, order_data)
        elif payment_method == "telegram":
            await handle_telegram_payment(callback, state, order_id, order_data)
        else:
            await handle_payment_error(callback, "❌ Невідомий спосіб оплати")
        
    except Exception as e:
        logger.error(f"Error in select_payment_method: {e}", exc_info=True)
        await handle_payment_error(callback, "❌ Помилка при обробці платежу")


async def handle_liqpay_payment(callback: CallbackQuery, state: FSMContext, order_id: int, order_data: dict) -> None:
    """Generate LiqPay payment link and send to user."""
    try:
        # Check if LiqPay is configured
        if not liqpay_service.public_key or not liqpay_service.private_key:
            await callback.message.edit_text(
                "❌ LiqPay платежі наразі недоступні.\n\n"
                "Будь ласка, спробуйте пізніше або виберіть інший спосіб оплати.",
                reply_markup=get_payment_method_keyboard()
            )
            await callback.answer()
            return
        
        # Create payment record
        payment_id = await db.create_payment_record(
            order_id=order_id,
            user_id=callback.from_user.id,
            amount=float(order_data['total_price']),
            payment_method="liqpay"
        )
        
        if not payment_id:
            await callback.answer("❌ Помилка при створенні платежу", show_alert=True)
            return
        
        # Generate payment URL
        payment_url = liqpay_service.generate_payment_url(
            order_id=order_id,
            amount=float(order_data['total_price']),
            user_id=callback.from_user.id,
            description=f"Замовлення #{order_id}"
        )
        
        if not payment_url:
            await callback.answer("❌ Помилка при генерації посилання на оплату", show_alert=True)
            return
        
        # Send payment link
        await state.set_state(PaymentStates.waiting_for_liqpay_confirmation)
        
        payment_text = (
            f"💳 {html.bold('LiqPay Оплата')}\n\n"
            f"📦 Замовлення: #{order_id}\n"
            f"💰 Сума: {float(order_data['total_price']):.2f} грн\n\n"
            f"Натисніть кнопку нижче, щоб перейти до оплати.\n"
            f"Після успішної оплати ми отримаємо сповіщення та\n"
            f"підтвердимо ваше замовлення."
        )
        
        await callback.message.edit_text(
            payment_text,
            reply_markup=get_liqpay_payment_keyboard(payment_url)
        )
        await callback.answer()
        
        logger.info(f"LiqPay payment initiated - Order: {order_id}, Payment ID: {payment_id}")
        
    except Exception as e:
        logger.error(f"Error in handle_liqpay_payment: {e}", exc_info=True)
        await callback.answer("❌ Помилка при обробці платежу", show_alert=True)


async def handle_telegram_payment(callback: CallbackQuery, state: FSMContext, order_id: int, order_data: dict) -> None:
    """Handle Telegram native payment (placeholder for future implementation)."""
    try:
        await callback.message.edit_text(
            "❌ Telegram платежі наразі недоступні.\n\n"
            "Будь ласка, виберіть LiqPay для оплати.",
            reply_markup=get_payment_method_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in handle_telegram_payment: {e}", exc_info=True)
        await callback.answer("❌ Помилка при обробці платежу", show_alert=True)


# ═════════════════════════════════════════════════════════════════════════════
# LIQPAY WEBHOOK CALLBACK
# ═════════════════════════════════════════════════════════════════════════════

@router.message(Command("webhook_test"))
async def webhook_test(message: Message) -> None:
    """Test webhook endpoint (for debugging)."""
    if message.from_user.id not in [int(id) for id in __import__('config').ADMIN_IDS if id]:
        await message.answer("❌ Доступ заборонений")
        return
    
    await message.answer(
        "🔗 Webhook endpoint ready\n\n"
        "POST to: /webhook/liqpay\n"
        f"Callback URL configured: {bool(LIQPAY_CALLBACK_URL)}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# PAYMENT RETRY
# ═════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "payment_retry", IsUserCallbackFilter())
async def payment_retry(callback: CallbackQuery, state: FSMContext) -> None:
    """Allow user to retry payment."""
    try:
        # Validate order_id
        order_id, is_valid = await validate_order_id(state)
        if not is_valid:
            await handle_payment_error(callback, "❌ Замовлення не знайдено")
            return
        
        # Reset to payment method selection
        await state.set_state(PaymentStates.waiting_for_payment_method)
        
        payment_text = (
            f"💳 {html.bold('Оплата замовлення')}\n\n"
            f"📦 Замовлення: #{order_id}\n\n"
            f"Виберіть спосіб оплати:"
        )
        
        await callback.message.edit_text(
            payment_text,
            reply_markup=get_payment_method_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in payment_retry: {e}", exc_info=True)
        await handle_payment_error(callback, "❌ Помилка при обробці платежу")


@router.callback_query(F.data == "payment_cancel", IsUserCallbackFilter())
async def payment_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    """Allow user to cancel payment and order."""
    try:
        data = await state.get_data()
        order_id = data.get('order_id')
        
        if order_id:
            # Mark order as cancelled
            await db.update_order_status(order_id, 'cancelled')
            
            # Update payment status if exists
            payment = await db.get_payment_by_order(order_id)
            if payment:
                await db.update_payment_status(payment['id'], 'cancelled')
            
            logger.info(f"Order cancelled - Order: {order_id}, User: {callback.from_user.id}")
        
        await state.clear()
        
        await callback.message.edit_text(
            "❌ Замовлення скасовано.\n\n"
            "Ви можете створити нове замовлення, натиснувши 🛒 Замовити ще",
            reply_markup=None
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in payment_cancel: {e}", exc_info=True)
        await callback.answer("❌ Помилка при обробці запиту", show_alert=True)
