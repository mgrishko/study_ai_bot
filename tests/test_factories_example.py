"""
Example tests demonstrating factory pattern usage.

These tests show how to use UserFactory, ProductFactory, and OrderFactory
to create test data flexibly without relying on mocks.
"""

import pytest


@pytest.mark.asyncio
async def test_user_factory_single_creation(user_factory):
    """Demonstrate creating a single user with factory."""
    user = await user_factory.create(first_name="John", last_name="Doe")
    
    assert user is not None
    assert user['first_name'] == "John"
    assert user['last_name'] == "Doe"
    assert 'id' in user
    assert 'username' in user


@pytest.mark.asyncio
async def test_user_factory_batch_creation(user_factory):
    """Demonstrate creating multiple users with factory."""
    users = await user_factory.create_batch(5)
    
    assert len(users) == 5
    for i, user in enumerate(users):
        assert 'id' in user
        assert 'username' in user
        assert user['first_name'] == f"Test{i+1}"
        assert user['last_name'] == f"User{i+1}"


@pytest.mark.asyncio
async def test_product_factory_single_creation(product_factory):
    """Demonstrate creating a single product with factory."""
    product = await product_factory.create(
        name="Premium Widget",
        price=250.00,
        stock=50
    )
    
    assert product is not None
    assert product['name'] == "Premium Widget"
    assert product['price'] == 250.00
    assert product['stock'] == 50


@pytest.mark.asyncio
async def test_product_factory_batch_creation(product_factory):
    """Demonstrate creating multiple products with factory."""
    products = await product_factory.create_batch(3)
    
    assert len(products) == 3
    for i, product in enumerate(products):
        assert 'id' in product
        assert 'name' in product
        # Auto-incrementing price: 100.00 + (i * 50)
        expected_price = 100.00 + (i * 50)
        assert product['price'] == expected_price


@pytest.mark.asyncio
async def test_order_factory_single_creation(user_factory, product_factory, order_factory):
    """Demonstrate creating a single order with factory."""
    user = await user_factory.create(first_name="Jane")
    product = await product_factory.create(name="Test Widget")
    
    order = await order_factory.create(
        user_id=user['id'],
        product_id=product['id'],
        quantity=2,
        phone="+380501111111"
    )
    
    assert order is not None
    assert order['user_id'] == user['id']
    assert order['product_id'] == product['id']
    assert order['quantity'] == 2
    assert order['phone'] == "+380501111111"


@pytest.mark.asyncio
async def test_order_factory_batch_creation(user_factory, product_factory, order_factory):
    """Demonstrate creating multiple orders with factory."""
    user = await user_factory.create()
    product = await product_factory.create()
    
    orders = await order_factory.create_batch(
        3,
        user_id=user['id'],
        product_id=product['id']
    )
    
    assert len(orders) == 3
    for i, order in enumerate(orders):
        assert order['user_id'] == user['id']
        assert order['product_id'] == product['id']
        # Auto-generated phone numbers
        assert order['phone'].startswith("+38050123456")


@pytest.mark.asyncio
async def test_combined_factory_workflow(user_factory, product_factory, order_factory):
    """Demonstrate a realistic workflow using all factories together."""
    # Create multiple users
    users = await user_factory.create_batch(2)
    
    # Create multiple products
    products = await product_factory.create_batch(3)
    
    # Create orders connecting them
    orders = []
    for user in users:
        for product in products[:2]:  # Each user orders first 2 products
            order = await order_factory.create(
                user_id=user['id'],
                product_id=product['id'],
                quantity=1
            )
            orders.append(order)
    
    assert len(orders) == 4  # 2 users * 2 products
    assert all(order['quantity'] == 1 for order in orders)


@pytest.mark.asyncio
async def test_factory_with_custom_values(user_factory, product_factory):
    """Demonstrate factory override capabilities."""
    from decimal import Decimal
    
    # Create user with custom username
    user = await user_factory.create(
        username="custom_user",
        first_name="Custom",
        last_name="Name"
    )
    
    assert user['username'] == "custom_user"
    assert user['first_name'] == "Custom"
    
    # Create product with custom values
    product = await product_factory.create(
        name="Exclusive Item",
        price=999.99,
        category="Premium",
        stock=1
    )
    
    assert product['name'] == "Exclusive Item"
    assert product['price'] == Decimal("999.99")
    assert product['category'] == "Premium"
    assert product['stock'] == 1
