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
    @app_commands.command(name="pay", description="💸 Передать валюту или предметы")
    @app_commands.autocomplete(item_id=item_autocomplete)
    @app_commands.describe(
        member="Кому передать?",
        amount="Количество монет",
        currency="Тип валюты",
        item_id="Предмет из инвентаря"
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
        currency: str = "balance",
        item_id: str = None
    ):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Нельзя отправлять себе.", ephemeral=True)
        if member.bot:
            return await interaction.response.send_message("❌ Ботам нельзя отправлять.", ephemeral=True)
        if amount <= 0 and item_id is None:
            return await interaction.response.send_message("❌ Укажите сумму или предмет.", ephemeral=True)

        sender = economy_db.get_user(interaction.user.id)
        receiver = economy_db.get_user(member.id)
        msg_parts = []

        if amount > 0:
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

        if item_id:
            inv = sender.get("inventory", {})
            if inv.get(item_id, 0) <= 0:
                return await interaction.response.send_message("❌ У вас нет этого предмета!", ephemeral=True)
            
            info = SHOP_ITEMS.get(item_id) or INVENTORY_ITEMS.get(item_id)
            inv[item_id] -= 1
            receiver.setdefault("inventory", {})[item_id] = receiver.get("inventory", {}).get(item_id, 0) + 1
            msg_parts.append(f"{info.get('emoji', '')} **{info['name']}**")

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
            if int(msg.content.strip()) != result:
                return await interaction.followup.send("❌ Неверный ответ!", ephemeral=True)

            captcha = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            await interaction.followup.send(f"✅ Верно!\n\nВведите капчу: **`{captcha}`**", ephemeral=True)
            
            msg2 = await self.bot.wait_for("message", check=check, timeout=20)
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

    @valute_group.command(name="exchange", description="💱 Обменять монеты на MortisCoin")
    async def valute_exchange(self, interaction: "discord.Interaction", amount_coins: int):
        if amount_coins < 500:
            return await interaction.response.send_message("❌ Минимум 500 монет.", ephemeral=True)

        user = economy_db.get_user(interaction.user.id)
        if not user.get("is_verified"):
            return await interaction.response.send_message("❌ Нужна верификация (/verify)", ephemeral=True)

        if user.get("balance", 0) < amount_coins:
            return await interaction.response.send_message("❌ Недостаточно монет!", ephemeral=True)

        rate = 500
        m_coins = amount_coins // rate
        spent = m_coins * rate

        user["balance"] -= spent
        user["mortis_coins"] = user.get("mortis_coins", 0) + m_coins
        economy_db.update_user(interaction.user.id, user)

        await interaction.response.send_message(
            f"✅ Обмен выполнен!\n"
            f"Отдано: **{format_number(spent)}** 🪙\n"
            f"Получено: **{m_coins}** 💎",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyTransactions(bot))
    logger.info("✅ EconomyTransactions успешно загружен")