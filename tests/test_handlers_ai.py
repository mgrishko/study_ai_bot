"""Тести для AI обробників (генерація зображень)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State

from handlers.ai import (
    command_generate_handler,
    process_image_prompt,
    process_image_size,
    process_image_style,
    confirm_generate_image,
    cancel_generate_image,
    GenerateImageStates,
)


class TestCommandGenerateHandler:
    """Тести для команди /generate."""
    
    @pytest.mark.asyncio
    async def test_command_generate_sets_state(self):
        """Тест що команда встановлює FSM стан."""
        # Налаштування моків
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(id=12345)
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.set_state = AsyncMock()
        
        # Виклик функції
        await command_generate_handler(message, state)
        
        # Перевірки
        state.set_state.assert_called_once_with(GenerateImageStates.waiting_for_prompt)
        message.answer.assert_called_once()
        
        # Перевірити що в відповіді упомінається генератор зображень
        call_args = message.answer.call_args[0][0]
        assert "Генератор" in call_args or "OpenAI" in call_args
    
    @pytest.mark.asyncio
    async def test_command_generate_message_content(self):
        """Тест що відповідь містить правильний контент."""
        message = MagicMock(spec=Message)
        message.from_user = MagicMock(id=12345)
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.set_state = AsyncMock()
        
        await command_generate_handler(message, state)
        
        # Перевірити що в тексті мінімум 10 символів
        call_args = message.answer.call_args[0][0]
        assert len(call_args) > 10
        # Мають бути приклади (перевіряємо как українські так і англійські варіанти)
        assert "приклад" in call_args.lower() or "example" in call_args.lower()


class TestProcessImagePrompt:
    """Тести для обробки опису зображення."""
    
    @pytest.mark.asyncio
    async def test_process_prompt_too_short(self):
        """Тест що промпт коротше 10 символів буде відхилено."""
        message = MagicMock(spec=Message)
        message.text = "short"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        
        await process_image_prompt(message, state)
        
        # Мають сказати що мало символів
        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "10" in call_args or "мало" in call_args.lower()
        # State не має оновлюватися
        state.update_data.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_prompt_exactly_10_chars(self):
        """Тест що промпт з 10 символів прийнято."""
        message = MagicMock(spec=Message)
        message.text = "a" * 10
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        
        with patch('handlers.ai.get_available_sizes', return_value=['1024x1024', '1792x1024']):
            await process_image_prompt(message, state)
        
        # State має оновитися
        state.update_data.assert_called_once()
        state.set_state.assert_called_once_with(GenerateImageStates.waiting_for_size)
    
    @pytest.mark.asyncio
    async def test_process_prompt_too_long(self):
        """Тест що промпт довше 4000 символів буде відхилено."""
        message = MagicMock(spec=Message)
        message.text = "a" * 4001
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        
        await process_image_prompt(message, state)
        
        # Мають сказати що забагато символів
        message.answer.assert_called_once()
        call_args = message.answer.call_args[0][0]
        assert "4000" in call_args or "много" in call_args.lower() or "забагато" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_process_prompt_valid(self):
        """Тест з валідним промптом."""
        message = MagicMock(spec=Message)
        message.text = "Beautiful landscape with mountains"
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        
        with patch('handlers.ai.get_available_sizes', return_value=['1024x1024']):
            await process_image_prompt(message, state)
        
        # Промпт має бути збережено без пробільних символів
        state.update_data.assert_called_with(prompt="Beautiful landscape with mountains")
    
    @pytest.mark.asyncio
    async def test_process_prompt_strips_whitespace(self):
        """Тест що пробільні символи на краях видаляються."""
        message = MagicMock(spec=Message)
        message.text = "  prompt with spaces  "
        message.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        
        with patch('handlers.ai.get_available_sizes', return_value=['1024x1024']):
            await process_image_prompt(message, state)
        
        # Промпт без крайних пробілів
        state.update_data.assert_called_with(prompt="prompt with spaces")


class TestProcessImageSize:
    """Тести для обробки вибору розміру."""
    
    @pytest.mark.asyncio
    async def test_process_size_updates_state(self):
        """Тест що розмір збережено в стан."""
        query = MagicMock(spec=CallbackQuery)
        query.data = "select_size:1024x1024"
        query.message = MagicMock()
        query.message.edit_text = AsyncMock()
        query.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        
        with patch('handlers.ai.get_available_styles', return_value=['vivid', 'natural']):
            await process_image_size(query, state)
        
        # Розмір має бути збережено
        state.update_data.assert_called_once_with(size="1024x1024")
        # State має перейти на вибір стилю
        state.set_state.assert_called_once_with(GenerateImageStates.waiting_for_style)
    
    @pytest.mark.asyncio
    async def test_process_size_shows_styles(self):
        """Тест що показує стилі для вибору."""
        query = MagicMock(spec=CallbackQuery)
        query.data = "select_size:1792x1024"
        query.message = MagicMock()
        query.message.edit_text = AsyncMock()
        query.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        
        with patch('handlers.ai.get_available_styles', return_value=['vivid', 'natural']):
            await process_image_size(query, state)
        
        # Має редагувати повідомлення з кнопками стилів
        query.message.edit_text.assert_called_once()


class TestProcessImageStyle:
    """Тести для обробки вибору стилю."""
    
    @pytest.mark.asyncio
    async def test_process_style_updates_state(self):
        """Тест що стиль збережено в стан."""
        query = MagicMock(spec=CallbackQuery)
        query.data = "select_style:vivid"
        query.message = MagicMock()
        query.message.edit_text = AsyncMock()
        query.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        state.get_data = AsyncMock(return_value={
            'prompt': 'test prompt here',
            'size': '1024x1024',
            'style': 'vivid'
        })
        
        await process_image_style(query, state)
        
        # Стиль має бути збережено
        state.update_data.assert_called_once_with(style="vivid")
        # State має перейти на підтвердження
        state.set_state.assert_called_once_with(GenerateImageStates.waiting_for_confirmation)
    
    @pytest.mark.asyncio
    async def test_process_style_shows_confirmation(self):
        """Тест що показує підтвердження."""
        query = MagicMock(spec=CallbackQuery)
        query.data = "select_style:natural"
        query.message = MagicMock()
        query.message.edit_text = AsyncMock()
        query.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()
        state.get_data = AsyncMock(return_value={
            'prompt': 'beautiful sunset',
            'size': '1792x1024',
            'style': 'natural'
        })
        
        await process_image_style(query, state)
        
        # Має редагувати повідомлення з параметрами
        query.message.edit_text.assert_called_once()
        call_args = query.message.edit_text.call_args[0][0]
        assert 'beautiful sunset' in call_args


class TestConfirmGenerateImage:
    """Тести для генерації зображення."""
    
    @pytest.mark.asyncio
    async def test_confirm_generate_success(self):
        """Тест успішної генерації."""
        # Мок message з методом edit_text
        mock_message = AsyncMock()
        mock_message.edit_text = AsyncMock(return_value=mock_message)
        mock_message.answer_photo = AsyncMock()
        
        query = MagicMock(spec=CallbackQuery)
        query.data = "confirm_generate"
        query.from_user = MagicMock(id=12345)
        query.message = mock_message
        query.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={
            'prompt': 'beautiful landscape',
            'size': '1024x1024',
            'style': 'vivid'
        })
        state.clear = AsyncMock()
        
        with patch('handlers.ai.generate_image', return_value='https://example.com/image.png'):
            await confirm_generate_image(query, state)
        
        # Має відправити фото
        query.message.answer_photo.assert_called_once()
        # State має очиститися
        state.clear.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_confirm_generate_api_failure(self):
        """Тест коли API повертає None."""
        query = MagicMock(spec=CallbackQuery)
        query.data = "confirm_generate"
        query.from_user = MagicMock(id=12345)
        query.message = MagicMock()
        query.message.edit_text = AsyncMock(return_value=MagicMock())
        query.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={
            'prompt': 'test prompt',
            'size': '1024x1024',
            'style': 'vivid'
        })
        state.clear = AsyncMock()
        
        with patch('handlers.ai.generate_image', return_value=None):
            await confirm_generate_image(query, state)
        
        # Має показати помилку
        assert query.message.edit_text.called
        # State має очиститися
        state.clear.assert_called_once()


class TestCancelGenerateImage:
    """Тести для скасування генерації."""
    
    @pytest.mark.asyncio
    async def test_cancel_clears_state(self):
        """Тест що скасування очищує стан."""
        query = MagicMock(spec=CallbackQuery)
        query.data = "cancel_generate"
        query.message = MagicMock()
        query.message.edit_text = AsyncMock()
        query.answer = AsyncMock()
        
        state = MagicMock(spec=FSMContext)
        state.clear = AsyncMock()
        
        await cancel_generate_image(query, state)
        
        # State має очиститися
        state.clear.assert_called_once()
        # Повідомлення має редагуватися
        query.message.edit_text.assert_called_once()
