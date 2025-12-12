"""FSM стани для обробки замовлень з контактною інформацією."""

from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """Стани для обробки замовлення з запитом контактної інформації."""
    
    waiting_for_quantity = State()      # Запит кількості товару
    waiting_for_phone = State()         # Запит телефонного номера
    waiting_for_email = State()         # Запит email
    waiting_for_confirmation = State()  # Підтвердження замовлення


class AdminOrderEditStates(StatesGroup):
    """Стани для редагування замовлення адміністратором."""
    
    choosing_edit_field = State()       # Вибір поля для редагування
    editing_phone = State()             # Редагування телефону
    editing_email = State()             # Редагування email
    editing_quantity = State()          # Редагування кількості
    editing_price = State()             # Редагування ціни
    editing_payment_status = State()    # Редагування статусу оплати
