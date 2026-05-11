# economy_shop.py
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands


from config.settings import logger
from .economy_ui import ShopView, CurrencySwitchView


class EconomyShop(commands.Cog):
    """Магазин и банк"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="shop", description="🛒 Открыть магазин MortisPlay")
    async def shop(self, interaction: "discord.Interaction"):
        embed = discord.Embed(
            title="🛒 Магазин MortisPlay",
            description="Выберите категорию товаров ниже.\nЦены могут меняться во время событий!",
            color=0x9B59B6
        )
        view = ShopView(interaction.user.id, interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="vault", description="🏦 Центральный банк Mortis")
    async def vault(self, interaction: "discord.Interaction"):
        embed = discord.Embed(
            title="🏦 Центральное Хранилище Mortis",
            description=(
                "Выберите тип валюты ниже, чтобы узнать все внутренние и реальные курсы.\n"
                "Добавлены реальные валюты: рубли, доллары, евро."
            ),
            color=0xf1c40f
        )
        await interaction.response.send_message(embed=embed, view=CurrencySwitchView(), ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyShop(bot))
    logger.info("✅ EconomyShop успешно загружен")