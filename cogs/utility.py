import discord
from discord import app_commands
from discord.ext import commands
import platform
import psutil
import time
from utils.db import economy_db

from config.settings import logger, format_number
from config.economy import ECONOMY_EMOJIS, JOBS

class UtilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    def get_progress_bar(self, percent):
        filled = int(percent / 10)
        bar = "▰" * filled + "▱" * (10 - filled)
        return bar

    @app_commands.command(name="user", description="👤 Подробная информация о пользователе")
    @app_commands.describe(member="Пользователь, чей профиль нужно посмотреть")
    async def user_info(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer(ephemeral=True)
        try:
            target = member or interaction.user
            guild_member = interaction.guild.get_member(target.id) if interaction.guild else target

            user_data = economy_db.get_user(target.id)
            balance = user_data.get("balance", 0)
            job = user_data.get("job", "Безработный").capitalize()

            embed = discord.Embed(title=f"👤 Досье: {target.display_name}", color=0x2b2d31)
            embed.set_thumbnail(url=target.display_avatar.url)

            embed.add_field(name="📝 Общие сведения", value=(
                f"**Аккаунт создан:** <t:{int(target.created_at.timestamp())}:D>\n"
                f"**На сервере с:** <t:{int(guild_member.joined_at.timestamp())}:R>" if guild_member.joined_at else "Неизвестно"
            ), inline=False)

            embed.add_field(name=f"{ECONOMY_EMOJIS['balance']} Экономика", 
                           value=f"**Баланс:** `{format_number(balance)}` {ECONOMY_EMOJIS['coin']}\n**Работа:** `{job}`", 
                           inline=True)

            embed.set_footer(text=f"ID: {target.id} • Семья Бензопил")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Ошибка user: {e}")
            await interaction.followup.send("❌ Ошибка при получении данных.", ephemeral=True)

    @app_commands.command(name="botinfo", description="🛰️ Состояние систем")
    async def botinfo(self, interaction: discord.Interaction):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        uptime = int(time.time() - self.start_time)

        embed = discord.Embed(title="🦾 System Status", color=0x2ECC71)
        embed.add_field(name="CPU", value=f"[{self.get_progress_bar(cpu)}] `{cpu}%`", inline=False)
        embed.add_field(name="RAM", value=f"[{self.get_progress_bar(mem)}] `{mem}%`", inline=False)
        embed.add_field(name="Uptime", value=f"<t:{int(time.time() - uptime)}:R>", inline=False)
        embed.set_footer(text=f"{platform.system()} • 2026")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="job", description="💼 Устроиться на работу")
    @app_commands.describe(job_name="Название работы")
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
            f"✅ Вы устроились на работу **{job_info['name']}**!\n"
            f"Зарплата: `{job_info['min_salary']}-{job_info['max_salary']}` {ECONOMY_EMOJIS['coin']}",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityCog(bot))
    logger.info("✅ UtilityCog загружен")