import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import User, Message, Chat
from handlers.common import command_start_handler, command_help_handler, command_info_handler


@pytest.fixture
def mock_message(test_user):
    """Фікстура для mock Message з тестовим користувачем."""
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = test_user['id']
    message.from_user.username = test_user['username']
    message.from_user.first_name = test_user['first_name']
    message.from_user.last_name = test_user['last_name']
    message.from_user.full_name = f"{test_user['first_name']} {test_user['last_name']}"
    message.answer = AsyncMock()
    return message


@pytest.mark.asyncio
async def test_command_start_handler(mock_message, db):
    """Тест команди /start з реальною БД та тестовим користувачем."""
    # Імпортуємо db та замінюємо в handlers.common
    import database
    original_db = database.db
    database.db = db
    
    # Також імпортуємо обробник модуль
    import handlers.common
    handlers.common.db = db
    
    try:
        await command_start_handler(mock_message)
        
        # Перевіряємо, що відповідь була надіслана
        mock_message.answer.assert_called_once()
        
        # Перевіряємо, що текст містить привітання
        call_args = mock_message.answer.call_args[0][0]
        assert "Вітаємо" in call_args
        assert "магазину верхнього одягу" in call_args
        
        # Перевіряємо, що користувач був доданий в БД
        user = await db.get_user(mock_message.from_user.id)
        assert user is not None
        assert user['username'] == mock_message.from_user.username
        assert user['first_name'] == mock_message.from_user.first_name
    finally:
        # Відновлюємо оригінальне db
        database.db = original_db
        handlers.common.db = original_db


@pytest.mark.asyncio
async def test_command_help_handler(mock_message):
    """Тест команди /help."""
    await command_help_handler(mock_message)
    
    mock_message.answer.assert_called_once()
    
    call_args = mock_message.answer.call_args[0][0]
    assert "Доступні команди" in call_args
    assert "/start" in call_args
    assert "/catalog" in call_args
    assert "/order" in call_args


@pytest.mark.asyncio
async def test_command_info_handler(mock_message):
    """Тест команди /info."""
    await command_info_handler(mock_message)
    
    mock_message.answer.assert_called_once()
    
    call_args = mock_message.answer.call_args[0][0]
    assert "Інформація про бота" in call_args
    assert "Python 3.13" in call_args
    assert "PostgreSQL" in call_args
