# cogs/casino.py
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import random
from config.economy import ECONOMY_EMOJIS
from utils.db import economy_db

class CasinoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="slots", description="🎰 Испытать удачу в слотах")
    async def slots(self, interaction: "discord.Interaction", bet: int):
        if bet < 10: return await interaction.response.send_message("❌ Мин. ставка: 10", ephemeral=True)
        
        user_data = economy_db.get_user(interaction.user.id)
        if user_data["balance"] < bet: return await interaction.response.send_message("❌ Недостаточно средств", ephemeral=True)
        
        emojis = ["🍎", "🍊", "🍇", "🍒", "💎", "7️⃣"]
        slots = [random.choice(emojis) for _ in range(3)]
        
        user_data["balance"] -= bet
        result_text = "Вы проиграли 😢"
        color = 0xE74C3C
        
        if slots[0] == slots[1] == slots[2]:
            win = bet * 10 if slots[0] == "7️⃣" else bet * 5
            user_data["balance"] += win
            result_text = f"К-К-КОМБО! Вы выиграли **{win}**!"
            color = 0x2ECC71
        elif slots[0] == slots[1] or slots[1] == slots[2] or slots[0] == slots[2]:
            win = int(bet * 1.5)
            user_data["balance"] += win
            result_text = f"Неплохо! Вы выиграли **{win}**!"
            color = 0xF1C40F
            
        await economy_db.save()
        
        embed = discord.Embed(title="🎰 Игровой автомат", description=f"**[ {slots[0]} | {slots[1]} | {slots[2]} ]**\n\n{result_text}", color=color)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(CasinoCog(bot))