# Конфігурація для тестування
import os
import sys
from dotenv import load_dotenv

# Завантажуємо .env файл
load_dotenv()

# ВАЖЛИВО: Встановити змінні окружено ДО імпорту будь-яких модулів
os.environ['TEST_DB_HOST'] = os.getenv('TEST_DB_HOST', 'localhost')
os.environ['TEST_DB_PORT'] = os.getenv('TEST_DB_PORT', '5432')
os.environ['TEST_DB_USER'] = os.getenv('TEST_DB_USER', 'test_shop_bot_user')
os.environ['TEST_DB_PASSWORD'] = os.getenv('TEST_DB_PASSWORD', '')
os.environ['TEST_DB_NAME'] = os.getenv('TEST_DB_NAME', 'test_shop_bot')
os.environ['BOT_TOKEN'] = os.getenv('BOT_TOKEN', 'test_token')
os.environ['ADMIN_IDS'] = os.getenv('ADMIN_IDS', '')

# Видалити модулі config та database з sys.modules для переімпорту
for module in list(sys.modules.keys()):
    if module.startswith('config') or module.startswith('database'):
        del sys.modules[module]

import pytest
import asyncio
import pytest_asyncio
from config import get_db_config, IS_TESTING
from database import Database


def pytest_configure(config):
    """Налаштування pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


@pytest.fixture
def event_loop():
    """Фікстура для event loop."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db():
    """Фікстура для бази даних."""
    db_instance = Database()
    
    # Перевірка, що використовується тестова БД
    assert db_instance.config["database"] == "test_shop_bot", \
        f"❌ Неправильна БД: {db_instance.config['database']}"
    
    await db_instance.connect()
    await db_instance.init_db()
    yield db_instance
    await db_instance.close()


@pytest.fixture
def test_user():
    """Фікстура для тестового користувача."""
    import time
    user_id = int(time.time() * 1000000) % 1000000000
    return {
        'id': user_id,
        'username': f'testuser_{user_id}',
        'first_name': 'Test',
        'last_name': 'User'
    }


@pytest_asyncio.fixture
async def test_user_in_db(db, test_user):
    """Фікстура для тестового користувача, доданого в БД."""
    await db.add_user(
        test_user['id'],
        test_user['username'],
        test_user['first_name'],
        test_user['last_name']
    )
    yield test_user
    # Видалення користувача після тесту
    async with db.pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id = $1", test_user['id'])
