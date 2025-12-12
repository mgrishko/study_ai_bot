"""Handlers для користувача."""
from .menu import router as menu_router
from .menu import (
    handle_catalog_button,
    handle_my_orders_button,
    handle_categories_button,
    handle_help_button,
    handle_about_button,
    handle_ai_button,
    handle_admin_button,
    back_to_start
)

from .catalog import router as catalog_router
from .catalog import (
    command_catalog_handler,
    choose_categories_callback,
    command_categories_handler,
    command_order_handler,
    category_selected_callback,
    all_products_callback,
    back_to_catalog_callback,
    back_to_categories_callback,
    back_to_category_callback
)

from .products import router as products_router
from .products import (
    listen_product_callback,
    product_details_callback,
    product_details_with_category_callback
)

from .orders import router as orders_router
from .orders import (
    command_my_orders_handler,
    my_orders_callback,
    order_product_with_contact_start,
    process_order_phone,
    process_order_email,
    confirm_order_with_contact
)

__all__ = [
    "menu_router",
    "catalog_router",
    "products_router",
    "orders_router",
    # Menu handlers
    "handle_catalog_button",
    "handle_my_orders_button",
    "handle_categories_button",
    "handle_help_button",
    "handle_about_button",
    "handle_ai_button",
    "handle_admin_button",
    "back_to_start",
    # Catalog handlers
    "command_catalog_handler",
    "choose_categories_callback",
    "command_categories_handler",
    "command_order_handler",
    "category_selected_callback",
    "all_products_callback",
    "back_to_catalog_callback",
    "back_to_categories_callback",
    "back_to_category_callback",
    # Product handlers
    "listen_product_callback",
    "product_details_callback",
    "product_details_with_category_callback",
    # Order handlers
    "command_my_orders_handler",
    "my_orders_callback",
    "order_product_with_contact_start",
    "process_order_phone",
    "process_order_email",
    "confirm_order_with_contact"
]
