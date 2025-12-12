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


def get_image_source_keyboard():
    """Клавіатура для вибору джерела зображення товару."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🎨 Генерувати через AI", callback_data="admin_generate_image")
    builder.button(text="🔗 Введіть URL", callback_data="admin_image_url")
    builder.adjust(1)
    return builder.as_markup()


def get_admin_generate_image_sizes_keyboard():
    """Клавіатура для вибору розміру генерованого зображення."""
    builder = InlineKeyboardBuilder()
    sizes = ["1024x1024", "1792x1024", "1024x1792"]
    for size in sizes:
        builder.button(
            text=f"📐 {size}",
            callback_data=f"admin_select_image_size:{size}"
        )
    builder.adjust(1)
    return builder.as_markup()


def get_admin_generate_image_styles_keyboard():
    """Клавіатура для вибору стилю генерованого зображення."""
    builder = InlineKeyboardBuilder()
    styles = [("✨ Vivid", "vivid"), ("🎨 Natural", "natural")]
    for style_text, style_value in styles:
        builder.button(
            text=style_text,
            callback_data=f"admin_select_image_style:{style_value}"
        )
    builder.adjust(2)
    return builder.as_markup()


def get_order_edit_menu_keyboard(order_id):
    """Клавіатура для вибору поля до редагування замовлення."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📱 Телефон", callback_data=f"admin_edit_order_field:{order_id}:phone")
    builder.button(text="📧 Email", callback_data=f"admin_edit_order_field:{order_id}:email")
    builder.button(text="📦 Кількість", callback_data=f"admin_edit_order_field:{order_id}:quantity")
    builder.button(text="💰 Ціна", callback_data=f"admin_edit_order_field:{order_id}:price")
    builder.button(text="💳 Статус оплати", callback_data=f"admin_edit_order_field:{order_id}:payment_status")
    builder.button(text="◀️ Назад", callback_data=f"admin_order_detail:{order_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_order_field_confirmation_keyboard(order_id, field_name):
    """Клавіатура для підтвердження редагування поля замовлення."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Зберегти", callback_data=f"admin_confirm_edit:{order_id}:{field_name}")
    builder.button(text="❌ Скасувати", callback_data=f"admin_edit_order_field:{order_id}:{field_name}")
    builder.adjust(2)
    return builder.as_markup()


def get_order_status_change_keyboard(order_id, current_status):
    """Клавіатура для зміни статусу замовлення з врахуванням стан-машини."""
    builder = InlineKeyboardBuilder()
    
    # Дозволені переходи на основі поточного статусу
    transitions = {
        'pending': [
            ("✅ Підтвердити", f"admin_change_order_status:{order_id}:confirmed"),
            ("❌ Скасувати", f"admin_change_order_status:{order_id}:cancelled")
        ],
        'confirmed': [
            ("🚚 Відправити", f"admin_change_order_status:{order_id}:shipped"),
            ("❌ Скасувати", f"admin_change_order_status:{order_id}:cancelled")
        ],
        'shipped': [
            ("📬 Доставлено", f"admin_change_order_status:{order_id}:delivered")
        ],
        'delivered': [],
        'cancelled': []
    }
    
    # Додаємо доступні кнопки переходу
    for text, callback in transitions.get(current_status, []):
        builder.button(text=text, callback_data=callback)
    
    builder.button(text="◀️ Назад", callback_data=f"admin_order_detail:{order_id}")
    builder.adjust(2)
    return builder.as_markup()


def get_order_detail_keyboard(order_id):
    """Клавіатура для деталей замовлення з опціями редагування."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редагувати", callback_data=f"admin_edit_order:{order_id}")
    builder.button(text="🔄 Змінити статус", callback_data=f"admin_change_status:{order_id}")
    builder.button(text="◀️ Назад", callback_data="admin_orders")
    builder.adjust(2)
    return builder.as_markup()


def get_orders_list_keyboard(orders):
    """Клавіатура зі списком замовлень як інлайн кнопками."""
    builder = InlineKeyboardBuilder()
    
    for order in orders:
        order_id = order['id']
        product_name = order['product_name']
        quantity = order['quantity']
        button_text = f"#{order_id} {product_name} ({quantity}шт)"
        builder.button(
            text=button_text,
            callback_data=f"admin_order_detail:{order_id}"
        )
    
    builder.button(text="◀️ Назад", callback_data="admin_orders")
    builder.adjust(1)
    return builder.as_markup()

