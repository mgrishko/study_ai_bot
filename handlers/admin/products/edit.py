"""Handlers для редагування товарів (адміністратор)."""
from aiogram import Router, html, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import db
from filters import IsAdminFilter
from keyboards import (
    get_admin_products_keyboard,
    get_product_edit_fields_keyboard,
    get_product_field_confirmation_keyboard,
    get_product_detail_keyboard
)
from logger_config import get_logger
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = get_logger("aiogram.handlers")

router = Router()


# FSM State for product editing
class ProductEditState(StatesGroup):
    """States for product field editing."""
    editing_field = State()


@router.callback_query(F.data == "admin_edit_products", IsAdminFilter())
async def admin_edit_products_menu(query: CallbackQuery) -> None:
    """Показує список товарів для редагування."""
    logger.info(f"Admin {query.from_user.id} opened product edit menu")
    
    products = await db.get_all_products()
    
    if not products:
        await query.message.edit_text(
            "❌ Товарів немає.",
            reply_markup=get_admin_products_keyboard()
        )
        await query.answer()
        return
    
    text = f"✏️ {html.bold('Виберіть товар для редагування:')}\n\n"
    
    builder = InlineKeyboardBuilder()
    for product in products[:15]:
        builder.button(
            text=f"📦 {product['name']} ({product['stock']} шт) - {float(product['price']):.0f} грн",
            callback_data=f"admin_edit_product_start:{product['id']}"
        )
    
    builder.button(text="◀️ Назад", callback_data="admin_products")
    builder.adjust(1)
    
    await query.message.edit_text(text, reply_markup=builder.as_markup())
    await query.answer()


@router.callback_query(F.data.startswith("admin_edit_product_start:"), IsAdminFilter())
async def show_product_detail(query: CallbackQuery) -> None:
    """Показує деталі товару та поля для редагування."""
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
        
        product_text = (
            f"📦 {html.bold(product['name'])}\n\n"
            f"📖 Опис: {product['description'] or 'N/A'}\n"
            f"💰 Ціна: {float(product['price']):.2f} грн\n"
            f"🏷 Категорія: {product['category']}\n"
            f"📦 Кількість: {product['stock']} шт\n"
            f"🔗 Зображення: {product['image_url'] or 'N/A'}\n"
        )
        
        # Отримання та форматування логів редагування
        logs = await db.get_product_edit_logs(product_id, limit=3)
        
        if logs:
            product_text += "\n📝 Останні редагування:\n"
            for log in logs:
                admin_id = log['admin_id']
                field_name = log['field_name']
                old_value = log['old_value']
                new_value = log['new_value']
                created_at = log['created_at']
                
                product_text += (
                    f"\n• {field_name} (admin: {admin_id})\n"
                    f"  Було: <code>{old_value[:30]}</code>\n"
                    f"  Стало: <code>{new_value[:30]}</code>\n"
                    f"  {created_at.strftime('%d.%m.%Y %H:%M')}"
                )
        
        await query.message.edit_text(product_text, reply_markup=get_product_detail_keyboard(product_id), parse_mode="HTML")
        await query.answer()
    except Exception as e:
        logger.exception(f"Error in product detail: {e}")
        await query.answer("❌ Помилка при обробці запиту", show_alert=True)


@router.callback_query(F.data.startswith("admin_edit_product_field:"), IsAdminFilter())
async def choose_product_field(query: CallbackQuery, state: FSMContext) -> None:
    """Виводить меню вибору поля товару для редагування."""
    try:
        parts = query.data.split(":")
        product_id = int(parts[1])
        
        product = await db.get_product_by_id(product_id)
        if not product:
            await query.answer("❌ Товар не знайдено", show_alert=True)
            return
        
        # Якщо це просто клік на вибір поля (без третього параметра), показуємо меню
        if len(parts) == 2:
            menu_text = f"📦 {html.bold(product['name'])}\n\n{html.bold('Виберіть поле для редагування:')}"
            await query.message.edit_text(menu_text, reply_markup=get_product_edit_fields_keyboard(product_id))
            await query.answer()
            return
        
        # Якщо вибране конкретне поле
        field_name = parts[2]
        field_display = {
            'name': '📝 Назва товару',
            'description': '📖 Опис товару',
            'price': '💰 Ціна товару',
            'category': '🏷 Категорія товару',
            'stock': '📦 Кількість товару',
            'image_url': '🔗 URL зображення'
        }
        
        current_value = str(product.get(field_name, ''))
        prompt_text = (
            f"✏️ {html.bold(field_display.get(field_name, field_name))}\n\n"
            f"Поточне значення: {current_value}\n\n"
            f"Введіть нове значення:"
        )
        
        await state.update_data(
            product_id=product_id,
            field_name=field_name,
            old_value=current_value
        )
        await state.set_state(ProductEditState.editing_field)
        
        await query.message.edit_text(prompt_text)
        await query.answer()
    except Exception as e:
        logger.exception(f"Error choosing field: {e}")
        await query.answer("❌ Помилка при обробці запиту", show_alert=True)


