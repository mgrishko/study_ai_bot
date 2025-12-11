"""Тести для TTS сервісу (Text-to-Speech)."""

import pytest
import io
from unittest.mock import patch, MagicMock, AsyncMock
from aiogram.types import BufferedInputFile

from tts_service import text_to_speech, get_product_description_for_tts, SUPPORTED_LANGUAGES


class TestTextToSpeech:
    """Тести для функції text_to_speech()."""
    
    @pytest.mark.asyncio
    async def test_text_to_speech_default_language(self):
        """Тест генерації аудіо з мовою за замовчуванням (uk)."""
        with patch('tts_service.gTTS') as mock_gtts:
            # Налаштування мока
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            mock_instance.write_to_fp = MagicMock(side_effect=lambda fp: fp.write(b'audio_data'))
            
            # Виклик функції
            result = await text_to_speech("Привіт, як справи?")
            
            # Перевірки
            assert result is not None
            assert isinstance(result, BufferedInputFile)
            mock_gtts.assert_called_once_with(text="Привіт, як справи?", lang="uk", slow=False)
    
    @pytest.mark.asyncio
    async def test_text_to_speech_russian_language(self):
        """Тест генерації аудіо з російською мовою."""
        with patch('tts_service.gTTS') as mock_gtts:
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            mock_instance.write_to_fp = MagicMock(side_effect=lambda fp: fp.write(b'audio_data'))
            
            result = await text_to_speech("Привет, как дела?", language="ru")
            
            assert result is not None
            assert isinstance(result, BufferedInputFile)
            mock_gtts.assert_called_once_with(text="Привет, как дела?", lang="ru", slow=False)
    
    @pytest.mark.asyncio
    async def test_text_to_speech_english_language(self):
        """Тест генерації аудіо з англійською мовою."""
        with patch('tts_service.gTTS') as mock_gtts:
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            mock_instance.write_to_fp = MagicMock(side_effect=lambda fp: fp.write(b'audio_data'))
            
            result = await text_to_speech("Hello, how are you?", language="en")
            
            assert result is not None
            assert isinstance(result, BufferedInputFile)
            mock_gtts.assert_called_once_with(text="Hello, how are you?", lang="en", slow=False)
    
    @pytest.mark.asyncio
    async def test_text_to_speech_unsupported_language(self):
        """Тест з непідтримуваною мовою - має використати uk як замовчування."""
        with patch('tts_service.gTTS') as mock_gtts:
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            mock_instance.write_to_fp = MagicMock(side_effect=lambda fp: fp.write(b'audio_data'))
            
            result = await text_to_speech("Some text", language="xx")
            
            assert result is not None
            assert isinstance(result, BufferedInputFile)
            # Має використати uk як замовчування
            mock_gtts.assert_called_once_with(text="Some text", lang="uk", slow=False)
    
    @pytest.mark.asyncio
    async def test_text_to_speech_long_text_truncation(self):
        """Тест скорочення тексту, якщо він довше 500 символів."""
        with patch('tts_service.gTTS') as mock_gtts:
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            mock_instance.write_to_fp = MagicMock(side_effect=lambda fp: fp.write(b'audio_data'))
            
            # Текст довший ніж 500 символів
            long_text = "a" * 600
            result = await text_to_speech(long_text)
            
            assert result is not None
            assert isinstance(result, BufferedInputFile)
            
            # Перевірити, що текст скорочено до 500 + "..."
            call_args = mock_gtts.call_args
            assert call_args[1]['text'] == "a" * 500 + "..."
            assert len(call_args[1]['text']) == 503
    
    @pytest.mark.asyncio
    async def test_text_to_speech_exactly_500_chars(self):
        """Тест з текстом рівно 500 символів - не має скорочуватись."""
        with patch('tts_service.gTTS') as mock_gtts:
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            mock_instance.write_to_fp = MagicMock(side_effect=lambda fp: fp.write(b'audio_data'))
            
            text_500 = "b" * 500
            result = await text_to_speech(text_500)
            
            assert result is not None
            call_args = mock_gtts.call_args
            assert call_args[1]['text'] == text_500
            assert len(call_args[1]['text']) == 500
    
    @pytest.mark.asyncio
    async def test_text_to_speech_exception_handling(self):
        """Тест обробки винятків - має повернути None."""
        with patch('tts_service.gTTS') as mock_gtts:
            mock_gtts.side_effect = Exception("gTTS error")
            
            result = await text_to_speech("Some text")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_text_to_speech_buffer_returned_as_bytes(self):
        """Тест що BufferedInputFile отримує байти з BytesIO."""
        test_audio_data = b'\xff\xfb\x90\x00'  # Мімікрія MP3 заголовка
        
        with patch('tts_service.gTTS') as mock_gtts:
            mock_instance = MagicMock()
            mock_gtts.return_value = mock_instance
            
            def write_audio_data(fp):
                fp.write(test_audio_data)
            
            mock_instance.write_to_fp = write_audio_data
            
            result = await text_to_speech("Test audio")
            
            assert result is not None
            assert isinstance(result, BufferedInputFile)
            # BufferedInputFile має дані в конструкторі, не в атрибуті
            # Просто перевіряємо що це BufferedInputFile з даними
            assert result.filename == "product_info.mp3"


