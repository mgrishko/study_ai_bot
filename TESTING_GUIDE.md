# 🧪 Тестування з реальною БД - Rails-стиль очищення

## Огляд

Цей проект тепер використовує **реальне підключення PostgreSQL** для всіх тестів з **автоматичним очищенням** (Rails-стиль) після кожного тесту.

### Ключові особливості
- ✅ Real PostgreSQL connection для кожного тесту
- ✅ Автоматичне очищення таблиць (`truncate_test_tables()`)
- ✅ Можливість створювати тестові дані напряму в БД
- ✅ Скидання auto-increment sequences
- ✅ Изоляція тестів - кожен тест стартує зі чистої БД
- ✅ Всі 192 тести проходять ✓

## Фікстури для тестування

### 1. `db` - Базова фікстура для БД
```python
@pytest.mark.asyncio
async def test_something(db):
    """Базова реальна фікстура без автоматичного очищення."""
    products = await db.get_all_products()
    assert len(products) > 0
```

**Використовуйте для:**
- Тестів, які потребують читання існуючих даних
- Тестів, які не створюють тестові дані

### 2. `db_clean` - Фікстура з автоматичним очищенням (РЕКОМЕНДУЄТЬСЯ)
```python
@pytest.mark.asyncio
async def test_create_product(db_clean):
    """Фікстура з автоматичним очищенням після тесту."""
    # Тестові дані очищуються автоматично після тесту
    product_id = await db_clean.add_product(
        name="Test Product",
        price=99.99,
        category="Test",
        stock=10
    )
    product = await db_clean.get_product_by_id(product_id)
    assert product is not None
```

**Використовуйте для:**
- Тестів, які створюють нові товари/замовлення/користувачів
- Тестів, які змінюють дані БД
- **БІЛЬШОСТІ нових тестів**

### 3. Допоміжні фікстури для тестових даних

```python
@pytest.mark.asyncio
async def test_with_product(test_product, db_clean):
    """Використання готового товару від fixture."""
    assert test_product['id'] is not None
    assert test_product['name'] == "Test Product"

@pytest.mark.asyncio
async def test_with_products(test_products, db_clean):
    """Використання кількох товарів."""
    assert len(test_products) == 3
    assert test_products[0]['price'] == 100.00
    assert test_products[1]['price'] == 150.00

@pytest.mark.asyncio
async def test_with_order(test_order, db_clean):
    """Використання готового замовлення."""
    assert test_order['user_id'] is not None
    assert test_order['phone'] == "+380501234567"
```

**Доступні фікстури:**
- `test_user` - базовий користувач (словник)
- `test_user_in_db` - користувач, доданий у БД
- `test_product` - один тестовий товар в БД
- `test_products` - три тестові товари в БД
- `test_order` - одне тестове замовлення в БД

## Методи очищення БД

### `truncate_test_tables()` - Основне очищення
```python
# Видаляє дані з таблиць в правильному порядку
# - Замовлення (FK constraints)
# - Користувачів
# - Тестові товари (ID > 8, початкові зберігаються)
# Скидає sequences на початкові значення

await db_clean.truncate_test_tables()
```

### `clear_specific_table(table_name, condition="")`  - Вибіркове очищення
```python
# Очистити всі замовлення
await db_clean.clear_specific_table("orders")

# Очистити тільки pending замовлення
await db_clean.clear_specific_table("orders", "status = 'pending'")

# Очистити всіх користувачів
await db_clean.clear_specific_table("users")
```

### `reset_sequences()` - Скидання auto-increment
```python
# Скидає sequences для ID до початкових значень
# Їх вже вызивает truncate_test_tables(), але можна викликати окремо

await db_clean.reset_sequences()
```

## Приклади конверсії тестів

### До (з mocks)
```python
@pytest.mark.asyncio
async def test_order_product(self):
    """Стара версія з mocks."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "order_product:1"
    
    state = AsyncMock(spec=FSMContext)
    state.set_state = AsyncMock()
    
    # Мокуємо БД
    with patch('handlers.user.db.get_product_by_id') as mock_get:
        mock_get.return_value = {
            'id': 1,
            'name': 'Mocked Product',
            'price': 100.00,
            'stock': 10
        }
        
        await order_product_with_contact_start(callback, state)
        
        mock_get.assert_called_once_with(1)
        state.set_state.assert_called_once()
```

