from aiogram import Router
from handlers.common import router as common_router
from handlers.ai import router as ai_router
from handlers.payments import router as payment_router

# Import all user routers
from handlers.user import (
    menu_router,
    catalog_router,
    products_router,
    orders_router as user_orders_router
)

# Combine all user routers into one
user_router = Router()
user_router.include_router(menu_router)
user_router.include_router(catalog_router)
user_router.include_router(products_router)
user_router.include_router(user_orders_router)

# Import all admin routers
from handlers.admin import (
    main_router,
    orders_router,
    users_router,
    menu_router as admin_menu_router,
    add_router,
    image_router,
    delete_router,
    edit_router
)

# Combine all admin routers into one
admin_router = Router()
admin_router.include_router(main_router)
admin_router.include_router(orders_router)
admin_router.include_router(users_router)
admin_router.include_router(admin_menu_router)
admin_router.include_router(add_router)
admin_router.include_router(image_router)
admin_router.include_router(delete_router)
admin_router.include_router(edit_router)

__all__ = ["common_router", "user_router", "admin_router", "ai_router", "payment_router"]
