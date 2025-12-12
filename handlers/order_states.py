"""FSM стани для обробки замовлень з контактною інформацією."""

from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """Стани для обробки замовлення з запитом контактної інформації."""
    
    waiting_for_quantity = State()      # Запит кількості товару
    waiting_for_phone = State()         # Запит телефонного номера
    waiting_for_email = State()         # Запит email
    waiting_for_confirmation = State()  # Підтвердження замовлення
