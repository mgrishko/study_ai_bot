"""Reply клавіатури (кнопки внизу чату)."""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """Повертає головне меню користувача."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Каталог"), KeyboardButton(text="📦 Мої замовлення")],
            [KeyboardButton(text="📚 Категорії"), KeyboardButton(text="❓ Допомога")],
            [KeyboardButton(text="ℹ️ Про магазин")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Виберіть опцію з меню...",
    )
    return keyboard


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Повертає меню адміністратора."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Каталог"), KeyboardButton(text="📦 Мої замовлення")],
            [KeyboardButton(text="⚙️ Адміністратор"), KeyboardButton(text="❓ Допомога")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Виберіть опцію з меню...",
    )
    return keyboard


def get_hidden_keyboard() -> ReplyKeyboardMarkup:
    """Повертає приховану клавіатуру."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard
