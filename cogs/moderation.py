from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from typing import Union

from config.settings import logger, MOD_LOG_CHANNEL_ID

class ModerationCog(commands.Cog):
    """Логирование и античит для сервера Семья бензопил"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def log_action(self, action_type: str, target: Union[discord.Member, discord.User], details: str, color: int, moderator: discord.Member = None):
        """Расширенное логирование действий в админ-канал"""
        channel = self.bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not channel:
            return

        embed = discord.Embed(title=f"📋 Лог: {action_type}", color=color, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Цель", value=f"{target.mention} (`{target.id}`)", inline=True)
        if moderator:
            embed.add_field(name="Модератор", value=f"{moderator.mention}", inline=True)
        embed.add_field(name="Детали", value=details, inline=False)
        
        if hasattr(target, 'avatar') and target.avatar:
            embed.set_thumbnail(url=target.avatar.url)
            
        await channel.send(embed=embed)

    # ====================== СОБЫТИЯ ЛОГИРОВАНИЯ ======================
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        await self.log_action(
            "Сообщение удалено",
            message.author,
            f"Канал: {message.channel.mention}\nКонтент: {message.content[:500] if message.content else '*[Вложение или пусто]*'}",
            0xE74C3C
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content or not before.guild: return
        await self.log_action(
            "Сообщение изменено",
            before.author,
            f"Канал: {before.channel.mention}\nДо: {before.content[:250] or '[Пусто]'}\nПосле: {after.content[:250] or '[Пусто]'}",
            0x3498DB
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self.log_action(
            "Пользователь присоединился",
            member,
            f"Аккаунт создан: <t:{int(member.created_at.timestamp())}:R>",
            0x2ECC71
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self.log_action(
            "Пользователь покинул",
            member,
            f"Был на сервере: <t:{int(member.joined_at.timestamp())}:R>",
            0xE74C3C
        )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            details = ""
            if added_roles:
                details += f"Добавлены роли: {', '.join(role.name for role in added_roles)}\n"
            if removed_roles:
                details += f"Удалены роли: {', '.join(role.name for role in removed_roles)}"
            if details:
                await self.log_action("Изменение ролей", after, details.strip(), 0xF1C40F)

        if before.nick != after.nick:
            await self.log_action(
                "Изменение ника",
                after,
                f"Старый: {before.nick or 'Нет'}\nНовый: {after.nick or 'Нет'}",
                0x9B59B6
            )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self.log_action(
            "Канал создан",
            channel.guild.owner,  # Или кто-то другой, но owner для примера
            f"Тип: {channel.type.name}\nНазвание: {channel.name}",
            0x2ECC71
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.log_action(
            "Канал удален",
            channel.guild.owner,
            f"Тип: {channel.type.name}\nНазвание: {channel.name}",
            0xE74C3C
        )

    # Античити можно добавить здесь, если нужно, например, проверка на спам или что-то

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
    logger.info("✅ ModerationCog (Logs & Anticheat) загружен")