from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from database import Database
from filters import IsAdminFilter
from keyboards import (
    get_admin_main_keyboard,
    get_admin_orders_keyboard,
    get_admin_products_keyboard,
    get_order_status_keyboard
)

router = Router()
db = Database()


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


@router.callback_query(F.data == "admin_orders", IsAdminFilter())
async def admin_orders_callback(callback: CallbackQuery) -> None:
    """Управління замовленнями."""
    orders_text = (
        f"📦 {html.bold('Управління замовленнями')}\n\n"
        f"Виберіть тип замовлень для перегляду:"
    )
    await callback.message.edit_text(orders_text, reply_markup=get_admin_orders_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_orders_"), IsAdminFilter())
async def admin_orders_list_callback(callback: CallbackQuery) -> None:
    """Перегляд списку замовлень за статусом."""
    status = callback.data.split("_")[-1]
    
    async with db.pool.acquire() as conn:
        orders = await conn.fetch(
            """SELECT o.*, p.name as product_name, u.username, u.first_name
               FROM orders o
               JOIN products p ON o.product_id = p.id
               LEFT JOIN users u ON o.user_id = u.id
               WHERE o.status = $1
               ORDER BY o.created_at DESC
               LIMIT 10""",
            status
        )
    
    if not orders:
        await callback.answer(f"❌ Немає замовлень зі статусом '{status}'", show_alert=True)
        return
    
    status_names = {
        'pending': 'Нові',
        'confirmed': 'Підтверджені',
        'shipped': 'Відправлені',
        'delivered': 'Доставлені'
    }
    
    orders_text = f"📦 {html.bold(f'{status_names.get(status, status)} замовлення:')}\n\n"
    
    for order in orders:
        user_name = order['first_name'] or order['username'] or f"ID: {order['user_id']}"
        orders_text += (
            f"🔹 Замовлення #{order['id']}\n"
            f"   Користувач: {user_name}\n"
            f"   Товар: {order['product_name']}\n"
            f"   Кількість: {order['quantity']} шт.\n"
            f"   Сума: {float(order['total_price']):.2f} грн\n"
            f"   Дата: {order['created_at']}\n"
            f"   /order_{order['id']}\n\n"
        )
    
    await callback.message.edit_text(orders_text, reply_markup=get_admin_orders_keyboard())
    await callback.answer()


@router.message(Command(commands=["order"]), IsAdminFilter())
async def admin_order_details(message: Message) -> None:
    """Деталі конкретного замовлення."""
    try:
        order_id = int(message.text.split("_")[1])
    except (IndexError, ValueError):
        return
    
    async with db.pool.acquire() as conn:
        order = await conn.fetchrow(
            """SELECT o.*, p.name as product_name, p.price, u.username, u.first_name, u.id as user_tg_id
               FROM orders o
               JOIN products p ON o.product_id = p.id
               LEFT JOIN users u ON o.user_id = u.id
               WHERE o.id = $1""",
            order_id
        )
    
    if not order:
        await message.answer("❌ Замовлення не знайдено")
        return
    
    status_emoji = {
        'pending': '🕐',
        'confirmed': '✅',
        'shipped': '🚚',
        'delivered': '📬',
        'cancelled': '❌'
    }
    
    user_name = order['first_name'] or order['username'] or f"ID: {order['user_tg_id']}"
    emoji = status_emoji.get(order['status'], '❓')
    
    order_text = (
        f"{emoji} {html.bold(f'Замовлення #{order['id']}')}\n\n"
        f"👤 Користувач: {user_name}\n"
        f"📱 Telegram ID: {order['user_tg_id']}\n\n"
        f"🛍 Товар: {order['product_name']}\n"
        f"💰 Ціна: {float(order['price']):.2f} грн\n"
        f"📦 Кількість: {order['quantity']} шт.\n"
        f"💵 Сума: {float(order['total_price']):.2f} грн\n\n"
        f"📅 Дата: {order['created_at']}\n"
        f"📊 Статус: {order['status']}\n"
    )
    
    await message.answer(order_text, reply_markup=get_order_status_keyboard(order_id))


@router.callback_query(F.data.startswith("admin_confirm_order:"), IsAdminFilter())
async def admin_confirm_order(callback: CallbackQuery) -> None:
    """Підтвердження замовлення."""
    order_id = int(callback.data.split(":")[1])
    await db.update_order_status(order_id, "confirmed")
    await callback.answer("✅ Замовлення підтверджено!")
    await callback.message.edit_reply_markup(reply_markup=get_order_status_keyboard(order_id))


@router.callback_query(F.data.startswith("admin_ship_order:"), IsAdminFilter())
async def admin_ship_order(callback: CallbackQuery) -> None:
    """Відправка замовлення."""
    order_id = int(callback.data.split(":")[1])
    await db.update_order_status(order_id, "shipped")
    await callback.answer("🚚 Замовлення відправлено!")
    await callback.message.edit_reply_markup(reply_markup=get_order_status_keyboard(order_id))


@router.callback_query(F.data.startswith("admin_deliver_order:"), IsAdminFilter())
async def admin_deliver_order(callback: CallbackQuery) -> None:
    """Доставка замовлення."""
    order_id = int(callback.data.split(":")[1])
    await db.update_order_status(order_id, "delivered")
    await callback.answer("📬 Замовлення доставлено!")
    await callback.message.edit_reply_markup(reply_markup=get_order_status_keyboard(order_id))


@router.callback_query(F.data.startswith("admin_cancel_order:"), IsAdminFilter())
async def admin_cancel_order(callback: CallbackQuery) -> None:
    """Скасування замовлення."""
    order_id = int(callback.data.split(":")[1])
    await db.update_order_status(order_id, "cancelled")
    await callback.answer("❌ Замовлення скасовано!")
    await callback.message.edit_reply_markup(reply_markup=get_order_status_keyboard(order_id))


@router.callback_query(F.data == "admin_products", IsAdminFilter())
async def admin_products_callback(callback: CallbackQuery) -> None:
    """Управління товарами."""
    products_text = (
        f"🛍 {html.bold('Управління товарами')}\n\n"
        f"Виберіть дію:"
    )
    await callback.message.edit_text(products_text, reply_markup=get_admin_products_keyboard())
    await callback.answer()


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
