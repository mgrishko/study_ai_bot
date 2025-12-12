"""Handlers для управління користувачами (адміністратор)."""
from aiogram import Router, html, F
from aiogram.types import CallbackQuery

from database import db
from filters import IsAdminFilter
from keyboards import get_admin_main_keyboard
from logger_config import get_logger

logger = get_logger("aiogram.handlers")

router = Router()


@router.callback_query(F.data == "admin_users", IsAdminFilter())
async def admin_users_callback(callback: CallbackQuery) -> None:
    """Перегляд користувачів."""
    async with db.pool.acquire() as conn:
        users = await conn.fetch(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT 20"
        )
    
    if not users:
        await callback.answer("❌ Користувачів не знайдено", show_alert=True)
        return
    
    users_text = f"👥 {html.bold('Користувачі (останні 20):')}\n\n"
    
    for user in users:
        username = f"@{user['username']}" if user['username'] else "—"
        full_name = f"{user['first_name']} {user['last_name'] or ''}".strip()
        users_text += (
            f"🔹 {full_name}\n"
            f"   ID: {user['id']}\n"
            f"   Username: {username}\n"
            f"   Дата реєстрації: {user['created_at']}\n\n"
        )
    
    await callback.message.edit_text(users_text, reply_markup=get_admin_main_keyboard())
    await callback.answer()