@router.message(ProductEditState.editing_field, IsAdminFilter())
async def process_product_field_input(message: Message, state: FSMContext) -> None:
    """Обробляє введене значення поля товару."""
    data = await state.get_data()
    
    # Only process if we have product edit state data
    if 'product_id' not in data or 'field_name' not in data:
        await message.answer("❌ Помилка при обробці. Спробуйте ще раз.")
        await state.clear()
        return
    
    product_id = data['product_id']
    field_name = data['field_name']
    old_value = data['old_value']
    new_value = message.text
    
    product = await db.get_product_by_id(product_id)
    if not product:
        await message.answer("❌ Товар не знайдено.")
        await state.clear()
        return
    
    # Валідація
    is_valid = True
    error_msg = ""
    
    if field_name == 'name':
        if not new_value or len(new_value) > 255:
            is_valid = False
            error_msg = "Назва має бути від 1 до 255 символів"
    
    elif field_name == 'description':
        if len(new_value) > 1000:
            is_valid = False
            error_msg = "Опис має бути не більше 1000 символів"
    
    elif field_name == 'price':
        try:
            price = float(new_value)
            if price < 0 or price > 999999.99:
                is_valid = False
                error_msg = "Ціна має бути від 0 до 999999.99"
            new_value = price
        except ValueError:
            is_valid = False
            error_msg = "Ціна має бути числом"
    
    elif field_name == 'stock':
        try:
            stock = int(new_value)
            if stock < 0:
                is_valid = False
                error_msg = "Кількість не може бути негативною"
            new_value = stock
        except ValueError:
            is_valid = False
            error_msg = "Кількість має бути цілим числом"
    
    elif field_name == 'category':
        if not new_value or len(new_value) > 100:
            is_valid = False
            error_msg = "Категорія має бути від 1 до 100 символів"
    
    elif field_name == 'image_url':
        if new_value and len(new_value) > 500:
            is_valid = False
            error_msg = "URL зображення занадто довгий"
    
    if not is_valid:
        await message.answer(f"❌ {error_msg}")
        return
    
    # Показуємо підтвердження
    confirmation_text = (
        f"✏️ {html.bold('ПІДТВЕРДЖЕННЯ ЗМІН')}\n\n"
        f"Поле: {field_name}\n"
        f"Старе значення: {old_value}\n"
        f"Нове значення: {new_value}\n\n"
        f"Ви впевнені?"
    )
    
    await state.update_data(new_value=new_value)
    await message.answer(
        confirmation_text,
        reply_markup=get_product_field_confirmation_keyboard(product_id, field_name)
    )


@router.callback_query(F.data.startswith("admin_confirm_edit_product:"), IsAdminFilter())
async def confirm_product_edit(query: CallbackQuery, state: FSMContext) -> None:
    """Підтверджує та зберігає зміни товару."""
    try:
        parts = query.data.split(":")
        product_id = int(parts[1])
        field_name = parts[2]
        
        data = await state.get_data()
        new_value = data.get('new_value')
        old_value = data.get('old_value')
        
        if new_value is None:
            await query.answer("❌ Помилка обробки даних", show_alert=True)
            await state.clear()
            return
        
        # Оновлюємо товар
        success = await db.update_product(product_id, **{field_name: new_value})
        
        if success:
            # Логуємо редагування
            await db.add_product_edit_log(
                product_id=product_id,
                admin_id=query.from_user.id,
                field_name=field_name,
                old_value=old_value,
                new_value=str(new_value)
            )
            
            logger.info(f"Admin {query.from_user.id} updated product {product_id}: {field_name} = {new_value}")
            product = await db.get_product_by_id(product_id)
            
            success_text = (
                f"✅ {html.bold('Товар успішно оновлено!')}\n\n"
                f"📦 {product['name']}\n"
                f"{field_name}: {new_value}"
            )
            
            await query.message.edit_text(success_text, reply_markup=get_product_detail_keyboard(product_id))
        else:
            await query.message.edit_text(
                "❌ Помилка при оновленні товару.",
                reply_markup=get_product_detail_keyboard(product_id)
            )
        
        await query.answer()
        await state.clear()
    except Exception as e:
        logger.exception(f"Error confirming edit: {e}")
        await query.answer("❌ Помилка при обробці запиту", show_alert=True)
        await state.clear()
