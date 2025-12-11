import logging
from typing import Optional, Any

from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from filters import IsAdminFilter
from keyboards import (
    get_admin_main_keyboard,
    get_admin_orders_keyboard,
    get_admin_products_keyboard,
    get_order_status_keyboard
)

logger = logging.getLogger(__name__)

router = Router()


# FSM States для добавления товара
class AddProductStates(StatesGroup):
    """Состояния FSM для добавления нового товара."""
    waiting_for_name = State()           # Шаг 1: название
    waiting_for_description = State()    # Шаг 2: описание
    waiting_for_price = State()          # Шаг 3: цена
    waiting_for_category = State()       # Шаг 4: категория
    waiting_for_stock = State()          # Шаг 5: количество
    waiting_for_image_url = State()      # Шаг 6: URL изображения
    waiting_for_confirmation = State()   # Шаг 7: подтверждение


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


# ═════════════════════════════════════════════════════════════════════════════
# HANDLERS ДЛЯ ДОБАВЛЕНИЯ ТОВАРА (FSM)
# ═════════════════════════════════════════════════════════════════════════════


@router.callback_query(F.data == "admin_add_product", IsAdminFilter())
async def admin_add_product_start(query: CallbackQuery, state: FSMContext) -> None:
    """Начало процесса добавления товара."""
    logger.info(f"Admin {query.from_user.id} started adding product")
    await state.set_state(AddProductStates.waiting_for_name)
    await query.message.edit_text("📝 Введіть назву товару (макс 255 символів):")
    await query.answer()


@router.message(AddProductStates.waiting_for_name)
async def process_product_name(message: Message, state: FSMContext) -> None:
    """Обработка названия товара."""
    if len(message.text) > 255:
        await message.answer("❌ Назва товару занадто довга (макс 255 символів)")
        return
    
    await state.update_data(name=message.text)
    await state.set_state(AddProductStates.waiting_for_description)
    await message.answer("📝 Введіть опис товару (макс 1000 символів):")


@router.message(AddProductStates.waiting_for_description)
async def process_product_description(message: Message, state: FSMContext) -> None:
    """Обработка описания товара."""
    if len(message.text) > 1000:
        await message.answer("❌ Опис занадто довгий (макс 1000 символів)")
        return
    
    await state.update_data(description=message.text)
    await state.set_state(AddProductStates.waiting_for_price)
    await message.answer("💰 Введіть ціну товару (в гривнях, наприклад 2500.50):")


@router.message(AddProductStates.waiting_for_price)
async def process_product_price(message: Message, state: FSMContext) -> None:
    """Обработка цены товара."""
    try:
        price = float(message.text)
        if price <= 0:
            await message.answer("❌ Ціна повинна бути більше 0")
            return
        if price > 999999:
            await message.answer("❌ Ціна занадто висока (макс 999999 грн)")
            return
        
        await state.update_data(price=price)
        
        # Получаем категории для выбора
        categories = await db.get_categories()
        if not categories:
            await message.answer("❌ Немає категорій. Спочатку додайте категорію в БД.")
            await state.clear()
            logger.warning(f"No categories available when adding product")
            return
        
        await state.set_state(AddProductStates.waiting_for_category)
        
        # Создаем клавиатуру с категориями
        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.button(
                text=f"📂 {category}",
                callback_data=f"select_category:{category}"
            )
        builder.adjust(2)
        
        await message.answer(
            "📂 Виберіть категорію:",
            reply_markup=builder.as_markup()
        )
    except ValueError:
        await message.answer("❌ Введіть дійсну ціну (число, наприклад 2500 або 2500.50)")


@router.callback_query(AddProductStates.waiting_for_category, F.data.startswith("select_category:"))
async def process_product_category(query: CallbackQuery, state: FSMContext) -> None:
    """Обработка выбора категории товара."""
    category = query.data.split(":", 1)[1]
    await state.update_data(category=category)
    await state.set_state(AddProductStates.waiting_for_stock)
    await query.message.edit_text("📦 Введіть кількість товару на складі (число):")
    await query.answer()


@router.message(AddProductStates.waiting_for_stock)
async def process_product_stock(message: Message, state: FSMContext) -> None:
    """Обработка количества товара."""
    try:
        stock = int(message.text)
        if stock < 0:
            await message.answer("❌ Кількість не може бути від'ємною")
            return
        if stock > 100000:
            await message.answer("❌ Кількість занадто велика (макс 100000)")
            return
        
        await state.update_data(stock=stock)
        await state.set_state(AddProductStates.waiting_for_image_url)
        await message.answer("🖼️ Введіть URL зображення товару (або напишіть 'skip' щоб пропустити):")
    except ValueError:
        await message.answer("❌ Введіть дійсну кількість (число)")


@router.message(AddProductStates.waiting_for_image_url)
async def process_product_image(message: Message, state: FSMContext) -> None:
    """Обработка URL изображения товара."""
    image_url = None if message.text.lower() == "skip" else message.text
    
    if image_url and not (image_url.startswith("http://") or image_url.startswith("https://")):
        await message.answer("❌ URL повинен починатися з http:// або https://")
        return
    
    await state.update_data(image_url=image_url)
    await state.set_state(AddProductStates.waiting_for_confirmation)
    
    # Показываем подтверждение
    data = await state.get_data()
    confirmation_text = (
        f"✅ {html.bold('Перевірте дані товару:')}\n\n"
        f"📝 Назва: {data['name']}\n"
        f"📄 Опис: {data['description']}\n"
        f"💰 Ціна: {data['price']:.2f} грн\n"
        f"📂 Категорія: {data['category']}\n"
        f"📦 Кількість: {data['stock']} шт\n"
        f"🖼️ Зображення: {'Так' if data['image_url'] else 'Ні'}\n\n"
        f"{html.bold('Додати товар?')}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Так, додати", callback_data="confirm_add_product")
    builder.button(text="❌ Ні, скасувати", callback_data="cancel_add_product")
    builder.adjust(2)
    
    await message.answer(confirmation_text, reply_markup=builder.as_markup())


