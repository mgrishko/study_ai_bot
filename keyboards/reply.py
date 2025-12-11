"""Reply клавиатуры (кнопки внизу чата)."""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_menu() -> ReplyKeyboardMarkup:
    """Возвращает главное меню пользователя."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Каталог"), KeyboardButton(text="📦 Мои заказы")],
            [KeyboardButton(text="📚 Категории"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="ℹ️ О магазине"), KeyboardButton(text="🎨 AI")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите опцию из меню...",
    )
    return keyboard


def get_admin_menu() -> ReplyKeyboardMarkup:
    """Возвращает меню администратора."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍️ Каталог"), KeyboardButton(text="📦 Мои заказы")],
            [KeyboardButton(text="⚙️ Администратор"), KeyboardButton(text="❓ Помощь")],
            [KeyboardButton(text="🎨 AI")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите опцию из меню...",
    )
    return keyboard


def get_hidden_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает скрытую клавиатуру."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard
