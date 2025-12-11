from handlers.common import router as common_router
from handlers.user import router as user_router
from handlers.admin import router as admin_router

__all__ = ["common_router", "user_router", "admin_router"]
