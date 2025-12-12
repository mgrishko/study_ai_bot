from aiogram import Router, html, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import db
from keyboards import (
    get_products_keyboard,
    get_order_keyboard,
    get_product_details_keyboard,
    get_order_confirmation_keyboard,
    get_my_orders_keyboard,
    get_main_menu,
    get_admin_menu
)
from filters import IsUserFilter, IsUserCallbackFilter
from config import ADMIN_IDS
from tts_service import text_to_speech, get_product_description_for_tts
from logger_config import get_logger
from handlers.order_states import OrderStates
from validators import validate_phone, validate_email

logger = get_logger("aiogram.handlers")
router = Router()


# Обробники для кнопок меню
@router.message(F.text == "🛍️ Каталог", IsUserFilter())
async def handle_catalog_button(message: Message) -> None:
    """Обробник кнопки каталога."""
    products = await db.get_all_products()
    
    if not products:
        await message.answer("😔 На жаль, наразі немає товарів в наявності.")
        return
    
    catalog_text = (
        f"🛍 {html.bold('Каталог товарів:')}\n\n"
        f"Натисніть на товар, щоб переглянути деталі та замовити:"
    )
    
    await message.answer(catalog_text, reply_markup=get_products_keyboard(products))


@router.message(F.text == "📦 Мої замовлення", IsUserFilter())
async def handle_my_orders_button(message: Message) -> None:
    """Обробник кнопки мої замовлення."""
    orders = await db.get_user_orders(message.from_user.id)
    
    if not orders:
        await message.answer("У вас ще немає замовлень.")
        return
    
    orders_text = f"📦 {html.bold('Ваші замовлення:')}\n\n"
    
    status_emoji = {
        'pending': '🕐',
        'confirmed': '✅',
        'shipped': '🚚',
        'delivered': '📬',
        'cancelled': '❌'
    }
    
    for order in orders:
        status = order['status']
        emoji = status_emoji.get(status, '❓')
        
        orders_text += (
            f"{emoji} {html.bold(f'Замовлення #{order['id']}')}"
            f"\n   Товар: {order['product_name']}"
            f"\n   Кількість: {order['quantity']} шт."
            f"\n   Сума: {float(order['total_price']):.2f} грн"
            f"\n   Статус: {status}"
            f"\n   Дата: {order['created_at']}\n\n"
        )
    
    await message.answer(orders_text, reply_markup=get_my_orders_keyboard())


@router.message(F.text == "📚 Категорії", IsUserFilter())
async def handle_categories_button(message: Message) -> None:
    """Обробник кнопки категорії."""
    categories = await db.get_categories()
    
    if not categories:
        await message.answer("😔 Категорії не знайдені.")
        return
    
    categories_text = f"📚 {html.bold('Категорії товарів:')}\n\n"
    categories_list = "\n".join([f"• {cat}" for cat in categories])
    
    await message.answer(f"{categories_text}{categories_list}")


@router.message(F.text == "❓ Допомога", IsUserFilter())
async def handle_help_button(message: Message) -> None:
    """Обробник кнопки допомога."""
    help_text = (
        f"📋 {html.bold('Доступні команди:')}\n\n"
        f"/start - Почати заново\n"
        f"/help - Це повідомлення\n"
        f"/info - Інформація про бота\n"
        f"/catalog - Перегляд каталогу\n"
        f"/order - Оформити замовлення\n"
        f"/myorders - Мої замовлення\n"
        f"/generate - AI генератор зображень\n\n"
        f"💡 Використовуйте кнопки меню нижче для швидкого доступу!"
    )
    await message.answer(help_text)


@router.message(F.text == "ℹ️ Про магазин", IsUserFilter())
async def handle_about_button(message: Message) -> None:
    """Обробник кнопки про магазин."""
    info_text = (
        f"ℹ️ {html.bold('Інформація про бота')}\n\n"
        f"🤖 Назва: Магазин верхнього одягу\n"
        f"📦 Версія: 1.0\n"
        f"🛠 Технології: Python 3.13, Aiogram 3.0, PostgreSQL\n\n"
        f"📝 {html.bold('Функціонал:')}\n"
        f"• Перегляд каталогу товарів\n"
        f"• Оформлення замовлень\n"
        f"• Відстеження статусу замовлень\n"
        f"• Пошук за категоріями\n"
        f"• AI генератор зображень\n\n"
        f"📞 {html.bold('Контакти:')}\n"
        f"📧 Email: shop@example.com\n"
        f"📱 Телефон: +380 XX XXX XX XX\n"
        f"🕐 Години роботи: 9:00 - 21:00 (щодня)\n\n"
        f"🚚 Безкоштовна доставка від 1000 грн!"
    )
    await message.answer(info_text)


