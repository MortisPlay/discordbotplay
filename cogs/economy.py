# economy.py
import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta, timezone
import asyncio
import string

from config.settings import logger, format_number
from config.economy import ECONOMY_EMOJIS, JOBS, DAILY_COOLDOWN
from config.shop import SHOP_ITEMS, SHOP_CATEGORIES, CURRENT_EVENT, INVENTORY_ITEMS
from utils.db import economy_db

# Импорт UI компонентов
from .economy_ui import (
    ShopView, 
    InventoryView,
    INVENTORY_ITEMS, 
    CurrencySwitchView, 
    get_item_price
)


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ====================== МАГАЗИН ======================
    @app_commands.command(name="shop", description="🛒 Открыть магазин MortisPlay")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 Магазин MortisPlay",
            description="Выберите категорию товаров ниже.\nЦены могут меняться во время событий!",
            color=0x9B59B6
        )
        view = ShopView(interaction.user.id, interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ====================== БАНК ======================
    @app_commands.command(name="vault", description="🏦 Центральный банк Mortis")
    async def vault(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🏦 Центральное Хранилище Mortis",
            description="Выберите тип валюты для подробной информации.",
            color=0xf1c40f
        )
        await interaction.response.send_message(embed=embed, view=CurrencySwitchView(), ephemeral=True)

    # ====================== ИНВЕНТАРЬ ======================
    @app_commands.command(name="inventory", description="🎒 Просмотр инвентаря")
    async def inventory(self, interaction: discord.Interaction):
        user = economy_db.get_user(interaction.user.id)
        # Фикс если инвентарь вдруг список
        if isinstance(user.get("inventory"), list):
            user["inventory"] = {}
            economy_db.update_user(interaction.user.id, user)
        
        view = InventoryView(interaction.user.id)
        embed = view.create_embed(user, interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ====================== DAILY ======================
    @app_commands.command(name="daily", description="🎁 Ежедневная награда")
    async def daily(self, interaction: discord.Interaction):
        user = economy_db.get_user(interaction.user.id)
        now = datetime.now()

        last_daily = user.get("last_daily")
        if isinstance(last_daily, str):
            try:
                last_dt = datetime.fromisoformat(last_daily)
                if now < last_dt + timedelta(seconds=DAILY_COOLDOWN):
                    delta = (last_dt + timedelta(seconds=DAILY_COOLDOWN)) - now
                    hours, remainder = divmod(int(delta.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)
                    return await interaction.response.send_message(
                        f"⏳ Вы уже получали награду.\nСледующая через **{hours}ч {minutes}м.**",
                        ephemeral=True
                    )
            except ValueError:
                pass

        reward = random.randint(30, 80)
        user["balance"] = user.get("balance", 0) + reward
        user["last_daily"] = now.isoformat()
        economy_db.update_user(interaction.user.id, user)

        embed = discord.Embed(
            title="🎁 Ежедневная награда",
            description=f"**+{reward}** {ECONOMY_EMOJIS['coin']}",
            color=0xffd700
        )
        embed.set_footer(text="Приходите завтра снова! • Семья Бензопил")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ====================== БАЛАНС ======================
    @app_commands.command(name="balance", description="💰 Баланс пользователя")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user_data = economy_db.get_user(target.id)
        balance = user_data.get("balance", 0)

        embed = discord.Embed(
            title=f"💰 Баланс — {target.display_name}",
            color=0x2ecc71 if balance > 0 else 0xe74c3c,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(
            name="Текущий счёт",
            value=f"```fix\n{format_number(balance)} {ECONOMY_EMOJIS['coin']}```",
            inline=False
        )
        embed.add_field(name="Статус", value=user_data.get("status", "Новичок 🍼"), inline=True)
        embed.set_footer(text="Семья Бензопил")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ====================== ПРОФИЛЬ ======================
    @app_commands.command(name="profile", description="👤 Профиль игрока")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        u = economy_db.get_user(target.id)
        
        is_verified = u.get("is_verified", False)
        color = 0xf1c40f if is_verified else 0x2ecc71
        badge = " ✅" if is_verified else ""

        emb = discord.Embed(title=f"Профиль {target.display_name}{badge}", color=color)
        emb.set_thumbnail(url=target.display_avatar.url)

        emb.add_field(name="🏷️ Статус", value=f"**{u.get('status', 'Новичок 🍼')}**", inline=False)
        emb.add_field(name="🪙 Монеты", value=f"`{format_number(u.get('balance', 0))}`", inline=True)
        emb.add_field(name="💎 MortisCoin", value=f"`{format_number(u.get('mortis_coins', 0))}`", inline=True)

        # Инвентарь
        inv = u.get("inventory", {})
        inv_lines = []
        if isinstance(inv, dict):
            for iid, amt in list(inv.items())[:10]:
                if amt > 0:
                    info = SHOP_ITEMS.get(iid) or INVENTORY_ITEMS.get(iid)
                    name = info['name'] if info else iid
                    inv_lines.append(f"{info.get('emoji', '📦')} **{name}** ×{amt}")

        emb.add_field(name="🎒 Инвентарь", value="\n".join(inv_lines) or "Пусто", inline=False)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    # ====================== РАБОТА ======================
    @app_commands.command(name="work", description="⚒️ Отправиться на работу")
    async def work(self, interaction: discord.Interaction):
        user = economy_db.get_user(interaction.user.id)
        now = datetime.now(timezone.utc)

        # Античит: возраст аккаунта
        if (now - interaction.user.created_at).days < 3:
            return await interaction.response.send_message(
                "❌ Ваш аккаунт слишком новый. Для работы нужно минимум 3 дня.", ephemeral=True)

        # Кулдаун 30 минут
        WORK_COOLDOWN = 1800
        last_work = user.get("last_work")
        if last_work:
            last_time = datetime.fromisoformat(last_work)
            if now < last_time + timedelta(seconds=WORK_COOLDOWN):
                remaining = (last_time + timedelta(seconds=WORK_COOLDOWN)) - now
                m, s = divmod(int(remaining.total_seconds()), 60)
                return await interaction.response.send_message(
                    f"⏳ Отдохните ещё **{m}м {s}с**", ephemeral=True)

        job_id = user.get("job", "unemployed")
        if job_id == "unemployed":
            return await interaction.response.send_message("❌ Сначала устройтесь на работу командой `/job`", ephemeral=True)

        job_info = JOBS.get(job_id)
        if not job_info:
            return await interaction.response.send_message("❌ Ошибка работы. Обратитесь к администрации.", ephemeral=True)

        reward = random.randint(job_info["min_salary"], job_info["max_salary"])

        # Бонусы
        bonus = 1.0
        bonus_text = ""
        if user.get("work_boost"):
            bonus += 0.5
            user["work_boost"] = False
            bonus_text += " +50% 🥤"

        final_reward = int(reward * bonus)

        user["balance"] = user.get("balance", 0) + final_reward
        user["last_work"] = now.isoformat()
        economy_db.update_user(interaction.user.id, user)

        await interaction.response.send_message(
            f"⚒️ Вы поработали на **{job_info['name']}** и получили **{format_number(final_reward)}** {ECONOMY_EMOJIS['coin']}{bonus_text}",
            ephemeral=True
        )

    # ====================== УСТРОЙСТВО НА РАБОТУ ======================
    @app_commands.command(name="job", description="💼 Устроиться на работу")
    @app_commands.describe(job_name="Выберите работу")
    @app_commands.choices(job_name=[
        app_commands.Choice(name=job["name"], value=job_id) 
        for job_id, job in JOBS.items()
    ])
    async def job(self, interaction: discord.Interaction, job_name: str):
        user = economy_db.get_user(interaction.user.id)
        
        if user.get("job") == job_name:
            return await interaction.response.send_message("✅ Вы уже работаете на этой должности!", ephemeral=True)

        job_info = JOBS.get(job_name)
        if not job_info:
            return await interaction.response.send_message("❌ Такой работы не существует.", ephemeral=True)

        user["job"] = job_name
        economy_db.update_user(interaction.user.id, user)

        await interaction.response.send_message(
            f"✅ Вы успешно устроились на работу **{job_info['name']}**!\n"
            f"Зарплата: `{job_info['min_salary']}-{job_info['max_salary']}` {ECONOMY_EMOJIS['coin']}",
            ephemeral=True
        )

    # ====================== ПЕРЕВОД ======================
    @app_commands.command(name="pay", description="💸 Передать валюту или предметы")
    @app_commands.autocomplete(item_id="item_autocomplete")
    # Автодополнение для предметов в /pay
    async def item_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
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
            name = f"{info['name']} (у вас {count} шт.)"
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=iid))
        
        return choices[:25]
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
        interaction: discord.Interaction, 
        member: discord.Member, 
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

        # Перевод валюты
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

        # Перевод предмета
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
            f"✅ {interaction.user.mention} → {member.mention}\n" + " и ".join(msg_parts),
            ephemeral=False
        )

    # ====================== ВЕРИФИКАЦИЯ ======================
    @app_commands.command(name="verify", description="🔐 Пройти верификацию")
    async def verify(self, interaction: discord.Interaction):
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

            # Капча
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

    # ====================== ОБМЕН ======================
    @app_commands.command(name="exchange", description="💱 Обменять монеты на MortisCoin")
    async def exchange(self, interaction: discord.Interaction, amount_coins: int):
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

    # ====================== SETUP ======================
async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))
    logger.info("✅ EconomyCog успешно загружен")