"""Handlers для управління товарами (адміністратор)."""
from .menu import router as menu_router
from .add import router as add_router
from .image import router as image_router
from .delete import router as delete_router

__all__ = ["menu_router", "add_router", "image_router", "delete_router"]
