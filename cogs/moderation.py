import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from config.settings import (
    logger, OWNER_ID, MOD_LOG_CHANNEL_ID,
    WARN_AUTO_MUTE_THRESHOLD, WARN_AUTO_KICK_THRESHOLD
)
from utils.db import warnings_db

class ModerationCog(commands.Cog):
    """Модерация сервера Семья бензопил"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def can_punish(self, executor: discord.Member, target: Union[discord.Member, discord.User]) -> bool:
        """Проверка иерархии"""
        if executor.id == OWNER_ID: return True
        if not isinstance(target, discord.Member): return True # Для разбана (User)
        
        if target.id == OWNER_ID or target == target.guild.owner: return False
        if executor.id == target.id: return False
        return executor.top_role > target.top_role

    async def log_action(self, action_type: str, moderator: discord.Member, target: Union[discord.Member, discord.User], reason: str, color: int):
        """Логирование действий в админ-канал"""
        channel = self.bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not channel:
            return

        embed = discord.Embed(title=f"🛡️ Лог: {action_type}", color=color, timestamp=datetime.now(timezone.utc))
        embed.add_field(name="Цель", value=f"{target.mention} (`{target.id}`)", inline=True)
        embed.add_field(name="Модератор", value=f"{moderator.mention}", inline=True)
        embed.add_field(name="Причина", value=reason, inline=False)
        
        if isinstance(target, discord.Member) and target.avatar:
            embed.set_thumbnail(url=target.avatar.url)
            
        await channel.send(embed=embed)

    # ====================== ГРУППА ВАРНОВ ======================
    warn_group = app_commands.Group(name="warn", description="Управление предупреждениями")

    @warn_group.command(name="add", description="⚠️ Выдать варн")
    @app_commands.describe(member="Нарушитель", reason="Причина")
    async def warn_add(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        if not self.can_punish(interaction.user, member):
            return await interaction.response.send_message("❌ Недостаточно прав для наказания этого пользователя.", ephemeral=True)
        
        warn_entry = {
            "mod_id": interaction.user.id, 
            "reason": reason, 
            "date": datetime.now(timezone.utc).isoformat()
        }
        await warnings_db.add_to_user_list(member.id, "warns", warn_entry)
        
        count = len(warnings_db.get_user(member.id).get("warns", []))
        await interaction.response.send_message(f"✅ Варн выдан {member.mention} (Всего: {count}).", ephemeral=True)
        await self.log_action("ВАРН", interaction.user, member, reason, 0xF1C40F)

        # Авто-наказание: 2 варна = мут на 24 часа
        if count == 2:
            try:
                await member.timeout(timedelta(hours=24), reason="Авто-мут за 2-й варн")
            except Exception as e:
                logger.error(f"Ошибка авто-мута: {e}")

    @warn_group.command(name="remove", description="✅ Снять последний варн")
    async def warn_remove(self, interaction: discord.Interaction, member: discord.Member):
        data = warnings_db.get_user(member.id)
        warns = data.get("warns", [])
        
        if not warns:
            return await interaction.response.send_message("❌ У пользователя нет активных варнов.", ephemeral=True)
        
        warns.pop()
        await warnings_db.save()
        await interaction.response.send_message(f"✅ Последний варн снят с {member.mention}.", ephemeral=True)
        await self.log_action("СНЯТИЕ ВАРНА", interaction.user, member, "Амнистия / Ошибка", 0x2ECC71)

    @warn_group.command(name="list", description="📋 Посмотреть историю варнов")
    async def warn_list(self, interaction: discord.Interaction, member: discord.Member):
        warns = warnings_db.get_user(member.id).get("warns", [])
        if not warns: 
            return await interaction.response.send_message(f"✅ У {member.display_name} нет нарушений.", ephemeral=True)
        
        embed = discord.Embed(title=f"Нарушения {member.display_name}", color=0xE74C3C)
        for i, w in enumerate(warns, 1):
            # Поддержка всех вариантов ключей (старых и новых)
            m_id = w.get('mod_id') or w.get('mod') or w.get('moderator_id')
            reason = w.get('reason', 'Не указана')
            embed.add_field(
                name=f"Варн #{i}", 
                value=f"**Мод:** <@{m_id}>\n**Суть:** {reason}", 
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ====================== ГРУППА МУТОВ ======================
    mute_group = app_commands.Group(name="mute", description="Управление мутами")

    @mute_group.command(name="add", description="🤐 Замутить")
    async def mute_add(self, interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str):
        if not self.can_punish(interaction.user, member):
            return await interaction.response.send_message("❌ Недостаточно прав.", ephemeral=True)
        
        await member.timeout(timedelta(minutes=minutes), reason=reason)
        await interaction.response.send_message(f"🤐 {member.mention} замучен на {minutes} мин.", ephemeral=True)
        await self.log_action("МУТ", interaction.user, member, f"[{minutes}м] {reason}", 0x34495E)

    @mute_group.command(name="remove", description="🔊 Снять мут")
    async def mute_remove(self, interaction: discord.Interaction, member: discord.Member):
        await member.timeout(None)
        await interaction.response.send_message(f"🔊 Мут с {member.mention} снят.", ephemeral=True)
        await self.log_action("РАЗМУТ", interaction.user, member, "Снято модератором", 0x2ECC71)

    # ====================== ГРУППА БАНОВ ======================
    ban_group = app_commands.Group(name="ban", description="Управление банами")

    @ban_group.command(name="add", description="🔨 Забанить")
    async def ban_add(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        if not self.can_punish(interaction.user, member):
            return await interaction.response.send_message("❌ Нельзя наказать этого пользователя.", ephemeral=True)
        
        await member.ban(reason=reason)
        await interaction.response.send_message(f"🔨 {member.mention} забанен.", ephemeral=True)
        await self.log_action("БАН", interaction.user, member, reason, 0x000000)

    @ban_group.command(name="remove", description="🤝 Разбанить по ID")
    async def ban_remove(self, interaction: discord.Interaction, user_id: str):
        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"🤝 Пользователь {user.name} разбанен.", ephemeral=True)
            await self.log_action("РАЗБАН", interaction.user, user, "Амнистия", 0x2ECC71)
        except Exception as e:
            await interaction.response.send_message(f"❌ Не удалось разбанить: {e}", ephemeral=True)

    # ====================== ОЧИСТКА ЧАТА ======================
    @app_commands.command(name="clear", description="🧹 Очистить чат")
    @commands.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            return await interaction.response.send_message("❌ Можно удалить от 1 до 100 за раз.", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"✅ Удалено сообщений: {len(deleted)}", ephemeral=True)

    # ====================== СОБЫТИЯ ЛОГИРОВАНИЯ ======================
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild: return
        channel = self.bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not channel: return

        embed = discord.Embed(title="🗑️ Сообщение удалено", color=0xE74C3C, timestamp=datetime.now(timezone.utc))
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.add_field(name="Автор", value=f"{message.author.mention}", inline=True)
        embed.add_field(name="Канал", value=message.channel.mention, inline=True)
        
        content = message.content[:1000] if message.content else "*[Текст отсутствует или это вложение]*"
        embed.add_field(name="Контент", value=content, inline=False)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content: return
        channel = self.bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not channel: return

        embed = discord.Embed(title="📝 Сообщение изменено", color=0x3498DB, timestamp=datetime.now(timezone.utc))
        embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url)
        embed.add_field(name="До", value=before.content[:500] or "[Пусто]", inline=False)
        embed.add_field(name="После", value=after.content[:500] or "[Пусто]", inline=False)
        await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))