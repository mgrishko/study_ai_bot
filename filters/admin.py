from aiogram.filters import Filter
from aiogram.types import Message
from config import ADMIN_IDS


class IsAdminFilter(Filter):
    """Фільтр для перевірки, чи є користувач адміністратором."""
    
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS
