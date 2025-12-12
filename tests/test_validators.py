"""Тести для валідації контактної інформації та FSM замовлень."""

import pytest
from validators import validate_phone, validate_email, validate_name, normalize_phone


class TestPhoneValidation:
    """Тести для валідації телефонних номерів."""
    
    def test_valid_phone_with_plus_380(self):
        """Тест валідного номера у форматі +380XXXXXXXXX."""
        is_valid, error = validate_phone("+380501234567")
        assert is_valid is True
        assert error == ""
    
    def test_valid_phone_with_zero(self):
        """Тест валідного номера у форматі 0XXXXXXXXX."""
        is_valid, error = validate_phone("0501234567")
        assert is_valid is True
        assert error == ""
    
    def test_valid_phone_with_spaces(self):
        """Тест валідного номера з пробілами."""
        is_valid, error = validate_phone("+380 50 123 45 67")
        assert is_valid is True
        assert error == ""
    
    def test_valid_phone_with_dashes(self):
        """Тест валідного номера з дефісами."""
        is_valid, error = validate_phone("050-123-45-67")
        assert is_valid is True
        assert error == ""
    
    def test_invalid_phone_too_short(self):
        """Тест занадто короткого номера."""
        is_valid, error = validate_phone("123")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_phone_wrong_country_code(self):
        """Тест номера з неправильним кодом країни."""
        is_valid, error = validate_phone("+381501234567")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_phone_empty_string(self):
        """Тест порожного рядка."""
        is_valid, error = validate_phone("")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_phone_only_letters(self):
        """Тест номера тільки з букв."""
        is_valid, error = validate_phone("abcdefghij")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_phone_starts_with_1(self):
        """Тест номера що починається з 1."""
        is_valid, error = validate_phone("1501234567")
        assert is_valid is False
        assert error != ""
    
    def test_normalize_phone_zero_format(self):
        """Тест нормалізації номера з формату 0."""
        normalized = normalize_phone("0501234567")
        assert normalized == "+380501234567"
    
    def test_normalize_phone_with_spaces(self):
        """Тест нормалізації номера з пробілами."""
        normalized = normalize_phone("050 123 45 67")
        assert normalized == "+380501234567"
    
    def test_normalize_invalid_phone_unchanged(self):
        """Тест що невалідний номер повертається як є."""
        phone = "invalid"
        normalized = normalize_phone(phone)
        assert normalized == phone


class TestEmailValidation:
    """Тести для валідації email адрес."""
    
    def test_valid_email_simple(self):
        """Тест простої валідної email адреси."""
        is_valid, error = validate_email("user@example.com")
        assert is_valid is True
        assert error == ""
    
    def test_valid_email_with_numbers(self):
        """Тест email з цифрами."""
        is_valid, error = validate_email("user123@example.com")
        assert is_valid is True
        assert error == ""
    
    def test_valid_email_with_dots_in_name(self):
        """Тест email з точками в імені."""
        is_valid, error = validate_email("user.name@example.com")
        assert is_valid is True
        assert error == ""
    
    def test_valid_email_with_plus(self):
        """Тест email з плюсом."""
        is_valid, error = validate_email("user+tag@example.com")
        assert is_valid is True
        assert error == ""
    
    def test_valid_email_with_subdomain(self):
        """Тест email з піддоменом."""
        is_valid, error = validate_email("user@mail.example.co.uk")
        assert is_valid is True
        assert error == ""
    
    def test_invalid_email_no_at_symbol(self):
        """Тест email без @."""
        is_valid, error = validate_email("userexample.com")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_email_no_domain(self):
        """Тест email без домену."""
        is_valid, error = validate_email("user@")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_email_no_local_part(self):
        """Тест email без локальної частини."""
        is_valid, error = validate_email("@example.com")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_email_no_extension(self):
        """Тест email без розширення."""
        is_valid, error = validate_email("user@example")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_email_double_dot(self):
        """Тест email з подвійною точкою."""
        is_valid, error = validate_email("user@example..com")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_email_empty_string(self):
        """Тест порожного email."""
        is_valid, error = validate_email("")
        assert is_valid is False
        assert error != ""
    
    def test_valid_email_uppercase_converted(self):
        """Тест що uppercase конвертується до lowercase."""
        is_valid, error = validate_email("USER@EXAMPLE.COM")
        assert is_valid is True
        assert error == ""


class TestNameValidation:
    """Тести для валідації імен користувачів."""
    
    def test_valid_name_simple(self):
        """Тест простого імена."""
        is_valid, error = validate_name("John")
        assert is_valid is True
        assert error == ""
    
    def test_valid_name_with_space(self):
        """Тест імена з пробілом."""
        is_valid, error = validate_name("John Doe")
        assert is_valid is True
        assert error == ""
    
    def test_valid_name_with_apostrophe(self):
        """Тест імена з апострофом."""
        is_valid, error = validate_name("O'Brien")
        assert is_valid is True
        assert error == ""
    
    def test_valid_name_with_hyphen(self):
        """Тест імена з дефісом."""
        is_valid, error = validate_name("Mary-Jane")
        assert is_valid is True
        assert error == ""
    
    def test_valid_name_cyrillic(self):
        """Тест імена кирилицею."""
        is_valid, error = validate_name("Іван Петренко")
        assert is_valid is True
        assert error == ""
    
    def test_invalid_name_too_short(self):
        """Тест занадто короткого імена."""
        is_valid, error = validate_name("A")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_name_empty(self):
        """Тест порожного імена."""
        is_valid, error = validate_name("")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_name_only_spaces(self):
        """Тест імена тільки з пробілів."""
        is_valid, error = validate_name("   ")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_name_with_special_characters(self):
        """Тест імена зі спеціальними символами."""
        is_valid, error = validate_name("John@Doe")
        assert is_valid is False
        assert error != ""
    
    def test_invalid_name_too_long(self):
        """Тест занадто довгого імена."""
        long_name = "A" * 101
        is_valid, error = validate_name(long_name)
        assert is_valid is False
        assert error != ""
    
    def test_valid_name_with_numbers(self):
        """Тест імена з цифрами."""
        is_valid, error = validate_name("Agent 007")
        assert is_valid is True
        assert error == ""


class TestOrderValidation:
    """Інтеграційні тести для валідації замовлень."""
    
    def test_order_contact_info_all_valid(self):
        """Тест замовлення з усією коректною контактною інформацією."""
        phone_valid, _ = validate_phone("+380501234567")
        email_valid, _ = validate_email("user@example.com")
        name_valid, _ = validate_name("John Doe")
        
        assert phone_valid is True
        assert email_valid is True
        assert name_valid is True
    
    def test_order_contact_info_invalid_phone(self):
        """Тест замовлення з невалідним телефоном."""
        phone_valid, error = validate_phone("123")
        
        assert phone_valid is False
        assert error != ""
    
    def test_order_contact_info_invalid_email(self):
        """Тест замовлення з невалідним email."""
        email_valid, error = validate_email("notanemail")
        
        assert email_valid is False
        assert error != ""
