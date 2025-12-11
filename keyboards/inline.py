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
    return builder.as_markup()


def get_product_details_keyboard(product_id):
    """Створює клавіатуру для деталей товару."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🛒 Замовити",
        callback_data=f"order_product:{product_id}"
    )
    builder.button(
        text="◀️ Назад до каталогу",
        callback_data="back_to_catalog"
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
    builder.adjust(1)
    return builder.as_markup()


def get_my_orders_keyboard():
    """Створює клавіатуру для перегляду замовлень."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🛍 Замовити ще",
        callback_data="back_to_catalog"
    )
    builder.adjust(1)
    return builder.as_markup()
