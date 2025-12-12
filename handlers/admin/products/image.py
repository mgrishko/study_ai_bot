"""Handlers для генерації зображень товарів (адміністратор)."""
from aiogram import Router, html, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import db
from filters import IsAdminFilter, IsAdminCallbackFilter
from openai_service import generate_image
from keyboards import get_admin_main_keyboard
from logger_config import get_logger
from handlers.admin.products.add import AddProductStates

logger = get_logger("aiogram.handlers")

router = Router()


# FSM Стани для генерації зображення товару (вкладений процес)
class AdminGenerateImageStates(StatesGroup):
    """Стани FSM для генерації зображення товару адміністратором."""
    waiting_for_prompt = State()      # Крок 1: опис зображення
    waiting_for_size = State()        # Крок 2: розмір
    waiting_for_style = State()       # Крок 3: стиль
    waiting_for_confirmation = State() # Крок 4: підтвердження перед генерацією


@router.callback_query(AddProductStates.waiting_for_image_source, F.data == "admin_generate_image", IsAdminCallbackFilter())
async def admin_choose_generate_image(query: CallbackQuery, state: FSMContext) -> None:
    """Початок процесу генерації зображення товару."""
    logger.info(f"Admin {query.from_user.id} started generating product image")
    
    help_text = (
        f"🎨 {html.bold('Генератор зображень товару через OpenAI')}\n\n"
        f"Опишіть зображення товару, яке ви хочете генерувати.\n\n"
        f"{html.italic('Приклади:')}\n"
        f"• A modern smartphone in sleek design on white background\n"
        f"• High-quality leather wallet with premium look\n"
        f"• Professional camera on studio backdrop\n\n"
        f"Мінімум 10 символів, максимум 4000."
    )
    
    # Переходимо до вкладеного FSM для генерації
    await state.set_state(AdminGenerateImageStates.waiting_for_prompt)
    await query.message.edit_text(help_text)
    await query.answer()


@router.message(AdminGenerateImageStates.waiting_for_prompt, IsAdminFilter())
async def admin_process_image_prompt(message: Message, state: FSMContext) -> None:
    """Обробка опису зображення товару."""
    prompt = message.text.strip()
    
    # Валідація
    if len(prompt) < 10:
        await message.answer("❌ Опис має бути не менше 10 символів")
        return
    
    if len(prompt) > 4000:
        await message.answer("❌ Опис не може бути більше 4000 символів")
        return
    
    await state.update_data(product_prompt=prompt)
    await state.set_state(AdminGenerateImageStates.waiting_for_size)
    
    # Показуємо вибір розміру
    from keyboards.admin import get_admin_generate_image_sizes_keyboard
    await message.answer(
        "📐 Виберіть розмір зображення:",
        reply_markup=get_admin_generate_image_sizes_keyboard()
    )


@router.callback_query(AdminGenerateImageStates.waiting_for_size, F.data.startswith("admin_select_image_size:"), IsAdminCallbackFilter())
async def admin_process_image_size(query: CallbackQuery, state: FSMContext) -> None:
    """Обробка вибору розміру."""
    size = query.data.split(":")[1]
    await state.update_data(product_image_size=size)
    await state.set_state(AdminGenerateImageStates.waiting_for_style)
    
    # Показуємо вибір стилю
    from keyboards.admin import get_admin_generate_image_styles_keyboard
    await query.message.edit_text(
        "🎨 Виберіть стиль зображення:",
        reply_markup=get_admin_generate_image_styles_keyboard()
    )
    await query.answer()


@router.callback_query(AdminGenerateImageStates.waiting_for_style, F.data.startswith("admin_select_image_style:"), IsAdminCallbackFilter())
async def admin_process_image_style(query: CallbackQuery, state: FSMContext) -> None:
    """Обробка вибору стилю."""
    style = query.data.split(":")[1]
    await state.update_data(product_image_style=style)
    await state.set_state(AdminGenerateImageStates.waiting_for_confirmation)
    
    # Показуємо підтвердження
    data = await state.get_data()
    confirmation_text = (
        f"✅ {html.bold('Перевірте параметри генерації:')}\n\n"
        f"📝 Опис: {data['product_prompt'][:100]}{'...' if len(data['product_prompt']) > 100 else ''}\n"
        f"📐 Розмір: {data['product_image_size']}\n"
        f"🎨 Стиль: {data['product_image_style']}\n\n"
        f"{html.italic('Генерація займе 10-30 секунд...')}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Генерувати", callback_data="admin_confirm_generate_image")
    builder.button(text="❌ Скасувати", callback_data="admin_cancel_generate_image")
    builder.adjust(2)
    
    await query.message.edit_text(confirmation_text, reply_markup=builder.as_markup())
    await query.answer()


