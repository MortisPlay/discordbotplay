# economy.py
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands

from config.settings import logger


class EconomyCog(commands.Cog):
    """Главный модуль экономики — точка входа"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot: commands.Bot):
    """Загружаем все части экономики"""
    
    from .economy_core import EconomyCore
    from .economy_shop import EconomyShop
    from .economy_transactions import EconomyTransactions
    # Импортируем наш новый класс из папки economy_bp
    from .economy_bp.bp_main import BattlePassCog 

    await bot.add_cog(BattlePassCog(bot)) 
    await bot.add_cog(EconomyCore(bot))
    await bot.add_cog(EconomyShop(bot))
    await bot.add_cog(EconomyTransactions(bot))

    logger.info("✅ Полный Economy модуль успешно загружен (Core + Shop + Transactions + BattlePass)")