"""Inline keyboards for payment selection."""

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_payment_method_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for payment method selection."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💳 LiqPay",
        callback_data="payment_method:liqpay"
    )
    builder.button(
        text="📱 Telegram Pay",
        callback_data="payment_method:telegram"
    )
    builder.button(
        text="🏠 На початок",
        callback_data="back_to_start"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_payment_retry_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard for payment retry options."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 Спробувати ще раз",
        callback_data="payment_retry"
    )
    builder.button(
        text="❌ Скасувати замовлення",
        callback_data="payment_cancel"
    )
    builder.button(
        text="🏠 На початок",
        callback_data="back_to_start"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_liqpay_payment_keyboard(payment_url: str) -> InlineKeyboardMarkup:
    """Create keyboard with LiqPay payment link."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💳 Перейти до оплати LiqPay",
        url=payment_url
    )
    builder.button(
        text="🏠 На початок",
        callback_data="back_to_start"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_order_with_payment_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Create keyboard for order confirmation with payment option."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="💳 Оплатити замовлення",
        callback_data=f"proceed_to_payment"
    )
    builder.button(
        text="🛍 Замовити ще",
        callback_data="back_to_catalog"
    )
    builder.button(
        text="📦 Мої замовлення",
        callback_data="my_orders"
    )
    builder.adjust(1)
    return builder.as_markup()
