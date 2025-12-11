import pytest
from config import ADMIN_IDS, BOT_TOKEN, IS_TESTING, get_db_config, TEST_DB_HOST, TEST_DB_PORT, TEST_DB_USER, TEST_DB_NAME
from filters import IsAdminFilter
from unittest.mock import MagicMock
from aiogram.types import User, Message


def test_config_loaded():
    """Тест завантаження конфігурації."""
    assert BOT_TOKEN is not None
    assert isinstance(ADMIN_IDS, list)


def test_admin_ids_parsing():
    """Тест парсингу ADMIN_IDS."""
    assert isinstance(ADMIN_IDS, list)
    if ADMIN_IDS:
        assert all(isinstance(id, int) for id in ADMIN_IDS)


def test_is_testing_flag():
    """Тест, що флаг IS_TESTING встановлено при тестуванні."""
    assert IS_TESTING is True, "IS_TESTING має бути True при запуску pytest"


def test_get_db_config_returns_test_database():
    """Тест, що get_db_config повертає конфіг тестової БД при тестуванні."""
    config = get_db_config()
    assert config["database"] == TEST_DB_NAME
    assert config["host"] == TEST_DB_HOST
    assert config["port"] == TEST_DB_PORT
    assert config["user"] == TEST_DB_USER


def test_db_config_has_all_keys():
    """Тест, що конфіг БД має всі необхідні ключі."""
    config = get_db_config()
    required_keys = {"host", "port", "user", "password", "database"}
    assert all(key in config for key in required_keys)


def test_db_config_types():
    """Тест типів параметрів конфігу БД."""
    config = get_db_config()
    assert isinstance(config["host"], str)
    assert isinstance(config["port"], int)
    assert isinstance(config["user"], str)
    assert isinstance(config["database"], str)


@pytest.mark.asyncio
async def test_is_admin_filter_true():
    """Тест IsAdminFilter - адмін."""
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
    filter_instance = IsAdminFilter()
    message = MagicMock(spec=Message)
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 999999999
    
    result = await filter_instance(message)
    assert result is False
    assert result is False
