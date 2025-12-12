"""Payment validation and error handling helpers."""

from typing import Optional, Tuple
from aiogram import html
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from database import db
from logger_config import get_logger

logger = get_logger("aiogram.utils.payment_helpers")


async def validate_order_id(state: FSMContext) -> Tuple[Optional[int], bool]:
    """
    Extract and validate order_id from FSM state.
    
    Args:
        state: FSM context containing order data
        
    Returns:
        Tuple of (order_id, is_valid)
        - order_id: int if valid, None otherwise
        - is_valid: bool indicating validation success
    """
    try:
        data = await state.get_data()
        order_id = data.get('order_id')
        
        if not order_id:
            logger.warning("Order ID not found in FSM state")
            return None, False
        
        if not isinstance(order_id, int) or order_id <= 0:
            logger.warning(f"Invalid order ID format: {order_id}")
            return None, False
        
        return order_id, True
    except Exception as e:
        logger.error(f"Error validating order ID: {e}", exc_info=True)
        return None, False


async def get_and_validate_order(order_id: int, user_id: int) -> Tuple[Optional[dict], bool]:
    """
    Fetch order from database and validate it belongs to the user.
    
    Args:
        order_id: Order ID to fetch
        user_id: Telegram user ID for ownership validation
        
    Returns:
        Tuple of (order_data, is_valid)
        - order_data: dict with order information if valid, None otherwise
        - is_valid: bool indicating validation success
    """
    try:
        order_data = await db.get_order(order_id)
        
        if not order_data:
            logger.warning(f"Order not found - Order: {order_id}")
            return None, False
        
        # Verify order belongs to user
        if order_data.get('user_id') != user_id:
            logger.warning(
                f"Order doesn't belong to user - Order: {order_id}, User: {user_id}"
            )
            return None, False
        
        return order_data, True
    except Exception as e:
        logger.error(f"Error validating order: {e}", exc_info=True)
        return None, False


def get_order_summary_text(order_data: dict) -> str:
    """
    Return formatted order summary for UI messages.
    
    Args:
        order_data: Order data dictionary from database
        
    Returns:
        Formatted text string with order details
    """
    try:
        order_id = order_data.get('id', 'N/A')
        total_price = float(order_data.get('total_price', 0))
        formatted_price = f"{total_price:.2f}"
        
        summary = (
            f"💳 {html.bold('Оплата замовлення')}\n\n"
            f"📦 Замовлення: #{order_id}\n"
            f"💰 Сума: {formatted_price} грн"
        )
        
        return summary
    except Exception as e:
        logger.error(f"Error formatting order summary: {e}", exc_info=True)
        return "❌ Помилка при форматуванні замовлення"


async def handle_payment_error(
    callback: CallbackQuery,
    error_msg: str,
    show_alert: bool = True
) -> None:
    """
    Handle common payment error responses.
    
    Logs error and sends callback answer with error message.
    
    Args:
        callback: Callback query from user
        error_msg: Error message to display to user
        show_alert: Whether to show as alert or notification (default True)
    """
    try:
        logger.error(
            f"Payment error - User: {callback.from_user.id}, "
            f"Message: {error_msg}"
        )
        await callback.answer(error_msg, show_alert=show_alert)
    except Exception as e:
        logger.error(f"Error handling payment error response: {e}", exc_info=True)


async def validate_payment_state(
    callback: CallbackQuery,
    order_id: Optional[int]
) -> bool:
    """
    Validate callback request and order_id.
    
    Returns True if valid, handles error response and returns False otherwise.
    
    Args:
        callback: Callback query from user
        order_id: Order ID to validate (can be None)
        
    Returns:
        bool indicating validation success
    """
    try:
        # Validate callback is still valid (not expired)
        if not callback.message:
            logger.warning(
                f"Invalid callback - message not available - "
                f"User: {callback.from_user.id}"
            )
            await handle_payment_error(
                callback,
                "❌ Запит більше не активний",
                show_alert=True
            )
            return False
        
        # Validate order_id exists and is valid
        if not order_id or not isinstance(order_id, int) or order_id <= 0:
            logger.warning(
                f"Invalid payment state - User: {callback.from_user.id}, "
                f"Order ID: {order_id}"
            )
            await handle_payment_error(
                callback,
                "❌ Замовлення не знайдено",
                show_alert=True
            )
            return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating payment state: {e}", exc_info=True)
        await handle_payment_error(
            callback,
            "❌ Помилка при перевірці платежу",
            show_alert=True
        )
        return False
