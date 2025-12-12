"""Handlers для замовлень (користувач)."""
from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import (
    get_order_confirmation_keyboard,
    get_my_orders_keyboard,
    get_order_with_payment_keyboard
)
from filters import IsUserFilter, IsUserCallbackFilter
from handlers.order_states import OrderStates
from handlers.payment_states import PaymentStates
from validators import validate_phone, validate_email
from logger_config import get_logger

logger = get_logger("aiogram.handlers")

router = Router()


@router.message(Command("myorders"), IsUserFilter())
async def command_my_orders_handler(message: Message) -> None:
    """Обробник команди /myorders."""
    orders = await db.get_user_orders(message.from_user.id)
    
    if not orders:
        await message.answer("📭 У вас ще немає замовлень. Перегляньте /catalog!")
        return
    
    orders_text = f"📦 {html.bold('Ваші замовлення:')}\n\n"
    
    status_emoji = {
        'pending': '🕐',
        'confirmed': '✅',
        'shipped': '🚚',
        'delivered': '📬',
        'cancelled': '❌'
    }
    
    for order in orders:
        status = order['status']
        emoji = status_emoji.get(status, '❓')
        
        orders_text += (
            f"{emoji} {html.bold(f'Замовлення #{order['id']}')}\n"
            f"   Товар: {order['product_name']}\n"
            f"   Кількість: {order['quantity']} шт.\n"
            f"   Сума: {float(order['total_price']):.2f} грн\n"
            f"   Статус: {status}\n"
            f"   Дата: {order['created_at']}\n\n"
        )
    
    await message.answer(orders_text)


@router.callback_query(F.data == "my_orders", IsUserCallbackFilter())
async def my_orders_callback(callback: CallbackQuery) -> None:
    """Обробник callback для перегляду замовлень."""
    orders = await db.get_user_orders(callback.from_user.id)
    
    if not orders:
        await callback.message.edit_text("📭 У вас ще немає замовлень. Перегляньте /catalog!")
        return
    
    orders_text = f"📦 {html.bold('Ваші замовлення:')}\n\n"
    
    status_emoji = {
        'pending': '🕐',
        'confirmed': '✅',
        'shipped': '🚚',
        'delivered': '📬',
        'cancelled': '❌'
    }
    
    for order in orders:
        status = order['status']
        emoji = status_emoji.get(status, '❓')
        
        orders_text += (
            f"{emoji} {html.bold(f'Замовлення #{order['id']}')}\n"
            f"   Товар: {order['product_name']}\n"
            f"   Кількість: {order['quantity']} шт.\n"
            f"   Сума: {float(order['total_price']):.2f} грн\n"
            f"   Статус: {status}\n"
            f"   Дата: {order['created_at']}\n\n"
        )
    
    await callback.message.edit_text(
        orders_text, 
        reply_markup=get_my_orders_keyboard()
    )
    await callback.answer()


# ═════════════════════════════════════════════════════════════════════════════
# HANDLERS ДЛЯ ЗАМОВЛЕННЯ З КОНТАКТНОЮ ІНФОРМАЦІЄЮ (FSM)
# ═════════════════════════════════════════════════════════════════════════════


