"""Handlers для управління товарами - меню (адміністратор)."""
from aiogram import Router, html, F
from aiogram.types import CallbackQuery

from filters import IsAdminFilter
from keyboards import get_admin_products_keyboard, get_admin_main_keyboard
from logger_config import get_logger

logger = get_logger("aiogram.handlers")

router = Router()


@router.callback_query(F.data == "admin_products", IsAdminFilter())
async def admin_products_callback(callback: CallbackQuery) -> None:
    """Управління товарами."""
    products_text = (
        f"🛍 {html.bold('Управління товарами')}\n\n"
        f"Виберіть дію:"
    )
    await callback.message.edit_text(products_text, reply_markup=get_admin_products_keyboard())
    await callback.answer()
