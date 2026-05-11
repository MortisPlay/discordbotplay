from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timezone

from config.settings import logger


class FunCog(commands.Cog):
    """Развлекательные команды"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ====================== КОМАНДЫ ======================

    @app_commands.command(name="iq", description="🧠 Узнать свой IQ")
    async def iq(self, interaction: "discord.Interaction"):
        """Ежедневный IQ с редкими высокими значениями"""
        seed = interaction.user.id + int(datetime.now(timezone.utc).timestamp() // 86400)
        random.seed(seed)

        iq_value = random.randint(70, 130)

        if random.random() < 0.03:
            iq_value = random.randint(145, 165)
            title = "🧠 ЛЕГЕНДАРНЫЙ ГЕНИЙ!"
            color = 0xFFD700
        elif random.random() < 0.12:
            iq_value = random.randint(115, 144)
            title = "🌟 Выдающийся ум"
            color = 0x3498DB
        else:
            title = "🧠 Твой IQ"
            color = 0x2ECC71

        embed = discord.Embed(
            title=title,
            description=f"{interaction.user.mention}, твой IQ сегодня: **{iq_value}**",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Обновляется раз в сутки • Результаты случайны")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="coinflip", description="🪙 Подбросить монетку")
    async def coinflip(self, interaction: "discord.Interaction"):
        result = random.choice(["Орёл", "Решка"])
        embed = discord.Embed(
            title="🪙 Монетка подброшена",
            description=f"**Выпало: {result}**",
            color=0xF1C40F
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="dice", description="🎲 Бросить кубик")
    @app_commands.describe(sides="Количество граней (от 2 до 100)")
    async def dice(self, interaction: "discord.Interaction", sides: int = 6):
        if sides < 2 or sides > 100:
            return await interaction.response.send_message(
                "❌ Количество граней должно быть от 2 до 100.",
                ephemeral=True
            )

        result = random.randint(1, sides)
        embed = discord.Embed(
            title="🎲 Бросок кубика",
            description=f"Выпало: **{result}** (d{sides})",
            color=0xE74C3C
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="rps", description="✂️ Камень-ножницы-бумага")
    @app_commands.describe(choice="Ваш выбор")
    async def rps(self, interaction: "discord.Interaction", choice: str):
        choices = ["камень", "ножницы", "бумага"]
        choice = choice.lower()

        if choice not in choices:
            return await interaction.response.send_message(
                f"❌ Выберите: `{', '.join(choices)}`",
                ephemeral=True
            )

        bot_choice = random.choice(choices)

        if choice == bot_choice:
            result = "Ничья! 🤝"
            color = 0x3498DB
        elif (choice == "камень" and bot_choice == "ножницы") or \
             (choice == "ножницы" and bot_choice == "бумага") or \
             (choice == "бумага" and bot_choice == "камень"):
            result = "Ты выиграл! 🎉"
            color = 0x2ECC71
        else:
            result = "Я выиграл! 🤖"
            color = 0xE74C3C

        embed = discord.Embed(
            title="✂️ Камень-ножницы-бумага",
            description=f"**Ты:** {choice.capitalize()}\n**Я:** {bot_choice.capitalize()}\n\n**{result}**",
            color=color
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(FunCog(bot))
    logger.info("✅ FunCog успешно загружен")