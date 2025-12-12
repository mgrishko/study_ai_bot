import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from database import Database


class TestDatabase:
    """Тести для класу Database."""
    
    @pytest.mark.asyncio
    async def test_get_all_products(self, db):
        """Тест отримання всіх товарів."""
        products = await db.get_all_products()
        assert isinstance(products, list)
        if products:
            assert 'id' in products[0]
            assert 'name' in products[0]
            assert 'price' in products[0]
    
    @pytest.mark.asyncio
    async def test_get_product_by_id(self, db):
        """Тест отримання товару за ID."""
        # Отримуємо всі товари
        products = await db.get_all_products()
        
        if products:
            product_id = products[0]['id']
            product = await db.get_product_by_id(product_id)
            
            assert product is not None
            assert product['id'] == product_id
            assert 'name' in product
            assert 'price' in product
    
    @pytest.mark.asyncio
    async def test_get_product_by_invalid_id(self, db):
        """Тест отримання товару з невірним ID."""
        product = await db.get_product_by_id(99999)
        assert product is None
    
    @pytest.mark.asyncio
    async def test_get_categories(self, db):
        """Тест отримання категорій."""
        categories = await db.get_categories()
        assert isinstance(categories, list)
        if categories:
            assert all(isinstance(cat, str) for cat in categories)
    
    @pytest.mark.asyncio
    async def test_get_products_by_category(self, db):
        """Тест отримання товарів за категорією."""
        categories = await db.get_categories()
        
        if categories:
            category = categories[0]
            products = await db.get_products_by_category(category)
            
            assert isinstance(products, list)
            if products:
                assert all(p['category'] == category for p in products)
    
    @pytest.mark.asyncio
    async def test_add_user(self, db_clean, user_factory):
        """Тест додавання користувача."""
        user = await user_factory.create(
            first_name="Тестовий",
            last_name="Користувач"
        )
        
        # Перевіряємо, що користувач доданий
        async with db_clean.pool.acquire() as conn:
            db_user = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1", user['id']
            )
            assert db_user is not None
            assert db_user['username'] == user['username']
            assert db_user['first_name'] == user['first_name']
            assert db_user['last_name'] == user['last_name']
    
    @pytest.mark.asyncio
    async def test_create_order(self, db_clean, user_factory, product_factory, order_factory):
        """Тест створення замовлення."""
        # Використовуємо factories для даних
        user = await user_factory.create()
        product = await product_factory.create()
        
        initial_stock = product['stock']
        
        # Створюємо замовлення через factory
        order = await order_factory.create(
            user_id=user['id'],
            product_id=product['id'],
            quantity=1
        )
        
        assert order is not None
        assert order['user_id'] == user['id']
        assert order['product_id'] == product['id']
        
        # Перевіряємо, що залишок зменшився
        updated_product = await db_clean.get_product_by_id(product['id'])
        assert updated_product['stock'] == initial_stock - 1
    
    @pytest.mark.asyncio
    async def test_get_user_orders(self, db_clean, user_factory, product_factory, order_factory):
        """Тест отримання замовлень користувача."""
        # Використовуємо factories
        user = await user_factory.create()
        product = await product_factory.create()
        
        # Створюємо замовлення через factory
        await order_factory.create(
            user_id=user['id'],
            product_id=product['id']
        )
        
        # Отримуємо замовлення користувача
        orders = await db_clean.get_user_orders(user['id'])
        
        assert isinstance(orders, list)
        assert len(orders) > 0
        assert orders[0]['user_id'] == user['id']
    
    @pytest.mark.asyncio
    async def test_update_order_status(self, db_clean, user_factory, product_factory, order_factory):
        """Тест оновлення статусу замовлення."""
        # Використовуємо factories
        user = await user_factory.create()
        product = await product_factory.create()
        
        # Створюємо замовлення через factory
        order = await order_factory.create(
            user_id=user['id'],
            product_id=product['id']
        )
        
        # Оновлюємо статус
        result = await db_clean.update_order_status(order['id'], "confirmed")
        assert result is True
        
        # Перевіряємо, що статус оновлено
        async with db_clean.pool.acquire() as conn:
            updated_order = await conn.fetchrow(
                "SELECT * FROM orders WHERE id = $1", order['id']
            )
            assert updated_order['status'] == "confirmed"
    
    @pytest.mark.asyncio
    async def test_add_product(self, db_clean, product_factory):
        """Тест додавання нового товару."""
        # Використовуємо factory для створення товару
        product = await product_factory.create(
            name="Custom Test Product",
            description="Test product description",
            price=999.99,
            category="Тестова категорія",
            stock=42
        )
        
        assert product is not None
        assert product['id'] is not None
        
        # Перевіряємо, що товар додано
        db_product = await db_clean.get_product_by_id(product['id'])
        assert db_product is not None
        assert db_product['name'] == "Custom Test Product"
        assert float(db_product['price']) == 999.99
        assert db_product['stock'] == 42
    
    @pytest.mark.asyncio
    async def test_add_product_without_image(self, db_clean, product_factory):
        """Тест додавання товару без зображення."""
        product = await product_factory.create(
            name="Product No Image",
            description="Product without image",
            price=500.00,
            category="Тестова категорія",
            stock=10
        )
        
        assert product is not None
        assert product['id'] is not None
        
        db_product = await db_clean.get_product_by_id(product['id'])
        assert db_product['image_url'] is None
    
    @pytest.mark.asyncio
    async def test_update_product(self, db_clean, product_factory):
        """Тест оновлення товару."""
        # Використовуємо factory для створення товару
        product = await product_factory.create(
            name="Original Product",
            description="Original description",
            price=100.00,
            stock=5
        )
        
        # Оновлюємо товар
        result = await db_clean.update_product(
            product_id=product['id'],
            name="Updated Name",
            price=200.00,
            stock=10
        )
        
        assert result is True
        
        # Перевіряємо оновлені дані
        updated_product = await db_clean.get_product_by_id(product['id'])
        assert updated_product['name'] == "Updated Name"
        assert float(updated_product['price']) == 200.00
        assert updated_product['stock'] == 10
        assert updated_product['description'] == "Original description"
    
    @pytest.mark.asyncio
    async def test_delete_product(self, db_clean, product_factory):
        """Тест видалення товару."""
        # Використовуємо factory для створення товару
        product = await product_factory.create(
            name="Product to Delete",
            description="Will be deleted",
            price=150.00,
            stock=3
        )
        
        assert product is not None
        
        # Видаляємо товар
        result = await db_clean.delete_product(product['id'])
        assert result is True
        
        # Перевіряємо, що товар видалено
        deleted_product = await db_clean.get_product_by_id(product['id'])
        assert deleted_product is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_product(self, db):
        """Тест видалення неіснуючого товару."""
        result = await db.delete_product(99999)
        assert result is False

