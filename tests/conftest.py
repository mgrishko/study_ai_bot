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
import sys
import os

# Add tests directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import get_db_config, IS_TESTING
from database import Database
from factories import UserFactory, ProductFactory, OrderFactory


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


@pytest_asyncio.fixture
async def db_clean(db):
    """Фікстура для бази даних з автоматичним очищенням після кожного тесту (Rails-style).
    
    Використовуйте цю фікстуру замість `db` для тестів, які потребують чистого стану БД.
    Таблиці будуть автоматично очищені після кожного тесту.
    """
    yield db
    # Очищуємо тестові дані після тесту (Rails-style cleanup)
    await db.truncate_test_tables()


# ═══════════════════════════════════════════════════════════════════════════════
# FACTORY FIXTURES FOR FLEXIBLE TEST DATA CREATION
# ═══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def user_factory(db_clean):
    """Factory for creating test users with auto-incrementing IDs.
    
    Usage:
        async def test_something(user_factory):
            user = await user_factory.create(first_name="John")
            users = await user_factory.create_batch(5)
    """
    return UserFactory(db_clean)


@pytest_asyncio.fixture
async def product_factory(db_clean):
    """Factory for creating test products with auto-incrementing features.
    
    Usage:
        async def test_something(product_factory):
            product = await product_factory.create(name="Widget", price=50.00)
            products = await product_factory.create_batch(5)
    """
    return ProductFactory(db_clean)


@pytest_asyncio.fixture
async def order_factory(db_clean):
    """Factory for creating test orders.
    
    Usage:
        async def test_something(user_factory, product_factory, order_factory):
            user = await user_factory.create()
            product = await product_factory.create()
            order = await order_factory.create(
                user_id=user['id'],
                product_id=product['id']
            )
    """
    return OrderFactory(db_clean)


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


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FIXTURES FOR TEST DATA CREATION (для заміни mocks)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest_asyncio.fixture
async def test_product(db_clean):
    """Фікстура для створення тестового товару в БД."""
    product_id = await db_clean.add_product(
        name="Test Product",
        description="Test Description",
        price=100.00,
        category="Test Category",
        stock=10
    )
    
    product = await db_clean.get_product_by_id(product_id)
    yield product
    # Cleanup не потрібен - db_clean автоматично очистить


@pytest_asyncio.fixture
async def test_products(db_clean):
    """Фікстура для створення кількох тестових товарів в БД."""
    product_ids = []
    products = []
    
    for i in range(3):
        product_id = await db_clean.add_product(
            name=f"Test Product {i+1}",
            description=f"Test Description {i+1}",
            price=100.00 + (i * 50),
            category="Test Category",
            stock=10 + i
        )
        product_ids.append(product_id)
        product = await db_clean.get_product_by_id(product_id)
        products.append(product)
    
    yield products


@pytest_asyncio.fixture
async def test_order(db_clean, test_user):
    """Фікстура для створення тестового замовлення в БД."""
    # Додаємо користувача
    await db_clean.add_user(
        test_user['id'],
        test_user['username'],
        test_user['first_name'],
        test_user['last_name']
    )
    
    # Отримуємо перший продукт (закачні товари)
    products = await db_clean.get_all_products()
    if not products:
        raise RuntimeError("No products available for test")
    
    product = products[0]
    
    # Створюємо замовлення
    order_id = await db_clean.create_order(
        user_id=test_user['id'],
        user_name=test_user['first_name'],
        product_id=product['id'],
        quantity=2,
        phone="+380501234567",
        email="test@example.com"
    )
    
    async with db_clean.pool.acquire() as conn:
        order = await conn.fetchrow(
            "SELECT * FROM orders WHERE id = $1",
            order_id
        )
    
    yield order

