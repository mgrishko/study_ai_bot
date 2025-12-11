import pytest
from keyboards.inline import (
    get_products_keyboard,
    get_order_keyboard,
    get_product_details_keyboard,
    get_order_confirmation_keyboard,
    get_my_orders_keyboard
)
from keyboards.admin import (
    get_admin_main_keyboard,
    get_admin_orders_keyboard,
    get_admin_products_keyboard,
    get_order_status_keyboard
)


def test_get_products_keyboard():
    """Тест створення клавіатури товарів."""
    products = [
        {'id': 1, 'name': 'Товар 1', 'price': 100},
        {'id': 2, 'name': 'Товар 2', 'price': 200}
    ]
    
    keyboard = get_products_keyboard(products)
    assert keyboard is not None
    assert hasattr(keyboard, 'inline_keyboard')


def test_get_order_keyboard():
    """Тест створення клавіатури замовлення."""
    products = [
        {'id': 1, 'name': 'Товар 1', 'price': 100}
    ]
    
    keyboard = get_order_keyboard(products)
    assert keyboard is not None
    assert hasattr(keyboard, 'inline_keyboard')


def test_get_product_details_keyboard():
    """Тест створення клавіатури деталей товару."""
    keyboard = get_product_details_keyboard(1)
    assert keyboard is not None
    assert hasattr(keyboard, 'inline_keyboard')
    assert len(keyboard.inline_keyboard) > 0


def test_get_order_confirmation_keyboard():
    """Тест створення клавіатури підтвердження замовлення."""
    keyboard = get_order_confirmation_keyboard()
    assert keyboard is not None
    assert hasattr(keyboard, 'inline_keyboard')


def test_get_my_orders_keyboard():
    """Тест створення клавіатури мої замовлення."""
    keyboard = get_my_orders_keyboard()
    assert keyboard is not None
    assert hasattr(keyboard, 'inline_keyboard')


def test_get_admin_main_keyboard():
    """Тест створення головної клавіатури адміна."""
    keyboard = get_admin_main_keyboard()
    assert keyboard is not None
    assert hasattr(keyboard, 'inline_keyboard')


def test_get_admin_orders_keyboard():
    """Тест створення клавіатури замовлень адміна."""
    keyboard = get_admin_orders_keyboard()
    assert keyboard is not None
    assert hasattr(keyboard, 'inline_keyboard')


def test_get_admin_products_keyboard():
    """Тест створення клавіатури товарів адміна."""
    keyboard = get_admin_products_keyboard()
    assert keyboard is not None
    assert hasattr(keyboard, 'inline_keyboard')


def test_get_order_status_keyboard():
    """Тест створення клавіатури статусу замовлення."""
    keyboard = get_order_status_keyboard(1)
    assert keyboard is not None
    assert hasattr(keyboard, 'inline_keyboard')
