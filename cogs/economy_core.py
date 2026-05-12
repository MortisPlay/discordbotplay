# economy_core.py
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta, timezone
import asyncio
import string

from config.settings import logger, format_number
from config.economy import ECONOMY_EMOJIS, JOBS, DAILY_COOLDOWN
from config.shop import SHOP_ITEMS, INVENTORY_ITEMS
from utils.db import economy_db


class EconomyCore(commands.Cog):
    """Базовые команды экономики (основные механики)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ====================== АВТОДОПОЛНЕНИЕ ======================
    async def item_autocomplete(
        self, interaction: discord.Interaction, current: str
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

        reward = random.randint(10, 50)
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

    # ====================== WORK ======================
    @app_commands.command(name="work", description="⚒️ Отправиться на работу")
    async def work(self, interaction: discord.Interaction):
        user = economy_db.get_user(interaction.user.id)
        now = datetime.now(timezone.utc)

        if (now - interaction.user.created_at).days < 3:
            return await interaction.response.send_message(
                "❌ Ваш аккаунт слишком новый. Для работы нужно минимум 3 дня.", ephemeral=True)

        WORK_COOLDOWN = 1800
        last_work = user.get("last_work")
        
        if last_work:
            try:
                last_time = datetime.fromisoformat(last_work)
                if now < last_time + timedelta(seconds=WORK_COOLDOWN):
                    remaining = (last_time + timedelta(seconds=WORK_COOLDOWN)) - now
                    m, s = divmod(int(remaining.total_seconds()), 60)
                    return await interaction.response.send_message(
                        f"⏳ Отдохните ещё **{m}м {s}с**", ephemeral=True)
            except (ValueError, TypeError):
                pass

        job_id = user.get("job", "unemployed")
        if job_id == "unemployed":
            return await interaction.response.send_message("❌ Сначала устройтесь на работу командой `/job`", ephemeral=True)

        job_info = JOBS.get(job_id)
        if not job_info:
            return await interaction.response.send_message(
                "❌ Ваша текущая работа не найдена. Попробуйте сменить должность командой `/job`.",
                ephemeral=True
            )

        reward = random.randint(job_info["min_salary"], job_info["max_salary"])
        multiplier = 1.0
        bonuses = []

        if user.get("work_boost"):
            multiplier += 0.5
            user["work_boost"] = False
            bonuses.append("🥤 +50% к следующей работе")

        if user.get("inventory", {}).get("pro_tools", 0) > 0:
            multiplier += 0.2
            bonuses.append("🛠️ +20% от набора инструментов")

        final_reward = int(reward * multiplier)
        bonus_text = ""
        if bonuses:
            bonus_text = " \n" + " \n".join(f"• {b}" for b in bonuses)

        user["balance"] = user.get("balance", 0) + final_reward
        user["last_work"] = now.isoformat()
        economy_db.update_user(interaction.user.id, user)

        embed = discord.Embed(
            title=f"⚒️ Работа — {job_info.get('emoji', '')} {job_info['name']}",
            description=(
                f"Вы отработали смену и заработали **{format_number(final_reward)}** {ECONOMY_EMOJIS['coin']}!"
                f"\n\nБазовая зарплата: `{format_number(reward)}` {ECONOMY_EMOJIS['coin']}"
                f"\nКоэффициент: `x{multiplier:.1f}`"
            ),
            color=0x2ecc71
        )
        if bonus_text:
            embed.add_field(name="Бонусы", value=bonus_text.strip(), inline=False)
        embed.set_footer(text="/job — смена работы, /vault — валюта")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ====================== JOB ======================
    @app_commands.command(name="job", description="💼 Устроиться на работу")
    async def job(self, interaction: discord.Interaction):
        user = economy_db.get_user(interaction.user.id)
        
        from .economy_ui import JobSelectionView
        view = JobSelectionView(interaction.user.id, user, interaction.user)
        
        embed = discord.Embed(
            title="💼 Выбор профессии",
            description="Выберите работу, которая вам нравится. Для каждой работы есть свои требования!",
            color=0x3498db
        )
        embed.add_field(name="💡 Совет", value="Скоро вы сможете работать и зарабатывать! Используйте `/work` для получения зарплаты.", inline=False)
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ====================== INVENTORY ======================
    @app_commands.command(name="inventory", description="🎒 Просмотр инвентаря")
    async def inventory(self, interaction: discord.Interaction):
        user = economy_db.get_user(interaction.user.id)
        if isinstance(user.get("inventory"), list):
            user["inventory"] = {}
            economy_db.update_user(interaction.user.id, user)
        
        from .economy_ui import InventoryView
        view = InventoryView(interaction.user.id)
        embed = view.create_embed(user, interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCore(bot))
    logger.info("✅ EconomyCore (базовые команды) успешно загружен")