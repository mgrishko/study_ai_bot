"""Модуль для валідації контактної інформації."""

import re
from typing import Tuple


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Валідує телефонний номер в форматі +380XXXXXXXXX або 0XXXXXXXXX.
    
    Args:
        phone: Телефонний номер для перевірки
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
        
    Examples:
        >>> validate_phone("+380501234567")
        (True, "")
        >>> validate_phone("0501234567")
        (True, "")
        >>> validate_phone("123")
        (False, "Телефон повинен містити 10 цифр")
    """
    phone = phone.strip()
    
    # Видаляємо всі символи крім цифр та +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Перевіряємо формат +380XXXXXXXXX
    if cleaned.startswith('+380'):
        if len(cleaned) == 13 and cleaned[1:].isdigit():
            return True, ""
        return False, "Номер у форматі +380 повинен мати 10 цифр після коду країни"
    
    # Перевіряємо формат 0XXXXXXXXX
    if cleaned.startswith('0'):
        if len(cleaned) == 10 and cleaned.isdigit():
            return True, ""
        return False, "Номер у форматі 0 повинен мати 10 цифр"
    
    return False, "Телефон повинен починатися з +380 або 0"


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Валідує email адресу.
    
    Args:
        email: Email для перевірки
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
        
    Examples:
        >>> validate_email("user@example.com")
        (True, "")
        >>> validate_email("invalid.email")
        (False, "Невірний формат email")
    """
    email = email.strip().lower()
    
    # Базова regex для email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False, "Невірний формат email. Приклад: user@example.com"
    
    # Додаткові перевірки
    if len(email) > 254:
        return False, "Email занадто довгий (макс 254 символи)"
    
    local_part = email.split('@')[0]
    if len(local_part) > 64:
        return False, "Частина перед @ занадто довга (макс 64 символи)"
    
    if '..' in email:
        return False, "Email не може містити послідовні точки"
    
    return True, ""


def validate_name(name: str) -> Tuple[bool, str]:
    """
    Валідує ім'я користувача.
    
    Args:
        name: Ім'я для перевірки
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    name = name.strip()
    
    if not name:
        return False, "Ім'я не може бути порожнім"
    
    if len(name) < 2:
        return False, "Ім'я повинно містити хоча б 2 символи"
    
    if len(name) > 100:
        return False, "Ім'я занадто довге (макс 100 символів)"
    
    # Дозволяємо літери, цифри, дефіси, апострофи та пробіли
    if not re.match(r"^[a-яіїєґ'а-яіїєґ\s\-\d]+$", name, re.IGNORECASE | re.UNICODE):
        return False, "Ім'я містить недопустимі символи"
    
    return True, ""


def normalize_phone(phone: str) -> str:
    """
    Нормалізує телефонний номер до формату +380XXXXXXXXX.
    
    Args:
        phone: Телефонний номер
        
    Returns:
        Нормалізований номер або оригінальний, якщо неправильний формат
    """
    is_valid, _ = validate_phone(phone)
    if not is_valid:
        return phone
    
    phone = phone.strip()
    cleaned = re.sub(r'[^\d]', '', phone)
    
    if cleaned.startswith('0'):
        return f"+38{cleaned}"
    
    return f"+{cleaned}"
