"""Обробники команд для роботи з AI (генерація зображень)."""

import logging
from typing import Optional

from aiogram import Router, F, html
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from openai_service import generate_image, get_available_sizes, get_available_styles

logger = logging.getLogger(__name__)

router = Router()


# FSM States для генерації зображення
class GenerateImageStates(StatesGroup):
    """Стани FSM для генерації зображення."""
    waiting_for_prompt = State()      # Крок 1: опис
    waiting_for_size = State()        # Крок 2: розмір
    waiting_for_style = State()       # Крок 3: стиль
    waiting_for_confirmation = State() # Крок 4: підтвердження


@router.message(Command("generate"))
async def command_generate_handler(message: Message, state: FSMContext) -> None:
    """Початок процесу генерації зображення."""
    logger.info(f"User {message.from_user.id} started image generation")
    
    help_text = (
        f"🎨 {html.bold('Генератор зображень через OpenAI')}\n\n"
        f"Опишіть зображення, яке ви хочете генерувати.\n\n"
        f"{html.italic('Приклади:')}\n"
        f"• A beautiful sunset over mountains\n"
        f"• A fluffy cat wearing a hat\n"
        f"• Modern skyscraper in cyberpunk style\n\n"
        f"Мінімум 10 символів, максимум 4000."
    )
    
    await state.set_state(GenerateImageStates.waiting_for_prompt)
    await message.answer(help_text)


@router.message(GenerateImageStates.waiting_for_prompt)
async def process_image_prompt(message: Message, state: FSMContext) -> None:
    """Обробка опису зображення."""
    prompt = message.text.strip()
    
    # Валідація
    if len(prompt) < 10:
        await message.answer("❌ Опис має бути не менше 10 символів")
        return
    
    if len(prompt) > 4000:
        await message.answer("❌ Опис не може бути більше 4000 символів")
        return
    
    await state.update_data(prompt=prompt)
    await state.set_state(GenerateImageStates.waiting_for_size)
    
    # Показуємо вибір розміру
    sizes = await get_available_sizes()
    builder = InlineKeyboardBuilder()
    
    for size in sizes:
        builder.button(
            text=f"📐 {size}",
            callback_data=f"select_size:{size}"
        )
    
    builder.adjust(1)
    
    await message.answer(
        "📐 Виберіть розмір зображення:",
        reply_markup=builder.as_markup()
    )


@router.callback_query(GenerateImageStates.waiting_for_size, F.data.startswith("select_size:"))
async def process_image_size(query: CallbackQuery, state: FSMContext) -> None:
    """Обробка вибору розміру."""
    size = query.data.split(":")[1]
    await state.update_data(size=size)
    await state.set_state(GenerateImageStates.waiting_for_style)
    
    # Показуємо вибір стилю
    styles = await get_available_styles()
    builder = InlineKeyboardBuilder()
    
    for style in styles:
        style_emoji = "✨" if style == "vivid" else "🎨"
        builder.button(
            text=f"{style_emoji} {style.capitalize()}",
            callback_data=f"select_style:{style}"
        )
    
    builder.adjust(2)
    
    await query.message.edit_text(
        "🎨 Виберіть стиль зображення:",
        reply_markup=builder.as_markup()
    )
    await query.answer()


@router.callback_query(GenerateImageStates.waiting_for_style, F.data.startswith("select_style:"))
async def process_image_style(query: CallbackQuery, state: FSMContext) -> None:
    """Обробка вибору стилю."""
    style = query.data.split(":")[1]
    await state.update_data(style=style)
    await state.set_state(GenerateImageStates.waiting_for_confirmation)
    
    # Показуємо підтвердження
    data = await state.get_data()
    confirmation_text = (
        f"✅ {html.bold('Перевірте параметри:')}\n\n"
        f"📝 Опис: {data['prompt'][:100]}{'...' if len(data['prompt']) > 100 else ''}\n"
        f"📐 Розмір: {data['size']}\n"
        f"🎨 Стиль: {data['style']}\n\n"
        f"{html.italic('Генерація займе 10-30 секунд...')}"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Генерувати", callback_data="confirm_generate")
    builder.button(text="❌ Скасувати", callback_data="cancel_generate")
    builder.adjust(2)
    
    await query.message.edit_text(confirmation_text, reply_markup=builder.as_markup())
    await query.answer()


@router.callback_query(GenerateImageStates.waiting_for_confirmation, F.data == "confirm_generate")
async def confirm_generate_image(query: CallbackQuery, state: FSMContext) -> None:
    """Генерує зображення."""
    try:
        data = await state.get_data()
        
        # Показуємо статус "обробка"
        status_msg = await query.message.edit_text("⏳ Генерую зображення...")
        await query.answer()
        
        logger.info(f"Generating image for user {query.from_user.id}")
        
        # Викликаємо OpenAI API
        image_url = await generate_image(
            prompt=data['prompt'],
            size=data['size'],
            style=data['style']
        )
        
        if not image_url:
            await status_msg.edit_text(
                "❌ Помилка при генерації зображення.\n"
                "Можливі причини:\n"
                "• Перевищено ліміт запитів (спробуйте пізніше)\n"
                "• Опис порушує політику OpenAI\n"
                "• Проблема з з'єднанням\n\n"
                "Спробуйте ще раз командою /generate"
            )
            logger.warning(f"Image generation failed for user {query.from_user.id}")
            await state.clear()
            return
        
        # Відправляємо статус успіху
        await status_msg.edit_text(
            f"✅ {html.bold('Зображення готове!')}\n\n"
            f"📝 Опис: {data['prompt'][:100]}{'...' if len(data['prompt']) > 100 else ''}\n"
            f"🔗 URL: {image_url[:50]}..."
        )
        
        # Відправляємо саме зображення
        await query.message.answer_photo(
            photo=image_url,
            caption=f"Генеровано за описом: {data['prompt'][:200]}"
        )
        
        logger.info(f"Image generated successfully for user {query.from_user.id}: {image_url[:50]}...")
        
        await state.clear()
        
    except Exception as e:
        logger.exception(f"Error generating image: {e}")
        await query.message.edit_text(f"❌ Помилка: {str(e)}")
        await state.clear()


@router.callback_query(GenerateImageStates.waiting_for_confirmation, F.data == "cancel_generate")
async def cancel_generate_image(query: CallbackQuery, state: FSMContext) -> None:
    """Скасування генерації."""
    await state.clear()
    await query.message.edit_text("❌ Генерація скасована.")
    await query.answer()