@router.callback_query(AdminGenerateImageStates.waiting_for_confirmation, F.data == "admin_confirm_generate_image", IsAdminCallbackFilter())
async def admin_confirm_generate_image(query: CallbackQuery, state: FSMContext) -> None:
    """Генерує зображення через OpenAI."""
    try:
        data = await state.get_data()
        
        # Показуємо статус "обробка"
        status_msg = await query.message.edit_text("⏳ Генерую зображення...")
        await query.answer()
        
        logger.info(f"Admin {query.from_user.id} generating product image")
        
        # Викликаємо OpenAI API
        image_url = await generate_image(
            prompt=data['product_prompt'],
            size=data['product_image_size'],
            style=data['product_image_style']
        )
        
        if not image_url:
            await status_msg.edit_text(
                "❌ Помилка при генерації зображення.\n"
                "Можливі причини:\n"
                "• Перевищено ліміт запитів (спробуйте пізніше)\n"
                "• Опис порушує політику OpenAI\n"
                "• Проблема з з'єднанням\n\n"
                "Спробуйте ще раз або виберіть інший опис."
            )
            logger.warning(f"Image generation failed for admin {query.from_user.id}")
            
            # Повертаємося до вибору розміру
            await state.set_state(AdminGenerateImageStates.waiting_for_prompt)
            await query.message.answer("🎨 Спробуйте з новим описом або виберіть інший спосіб отримання зображення")
            return
        
        # Зберігаємо URL у основному FSM стані
        await state.update_data(image_url=image_url)
        
        # Відправляємо статус успіху та зображення
        await status_msg.edit_text(
            f"✅ {html.bold('Зображення готове!')}\n\n"
            f"📝 Опис: {data['product_prompt'][:100]}{'...' if len(data['product_prompt']) > 100 else ''}"
        )
        
        # Відправляємо саме зображення
        await query.message.answer_photo(
            photo=image_url,
            caption="Генеровано через AI для товару"
        )
        
        logger.info(f"Image generated successfully for admin {query.from_user.id}: {image_url[:50]}...")
        
        # Повертаємося до основного FSM для підтвердження товару
        await state.set_state(AddProductStates.waiting_for_confirmation)
        
        # Показуємо підтвердження товару з зображенням
        data = await state.get_data()
        confirmation_text = (
            f"✅ {html.bold('Перевірте дані товару:')}\n\n"
            f"📝 Назва: {data['name']}\n"
            f"📄 Опис: {data['description']}\n"
            f"💰 Ціна: {data['price']:.2f} грн\n"
            f"📂 Категорія: {data['category']}\n"
            f"📦 Кількість: {data['stock']} шт\n"
            f"🖼️ Зображення: Генероване через AI ✅\n\n"
            f"{html.bold('Додати товар?')}"
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Так, додати", callback_data="confirm_add_product")
        builder.button(text="❌ Ні, скасувати", callback_data="cancel_add_product")
        builder.adjust(2)
        
        await query.message.answer(confirmation_text, reply_markup=builder.as_markup())
        
    except Exception as e:
        logger.exception(f"Error generating product image: {e}")
        await query.message.edit_text(f"❌ Помилка: {str(e)}")


@router.callback_query(AdminGenerateImageStates.waiting_for_confirmation, F.data == "admin_cancel_generate_image", IsAdminCallbackFilter())
async def admin_cancel_generate_image(query: CallbackQuery, state: FSMContext) -> None:
    """Скасування генерації і повернення до вибору розміру."""
    # Повертаємо стан до вибору способу отримання зображення
    await state.set_state(AddProductStates.waiting_for_image_source)
    
    from keyboards.admin import get_image_source_keyboard
    await query.message.edit_text(
        "🖼️ Як ви хочете отримати зображення товару?",
        reply_markup=get_image_source_keyboard()
    )
    await query.answer()
