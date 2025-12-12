"""Handlers для адміністратора."""
from .main import router as main_router
from .main import command_admin_handler, admin_main_callback, admin_stats_callback
from .orders import router as orders_router
from .orders import (
    admin_orders_callback,
    admin_orders_list_callback,
    admin_order_details,
    admin_confirm_order,
    admin_ship_order,
    admin_deliver_order,
    admin_cancel_order,
    start_edit_order_callback,
    choose_edit_field_callback,
    process_phone_edit,
    process_email_edit,
    process_quantity_edit,
    process_price_edit,
    process_payment_status_edit,
    confirm_field_edit_callback,
    show_status_change_options,
    change_order_status_callback,
    show_order_detail_callback
)
from .users import router as users_router
from .users import admin_users_callback
from .products import menu_router, add_router, image_router, delete_router, edit_router
from .products.menu import admin_products_callback
from .products.add import (
    AddProductStates,
    admin_add_product_start,
    process_product_name,
    process_product_description,
    process_product_price,
    process_product_category,
    process_product_stock,
    process_product_image,
    admin_choose_image_url,
    confirm_add_product,
    cancel_add_product
)
from .products.delete import (
    admin_delete_products_menu,
    confirm_delete_product,
    execute_delete_product
)
from .products.edit import (
    admin_edit_products_menu,
    show_product_detail,
    choose_product_field,
    process_product_field_input,
    confirm_product_edit
)
from .products.image import (
    AdminGenerateImageStates,
    admin_choose_generate_image,
    admin_process_image_prompt,
    admin_process_image_size,
    admin_process_image_style,
    admin_confirm_generate_image,
    admin_cancel_generate_image
)

__all__ = [
    "main_router",
    "command_admin_handler",
    "admin_main_callback",
    "admin_stats_callback",
    "orders_router",
    "admin_orders_callback",
    "admin_orders_list_callback",
    "admin_order_details",
    "admin_confirm_order",
    "admin_ship_order",
    "admin_deliver_order",
    "admin_cancel_order",
    "start_edit_order_callback",
    "choose_edit_field_callback",
    "process_phone_edit",
    "process_email_edit",
    "process_quantity_edit",
    "process_price_edit",
    "process_payment_status_edit",
    "confirm_field_edit_callback",
    "show_status_change_options",
    "change_order_status_callback",
    "show_order_detail_callback",
    "users_router",
    "admin_users_callback",
    "menu_router",
    "add_router",
    "image_router",
    "delete_router",
    "edit_router",
    "admin_products_callback",
    "AddProductStates",
    "admin_add_product_start",
    "process_product_name",
    "process_product_description",
    "process_product_price",
    "process_product_category",
    "process_product_stock",
    "process_product_image",
    "admin_choose_image_url",
    "confirm_add_product",
    "cancel_add_product",
    "admin_delete_products_menu",
    "confirm_delete_product",
    "execute_delete_product",
    "admin_edit_products_menu",
    "show_product_detail",
    "choose_product_field",
    "process_product_field_input",
    "confirm_product_edit",
    "AdminGenerateImageStates",
    "admin_choose_generate_image",
    "admin_process_image_prompt",
    "admin_process_image_size",
    "admin_process_image_style",
    "admin_confirm_generate_image",
    "admin_cancel_generate_image"
]
