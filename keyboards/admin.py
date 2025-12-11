from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_admin_main_keyboard():
    """Головне меню адміністратора."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin_stats")
    builder.button(text="📦 Замовлення", callback_data="admin_orders")
    builder.button(text="🛍 Товари", callback_data="admin_products")
    builder.button(text="👥 Користувачі", callback_data="admin_users")
    builder.adjust(2)
    return builder.as_markup()


def get_admin_orders_keyboard():
    """Меню управління замовленнями."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🕐 Нові", callback_data="admin_orders_pending")
    builder.button(text="✅ Підтверджені", callback_data="admin_orders_confirmed")
    builder.button(text="🚚 Відправлені", callback_data="admin_orders_shipped")
    builder.button(text="📬 Доставлені", callback_data="admin_orders_delivered")
    builder.button(text="◀️ Назад", callback_data="admin_main")
    builder.adjust(2)
    return builder.as_markup()


def get_admin_products_keyboard():
    """Меню управління товарами."""
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Додати товар", callback_data="admin_add_product")
    builder.button(text="📝 Редагувати", callback_data="admin_edit_products")
    builder.button(text="🗑 Видалити", callback_data="admin_delete_products")
    builder.button(text="◀️ Назад", callback_data="admin_main")
    builder.adjust(2)
    return builder.as_markup()


def get_order_status_keyboard(order_id):
    """Клавіатура для зміни статусу замовлення."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Підтвердити", callback_data=f"admin_confirm_order:{order_id}")
    builder.button(text="🚚 Відправити", callback_data=f"admin_ship_order:{order_id}")
    builder.button(text="📬 Доставлено", callback_data=f"admin_deliver_order:{order_id}")
    builder.button(text="❌ Скасувати", callback_data=f"admin_cancel_order:{order_id}")
    builder.button(text="◀️ Назад", callback_data="admin_orders")
    builder.adjust(2)
    return builder.as_markup()
