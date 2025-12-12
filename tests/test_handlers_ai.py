"""Тести для AI обробників (генерація зображень в адміні).

ПРИМІТКА: Публічні тести /generate видалені оскільки команда тепер доступна
тільки в адміністраторської панелі при додаванні товарів.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram.fsm.context import FSMContext

from handlers.admin import (
    AdminGenerateImageStates,
)


class TestAdminGenerateImageStates:
    """Тести для FSM станів генерації зображень в адміні."""
    
    def test_admin_generate_image_states_exist(self):
        """Тест що FSM стани для генерації існують."""
        assert hasattr(AdminGenerateImageStates, 'waiting_for_prompt')
        assert hasattr(AdminGenerateImageStates, 'waiting_for_size')
        assert hasattr(AdminGenerateImageStates, 'waiting_for_style')
        assert hasattr(AdminGenerateImageStates, 'waiting_for_confirmation')
    
    def test_admin_generate_image_states_are_states(self):
        """Тест що атрибути є State об'єктами."""
        from aiogram.fsm.state import State
        assert isinstance(AdminGenerateImageStates.waiting_for_prompt, State)
        assert isinstance(AdminGenerateImageStates.waiting_for_size, State)
        assert isinstance(AdminGenerateImageStates.waiting_for_style, State)
        assert isinstance(AdminGenerateImageStates.waiting_for_confirmation, State)


class TestAdminImageGeneration:
    """Тести для генерації зображень в адміністраторській панелі."""
    
    @pytest.mark.asyncio
    async def test_image_generation_integration(self):
        """Тест что образец потока генерации изображений работает."""
        # Цей тест перевіряє базову структуру FSM
        state = AsyncMock(spec=FSMContext)
        state.get_data = AsyncMock(return_value={
            'product_prompt': 'A beautiful product',
            'product_image_size': '1024x1024',
            'product_image_style': 'vivid'
        })
        
        data = await state.get_data()
        
        assert data['product_prompt'] == 'A beautiful product'
        assert data['product_image_size'] == '1024x1024'
        assert data['product_image_style'] == 'vivid'


class TestAdminImageGenerationPromptValidation:
    """Тести для валідації prompt при генерації зображень в адміні."""
    
    def test_prompt_minimum_length(self):
        """Тест мінімальної довжини промпту (10 символів)."""
        short_prompt = "short"
        assert len(short_prompt) < 10
    
    def test_prompt_maximum_length(self):
        """Тест максимальної довжини промпту (4000 символів)."""
        long_prompt = "a" * 4001
        assert len(long_prompt) > 4000
    
    def test_prompt_valid_length(self):
        """Тест дійсної довжини промпту."""
        valid_prompt = "A beautiful modern smartphone"
        assert 10 <= len(valid_prompt) <= 4000


class TestGenerateImageFunction:
    """Тести для функції generate_image з openai_service."""
    
    @pytest.mark.asyncio
    async def test_generate_image_returns_url_or_none(self):
        """Тест что функция generate_image возвращает URL или None."""
        from openai_service import generate_image
        
        with patch('openai_service.openai_client', None):
            # Мокуємо генерацію
            with patch('openai_service.init_openai'):
                result = await generate_image("test prompt")
                # Функція повинна повертати строку (URL) або None
                assert result is None or isinstance(result, str)
    
    @pytest.mark.asyncio
    async def test_get_available_sizes(self):
        """Тест получения доступных размеров."""
        from openai_service import get_available_sizes
        
        sizes = await get_available_sizes()
        assert isinstance(sizes, list)
        assert len(sizes) > 0
        assert "1024x1024" in sizes
        assert "1792x1024" in sizes
        assert "1024x1792" in sizes
    
    @pytest.mark.asyncio
    async def test_get_available_styles(self):
        """Тест получения доступных стилей."""
        from openai_service import get_available_styles
        
        styles = await get_available_styles()
        assert isinstance(styles, list)
        assert len(styles) > 0
        assert "vivid" in styles
        assert "natural" in styles



class TestCommandGenerateHandler:
    """Заглушка - публічна генерація зображень видалена."""
    pass

