from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone

from config.settings import logger, OWNER_ID, format_number
# Добавляем импорт базы данных
from utils.db import economy_db

class AdminCog(commands.Cog):
    """Административные команды"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ====================== КОМАНДЫ ======================

    @app_commands.command(name="addcoins", description="💸 Добавить монеты пользователю (Админ)")
    @app_commands.checks.has_permissions(administrator=True)
    async def addcoins(self, interaction: "discord.Interaction", member: "discord.Member", amount: int):
        # 1. Получаем данные пользователя из БД
        user = economy_db.get_user(member.id)
        
        # 2. Обновляем баланс
        old_balance = user.get("balance", 0)
        user["balance"] = old_balance + amount
        
        # 3. Сохраняем изменения в БД
        economy_db.update_user(member.id, user)
        
        await interaction.response.send_message(
            f"✅ Пользователю {member.mention} добавлено **{format_number(amount)}** монет.\n"
            f"💰 Новый баланс: **{format_number(user['balance'])}**",
            ephemeral=True
        )

    @app_commands.command(name="stats", description="� Статистика бота")
    async def statistics(self, interaction: "discord.Interaction"):
        if interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ Только владелец бота.", ephemeral=True)

        embed = discord.Embed(title="📊 Статистика MortisBot", color=0x9B59B6, timestamp=datetime.now(timezone.utc))

        embed.add_field(name="Серверов", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Пользователей", value=len(set(m for m in self.bot.get_all_members())), inline=True)
        embed.add_field(name="Пинг", value=f"{round(self.bot.latency * 1000)}ms", inline=True)

        # Подсчет общего количества монет в экономике
        total_balance = sum(
            u.get("balance", 0) 
            for uid, u in economy_db.data.items() 
            if isinstance(u, dict)
        )
        embed.add_field(name="Всего монет в обороте", value=format_number(total_balance), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ====================== SETUP ======================
async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
    logger.info("✅ AdminCog успешно загружен")