@router.callback_query(F.data.startswith("order_product:"), IsUserCallbackFilter())
async def order_product_with_contact_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Почати замовлення з запитом контактної інформації."""
    try:
        product_id = int(callback.data.split(":")[1])
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return
        
        if product['stock'] < 1:
            await callback.answer("❌ Товар закінчився на складі", show_alert=True)
            return
        
        # Зберігаємо дані в FSM
        await state.update_data(
            product_id=product_id,
            product_name=product['name'],
            product_price=float(product['price']),
            quantity=1,
            user_id=callback.from_user.id,
            user_name=callback.from_user.full_name or "User"
        )
        
        # Просимо телефон
        await state.set_state(OrderStates.waiting_for_phone)
        await callback.message.edit_text(
            f"📱 {html.bold('Введіть ваш телефонний номер')}\n\n"
            f"Формати: +380501234567 або 0501234567\n\n"
            f"Товар: {product['name']}\n"
            f"Ціна: {float(product['price']):.2f} грн",
            reply_markup=None
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in order_product_with_contact_start: {e}", exc_info=True)
        await callback.answer("❌ Помилка при обробці запиту", show_alert=True)


@router.message(OrderStates.waiting_for_phone, IsUserFilter())
async def process_order_phone(message: Message, state: FSMContext) -> None:
    """Обробка телефонного номера."""
    phone = message.text
    is_valid, error = validate_phone(phone)
    
    if not is_valid:
        await message.answer(
            f"❌ {error}\n\n"
            f"Спробуйте знову. Формати: +380501234567 або 0501234567"
        )
        return
    
    # Зберігаємо телефон та просимо email
    await state.update_data(phone=phone)
    await state.set_state(OrderStates.waiting_for_email)
    
    await message.answer(
        f"📧 {html.bold('Введіть ваш email')}\n\n"
        f"Приклад: user@example.com"
    )


@router.message(OrderStates.waiting_for_email, IsUserFilter())
async def process_order_email(message: Message, state: FSMContext) -> None:
    """Обробка email адреси."""
    email = message.text
    is_valid, error = validate_email(email)
    
    if not is_valid:
        await message.answer(
            f"❌ {error}\n\n"
            f"Спробуйте знову. Приклад: user@example.com"
        )
        return
    
    # Зберігаємо email та просимо підтвердження
    data = await state.update_data(email=email)
    await state.set_state(OrderStates.waiting_for_confirmation)
    
    # Показуємо підсумок замовлення
    confirmation_text = (
        f"✅ {html.bold('Підтвердження замовлення')}\n\n"
        f"📋 Товар: {data['product_name']}\n"
        f"💰 Ціна: {data['product_price']:.2f} грн\n"
        f"📦 Кількість: {data['quantity']} шт.\n"
        f"📱 Телефон: {data['phone']}\n"
        f"📧 Email: {data['email']}\n\n"
        f"Всього: {data['product_price'] * data['quantity']:.2f} грн\n\n"
        f"Введіть 'так' для підтвердження або 'ні' для скасування:"
    )
    
    await message.answer(confirmation_text)


@router.message(OrderStates.waiting_for_confirmation, IsUserFilter())
async def confirm_order_with_contact(message: Message, state: FSMContext) -> None:
    """Підтвердження замовлення з контактною інформацією."""
    if message.text.lower() not in ["так", "yes", "у", "y"]:
        await state.clear()
        await message.answer(
            "❌ Замовлення скасовано.",
            reply_markup=get_order_confirmation_keyboard()
        )
        return
    
    try:
        data = await state.get_data()
        
        # Створюємо замовлення з контактною інформацією
        order_id = await db.create_order(
            user_id=data['user_id'],
            user_name=data['user_name'],
            product_id=data['product_id'],
            quantity=data['quantity'],
            phone=data['phone'],
            email=data['email']
        )
        
        if order_id:
            confirmation_text = (
                f"✅ {html.bold('Замовлення оформлено!')}\n\n"
                f"📋 Номер замовлення: #{order_id}\n"
                f"🛍 Товар: {data['product_name']}\n"
                f"💰 Сума: {data['product_price'] * data['quantity']:.2f} грн\n"
                f"📦 Кількість: {data['quantity']} шт.\n"
                f"📱 Телефон: {data['phone']}\n"
                f"📧 Email: {data['email']}\n\n"
                f"Виберіть спосіб оплати замовлення:"
            )
            
            logger.info(f"Order #{order_id} created with contact info - Phone: {data['phone']}, Email: {data['email']}")
            
            # Store order_id in FSM context for payment flow
            await state.update_data(order_id=order_id)
            
            # Move to payment state
            await state.set_state(PaymentStates.waiting_for_payment_method)
            
            await message.answer(
                confirmation_text,
                reply_markup=get_order_with_payment_keyboard(order_id)
            )
        else:
            await message.answer(
                "❌ Помилка оформлення замовлення. Можливо товар закінчився.",
                reply_markup=get_order_confirmation_keyboard()
            )
            await state.clear()
        
    except Exception as e:
        logger.error(f"Error in confirm_order_with_contact: {e}", exc_info=True)
        await message.answer(
            "❌ Помилка при обробці замовлення",
            reply_markup=get_order_confirmation_keyboard()
        )
        await state.clear()
