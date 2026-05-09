import discord
from discord import app_commands
from discord.ext import commands
import platform
import psutil
import time
from datetime import datetime
from typing import Optional

from config.settings import logger, format_number
from config.economy import ECONOMY_EMOJIS
from utils.db import economy_db

class UtilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    def get_progress_bar(self, percent):
        """Создает текстовый визуальный индикатор нагрузки"""
        filled = int(percent / 10)
        bar = "▰" * filled + "▱" * (10 - filled)
        return bar

    @app_commands.command(name="user", description="👤 Подробная информация о пользователе")
    @app_commands.describe(member="Пользователь, чей профиль нужно посмотреть")
    async def user_info(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        # 1. СРАЗУ отправляем сигнал ожидания (даем боту +15 минут на ответ)
        # ephemeral=True, так как финальный ответ тоже будет скрытым
        await interaction.response.defer(ephemeral=True)

        try:
            # 2. Теперь спокойно выполняем все расчеты
            target = member or interaction.user
            
            if interaction.guild:
                member = interaction.guild.get_member(target.id) or target
            else:
                member = target

            user_data = economy_db.get_user(member.id)
            
            balance = user_data.get("balance", 0)
            job = user_data.get("job", "Безработный").capitalize()
            inventory = user_data.get("inventory", {})
            total_items = sum(inventory.values()) if inventory else 0
            
            status_map = {
                discord.Status.online: "🟢 В сети",
                discord.Status.idle: "🌙 Не активен",
                discord.Status.dnd: "🔴 Не беспокоить",
                discord.Status.offline: "⚪ Не в сети",
                discord.Status.invisible: "⚪ Не в сети"
            }
            
            current_status = getattr(member, "status", discord.Status.offline)
            status_text = status_map.get(current_status, "⚪ Вне зоны доступа")

            embed = discord.Embed(title=f"👤 Досье: {member.display_name}", color=0x2b2d31)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            joined_at = f"<t:{int(member.joined_at.timestamp())}:R>" if hasattr(member, "joined_at") and member.joined_at else "Неизвестно"
            top_role = member.top_role.mention if hasattr(member, "top_role") else "Нет ролей"

            embed.add_field(
                name="📝 Общие сведения",
                value=(
                    f"**Статус:** `{status_text}`\n"
                    f"**Аккаунт создан:** <t:{int(member.created_at.timestamp())}:D>\n"
                    f"**Зашел на сервер:** {joined_at}\n"
                    f"**Топ роль:** {top_role}"
                ),
                inline=False
            )

            embed.add_field(
                name=f"{ECONOMY_EMOJIS['balance']} Экономика",
                value=(
                    f"**Баланс:** `{format_number(balance)}` {ECONOMY_EMOJIS['coin']}\n"
                    f"**Место работы:** `{job}`\n"
                    f"**Предметов:** `{total_items}` шт."
                ),
                inline=True
            )

            if hasattr(member, "roles"):
                roles = [role.mention for role in reversed(member.roles[1:])]
                roles_text = ", ".join(roles[:5]) + (f" и еще {len(roles)-5}" if len(roles) > 5 else "")
            else:
                roles_text = "Нет ролей"

            embed.add_field(name="🎭 Роли", value=roles_text if roles_text else "Нет ролей", inline=True)
            embed.set_footer(text=f"ID: {member.id} • Семья Бензопил")

            # 3. ТАК КАК МЫ ИСПОЛЬЗОВАЛИ defer(), отвечаем через follow-up
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Ошибка в команде user: {e}")
            # Если что-то пошло не так, сообщаем пользователю
            await interaction.followup.send("❌ Произошла ошибка при получении данных.", ephemeral=True)

    @app_commands.command(name="botinfo", description="🛰️ Состояние систем и технические характеристики")
    async def botinfo(self, interaction: discord.Interaction):
        uptime_seconds = int(time.time() - self.start_time)
        days, rem = divmod(uptime_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{days}д {hours}ч {minutes}м"

        cpu_pct = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        ping = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🦾 Mortis Bot Control Center",
            description=f"**Состояние системы:** `СТАБИЛЬНО` ✅\n**Версия протокола:** `v2.4.0-build`",
            color=0x2b2d31
        )
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        embed.add_field(
            name="📊 Ресурсы хоста",
            value=(
                f"**CPU:** `{cpu_pct}%`\n`{self.get_progress_bar(cpu_pct)}`\n"
                f"**RAM:** `{ram.percent}%`\n`{self.get_progress_bar(ram.percent)}`"
            ),
            inline=False
        )

        embed.add_field(
            name="📡 Сеть и Статистика",
            value=(
                f"**Пинг:** `{ping}ms`\n"
                f"**Серверы:** `{len(self.bot.guilds)}`\n"
                f"**Аптайм:** `{uptime_str}`"
            ),
            inline=True
        )

        embed.set_footer(text=f"MortisPlay.ru • 2026")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))