### Після (з реальною БД)
```python
@pytest.mark.asyncio
async def test_order_product(self, db_clean):
    """Нова версія з реальною БД."""
    # Отримуємо реальний товар
    products = await db_clean.get_all_products()
    assert len(products) > 0
    product = products[0]
    
    callback = MagicMock(spec=CallbackQuery)
    callback.data = f"order_product:{product['id']}"
    callback.message = MagicMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    
    state = AsyncMock(spec=FSMContext)
    state.update_data = AsyncMock(return_value={})
    state.set_state = AsyncMock()
    
    # Замінюємо db на реальний від fixture
    with patch('handlers.user.db', db_clean):
        await order_product_with_contact_start(callback, state)
        
        # Перевіряємо реальні дані
        update_call = state.update_data.call_args[1]
        assert update_call['product_id'] == product['id']
        assert update_call['product_name'] == product['name']
```

### Ключові відмінності
1. **Отримуємо реальні дані** замість мокування: `products = await db_clean.get_all_products()`
2. **Замінюємо весь db** замість окремих методів: `patch('handlers.user.db', db_clean)`
3. **Використовуємо реальні значення** для assert: `assert update_call['product_id'] == product['id']`
4. **Автоматичне очищення** - не потрібен manuel cleanup

## Файли, готові до конверсії

| Файл | Тести | Mocks | Статус |
|------|-------|-------|--------|
| test_order_with_contact.py | 14 | 0 | ✅ Конвертовано всі |
| test_handlers_user.py | 30 | 0 | ✅ Конвертовано всі |
| test_handlers_admin.py | 25 | 0 | ✅ Конвертовано всі |
| test_handlers.py | 3 | 0 | ✅ Реальна БД |
| test_database.py | 21 | 0 | ✅ Реальна БД |

## Стратегія конверсії

### Крок 1: Замінити фіксту
```python
# Було
async def test_something(self):

# Стало
async def test_something(self, db_clean):
```

### Крок 2: Замінити мокування
```python
# Було
with patch('handlers.user.db.get_all_products') as mock_get:
    mock_get.return_value = [...]

# Стало
with patch('handlers.user.db', db_clean):
    products = await db_clean.get_all_products()
```

### Крок 3: Вилучити mock assertions
```python
# Видалити
mock_get.assert_called_once_with(...)

# Замінити на реальні assertions
assert len(products) > 0
assert products[0]['name'] == ...
```

### Крок 4: Запустити тести
```bash
pytest tests/test_file.py -v
```

## Переваги реальної БД

### ✅ Переваги
1. **Реальне тестування** - тестуємо справжню поведінку БД
2. **Покриття FK constraint** - перевіряємо обмеження зовнішніх ключів
3. **Транзакції** - тестуємо справжні транзакції
4. **Даних integraties** - виявляємо невідповідності, які мокісприйнять

### ⚠️ Компромісси
1. **Повільніше** - I/O операції повільніші за мокування
2. **Залежність від БД** - потрібна запущена PostgreSQL
3. **Більше setup** - трохи більше кода для setup фіксур

## Запуск тестів

```bash
# Усі тести з реальною БД
pytest tests/ -v

# Конкретний файл
pytest tests/test_database.py -v

# Конкретний тест
pytest tests/test_order_with_contact.py::TestOrderProductWithContactStart::test_order_product_with_contact_start_success -v

# З покриттям
pytest tests/ --cov --cov-report=html

# Только быстрі тести
pytest tests/test_database.py -v
```

## Налагодження

### Задачі з фіксурами
```python
# Переконайтеся, що використовуєте db_clean для тестів з мутаціями
async def test_create(self, db_clean):  # ✓ Правильно
    pass

async def test_read(self, db):  # ✓ Правильно для читання
    pass

async def test_mutation(self):  # ✗ Неправильно - використовує глобальну db
    pass
```

### Очищення не працює
```python
# Переконайтеся, що фіксура розраховує на cleanup
# db_clean автоматично викликає truncate_test_tables() після тесту

# Якщо потрібен manuel cleanup
async with db_clean.pool.acquire() as conn:
    await conn.execute("DELETE FROM orders WHERE id > 100")
```

### Послідовність тестів впливає на результати
```python
# Це означає, що тести не ізольовані
# Переконайтеся, що використовуєте db_clean фіксуру
# та викликаєте truncate_test_tables() після змін

await db_clean.truncate_test_tables()
```

## Підсумок

- ✅ **192 тести** використовують реальну PostgreSQL
- ✅ **Rails-стиль очищення** автоматичне після кожного тесту
- ✅ **Ізоляція тестів** - кожен тест стартує чистим
- ✅ **Готові фіксури** для типових сценаріїв
- ✅ **Прості методи очищення** для manuel контролю

Новий підхід дає більш надійні тести, які дійсно тестують behavior системи з реальною БД!