@router.callback_query(AddProductStates.waiting_for_confirmation, F.data == "confirm_add_product")
async def confirm_add_product(query: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение и сохранение нового товара."""
    try:
        data = await state.get_data()
        
        product_id = await db.add_product(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            category=data['category'],
            stock=data['stock'],
            image_url=data['image_url']
        )
        
        if product_id:
            logger.info(f"Admin {query.from_user.id} added product: {data['name']} (ID: {product_id})")
            await query.message.edit_text(
                f"✅ {html.bold('Товар успішно додано!')}\n\n"
                f"ID товару: {product_id}\n"
                f"Назва: {data['name']}\n"
                f"Ціна: {data['price']:.2f} грн",
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await query.message.edit_text(
                "❌ Помилка при додаванні товару. Спробуйте пізніше.",
                reply_markup=get_admin_main_keyboard()
            )
        
        await query.answer()
        await state.clear()
    except Exception as e:
        logger.exception(f"Error adding product: {e}")
        await query.message.edit_text(
            f"❌ Помилка: {str(e)}",
            reply_markup=get_admin_main_keyboard()
        )
        await query.answer()
        await state.clear()


@router.callback_query(AddProductStates.waiting_for_confirmation, F.data == "cancel_add_product")
async def cancel_add_product(query: CallbackQuery, state: FSMContext) -> None:
    """Отмена добавления товара."""
    await state.clear()
    await query.message.edit_text(
        "❌ Додавання товару скасовано.",
        reply_markup=get_admin_main_keyboard()
    )
    await query.answer()


# ═════════════════════════════════════════════════════════════════════════════
# HANDLERS ДЛЯ УДАЛЕНИЯ ТОВАРА
# ═════════════════════════════════════════════════════════════════════════════


@router.callback_query(F.data == "admin_delete_products", IsAdminFilter())
async def admin_delete_products_menu(query: CallbackQuery) -> None:
    """Показывает список товаров для удаления."""
    logger.info(f"Admin {query.from_user.id} opened product deletion menu")
    
    products = await db.get_all_products()
    
    if not products:
        await query.message.edit_text(
            "❌ Товарів немає.",
            reply_markup=get_admin_products_keyboard()
        )
        await query.answer()
        return
    
    # Показываем товары для удаления (максимум 15 товаров в одном сообщении)
    text = f"❌ {html.bold('Виберіть товар для видалення:')}\n\n"
    
    builder = InlineKeyboardBuilder()
    for product in products[:15]:
        builder.button(
            text=f"❌ {product['name']} ({product['stock']} шт) - {float(product['price']):.0f} грн",
            callback_data=f"delete_product:{product['id']}"
        )
    
    builder.button(text="◀️ Назад", callback_data="admin_products")
    builder.adjust(1)
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())
    await query.answer()


@router.callback_query(F.data.startswith("delete_product:"), IsAdminFilter())
async def confirm_delete_product(query: CallbackQuery) -> None:
    """Подтверждение удаления товара."""
    try:
        product_id = int(query.data.split(":")[1])
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await query.message.edit_text(
                "❌ Товар не знайдено.",
                reply_markup=get_admin_products_keyboard()
            )
            await query.answer()
            return
        
        confirmation_text = (
            f"⚠️ {html.bold('ПІДТВЕРДЖЕННЯ ВИДАЛЕННЯ')}\n\n"
            f"Товар: {product['name']}\n"
            f"Ціна: {float(product['price']):.2f} грн\n"
            f"Кількість: {product['stock']} шт\n\n"
            f"{html.italic('Ви впевнені що хочете видалити цей товар?')}\n"
            f"{html.italic('Це дійство не можна скасувати!')}"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Так, видалити", callback_data=f"confirm_delete_product:{product_id}")
        builder.button(text="❌ Ні, скасувати", callback_data="admin_delete_products")
        builder.adjust(2)
        
        await query.message.edit_text(confirmation_text, reply_markup=builder.as_markup())
        await query.answer()
    except Exception as e:
        logger.exception(f"Error in delete confirmation: {e}")
        await query.answer("❌ Помилка при обробці запиту", show_alert=True)


@router.callback_query(F.data.startswith("confirm_delete_product:"), IsAdminFilter())
async def execute_delete_product(query: CallbackQuery) -> None:
    """Удаляет товар из БД."""
    try:
        product_id = int(query.data.split(":")[1])
        product = await db.get_product_by_id(product_id)
        
        success = await db.delete_product(product_id)
        
        if success:
            logger.info(f"Admin {query.from_user.id} deleted product: {product['name']} (ID: {product_id})")
            await query.message.edit_text(
                f"✅ Товар '{product['name']}' успішно видалено!",
                reply_markup=get_admin_products_keyboard()
            )
        else:
            await query.message.edit_text(
                "❌ Помилка при видаленні товару.",
                reply_markup=get_admin_products_keyboard()
            )
        
        await query.answer()
    except Exception as e:
        logger.exception(f"Error deleting product: {e}")
        await query.message.edit_text(
            f"❌ Помилка: {str(e)}",
            reply_markup=get_admin_products_keyboard()
        )
        await query.answer()
