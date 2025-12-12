from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_products_keyboard(products):
    """Створює клавіатуру зі списком товарів."""
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product['name']} - {float(product['price']):.0f} грн",
            callback_data=f"product:{product['id']}"
        )
    builder.adjust(1)
    builder.button(
        text="🏠 На початок",
        callback_data="back_to_start"
    )
    return builder.as_markup()


def get_order_keyboard(products):
    """Створює клавіатуру для замовлення товарів."""
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product['name']} - {float(product['price']):.0f} грн",
            callback_data=f"order_product:{product['id']}"
        )
    builder.adjust(1)
    builder.button(
        text="🏠 На початок",
        callback_data="back_to_start"
    )
    return builder.as_markup()


def get_product_details_keyboard(product_id):
    """Створює клавіатуру для деталей товару."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔊 Прослухати опис",
        callback_data=f"listen_product:{product_id}"
    )
    builder.button(
        text="🛒 Замовити",
        callback_data=f"order_product:{product_id}"
    )
    builder.button(
        text="◀️ Назад до каталогу",
        callback_data="back_to_catalog"
    )
    builder.button(
        text="🏠 На початок",
        callback_data="back_to_start"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_order_confirmation_keyboard():
    """Створює клавіатуру після оформлення замовлення."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🛍 Замовити ще",
        callback_data="back_to_catalog"
    )
    builder.button(
        text="📦 Мої замовлення",
        callback_data="my_orders"
    )
    builder.button(
        text="🏠 На початок",
        callback_data="back_to_start"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_my_orders_keyboard():
    """Створює клавіатуру для перегляду замовлень."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🛍 Замовити ще",
        callback_data="back_to_catalog"
    )
    builder.button(
        text="🏠 На початок",
        callback_data="back_to_start"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_categories_keyboard(categories_with_counts):
    """Створює клавіатуру для вибору категорії.
    
    Args:
        categories_with_counts: Список кортежів (категорія, кількість товарів)
    """
    builder = InlineKeyboardBuilder()
    
    for category, count in categories_with_counts:
        builder.button(
            text=f"🔹 {category} ({count})",
            callback_data=f"category:{category}"
        )
    
    builder.button(
        text="📦 Всі товари",
        callback_data="all_products"
    )
    builder.button(
        text="🏠 На початок",
        callback_data="back_to_start"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_products_by_category_keyboard(products, category_name):
    """Створює клавіатуру для товарів у вибраній категорії.
    
    Args:
        products: Список товарів з категорії
        category_name: Назва категорії для контексту
    """
    builder = InlineKeyboardBuilder()
    
    for product in products:
        builder.button(
            text=f"{product['name']} - {float(product['price']):.0f} грн",
            callback_data=f"product_cat:{product['id']}:{category_name}"
        )
    
    builder.button(
        text="◀️ Назад до категорій",
        callback_data="back_to_categories"
    )
    builder.button(
        text="🏠 На початок",
        callback_data="back_to_start"
    )
    builder.adjust(1)
    return builder.as_markup()


def get_product_details_with_category_keyboard(product_id, category_name):
    """Створює клавіатуру для деталей товару з навігацією до категорії.
    
    Args:
        product_id: ID товару
        category_name: Назва категорії, з якої товар відкритий
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔊 Прослухати опис",
        callback_data=f"listen_product:{product_id}"
    )
    builder.button(
        text="🛒 Замовити",
        callback_data=f"order_product:{product_id}"
    )
    builder.button(
        text="◀️ Назад до категорії",
        callback_data=f"back_to_category:{category_name}"
    )
    builder.button(
        text="🏠 На початок",
        callback_data="back_to_start"
    )
    builder.adjust(1)
    return builder.as_markup()
