# cogs/casino.py
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import random
from config.economy import ECONOMY_EMOJIS
from config.settings import format_number
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

    @app_commands.command(name="chips", description="🎲 Игра с фишками")
    @app_commands.describe(bet="Размер ставки в монетах", choice="Выберите сторону: чёт или нечёт")
    @app_commands.choices(choice=[
        app_commands.Choice(name="🟢 Чётное число", value="even"),
        app_commands.Choice(name="🔴 Нечётное число", value="odd")
    ])
    async def chips(self, interaction: "discord.Interaction", bet: int, choice: str):
        if bet < 25:
            return await interaction.response.send_message("❌ Минимальная ставка: 25 монет", ephemeral=True)
        
        user_data = economy_db.get_user(interaction.user.id)
        if user_data.get("balance", 0) < bet:
            return await interaction.response.send_message("❌ Недостаточно монет!", ephemeral=True)
        
        # Генерируем случайное число от 1 до 10
        dice_roll = random.randint(1, 10)
        is_even = dice_roll % 2 == 0
        actual_choice = "even" if is_even else "odd"
        
        user_data["balance"] -= bet
        
        if actual_choice == choice:
            # Вероятность выигрыша 50%, выигрыш x1.95 (чистый доход = bet * 0.95)
            win = int(bet * 1.95)
            user_data["balance"] += win
            
            embed = discord.Embed(
                title="🎲 Игра с фишками",
                description=f"Выпало число: **{dice_roll}** ({'чётное' if is_even else 'нечётное'})\n\n🎉 **ВЫ ВЫИГРАЛИ!**",
                color=0x2ECC71
            )
            embed.add_field(name="Ставка", value=f"{bet} 🪙", inline=True)
            embed.add_field(name="Выигрыш", value=f"{win} 🪙", inline=True)
            embed.add_field(name="Чистая прибыль", value=f"+{win - bet} 🪙", inline=True)
        else:
            embed = discord.Embed(
                title="🎲 Игра с фишками",
                description=f"Выпало число: **{dice_roll}** ({'чётное' if is_even else 'нечётное'})\n\n😢 **ВЫ ПРОИГРАЛИ**",
                color=0xE74C3C
            )
            embed.add_field(name="Ставка", value=f"{bet} 🪙", inline=True)
            embed.add_field(name="Остаток", value=f"{user_data['balance']} 🪙", inline=True)
        
        embed.set_footer(text="Вероятность выигрыша: 50%")
        
        await economy_db.save()
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(CasinoCog(bot))