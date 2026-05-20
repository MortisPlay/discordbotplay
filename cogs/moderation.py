from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from typing import Union
import io

from config.settings import logger, MOD_LOG_CHANNEL_ID

class ModerationCog(commands.Cog):
    """Логирование и античит для сервера Семья бензопил"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def log_action(
        self,
        action_type: str,
        target: Union[discord.Member, discord.User, discord.Role, discord.abc.GuildChannel, discord.Guild, str],
        details: str = None,
        color: int = 0x5865F2,
        moderator: discord.Member = None,
        files: list[discord.File] = None,
    ):
        """Расширенное логирование действий в админ-канал"""
        channel = self.bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not channel:
            return

        embed = discord.Embed(title=f"📋 Лог: {action_type}", color=color, timestamp=datetime.now(timezone.utc))
        target_value = target.mention if hasattr(target, "mention") else str(target)
        embed.add_field(name="Цель", value=target_value, inline=True)

        if moderator:
            embed.add_field(name="Модератор", value=f"{moderator.mention}", inline=True)

        if details:
            embed.add_field(name="Детали", value=details, inline=False)

        if hasattr(target, "avatar") and target.avatar:
            embed.set_thumbnail(url=target.avatar.url)

        await channel.send(embed=embed, files=files or [])

    # ====================== СОБЫТИЯ ЛОГИРОВАНИЯ ======================
    def _create_text_file(self, filename: str, content: str) -> discord.File:
        return discord.File(io.BytesIO(content.encode('utf-8')), filename=filename)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        details = f"Канал: {message.channel.mention}\n"
        if message.content:
            details += f"Контент: {message.content[:500]}"
        else:
            details += "Контент: *[Вложение или пусто]*"

        files = None
        if message.content and len(message.content) > 500:
            details = f"Канал: {message.channel.mention}\nСообщение слишком длинное, подробности в файле."
            text = f"Сообщение удалено от {message.author} ({message.author.id})\n\n{message.content}"
            files = [self._create_text_file(f"deleted_message_{message.id}.txt", text)]

        await self.log_action(
            "Сообщение удалено",
            message.author,
            details,
            0xE74C3C,
            files=files
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content or not before.guild:
            return

        before_text = before.content or "[Пусто]"
        after_text = after.content or "[Пусто]"
        long_before = len(before_text) > 300
        long_after = len(after_text) > 300
        file_content = None
        files = None

        if long_before or long_after or len(before_text) + len(after_text) > 900:
            details = f"Канал: {before.channel.mention}\nСообщение слишком длинное, полная версия в файле."
            file_content = f"До:\n{before_text}\n\nПосле:\n{after_text}"
            files = [self._create_text_file(f"message_edit_{before.id}.txt", file_content)]
        else:
            details = (
                f"Канал: {before.channel.mention}\n"
                f"До: {before_text[:250]}\n"
                f"После: {after_text[:250]}"
            )

        await self.log_action(
            "Сообщение изменено",
            before.author,
            details,
            0x3498DB,
            files=files
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
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        await self.log_action(
            "Пользователь забанен",
            user,
            f"Сервер: {guild.name}",
            0xE74C3C
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        await self.log_action(
            "Пользователь разбанен",
            user,
            f"Сервер: {guild.name}",
            0x2ECC71
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        changes = []
        if before.name != after.name:
            changes.append(f"Название: `{before.name}` → `{after.name}`")
        if getattr(before, "topic", None) != getattr(after, "topic", None):
            changes.append(f"Тема: `{getattr(before, 'topic', 'Нет') or 'Нет'}` → `{getattr(after, 'topic', 'Нет') or 'Нет'}`")
        if getattr(before, "rate_limit_per_user", None) != getattr(after, "rate_limit_per_user", None):
            changes.append(f"Slowmode: `{getattr(before, 'rate_limit_per_user', '0')}s` → `{getattr(after, 'rate_limit_per_user', '0')}s`")

        if changes:
            await self.log_action(
                "Канал обновлен",
                after,
                "\n".join(changes),
                0xF39C12
            )

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        await self.log_action(
            "Роль создана",
            role,
            f"Название: {role.name}\nЦвет: {role.color}",
            0x2ECC71
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await self.log_action(
            "Роль удалена",
            role.name,
            f"Название: {role.name}",
            0xE74C3C
        )

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        changes = []
        if before.name != after.name:
            changes.append(f"Название: `{before.name}` → `{after.name}`")
        if before.color != after.color:
            changes.append(f"Цвет: `{before.color}` → `{after.color}`")
        if before.permissions != after.permissions:
            changes.append("Права роли изменены")

        if changes:
            await self.log_action(
                "Роль обновлена",
                after,
                "\n".join(changes),
                0xF1C40F
            )

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        await self.log_action(
            "Канал создан",
            channel,
            f"Тип: {channel.type.name}\nНазвание: {channel.name}",
            0x2ECC71
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        await self.log_action(
            "Канал удален",
            channel,
            f"Тип: {channel.type.name}\nНазвание: {channel.name}",
            0xE74C3C
        )

    # Античити можно добавить здесь, если нужно, например, проверка на спам или что-то

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))
    logger.info("✅ ModerationCog (Logs & Anticheat) загружен")