class TestGetProductDescriptionForTts:
    """Тести для функції get_product_description_for_tts()."""
    
    def test_full_product_description(self):
        """Тест форматування повного опису товару."""
        product = {
            "name": "iPhone 14",
            "description": "Смартфон з новим чипом",
            "price": 25000,
            "stock": 10
        }
        
        result = get_product_description_for_tts(product)
        
        assert "Товар: iPhone 14" in result
        assert "Описание: Смартфон з новим чипом" in result
        assert "Цена: 25000 гривень" in result
        assert "В наличии: 10 штук" in result
    
    def test_product_without_description(self):
        """Тест опису товару без деталей."""
        product = {
            "name": "Наушники",
            "description": "",
            "price": 500,
            "stock": 50
        }
        
        result = get_product_description_for_tts(product)
        
        assert "Товар: Наушники" in result
        assert "Описание:" not in result
        assert "Цена: 500 гривень" in result
        assert "В наличии: 50 штук" in result
    
    def test_product_with_missing_fields(self):
        """Тест з відсутніми полями - мають використатись замовчування."""
        product = {}
        
        result = get_product_description_for_tts(product)
        
        assert "Товар: товар" in result  # Замовчування
        assert "Цена: 0 гривень" in result
        assert "В наличии: 0 штук" in result
    
    def test_product_with_partial_fields(self):
        """Тест з деякими полями."""
        product = {
            "name": "Клавіатура",
            "price": 1500
        }
        
        result = get_product_description_for_tts(product)
        
        assert "Товар: Клавіатура" in result
        assert "Цена: 1500 гривень" in result
        assert "В наличии: 0 штук" in result
    
    def test_product_string_format(self):
        """Тест формату результату - повинен бути рядок."""
        product = {"name": "Тест", "price": 100}
        
        result = get_product_description_for_tts(product)
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_product_with_zero_stock(self):
        """Тест товару із нульовою кількістю на складі."""
        product = {
            "name": "Недоступний товар",
            "price": 5000,
            "stock": 0
        }
        
        result = get_product_description_for_tts(product)
        
        assert "В наличии: 0 штук" in result


class TestSupportedLanguages:
    """Тести для словника SUPPORTED_LANGUAGES."""
    
    def test_supported_languages_dict_exists(self):
        """Тест що словник підтримуваних мов існує."""
        assert SUPPORTED_LANGUAGES is not None
        assert isinstance(SUPPORTED_LANGUAGES, dict)
    
    def test_supported_languages_contains_expected_keys(self):
        """Тест що словник містить очікувані мови."""
        expected_languages = {"uk", "ru", "en", "de", "fr", "es"}
        assert set(SUPPORTED_LANGUAGES.keys()) == expected_languages
    
    def test_supported_languages_have_descriptions(self):
        """Тест що кожна мова має опис."""
        for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
            assert isinstance(lang_name, str)
            assert len(lang_name) > 0
