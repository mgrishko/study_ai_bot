"""FSM states for payment processing."""

from aiogram.fsm.state import State, StatesGroup


class PaymentStates(StatesGroup):
    """FSM states for payment flow."""
    
    waiting_for_payment_method = State()     # Choose payment method (LiqPay/Telegram)
    waiting_for_liqpay_confirmation = State()  # Pending LiqPay callback
    waiting_for_telegram_payment = State()   # Waiting for Telegram payment
    payment_completed = State()               # Payment successful
