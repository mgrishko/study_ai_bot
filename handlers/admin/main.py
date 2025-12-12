"""Handlers для головного меню адміністратора."""
from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import db
from filters import IsAdminFilter
from keyboards import get_admin_main_keyboard
from logger_config import get_logger

logger = get_logger("aiogram.handlers")

router = Router()


@router.message(Command("admin"), IsAdminFilter())
async def command_admin_handler(message: Message) -> None:
    """Обробник команди /admin - головне меню адміністратора."""
    admin_text = (
        f"🔐 {html.bold('Панель адміністратора')}\n\n"
        f"Виберіть розділ для управління:"
    )
    await message.answer(admin_text, reply_markup=get_admin_main_keyboard())


@router.callback_query(F.data == "admin_main", IsAdminFilter())
async def admin_main_callback(callback: CallbackQuery) -> None:
    """Повернення до головного меню адміністратора."""
    admin_text = (
        f"🔐 {html.bold('Панель адміністратора')}\n\n"
        f"Виберіть розділ для управління:"
    )
    await callback.message.edit_text(admin_text, reply_markup=get_admin_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_stats", IsAdminFilter())
async def admin_stats_callback(callback: CallbackQuery) -> None:
    """Статистика бота."""
    # Отримуємо статистику
    async with db.pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        total_orders = await conn.fetchval("SELECT COUNT(*) FROM orders")
        total_products = await conn.fetchval("SELECT COUNT(*) FROM products")
        pending_orders = await conn.fetchval(
            "SELECT COUNT(*) FROM orders WHERE status = 'pending'"
        )
        total_revenue = await conn.fetchval(
            "SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE status != 'cancelled'"
        )
    
    stats_text = (
        f"📊 {html.bold('Статистика')}\n\n"
        f"👥 Всього користувачів: {total_users}\n"
        f"📦 Всього замовлень: {total_orders}\n"
        f"🛍 Товарів в каталозі: {total_products}\n"
        f"🕐 Нових замовлень: {pending_orders}\n"
        f"💰 Загальний дохід: {float(total_revenue):.2f} грн\n"
    )
    
    await callback.message.edit_text(stats_text, reply_markup=get_admin_main_keyboard())
    await callback.answer()
