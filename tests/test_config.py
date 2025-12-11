import pytest
from config import ADMIN_IDS, BOT_TOKEN, DB_HOST, DB_PORT, DB_USER, DB_NAME
from filters import IsAdminFilter


def test_config_loaded():
    """Тест завантаження конфігурації."""
    assert BOT_TOKEN is not None
    assert DB_HOST is not None
    assert DB_PORT > 0
    assert isinstance(DB_PORT, int)
    assert DB_USER is not None
    assert DB_NAME is not None


def test_admin_ids_parsing():
    """Тест парсингу ADMIN_IDS."""
    assert isinstance(ADMIN_IDS, list)
    if ADMIN_IDS:
        assert all(isinstance(id, int) for id in ADMIN_IDS)


@pytest.mark.asyncio
async def test_is_admin_filter_true():
    """Тест IsAdminFilter - адмін."""
    from unittest.mock import MagicMock
    from aiogram.types import User, Message
    
    filter_instance = IsAdminFilter()
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    
    if ADMIN_IDS:
        message.from_user.id = ADMIN_IDS[0]
        result = await filter_instance(message)
        assert result is True


@pytest.mark.asyncio
async def test_is_admin_filter_false():
    """Тест IsAdminFilter - не адмін."""
    from unittest.mock import MagicMock
    from aiogram.types import User, Message
    
    filter_instance = IsAdminFilter()
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 999999999
    
    result = await filter_instance(message)
    assert result is False
