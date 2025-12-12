"""Handlers для управління замовленнями (адміністратор)."""
from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import db
from filters import IsAdminFilter
from keyboards import (
    get_admin_orders_keyboard,
    get_order_status_keyboard,
    get_order_edit_menu_keyboard,
    get_order_field_confirmation_keyboard,
    get_order_status_change_keyboard,
    get_order_detail_keyboard,
    get_orders_list_keyboard
)
from handlers.order_states import AdminOrderEditStates
from utils.validators import (
    validate_phone,
    validate_email,
    validate_quantity,
    validate_price,
    validate_payment_status,
    validate_order_status_transition
)
from logger_config import get_logger

logger = get_logger("aiogram.handlers")

router = Router()


@router.callback_query(F.data == "admin_orders", IsAdminFilter())
async def admin_orders_callback(callback: CallbackQuery) -> None:
    """Управління замовленнями."""
    orders_text = (
        f"📦 {html.bold('Управління замовленнями')}\n\n"
        f"Виберіть тип замовлень для перегляду:"
    )
    await callback.message.edit_text(orders_text, reply_markup=get_admin_orders_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_orders_"), IsAdminFilter())
async def admin_orders_list_callback(callback: CallbackQuery) -> None:
    """Перегляд списку замовлень за статусом."""
    status = callback.data.split("_")[-1]
    
    async with db.pool.acquire() as conn:
        orders = await conn.fetch(
            """SELECT o.*, p.name as product_name, u.username, u.first_name
               FROM orders o
               JOIN products p ON o.product_id = p.id
               LEFT JOIN users u ON o.user_id = u.id
               WHERE o.status = $1
               ORDER BY o.created_at DESC
               LIMIT 10""",
            status
        )
    
    if not orders:
        await callback.answer(f"❌ Немає замовлень зі статусом '{status}'", show_alert=True)
        return
    
    status_names = {
        'pending': 'Нові',
        'confirmed': 'Підтверджені',
        'shipped': 'Відправлені',
        'delivered': 'Доставлені'
    }
    
    orders_text = f"📦 {html.bold(f'{status_names.get(status, status)} замовлення:')}\n\n"
    
    for order in orders:
        user_name = order['first_name'] or order['username'] or f"ID: {order['user_id']}"
        orders_text += (
            f"🔹 Замовлення #{order['id']}\n"
            f"   Користувач: {user_name}\n"
            f"   Товар: {order['product_name']}\n"
            f"   Кількість: {order['quantity']} шт.\n"
            f"   Сума: {float(order['total_price']):.2f} грн\n"
            f"   Дата: {order['created_at']}\n\n"
        )
    
    await callback.message.edit_text(orders_text, reply_markup=get_orders_list_keyboard(orders))
    await callback.answer()


@router.message(Command(commands=["order"]), IsAdminFilter())
async def admin_order_details(message: Message) -> None:
    """Деталі конкретного замовлення."""
    try:
        order_id = int(message.text.split("_")[1])
    except (IndexError, ValueError):
        return
    
    order = await db.get_order(order_id)
    if not order:
        await message.answer("❌ Замовлення не знайдено")
        return
    
    status_emoji = {
        'pending': '🕐',
        'confirmed': '✅',
        'shipped': '🚚',
        'delivered': '📬',
        'cancelled': '❌'
    }
    
    user_name = order.get('first_name') or order.get('username') or f"ID: {order['user_id']}"
    emoji = status_emoji.get(order['status'], '❓')
    
    order_text = (
        f"{emoji} {html.bold(f'Замовлення #{order['id']}')}\n\n"
        f"👤 Користувач: {user_name}\n"
        f"📱 Telegram ID: {order['user_id']}\n\n"
        f"🛍 Товар: {order['product_name']}\n"
        f"💰 Ціна: {float(order['product_price']):.2f} грн\n"
        f"📦 Кількість: {order['quantity']} шт.\n"
        f"💵 Сума: {float(order['total_price']):.2f} грн\n"
        f"📱 Телефон: {order['phone'] or 'N/A'}\n"
        f"📧 Email: {order['email'] or 'N/A'}\n\n"
        f"📅 Дата: {order['created_at']}\n"
        f"📊 Статус: {order['status']}\n"
        f"💳 Оплата: {order['payment_status']}\n"
    )
    
    await message.answer(order_text, reply_markup=get_order_detail_keyboard(order_id))


@router.callback_query(F.data.startswith("admin_confirm_order:"), IsAdminFilter())
async def admin_confirm_order(callback: CallbackQuery) -> None:
    """Підтвердження замовлення."""
    order_id = int(callback.data.split(":")[1])
    await db.update_order_status(order_id, "confirmed")
    await callback.answer("✅ Замовлення підтверджено!")
    await callback.message.edit_reply_markup(reply_markup=get_order_status_keyboard(order_id))


@router.callback_query(F.data.startswith("admin_ship_order:"), IsAdminFilter())
async def admin_ship_order(callback: CallbackQuery) -> None:
    """Відправка замовлення."""
    order_id = int(callback.data.split(":")[1])
    await db.update_order_status(order_id, "shipped")
    await callback.answer("🚚 Замовлення відправлено!")
    await callback.message.edit_reply_markup(reply_markup=get_order_status_keyboard(order_id))


@router.callback_query(F.data.startswith("admin_deliver_order:"), IsAdminFilter())
async def admin_deliver_order(callback: CallbackQuery) -> None:
    """Доставка замовлення."""
    order_id = int(callback.data.split(":")[1])
    await db.update_order_status(order_id, "delivered")
    await callback.answer("📬 Замовлення доставлено!")
    await callback.message.edit_reply_markup(reply_markup=get_order_status_keyboard(order_id))


@router.callback_query(F.data.startswith("admin_cancel_order:"), IsAdminFilter())
async def admin_cancel_order(callback: CallbackQuery) -> None:
    """Скасування замовлення."""
    order_id = int(callback.data.split(":")[1])
    await db.update_order_status(order_id, "cancelled")
    await callback.answer("❌ Замовлення скасовано!")
    await callback.message.edit_reply_markup(reply_markup=get_order_status_keyboard(order_id))


# ═════════════════════════════════════════════════════════════════════════════
# HANDLERS ДЛЯ РЕДАГУВАННЯ ЗАМОВЛЕНЬ
# ═════════════════════════════════════════════════════════════════════════════


@router.callback_query(F.data.startswith("admin_edit_order:"), IsAdminFilter())
async def start_edit_order_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Розпочати редагування замовлення."""
    order_id = int(callback.data.split(":")[1])
    
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("❌ Замовлення не знайдено", show_alert=True)
        return
    
    await state.update_data(order_id=order_id, order=dict(order))
    await state.set_state(AdminOrderEditStates.choosing_edit_field)
    
    edit_text = (
        f"✏️ {html.bold(f'Редагування замовлення #{order_id}')}\n\n"
        f"Виберіть поле для редагування:"
    )
    
    await callback.message.edit_text(edit_text, reply_markup=get_order_edit_menu_keyboard(order_id))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_order_field:"), 
                      AdminOrderEditStates.choosing_edit_field, IsAdminFilter())
async def choose_edit_field_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Вибір поля для редагування."""
    parts = callback.data.split(":")
    order_id = int(parts[1])
    field_name = parts[2]
    
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("❌ Замовлення не знайдено", show_alert=True)
        return
    
    current_value = order.get(field_name, "N/A")
    
    field_labels = {
        'phone': '📱 Телефон',
        'email': '📧 Email',
        'quantity': '📦 Кількість',
        'price': '💰 Ціна',
        'payment_status': '💳 Статус оплати'
    }
    
    field_label = field_labels.get(field_name, field_name)
    
    prompt_text = (
        f"✏️ {html.bold(f'Редагування {field_label}')}\n\n"
        f"Поточне значення: {html.code(str(current_value))}\n\n"
        f"Введіть нове значення:"
    )
    
    await state.update_data(order_id=order_id, field_name=field_name, current_value=current_value)
    
    # Встановлюємо відповідний стан на основі поля
    state_map = {
        'phone': AdminOrderEditStates.editing_phone,
        'email': AdminOrderEditStates.editing_email,
        'quantity': AdminOrderEditStates.editing_quantity,
        'price': AdminOrderEditStates.editing_price,
        'payment_status': AdminOrderEditStates.editing_payment_status
    }
    
    await state.set_state(state_map.get(field_name, AdminOrderEditStates.choosing_edit_field))
    await callback.message.edit_text(prompt_text)
    await callback.answer()


@router.message(AdminOrderEditStates.editing_phone, IsAdminFilter())
async def process_phone_edit(message: Message, state: FSMContext) -> None:
    """Обробка редагування телефону."""
    new_phone = message.text.strip()
    
    is_valid, error_msg = validate_phone(new_phone)
    if not is_valid:
        await message.answer(error_msg)
        return
    
    data = await state.get_data()
    order_id = data['order_id']
    current_value = data['current_value']
    
    # Показуємо підтвердження
    confirmation_text = (
        f"✏️ {html.bold('Підтвердіть зміну')}\n\n"
        f"📱 Телефон\n"
        f"Старе значення: {html.code(str(current_value))}\n"
        f"Нове значення: {html.code(new_phone)}\n\n"
        f"Збереженемо зміну?"
    )
    
    await state.update_data(new_value=new_phone)
    await message.answer(confirmation_text, reply_markup=get_order_field_confirmation_keyboard(order_id, 'phone'))


@router.message(AdminOrderEditStates.editing_email, IsAdminFilter())
async def process_email_edit(message: Message, state: FSMContext) -> None:
    """Обробка редагування email."""
    new_email = message.text.strip()
    
    is_valid, error_msg = validate_email(new_email)
    if not is_valid:
        await message.answer(error_msg)
        return
    
    data = await state.get_data()
    order_id = data['order_id']
    current_value = data['current_value']
    
    confirmation_text = (
        f"✏️ {html.bold('Підтвердіть зміну')}\n\n"
        f"📧 Email\n"
        f"Старе значення: {html.code(str(current_value))}\n"
        f"Нове значення: {html.code(new_email)}\n\n"
        f"Збереженемо зміну?"
    )
    
    await state.update_data(new_value=new_email)
    await message.answer(confirmation_text, reply_markup=get_order_field_confirmation_keyboard(order_id, 'email'))


@router.message(AdminOrderEditStates.editing_quantity, IsAdminFilter())
async def process_quantity_edit(message: Message, state: FSMContext) -> None:
    """Обробка редагування кількості."""
    new_quantity = message.text.strip()
    
    data = await state.get_data()
    order_id = data['order_id']
    order = data['order']
    
    # Отримаємо актуальний стан товару
    product = await db.get_product_by_id(order['product_id'])
    if not product:
        await message.answer("❌ Товар не знайдено")
        return
    
    # Максимальна кількість = поточний stock + поточна кількість в замовленні
    max_available = product['stock'] + order['quantity']
    
    is_valid, error_msg = validate_quantity(new_quantity, max_available)
    if not is_valid:
        await message.answer(error_msg)
        return
    
    current_value = data['current_value']
    
    confirmation_text = (
        f"✏️ {html.bold('Підтвердіть зміну')}\n\n"
        f"📦 Кількість\n"
        f"Старе значення: {html.code(str(current_value))} шт.\n"
        f"Нове значення: {html.code(new_quantity)} шт.\n\n"
        f"Збереженемо зміну?"
    )
    
    await state.update_data(new_value=int(new_quantity))
    await message.answer(confirmation_text, reply_markup=get_order_field_confirmation_keyboard(order_id, 'quantity'))


@router.message(AdminOrderEditStates.editing_price, IsAdminFilter())
async def process_price_edit(message: Message, state: FSMContext) -> None:
    """Обробка редагування ціни."""
    new_price = message.text.strip()
    
    is_valid, error_msg = validate_price(new_price)
    if not is_valid:
        await message.answer(error_msg)
        return
    
    data = await state.get_data()
    order_id = data['order_id']
    current_value = data['current_value']
    
    new_price_float = float(new_price)
    
    confirmation_text = (
        f"✏️ {html.bold('Підтвердіть зміну')}\n\n"
        f"💰 Ціна\n"
        f"Старе значення: {html.code(f'{float(current_value):.2f} грн')}\n"
        f"Нове значення: {html.code(f'{new_price_float:.2f} грн')}\n\n"
        f"Збереженемо зміну?"
    )
    
    await state.update_data(new_value=new_price_float)
    await message.answer(confirmation_text, reply_markup=get_order_field_confirmation_keyboard(order_id, 'price'))


@router.message(AdminOrderEditStates.editing_payment_status, IsAdminFilter())
async def process_payment_status_edit(message: Message, state: FSMContext) -> None:
    """Обробка редагування статусу оплати."""
    new_status = message.text.strip()
    
    is_valid, error_msg = validate_payment_status(new_status)
    if not is_valid:
        await message.answer(error_msg)
        return
    
    data = await state.get_data()
    order_id = data['order_id']
    current_value = data['current_value']
    
    confirmation_text = (
        f"✏️ {html.bold('Підтвердіть зміну')}\n\n"
        f"💳 Статус оплати\n"
        f"Старе значення: {html.code(str(current_value))}\n"
        f"Нове значення: {html.code(new_status)}\n\n"
        f"Збереженемо зміну?"
    )
    
    await state.update_data(new_value=new_status.lower())
    await message.answer(confirmation_text, reply_markup=get_order_field_confirmation_keyboard(order_id, 'payment_status'))


@router.callback_query(F.data.startswith("admin_confirm_edit:"), IsAdminFilter())
async def confirm_field_edit_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """Підтвердження редагування поля."""
    parts = callback.data.split(":")
    order_id = int(parts[1])
    field_name = parts[2]
    
    data = await state.get_data()
    new_value = data.get('new_value')
    current_value = data.get('current_value')
    
    # Зберігаємо зміну
    update_kwargs = {field_name: new_value}
    success = await db.update_order(order_id, **update_kwargs)
    
    if success:
        # Логуємо зміну
        await db.add_order_edit_log(
            order_id=order_id,
            admin_id=callback.from_user.id,
            field_name=field_name,
            old_value=str(current_value),
            new_value=str(new_value)
        )
        
        await callback.answer(f"✅ {field_name.capitalize()} оновлено!", show_alert=True)
        
        # Повертаємося до деталей замовлення
        order = await db.get_order(order_id)
        if order:
            status_emoji = {
                'pending': '🕐',
                'confirmed': '✅',
                'shipped': '🚚',
                'delivered': '📬',
                'cancelled': '❌'
            }
            
            user_name = order.get('first_name') or order.get('username') or f"ID: {order['user_id']}"
            emoji = status_emoji.get(order['status'], '❓')
            
            order_text = (
                f"{emoji} {html.bold(f'Замовлення #{order['id']}')}\n\n"
                f"👤 Користувач: {user_name}\n"
                f"📱 Telegram ID: {order['user_id']}\n\n"
                f"🛍 Товар: {order['product_name']}\n"
                f"💰 Ціна: {float(order['product_price']):.2f} грн\n"
                f"📦 Кількість: {order['quantity']} шт.\n"
                f"💵 Сума: {float(order['total_price']):.2f} грн\n"
                f"📱 Телефон: {order['phone'] or 'N/A'}\n"
                f"📧 Email: {order['email'] or 'N/A'}\n\n"
                f"📅 Дата: {order['created_at']}\n"
                f"📊 Статус: {order['status']}\n"
                f"💳 Оплата: {order['payment_status']}\n"
            )
            
            await callback.message.edit_text(order_text, reply_markup=get_order_detail_keyboard(order_id))
    else:
        await callback.answer("❌ Помилка при збереженні зміни", show_alert=True)
    
    await state.clear()


@router.callback_query(F.data.startswith("admin_change_status:"), IsAdminFilter())
async def show_status_change_options(callback: CallbackQuery) -> None:
    """Показати опції зміни статусу."""
    order_id = int(callback.data.split(":")[1])
    
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("❌ Замовлення не знайдено", show_alert=True)
        return
    
    current_status = order['status']
    status_text = (
        f"🔄 {html.bold('Зміна статусу замовлення')}\n\n"
        f"Поточний статус: {html.code(current_status)}\n\n"
        f"Виберіть новий статус:"
    )
    
    await callback.message.edit_text(status_text, reply_markup=get_order_status_change_keyboard(order_id, current_status))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_change_order_status:"), IsAdminFilter())
async def change_order_status_callback(callback: CallbackQuery) -> None:
    """Зміна статусу замовлення з валідацією стан-машини."""
    parts = callback.data.split(":")
    order_id = int(parts[1])
    new_status = parts[2]
    
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("❌ Замовлення не знайдено", show_alert=True)
        return
    
    current_status = order['status']
    
    # Валідуємо перехід
    is_valid, error_msg = validate_order_status_transition(current_status, new_status)
    if not is_valid:
        await callback.answer(error_msg, show_alert=True)
        return
    
    # Виконуємо зміну статусу
    success = await db.update_order_status(order_id, new_status)
    
    if success:
        # Логуємо зміну
        await db.add_order_edit_log(
            order_id=order_id,
            admin_id=callback.from_user.id,
            field_name='status',
            old_value=current_status,
            new_value=new_status
        )
        
        status_msgs = {
            'confirmed': '✅ Замовлення підтверджено!',
            'shipped': '🚚 Замовлення відправлено!',
            'delivered': '📬 Замовлення доставлено!',
            'cancelled': '❌ Замовлення скасовано!'
        }
        
        await callback.answer(status_msgs.get(new_status, f"Статус змінено на {new_status}"), show_alert=True)
        
        # Оновлюємо деталі замовлення
        order = await db.get_order(order_id)
        if order:
            status_emoji = {
                'pending': '🕐',
                'confirmed': '✅',
                'shipped': '🚚',
                'delivered': '📬',
                'cancelled': '❌'
            }
            
            user_name = order.get('first_name') or order.get('username') or f"ID: {order['user_id']}"
            emoji = status_emoji.get(order['status'], '❓')
            
            order_text = (
                f"{emoji} {html.bold(f'Замовлення #{order['id']}')}\n\n"
                f"👤 Користувач: {user_name}\n"
                f"📱 Telegram ID: {order['user_id']}\n\n"
                f"🛍 Товар: {order['product_name']}\n"
                f"💰 Ціна: {float(order['product_price']):.2f} грн\n"
                f"📦 Кількість: {order['quantity']} шт.\n"
                f"💵 Сума: {float(order['total_price']):.2f} грн\n"
                f"📱 Телефон: {order['phone'] or 'N/A'}\n"
                f"📧 Email: {order['email'] or 'N/A'}\n\n"
                f"📅 Дата: {order['created_at']}\n"
                f"📊 Статус: {order['status']}\n"
                f"💳 Оплата: {order['payment_status']}\n"
            )
            
            await callback.message.edit_text(order_text, reply_markup=get_order_detail_keyboard(order_id))
    else:
        await callback.answer("❌ Помилка при зміні статусу", show_alert=True)


@router.callback_query(F.data.startswith("admin_order_detail:"), IsAdminFilter())
async def show_order_detail_callback(callback: CallbackQuery) -> None:
    """Показати деталі замовлення з опціями редагування."""
    order_id = int(callback.data.split(":")[1])
    
    order = await db.get_order(order_id)
    if not order:
        await callback.answer("❌ Замовлення не знайдено", show_alert=True)
        return
    
    status_emoji = {
        'pending': '🕐',
        'confirmed': '✅',
        'shipped': '🚚',
        'delivered': '📬',
        'cancelled': '❌'
    }
    
    user_name = order.get('first_name') or order.get('username') or f"ID: {order['user_id']}"
    emoji = status_emoji.get(order['status'], '❓')
    
    # Отримуємо логи редагування
    edit_logs = await db.get_order_edit_logs(order_id, limit=3)
    
    logs_text = ""
    if edit_logs:
        logs_text = f"\n📝 {html.bold('Останні зміни:')}\n"
        for log in edit_logs:
            logs_text += f"   {log['field_name']}: {log['old_value']} → {log['new_value']}\n"
    
    order_text = (
        f"{emoji} {html.bold(f'Замовлення #{order['id']}')}\n\n"
        f"👤 Користувач: {user_name}\n"
        f"📱 Telegram ID: {order['user_id']}\n\n"
        f"🛍 Товар: {order['product_name']}\n"
        f"💰 Ціна: {float(order['product_price']):.2f} грн\n"
        f"📦 Кількість: {order['quantity']} шт.\n"
        f"💵 Сума: {float(order['total_price']):.2f} грн\n"
        f"📱 Телефон: {order['phone'] or 'N/A'}\n"
        f"📧 Email: {order['email'] or 'N/A'}\n\n"
        f"📅 Дата: {order['created_at']}\n"
        f"📊 Статус: {order['status']}\n"
        f"💳 Оплата: {order['payment_status']}"
        f"{logs_text}"
    )
    
    await callback.message.edit_text(order_text, reply_markup=get_order_detail_keyboard(order_id))
    await callback.answer()
