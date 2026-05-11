"""
Импорт всех Cog'ов для удобного подключения в main.py
"""

from .fun import FunCog
from .economy import EconomyCog
from .moderation import ModerationCog
from .tickets import TicketsCog
from .admin import AdminCog

__all__ = [
    "FunCog",
    "EconomyCog", 
    "ModerationCog",
    "TicketsCog",
    "AdminCog"
]

# Удобная функция для загрузки всех cog'ов
async def setup_all_cogs(bot):
    """Загружает все cog'ы сразу"""
    cogs = [FunCog, EconomyCog, ModerationCog, TicketsCog, AdminCog]
    for cog_class in cogs:
        try:
            await bot.add_cog(cog_class(bot))
            print(f"✅ Cog {cog_class.__name__} успешно загружен")
        except Exception as e:
            print(f"❌ Ошибка загрузки {cog_class.__name__}: {e}")