# utility.py
from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
import platform
import psutil
import time
from datetime import datetime, timezone
from utils.db import economy_db

from config.settings import logger, format_number
from config.economy import ECONOMY_EMOJIS


class UtilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    def get_progress_bar(self, percent):
        filled = int(percent / 10)
        bar = "▰" * filled + "▱" * (10 - filled)
        return bar

    def format_uptime(self, seconds: int) -> str:
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        parts = []
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)

    @app_commands.command(name="user", description="👤 Подробная информация о пользователе")
    @app_commands.describe(member="Пользователь, чей профиль нужно посмотреть")
    async def user_info(self, interaction: "discord.Interaction", member: "discord.Member" = None):
        await interaction.response.defer(ephemeral=True)
        try:
            target = member or interaction.user
            guild_member = interaction.guild.get_member(target.id) if interaction.guild else target

            user_data = economy_db.get_user(target.id)
            balance = user_data.get("balance", 0)
            job = user_data.get("job", "Безработный").capitalize()
            mortis_coins = user_data.get("mortis_coins", 0)
            is_verified = user_data.get("is_verified", False)

            embed = discord.Embed(title=f"👤 Профиль: {target.display_name}", color=0x5865F2, timestamp=datetime.now(timezone.utc))
            embed.set_author(name="Пользовательская карточка", icon_url=target.display_avatar.url)
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.description = f"{target.mention}"

            # Основная информация
            embed.add_field(
                name="📋 Основное",
                value=(
                    f"**Имя:** {target.name}\n"
                    f"**Дискриминатор:** #{target.discriminator}\n"
                    f"**ID:** `{target.id}`\n"
                    f"**Бот:** {'Да' if target.bot else 'Нет'}"
                ),
                inline=True
            )

            # Даты
            embed.add_field(
                name="📅 Даты",
                value=(
                    f"**Аккаунт создан:** <t:{int(target.created_at.timestamp())}:R>\n"
                    f"**На сервере с:** <t:{int(guild_member.joined_at.timestamp())}:R>" if guild_member and guild_member.joined_at else "**На сервере с:** Неизвестно"
                ),
                inline=True
            )

            # Экономика
            embed.add_field(
                name=f"{ECONOMY_EMOJIS['balance']} Экономика",
                value=(
                    f"**Баланс:** `{format_number(balance)}` {ECONOMY_EMOJIS['coin']}\n"
                    f"**MortisCoins:** `{mortis_coins}` 💎\n"
                    f"**Работа:** `{job}`\n"
                    f"**Верифицирован:** {'✅' if is_verified else '❌'}"
                ),
                inline=False
            )

            # Роли (если на сервере)
            if guild_member and guild_member.roles:
                roles = [role.mention for role in guild_member.roles[1:]]  # Исключаем @everyone
                roles_str = ", ".join(roles) if roles else "Нет ролей"
                embed.add_field(
                    name="🎭 Роли",
                    value=roles_str[:1024],  # Ограничение Discord
                    inline=False
                )

            # Статус
            status_emoji = {
                discord.Status.online: "🟢",
                discord.Status.idle: "🟡",
                discord.Status.dnd: "🔴",
                discord.Status.offline: "⚫"
            }.get(guild_member.status if guild_member else discord.Status.offline, "⚫")
            embed.add_field(
                name="📊 Статус",
                value=f"{status_emoji} {guild_member.status.name.capitalize() if guild_member else 'Оффлайн'}",
                inline=True
            )

            embed.set_footer(text="MortisBot • Семья Бензопил", icon_url=self.bot.user.display_avatar.url)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Ошибка user: {e}")
            await interaction.followup.send("❌ Ошибка при получении данных.", ephemeral=True)

    @app_commands.command(name="botinfo", description="🛰️ Состояние систем")
    async def botinfo(self, interaction: "discord.Interaction"):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        uptime = int(time.time() - self.start_time)

        total_members = len(set(self.bot.get_all_members()))
        verified_count = sum(
            1
            for user in economy_db.data.values()
            if isinstance(user, dict) and user.get("is_verified")
        )
        total_jobs = sum(
            1
            for user in economy_db.data.values()
            if isinstance(user, dict) and user.get("job") and user.get("job") != "unemployed"
        )
        command_count = len(list(self.bot.tree.walk_commands()))

        # Пинг и вебсокет
        ping = round(self.bot.latency * 1000)
        websocket_ping = round(self.bot.latency * 1000)  # Примерно то же самое

        embed = discord.Embed(
            title="🛰️ Статус MortisBot",
            description="Текущие показатели системы и активности.",
            color=0x5865F2,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # Системные ресурсы
        embed.add_field(name="💻 CPU", value=f"[{self.get_progress_bar(cpu)}] `{cpu}%`", inline=True)
        embed.add_field(name="🧠 RAM", value=f"[{self.get_progress_bar(mem)}] `{mem}%`", inline=True)
        embed.add_field(name="⏱️ Uptime", value=self.format_uptime(uptime), inline=True)

        # Статистика бота
        embed.add_field(name="🏠 Серверов", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="👥 Участников", value=f"`{total_members}`", inline=True)
        embed.add_field(name="⚡ Команд", value=f"`{command_count}`", inline=True)

        # Экономика
        embed.add_field(name="✅ Верифицированных", value=f"`{verified_count}`", inline=True)
        embed.add_field(name="💼 Работающих", value=f"`{total_jobs}`", inline=True)

        # Версии
        embed.add_field(name="🐍 Python", value=f"`{platform.python_version()}`", inline=True)
        embed.add_field(name="📚 discord.py", value=f"`{discord.__version__}`", inline=True)

        # Пинг и вебсокет
        embed.add_field(name="🏓 Пинг", value=f"`{ping}ms`", inline=True)
        embed.add_field(name="🌐 Вебсокет", value=f"`{websocket_ping}ms`", inline=True)

        embed.set_footer(text="MortisBot • Семья Бензопил", icon_url=self.bot.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))
    logger.info("✅ UtilityCog загружен")