import discord
from discord.ext import commands
from config.settings import OWNER_ID


def is_owner():
    async def predicate(ctx):
        return ctx.author.id == OWNER_ID
    return commands.check(predicate)


def is_moderator():
    async def predicate(ctx):
        if ctx.author.id == OWNER_ID:
            return True
        return ctx.author.guild_permissions.manage_messages or ctx.author.guild_permissions.administrator
    return commands.check(predicate)


def can_punish(target: discord.Member):
    """Проверка, можно ли наказать пользователя"""
    async def predicate(ctx):
        if target.id == OWNER_ID:
            return False
        if target.id == ctx.author.id:
            return False
        if target.top_role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return False
        return True
    return commands.check(predicate)