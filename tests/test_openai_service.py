"""Тести для OpenAI сервісу (DALL-E)."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from openai import APIError, RateLimitError

from openai_service import init_openai, generate_image, get_available_sizes, get_available_styles


class TestInitOpenAI:
    """Тести для функції init_openai()."""
    
    def test_init_openai_with_valid_token(self):
        """Тест ініціалізації з валідним токеном."""
        with patch('openai_service.OPEN_AI_TOKEN', 'valid_token_123'):
            with patch('openai_service.AsyncOpenAI') as mock_client:
                result = init_openai()
                
                assert result is not None
                mock_client.assert_called_once_with(api_key='valid_token_123')
    
    def test_init_openai_without_token_raises_error(self):
        """Тест що помилка при відсутності токена."""
        with patch('openai_service.OPEN_AI_TOKEN', None):
            with pytest.raises(ValueError, match="OPEN_AI_TOKEN не встановлен"):
                init_openai()
    
    def test_init_openai_with_empty_token_raises_error(self):
        """Тест що помилка при пустому токені."""
        with patch('openai_service.OPEN_AI_TOKEN', ''):
            with pytest.raises(ValueError, match="OPEN_AI_TOKEN не встановлен"):
                init_openai()


class TestGenerateImage:
    """Тести для функції generate_image()."""
    
    @pytest.mark.asyncio
    async def test_generate_image_success(self):
        """Тест успішної генерації зображення."""
        with patch('openai_service.openai_client') as mock_client:
            # Налаштування мока
            mock_response = MagicMock()
            mock_response.data = [MagicMock(url="https://example.com/image.png")]
            
            mock_client.images.generate = AsyncMock(return_value=mock_response)
            
            with patch('openai_service.init_openai', return_value=mock_client):
                result = await generate_image("beautiful landscape")
                
                assert result == "https://example.com/image.png"
                mock_client.images.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_image_default_parameters(self):
        """Тест що використовуються правильні параметри за замовчуванням."""
        with patch('openai_service.openai_client') as mock_client:
            mock_response = MagicMock()
            mock_response.data = [MagicMock(url="https://example.com/image.png")]
            
            mock_client.images.generate = AsyncMock(return_value=mock_response)
            
            with patch('openai_service.init_openai', return_value=mock_client):
                await generate_image("test prompt")
                
                # Перевірити параметри виклику
                call_kwargs = mock_client.images.generate.call_args[1]
                assert call_kwargs['model'] == "dall-e-3"
                assert call_kwargs['prompt'] == "test prompt"
                assert call_kwargs['size'] == "1024x1024"
                assert call_kwargs['style'] == "vivid"
                assert call_kwargs['quality'] == "standard"
                assert call_kwargs['n'] == 1
    
    @pytest.mark.asyncio
    async def test_generate_image_custom_parameters(self):
        """Тест генерації з користувацькими параметрами."""
        with patch('openai_service.openai_client') as mock_client:
            mock_response = MagicMock()
            mock_response.data = [MagicMock(url="https://example.com/image.png")]
            
            mock_client.images.generate = AsyncMock(return_value=mock_response)
            
            with patch('openai_service.init_openai', return_value=mock_client):
                await generate_image(
                    "test prompt",
                    size="1792x1024",
                    style="natural"
                )
                
                call_kwargs = mock_client.images.generate.call_args[1]
                assert call_kwargs['size'] == "1792x1024"
                assert call_kwargs['style'] == "natural"
    
    @pytest.mark.asyncio
    async def test_generate_image_prompt_too_short(self):
        """Тест з промптом коротше 10 символів - має повернути None."""
        with patch('openai_service.openai_client', None):
            result = await generate_image("short")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_image_prompt_exactly_10_chars(self):
        """Тест з промптом рівно 10 символів."""
        with patch('openai_service.openai_client') as mock_client:
            mock_response = MagicMock()
            mock_response.data = [MagicMock(url="https://example.com/image.png")]
            
            mock_client.images.generate = AsyncMock(return_value=mock_response)
            
            with patch('openai_service.init_openai', return_value=mock_client):
                prompt_10_chars = "a" * 10
                result = await generate_image(prompt_10_chars)
                
                assert result is not None
                assert result == "https://example.com/image.png"
    
    @pytest.mark.asyncio
    async def test_generate_image_prompt_too_long(self):
        """Тест з промптом довше 4000 символів - має скоротити."""
        with patch('openai_service.openai_client') as mock_client:
            mock_response = MagicMock()
            mock_response.data = [MagicMock(url="https://example.com/image.png")]
            
            mock_client.images.generate = AsyncMock(return_value=mock_response)
            
            with patch('openai_service.init_openai', return_value=mock_client):
                long_prompt = "a" * 5000
                result = await generate_image(long_prompt)
                
                assert result is not None
                # Перевірити що промпт скорочено до 4000
                call_kwargs = mock_client.images.generate.call_args[1]
                assert len(call_kwargs['prompt']) == 4000
                assert call_kwargs['prompt'] == "a" * 4000
    
    @pytest.mark.asyncio
    async def test_generate_image_prompt_exactly_4000_chars(self):
        """Тест з промптом рівно 4000 символів - не має скорочуватись."""
        with patch('openai_service.openai_client') as mock_client:
            mock_response = MagicMock()
            mock_response.data = [MagicMock(url="https://example.com/image.png")]
            
            mock_client.images.generate = AsyncMock(return_value=mock_response)
            
            with patch('openai_service.init_openai', return_value=mock_client):
                prompt_4000 = "b" * 4000
                result = await generate_image(prompt_4000)
                
                assert result is not None
                call_kwargs = mock_client.images.generate.call_args[1]
                assert call_kwargs['prompt'] == prompt_4000
    
    @pytest.mark.asyncio
    async def test_generate_image_rate_limit_error(self):
        """Тест обробки RateLimitError."""
        with patch('openai_service.openai_client') as mock_client:
            # RateLimitError приймає message та response
            error = MagicMock(spec=RateLimitError)
            error.__class__ = RateLimitError
            mock_client.images.generate = AsyncMock(side_effect=error)
            
            with patch('openai_service.init_openai', return_value=mock_client):
                result = await generate_image("test prompt with good length")
                
                assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_image_api_error(self):
        """Тест обробки APIError."""
        with patch('openai_service.openai_client') as mock_client:
            # APIError - спеціалізований клас помилок OpenAI
            error = MagicMock(spec=APIError)
            error.__class__ = APIError
            mock_client.images.generate = AsyncMock(side_effect=error)
            
            with patch('openai_service.init_openai', return_value=mock_client):
                result = await generate_image("test prompt with good length")
                
                assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_image_generic_exception(self):
        """Тест обробки загального винятку."""
        with patch('openai_service.openai_client') as mock_client:
            mock_client.images.generate = AsyncMock(side_effect=Exception("Unknown error"))
            
            with patch('openai_service.init_openai', return_value=mock_client):
                result = await generate_image("test prompt with good length")
                
                assert result is None
    
    @pytest.mark.asyncio
    async def test_generate_image_client_initialization_failure(self):
        """Тест коли ініціалізація клієнта не вдається."""
        with patch('openai_service.openai_client', None):
            with patch('openai_service.init_openai', side_effect=ValueError("No token")):
                result = await generate_image("test prompt with good length")
                
                assert result is None


class TestGetAvailableSizes:
    """Тести для функції get_available_sizes()."""
    
    @pytest.mark.asyncio
    async def test_get_available_sizes_returns_list(self):
        """Тест що функція повертає список."""
        result = await get_available_sizes()
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_get_available_sizes_contains_expected_sizes(self):
        """Тест що список містить очікувані розміри."""
        result = await get_available_sizes()
        
        expected_sizes = ["1024x1024", "1792x1024", "1024x1792"]
        assert set(result) == set(expected_sizes)
    
    @pytest.mark.asyncio
    async def test_get_available_sizes_all_are_strings(self):
        """Тест що всі розміри - це рядки."""
        result = await get_available_sizes()
        
        for size in result:
            assert isinstance(size, str)


class TestGetAvailableStyles:
    """Тести для функції get_available_styles()."""
    
    @pytest.mark.asyncio
    async def test_get_available_styles_returns_list(self):
        """Тест що функція повертає список."""
        result = await get_available_styles()
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_get_available_styles_contains_expected_styles(self):
        """Тест що список містить очікувані стилі."""
        result = await get_available_styles()
        
        expected_styles = ["vivid", "natural"]
        assert set(result) == set(expected_styles)
    
    @pytest.mark.asyncio
    async def test_get_available_styles_all_are_strings(self):
        """Тест що всі стилі - це рядки."""
        result = await get_available_styles()
        
        for style in result:
            assert isinstance(style, str)
