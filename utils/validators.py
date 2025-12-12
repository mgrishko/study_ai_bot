"""Валідатори для адміністративної зони."""

import re
from typing import Tuple


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Валідує формат телефону.
    
    Args:
        phone: Телефонний номер
        
    Returns:
        Tuple[bool, str]: (Is valid, Error message)
    """
    # Приймаємо формати: +380XXXXXXXXX або 0XXXXXXXXX
    phone = phone.strip()
    
    pattern = r'^(\+380|0)\d{9}$'
    if not re.match(pattern, phone):
        return False, "❌ Неправильний формат телефону. Використовуйте +380XXXXXXXXX або 0XXXXXXXXX"
    
    return True, ""


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Валідує формат email.
    
    Args:
        email: Email адреса
        
    Returns:
        Tuple[bool, str]: (Is valid, Error message)
    """
    email = email.strip()
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "❌ Неправильний формат email."
    
    return True, ""


def validate_quantity(quantity: str, max_available: int) -> Tuple[bool, str]:
    """
    Валідує кількість товару.
    
    Args:
        quantity: Нова кількість
        max_available: Максимально доступна кількість (stock + current_quantity)
        
    Returns:
        Tuple[bool, str]: (Is valid, Error message)
    """
    try:
        qty = int(quantity.strip())
        
        if qty < 1:
            return False, "❌ Кількість має бути не менше 1."
        
        if qty > max_available:
            return False, f"❌ Максимально можна замовити {max_available} шт."
        
        return True, ""
    except ValueError:
        return False, "❌ Кількість повинна бути числом."


def validate_price(price: str) -> Tuple[bool, str]:
    """
    Валідує ціну замовлення.
    
    Args:
        price: Нова ціна
        
    Returns:
        Tuple[bool, str]: (Is valid, Error message)
    """
    try:
        amount = float(price.strip())
        
        if amount < 0:
            return False, "❌ Ціна не може бути від'ємною."
        
        if amount > 999999.99:
            return False, "❌ Ціна занадто велика."
        
        return True, ""
    except ValueError:
        return False, "❌ Ціна повинна бути числом."


def validate_payment_status(status: str) -> Tuple[bool, str]:
    """
    Валідує статус оплати.
    
    Args:
        status: Статус оплати
        
    Returns:
        Tuple[bool, str]: (Is valid, Error message)
    """
    valid_statuses = {'paid', 'unpaid', 'failed'}
    status = status.lower().strip()
    
    if status not in valid_statuses:
        return False, f"❌ Неправильний статус оплати. Дозволені: {', '.join(valid_statuses)}"
    
    return True, ""


def validate_order_status_transition(current_status: str, new_status: str) -> Tuple[bool, str]:
    """
    Валідує переход між статусами замовлення (стан-машина).
    
    Args:
        current_status: Поточний статус
        new_status: Новий статус
        
    Returns:
        Tuple[bool, str]: (Is valid, Error message)
    """
    # Дозволені переходи: pending -> confirmed/cancelled
    # confirmed -> shipped/cancelled
    # shipped -> delivered
    # delivered -> (no transitions)
    # cancelled -> (no transitions)
    
    valid_transitions = {
        'pending': {'confirmed', 'cancelled'},
        'confirmed': {'shipped', 'cancelled'},
        'shipped': {'delivered'},
        'delivered': set(),
        'cancelled': set()
    }
    
    current_status = current_status.lower().strip()
    new_status = new_status.lower().strip()
    
    if current_status not in valid_transitions:
        return False, f"❌ Невідомий поточний статус: {current_status}"
    
    if new_status not in valid_transitions.get(current_status, set()):
        allowed = valid_transitions.get(current_status, set())
        return False, f"❌ З статусу '{current_status}' можна перейти до: {', '.join(allowed) if allowed else 'немає переходів'}"
    
    return True, ""
