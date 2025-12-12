"""Handlers для додавання товарів (адміністратор)."""
from aiogram import Router, html, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from filters import IsAdminFilter, IsAdminCallbackFilter
from keyboards import get_admin_main_keyboard
from logger_config import get_logger

logger = get_logger("aiogram.handlers")

router = Router()


# FSM Стани для додавання товару
class AddProductStates(StatesGroup):
    """Стани FSM для додавання нового товару."""
    waiting_for_name = State()           # Крок 1: назва
    waiting_for_description = State()    # Крок 2: опис
    waiting_for_price = State()          # Крок 3: ціна
    waiting_for_category = State()       # Крок 4: категорія
    waiting_for_stock = State()          # Крок 5: кількість
    waiting_for_image_source = State()   # Крок 6: вибір джерела зображення (Генерувати/URL)
    waiting_for_image_url = State()      # Крок 6b: URL зображення (якщо обрано URL)
    waiting_for_confirmation = State()   # Крок 7: підтвердження


@router.callback_query(F.data == "admin_add_product", IsAdminFilter())
async def admin_add_product_start(query: CallbackQuery, state: FSMContext) -> None:
    """Начало процесса добавления товара."""
    logger.info(f"Admin {query.from_user.id} started adding product")
    await state.set_state(AddProductStates.waiting_for_name)
    await query.message.edit_text("📝 Введіть назву товару (макс 255 символів):")
    await query.answer()


@router.message(AddProductStates.waiting_for_name, IsAdminFilter())
async def process_product_name(message: Message, state: FSMContext) -> None:
    """Обробка назви товару."""
    if len(message.text) > 255:
        await message.answer("❌ Назва товару занадто довга (макс 255 символів)")
        return
    
    await state.update_data(name=message.text)
    await state.set_state(AddProductStates.waiting_for_description)
    await message.answer("📝 Введіть опис товару (макс 1000 символів):")


@router.message(AddProductStates.waiting_for_description, IsAdminFilter())
async def process_product_description(message: Message, state: FSMContext) -> None:
    """Обробка опису товару."""
    if len(message.text) > 1000:
        await message.answer("❌ Опис занадто довгий (макс 1000 символів)")
        return
    
    await state.update_data(description=message.text)
    await state.set_state(AddProductStates.waiting_for_price)
    await message.answer("💰 Введіть ціну товару (в гривнях, наприклад 2500.50):")


@router.message(AddProductStates.waiting_for_price, IsAdminFilter())
async def process_product_price(message: Message, state: FSMContext) -> None:
    """Обробка ціни товару."""
    try:
        price = float(message.text)
        if price <= 0:
            await message.answer("❌ Ціна повинна бути більше 0")
            return
        if price > 999999:
            await message.answer("❌ Ціна занадто висока (макс 999999 грн)")
            return
        
        await state.update_data(price=price)
        
        # Отримуємо категорії для вибору
        categories = await db.get_categories()
        if not categories:
            await message.answer("❌ Немає категорій. Спочатку додайте категорію в БД.")
            await state.clear()
            logger.warning(f"No categories available when adding product")
            return
        
        await state.set_state(AddProductStates.waiting_for_category)
        
        # Створюємо клавіатуру з категоріями
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


@router.callback_query(AddProductStates.waiting_for_category, F.data.startswith("select_category:"), IsAdminCallbackFilter())
async def process_product_category(query: CallbackQuery, state: FSMContext) -> None:
    """Обробка вибору категорії товару."""
    category = query.data.split(":", 1)[1]
    await state.update_data(category=category)
    await state.set_state(AddProductStates.waiting_for_stock)
    await query.message.edit_text("📦 Введіть кількість товару на складі (число):")
    await query.answer()


@router.message(AddProductStates.waiting_for_stock, IsAdminFilter())
async def process_product_stock(message: Message, state: FSMContext) -> None:
    """Обробка кількості товару."""
    try:
        stock = int(message.text)
        if stock < 0:
            await message.answer("❌ Кількість не може бути від'ємною")
            return
        if stock > 100000:
            await message.answer("❌ Кількість занадто велика (макс 100000)")
            return
        
        await state.update_data(stock=stock)
        await state.set_state(AddProductStates.waiting_for_image_source)
        
        # Показуємо вибір способу отримання зображення
        from keyboards.admin import get_image_source_keyboard
        await message.answer(
            "🖼️ Як ви хочете отримати зображення товару?",
            reply_markup=get_image_source_keyboard()
        )
    except ValueError:
        await message.answer("❌ Введіть дійсну кількість (число)")


@router.callback_query(AddProductStates.waiting_for_image_source, F.data == "admin_image_url", IsAdminCallbackFilter())
async def admin_choose_image_url(query: CallbackQuery, state: FSMContext) -> None:
    """Перехід до введення URL зображення."""
    await state.set_state(AddProductStates.waiting_for_image_url)
    await query.message.edit_text("🖼️ Введіть URL зображення товару (або напишіть 'skip' щоб пропустити):")
    await query.answer()


@router.message(AddProductStates.waiting_for_image_url, IsAdminFilter())
async def process_product_image(message: Message, state: FSMContext) -> None:
    """Обробка URL зображення товару."""
    image_url = None if message.text.lower() == "skip" else message.text
    
    if image_url and not (image_url.startswith("http://") or image_url.startswith("https://")):
        await message.answer("❌ URL повинен починатися з http:// або https://")
        return
    
    await state.update_data(image_url=image_url)
    await state.set_state(AddProductStates.waiting_for_confirmation)
    
    # Показуємо підтвердження
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


@router.callback_query(AddProductStates.waiting_for_confirmation, F.data == "confirm_add_product", IsAdminCallbackFilter())
async def confirm_add_product(query: CallbackQuery, state: FSMContext) -> None:
    """Подтверждение и сохранение товара."""
    try:
        data = await state.get_data()
        
        product_id = await db.add_product(
            name=data['name'],
            description=data['description'],
            price=data['price'],
            category=data['category'],
            stock=data['stock'],
            image_url=data.get('image_url')
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


@router.callback_query(AddProductStates.waiting_for_confirmation, F.data == "cancel_add_product", IsAdminCallbackFilter())
async def cancel_add_product(query: CallbackQuery, state: FSMContext) -> None:
    """Отмена добавления товара."""
    await state.clear()
    await query.message.edit_text(
        "❌ Додавання товару скасовано.",
        reply_markup=get_admin_main_keyboard()
    )
    await query.answer()