@router.message(F.text == "🎨 AI")
async def handle_ai_button(message: Message) -> None:
    """Обробник кнопки AI генератора."""
    await message.answer(
        "🎨 Для використання AI генератора використовуйте команду /generate"
    )


@router.message(F.text == "⚙️ Адміністратор")
async def handle_admin_button(message: Message) -> None:
    """Обробник кнопки адміністратор."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нема доступу до панелі адміністратора.")
        return
    
    await message.answer(
        "⚙️ Для доступу до панелі адміністратора використовуйте команду /admin"
    )


@router.message(Command("catalog"), IsUserFilter())
async def command_catalog_handler(message: Message) -> None:
    """Обробник команди /catalog."""
    products = await db.get_all_products()
    
    if not products:
        await message.answer("😔 На жаль, наразі немає товарів в наявності.")
        return
    
    catalog_text = (
        f"🛍 {html.bold('Каталог товарів:')}\n\n"
        f"Натисніть на товар, щоб переглянути деталі та замовити:"
    )
    
    await message.answer(catalog_text, reply_markup=get_products_keyboard(products))


@router.message(Command("order"), IsUserFilter())
async def command_order_handler(message: Message) -> None:
    """Обробник команди /order."""
    products = await db.get_all_products()
    
    if not products:
        await message.answer("😔 На жаль, наразі немає товарів в наявності.")
        return
    
    order_text = (
        f"🛒 {html.bold('Оформлення замовлення')}\n\n"
        f"Виберіть товар, який бажаєте замовити:"
    )
    
    await message.answer(order_text, reply_markup=get_order_keyboard(products))


@router.message(Command("categories"), IsUserFilter())
async def command_categories_handler(message: Message) -> None:
    """Обробник команди /categories."""
    categories = await db.get_categories()
    
    if not categories:
        await message.answer("😔 Наразі немає доступних категорій.")
        return
    
    categories_text = f"📂 {html.bold('Доступні категорії:')}\n\n"
    
    for category in categories:
        products_count = len(await db.get_products_by_category(category))
        categories_text += f"🔸 {category} ({products_count} товарів)\n"
    
    await message.answer(categories_text)


@router.message(Command("myorders"), IsUserFilter())
async def command_my_orders_handler(message: Message) -> None:
    """Обробник команди /myorders."""
    orders = await db.get_user_orders(message.from_user.id)
    
    if not orders:
        await message.answer("📭 У вас ще немає замовлень. Перегляньте /catalog!")
        return
    
    orders_text = f"📦 {html.bold('Ваші замовлення:')}\n\n"
    
    status_emoji = {
        'pending': '🕐',
        'confirmed': '✅',
        'shipped': '🚚',
        'delivered': '📬',
        'cancelled': '❌'
    }
    
    for order in orders:
        status = order['status']
        emoji = status_emoji.get(status, '❓')
        
        orders_text += (
            f"{emoji} {html.bold(f'Замовлення #{order['id']}')}\n"
            f"   Товар: {order['product_name']}\n"
            f"   Кількість: {order['quantity']} шт.\n"
            f"   Сума: {float(order['total_price']):.2f} грн\n"
            f"   Статус: {status}\n"
            f"   Дата: {order['created_at']}\n\n"
        )
    
    await message.answer(orders_text)


# =============== CALLBACK ОБРОБНИКИ ===============

@router.callback_query(F.data.startswith("listen_product:"), IsUserCallbackFilter())
async def listen_product_callback(callback: CallbackQuery) -> None:
    """Обробник для озвучування опису товару."""
    try:
        product_id = int(callback.data.split(":")[1])
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return
        
        # Показуємо статус обробки
        await callback.answer("🔊 Генерую аудіофайл...")
        
        # Підготовляємо текст для озвучування
        tts_text = get_product_description_for_tts(product)
        
        # Генеруємо аудіофайл
        audio_buffer = await text_to_speech(tts_text, language="uk")
        
        if audio_buffer:
            # Відправляємо аудіофайл
            await callback.message.answer_voice(
                voice=audio_buffer,
                caption=f"🔊 Інформація про товар '{product['name']}'"
            )
            logger.info(f"Product audio sent for product_id={product_id}")
        else:
            await callback.message.answer(
                "❌ Помилка при генерації аудіо. Спробуйте пізніше."
            )
        
    except Exception as e:
        logger.error(f"Error in listen_product_callback: {e}", exc_info=True)
        await callback.answer("❌ Помилка при обробці запиту", show_alert=True)


@router.callback_query(F.data == "back_to_start", IsUserCallbackFilter())
async def back_to_start(callback: CallbackQuery) -> None:
    """Обробник кнопки повернення на початок."""
    is_admin = callback.from_user.id in ADMIN_IDS
    menu = get_admin_menu() if is_admin else get_main_menu()
    
    await callback.message.answer(
        f"👋 Вітаємо, {html.bold(callback.from_user.full_name)}!\n\n"
        f"🧥 Ласкаво просимо до нашого магазину верхнього одягу!",
        reply_markup=menu
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:"), IsUserCallbackFilter())
async def product_details_callback(callback: CallbackQuery) -> None:
    """Обробник callback для перегляду деталей товару."""
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product_by_id(product_id)
    
    if not product:
        await callback.answer("❌ Товар не знайдено", show_alert=True)
        return
    
    details_text = (
        f"🔍 {html.bold(product['name'])}\n\n"
        f"📝 Опис: {product['description']}\n"
        f"📂 Категорія: {product['category']}\n"
        f"💰 Ціна: {float(product['price']):.2f} грн\n"
        f"📦 В наявності: {product['stock']} шт.\n"
    )
    
    await callback.message.edit_text(
        details_text, 
        reply_markup=get_product_details_keyboard(product['id'])
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_catalog", IsUserCallbackFilter())
async def back_to_catalog_callback(callback: CallbackQuery) -> None:
    """Обробник callback для повернення до каталогу."""
    products = await db.get_all_products()
    
    if not products:
        await callback.message.edit_text("😔 На жаль, наразі немає товарів в наявності.")
        return
    
    catalog_text = (
        f"🛍 {html.bold('Каталог товарів:')}\n\n"
        f"Натисніть на товар, щоб переглянути деталі та замовити:"
    )
    
    await callback.message.edit_text(
        catalog_text, 
        reply_markup=get_products_keyboard(products)
    )
    await callback.answer()


@router.callback_query(F.data == "my_orders", IsUserCallbackFilter())
async def my_orders_callback(callback: CallbackQuery) -> None:
    """Обробник callback для перегляду замовлень."""
    orders = await db.get_user_orders(callback.from_user.id)
    
    if not orders:
        await callback.message.edit_text("📭 У вас ще немає замовлень. Перегляньте /catalog!")
        return
    
    orders_text = f"📦 {html.bold('Ваші замовлення:')}\n\n"
    
    status_emoji = {
        'pending': '🕐',
        'confirmed': '✅',
        'shipped': '🚚',
        'delivered': '📬',
        'cancelled': '❌'
    }
    
    for order in orders:
        status = order['status']
        emoji = status_emoji.get(status, '❓')
        
        orders_text += (
            f"{emoji} {html.bold(f'Замовлення #{order['id']}')}\n"
            f"   Товар: {order['product_name']}\n"
            f"   Кількість: {order['quantity']} шт.\n"
            f"   Сума: {float(order['total_price']):.2f} грн\n"
            f"   Статус: {status}\n"
            f"   Дата: {order['created_at']}\n\n"
        )
    
    await callback.message.edit_text(
        orders_text, 
        reply_markup=get_my_orders_keyboard()
    )
    await callback.answer()


# ═════════════════════════════════════════════════════════════════════════════
# HANDLERS ДЛЯ ЗАМОВЛЕННЯ З КОНТАКТНОЮ ІНФОРМАЦІЄЮ (FSM)
# ═════════════════════════════════════════════════════════════════════════════


@router.callback_query(F.data.startswith("order_product:"), IsUserCallbackFilter())
async def order_product_with_contact_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Почати замовлення з запитом контактної інформації."""
    try:
        product_id = int(callback.data.split(":")[1])
        product = await db.get_product_by_id(product_id)
        
        if not product:
            await callback.answer("❌ Товар не знайдено", show_alert=True)
            return
        
        if product['stock'] < 1:
            await callback.answer("❌ Товар закінчився на складі", show_alert=True)
            return
        
        # Зберігаємо дані в FSM
        await state.update_data(
            product_id=product_id,
            product_name=product['name'],
            product_price=float(product['price']),
            quantity=1,
            user_id=callback.from_user.id,
            user_name=callback.from_user.full_name or "User"
        )
        
        # Просимо телефон
        await state.set_state(OrderStates.waiting_for_phone)
        await callback.message.edit_text(
            f"📱 {html.bold('Введіть ваш телефонний номер')}\n\n"
            f"Формати: +380501234567 або 0501234567\n\n"
            f"Товар: {product['name']}\n"
            f"Ціна: {float(product['price']):.2f} грн",
            reply_markup=None
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error in order_product_with_contact_start: {e}", exc_info=True)
        await callback.answer("❌ Помилка при обробці запиту", show_alert=True)


@router.message(OrderStates.waiting_for_phone, IsUserFilter())
async def process_order_phone(message: Message, state: FSMContext) -> None:
    """Обробка телефонного номера."""
    phone = message.text
    is_valid, error = validate_phone(phone)
    
    if not is_valid:
        await message.answer(
            f"❌ {error}\n\n"
            f"Спробуйте знову. Формати: +380501234567 або 0501234567"
        )
        return
    
    # Зберігаємо телефон та просимо email
    await state.update_data(phone=phone)
    await state.set_state(OrderStates.waiting_for_email)
    
    await message.answer(
        f"📧 {html.bold('Введіть ваш email')}\n\n"
        f"Приклад: user@example.com"
    )


@router.message(OrderStates.waiting_for_email, IsUserFilter())
async def process_order_email(message: Message, state: FSMContext) -> None:
    """Обробка email адреси."""
    email = message.text
    is_valid, error = validate_email(email)
    
    if not is_valid:
        await message.answer(
            f"❌ {error}\n\n"
            f"Спробуйте знову. Приклад: user@example.com"
        )
        return
    
    # Зберігаємо email та просимо підтвердження
    data = await state.update_data(email=email)
    await state.set_state(OrderStates.waiting_for_confirmation)
    
    # Показуємо підсумок замовлення
    confirmation_text = (
        f"✅ {html.bold('Підтвердження замовлення')}\n\n"
        f"📋 Товар: {data['product_name']}\n"
        f"💰 Ціна: {data['product_price']:.2f} грн\n"
        f"📦 Кількість: {data['quantity']} шт.\n"
        f"📱 Телефон: {data['phone']}\n"
        f"📧 Email: {data['email']}\n\n"
        f"Всього: {data['product_price'] * data['quantity']:.2f} грн\n\n"
        f"Введіть 'так' для підтвердження або 'ні' для скасування:"
    )
    
    await message.answer(confirmation_text)


@router.message(OrderStates.waiting_for_confirmation, IsUserFilter())
async def confirm_order_with_contact(message: Message, state: FSMContext) -> None:
    """Підтвердження замовлення з контактною інформацією."""
    if message.text.lower() not in ["так", "yes", "у", "y"]:
        await state.clear()
        await message.answer(
            "❌ Замовлення скасовано.",
            reply_markup=get_order_confirmation_keyboard()
        )
        return
    
    try:
        data = await state.get_data()
        
        # Створюємо замовлення з контактною інформацією
        order_id = await db.create_order(
            user_id=data['user_id'],
            user_name=data['user_name'],
            product_id=data['product_id'],
            quantity=data['quantity'],
            phone=data['phone'],
            email=data['email']
        )
        
        if order_id:
            confirmation_text = (
                f"✅ {html.bold('Замовлення оформлено!')}\n\n"
                f"📋 Номер замовлення: #{order_id}\n"
                f"🛍 Товар: {data['product_name']}\n"
                f"💰 Сума: {data['product_price'] * data['quantity']:.2f} грн\n"
                f"📦 Кількість: {data['quantity']} шт.\n"
                f"📱 Телефон: {data['phone']}\n"
                f"📧 Email: {data['email']}\n\n"
                f"Дякуємо за замовлення! Наш менеджер зв'яжеться з вами найближчим часом.\n\n"
                f"Ви можете переглянути свої замовлення командою /myorders"
            )
            
            logger.info(f"Order #{order_id} created with contact info - Phone: {data['phone']}, Email: {data['email']}")
            
            await message.answer(
                confirmation_text,
                reply_markup=get_order_confirmation_keyboard()
            )
        else:
            await message.answer(
                "❌ Помилка оформлення замовлення. Можливо товар закінчився.",
                reply_markup=get_order_confirmation_keyboard()
            )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error in confirm_order_with_contact: {e}", exc_info=True)
        await message.answer(
            "❌ Помилка при обробці замовлення",
            reply_markup=get_order_confirmation_keyboard()
        )
        await state.clear()
