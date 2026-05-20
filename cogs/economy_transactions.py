# economy_transactions.py
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import string

from config.settings import logger, format_number
from config.economy import ECONOMY_EMOJIS
from config.shop import SHOP_ITEMS, INVENTORY_ITEMS
from utils.db import economy_db


class EconomyTransactions(commands.Cog):
    """Команды переводов, обмена и верификации"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ====================== АВТОДОПОЛНЕНИЕ ======================
    async def item_autocomplete(
        self, interaction: "discord.Interaction", current: str
    ) -> list[app_commands.Choice[str]]:
        user = economy_db.get_user(interaction.user.id)
        inventory = user.get("inventory", {})
        
        choices = []
        for iid, count in inventory.items():
            if count <= 0:
                continue
            info = SHOP_ITEMS.get(iid) or INVENTORY_ITEMS.get(iid)
            if not info:
                continue
            name = f"{info.get('emoji', '')} {info['name']} ({count} шт.)"
            if current.lower() in name.lower() or current.lower() in iid.lower():
                choices.append(app_commands.Choice(name=name[:100], value=iid))
        return choices[:25]

    # ====================== ПЕРЕВОД ======================
    @app_commands.command(name="pay", description="💸 Передать валюту")
    @app_commands.describe(
        member="Кому передать?",
        amount="Количество монет",
        currency="Тип валюты"
    )
    @app_commands.choices(currency=[
        app_commands.Choice(name="🪙 Монеты (5% комиссия)", value="balance"),
        app_commands.Choice(name="💎 MortisCoin (без комиссии)", value="mortis_coins")
    ])
    async def pay(
        self, 
        interaction: "discord.Interaction", 
        member: "discord.Member", 
        amount: int = 0, 
        currency: str = "balance"
    ):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Нельзя отправлять себе.", ephemeral=True)
        if member.bot:
            return await interaction.response.send_message("❌ Ботам нельзя отправлять.", ephemeral=True)
        if amount <= 0:
            return await interaction.response.send_message("❌ Укажите сумму.", ephemeral=True)

        sender = economy_db.get_user(interaction.user.id)
        receiver = economy_db.get_user(member.id)
        msg_parts = []

        if sender.get(currency, 0) < amount:
            return await interaction.response.send_message("❌ Недостаточно средств!", ephemeral=True)

        if currency == "balance":
            commission = int(amount * 0.05)
            receive = amount - commission
            sender["balance"] -= amount
            receiver["balance"] = receiver.get("balance", 0) + receive
            msg_parts.append(f"**{format_number(receive)}** {ECONOMY_EMOJIS['coin']} (комиссия {commission})")
        else:
            if not sender.get("is_verified", False):
                return await interaction.response.send_message("❌ Для MortisCoin нужна верификация (/verify)", ephemeral=True)
            sender["mortis_coins"] = sender.get("mortis_coins", 0) - amount
            receiver["mortis_coins"] = receiver.get("mortis_coins", 0) + amount
            msg_parts.append(f"**{amount}** 💎 MortisCoin")

        economy_db.update_user(interaction.user.id, sender)
        economy_db.update_user(member.id, receiver)

        await interaction.response.send_message(
            f"✅ {interaction.user.mention} → {member.mention}\n" + " и ".join(msg_parts)
        )

    # ====================== ВЕРИФИКАЦИЯ ======================
    @app_commands.command(name="verify", description="🔐 Пройти верификацию")
    async def verify(self, interaction: "discord.Interaction"):
        user = economy_db.get_user(interaction.user.id)
        
        if user.get("is_verified"):
            return await interaction.response.send_message("✅ Вы уже верифицированы!", ephemeral=True)

        a, b = random.randint(15, 60), random.randint(15, 60)
        result = a + b

        await interaction.response.send_message(
            f"🛡️ **Верификация**\n\nСколько будет **{a} + {b}**?", 
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await self.bot.wait_for("message", check=check, timeout=20)
            try:
                await msg.delete()
            except:
                pass
            
            if int(msg.content.strip()) != result:
                return await interaction.followup.send("❌ Неверный ответ!", ephemeral=True)

            captcha = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            await interaction.followup.send(f"✅ Верно!\n\nВведите капчу: **`{captcha}`**", ephemeral=True)
            
            msg2 = await self.bot.wait_for("message", check=check, timeout=20)
            try:
                await msg2.delete()
            except:
                pass
            
            if msg2.content.strip() != captcha:
                return await interaction.followup.send("❌ Неверная капча!", ephemeral=True)

            user["is_verified"] = True
            user["mortis_coins"] = user.get("mortis_coins", 0) + 1
            economy_db.update_user(interaction.user.id, user)

            await interaction.followup.send(
                "🎉 **Верификация пройдена!**\n"
                "• Доступен MortisCoin\n"
                "• +1 💎 в подарок", 
                ephemeral=True
            )
        except asyncio.TimeoutError:
            await interaction.followup.send("⏱️ Время вышло.", ephemeral=True)

    # ====================== ВАЛЮТА ======================
    valute_group = app_commands.Group(name="valute", description="💱 Управление валютами")

    @valute_group.command(name="exchange", description="💱 Двусторонний обмен валют")
    async def valute_exchange(self, interaction: "discord.Interaction"):
        user = economy_db.get_user(interaction.user.id)
        if not user.get("is_verified"):
            return await interaction.response.send_message("❌ Нужна верификация (/verify)", ephemeral=True)

        balance = user.get("balance", 0)
        mcoins = user.get("mortis_coins", 0)

        embed = discord.Embed(
            title="💱 Обмен валют",
            description="Выберите направление обмена",
            color=0x9b59b6
        )
        embed.add_field(
            name="🪙 Ваш баланс монет",
            value=f"`{format_number(balance)}` 🪙",
            inline=True
        )
        embed.add_field(
            name="💎 Ваш баланс MortisCoin",
            value=f"`{mcoins}` 💎",
            inline=True
        )
        embed.add_field(
            name="📊 Курс обмена",
            value="500 🪙 = 1 💎\n1 💎 = 500 🪙",
            inline=False
        )

        view = ExchangeDirectionView(interaction.user.id, user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ====================== ВЫБОР НАПРАВЛЕНИЯ ОБМЕНА ======================
class ExchangeDirectionView(discord.ui.View):
    def __init__(self, user_id: int, user_data: dict):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.user_data = user_data

    @discord.ui.button(label="🪙 → 💎 (Монеты → MortisCoin)", style=discord.ButtonStyle.green, emoji="🪙")
    async def coins_to_mcoins(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)

        # Создаём модальное окно для ввода количества
        modal = ExchangeModal(
            title="🪙 → 💎 Монеты → MortisCoin",
            exchange_type="coins_to_mcoins",
            user_data=self.user_data
        )
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="💎 → 🪙 (MortisCoin → Монеты)", style=discord.ButtonStyle.blurple, emoji="💎")
    async def mcoins_to_coins(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)

        # Создаём модальное окно для ввода количества
        modal = ExchangeModal(
            title="💎 → 🪙 MortisCoin → Монеты",
            exchange_type="mcoins_to_coins",
            user_data=self.user_data
        )
        await interaction.response.send_modal(modal)


# ====================== МОДАЛЬНОЕ ОКНО ОБМЕНА ======================
class ExchangeModal(discord.ui.Modal):
    amount = discord.ui.TextInput(label="Количество", placeholder="Минимум: 1", required=True, min_length=1, max_length=10)

    def __init__(self, title: str, exchange_type: str, user_data: dict):
        super().__init__(title=title)
        self.exchange_type = exchange_type
        self.user_data = user_data

    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount.value)
        except ValueError:
            return await interaction.response.send_message("❌ Введите число!", ephemeral=True)

        user = economy_db.get_user(interaction.user.id)
        rate = 500

        if self.exchange_type == "coins_to_mcoins":
            if amount < 500:
                return await interaction.response.send_message("❌ Минимум 500 🪙!", ephemeral=True)
            
            if user.get("balance", 0) < amount:
                return await interaction.response.send_message("❌ Недостаточно монет!", ephemeral=True)

            mcoins_to_get = amount // rate
            spent = mcoins_to_get * rate
            remainder = amount % rate

            user["balance"] -= spent
            user["mortis_coins"] = user.get("mortis_coins", 0) + mcoins_to_get
            economy_db.update_user(interaction.user.id, user)

            embed = discord.Embed(
                title="✅ Обмен завершён!",
                description="🪙 → 💎",
                color=0x2ecc71
            )
            embed.add_field(name="Отдано", value=f"`{format_number(spent)}` 🪙", inline=True)
            embed.add_field(name="Получено", value=f"`{mcoins_to_get}` 💎", inline=True)
            if remainder > 0:
                embed.add_field(name="💡 Остаток", value=f"`{format_number(remainder)}` 🪙 (менее 500)", inline=False)
            embed.set_footer(text="Спасибо за использование сервиса!")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        elif self.exchange_type == "mcoins_to_coins":
            if amount < 1:
                return await interaction.response.send_message("❌ Минимум 1 💎!", ephemeral=True)
            
            if user.get("mortis_coins", 0) < amount:
                return await interaction.response.send_message("❌ Недостаточно MortisCoin!", ephemeral=True)

            coins_to_get = amount * rate
            
            user["mortis_coins"] -= amount
            user["balance"] = user.get("balance", 0) + coins_to_get
            economy_db.update_user(interaction.user.id, user)

            embed = discord.Embed(
                title="✅ Обмен завершён!",
                description="💎 → 🪙",
                color=0x2ecc71
            )
            embed.add_field(name="Отдано", value=f"`{amount}` 💎", inline=True)
            embed.add_field(name="Получено", value=f"`{format_number(coins_to_get)}` 🪙", inline=True)
            embed.set_footer(text="Спасибо за использование сервиса!")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyTransactions(bot))
    logger.info("✅ EconomyTransactions успешно загружен")