from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from config import ADMIN_IDS


class IsAdminFilter(Filter):
    """Фільтр для перевірки, чи є користувач адміністратором."""
    
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS


class IsUserFilter(Filter):
    """Фільтр для перевірки, чи є користувач звичайним користувачем (не адміністратором)."""
    
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id not in ADMIN_IDS


class IsAdminCallbackFilter(Filter):
    """Фільтр для перевірки, чи є користувач адміністратором в callback queries."""
    
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.from_user.id in ADMIN_IDS


class IsUserCallbackFilter(Filter):
    """Фільтр для перевірки звичайного користувача в callback queries."""
    
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.from_user.id not in ADMIN_IDS
