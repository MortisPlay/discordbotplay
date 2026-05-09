import discord
from datetime import datetime, timezone

def success_embed(title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=0x00FF00)
    embed.timestamp = datetime.now(timezone.utc)
    return embed


def error_embed(title: str, description: str):
    embed = discord.Embed(title=title, description=description, color=0xFF0000)
    embed.timestamp = datetime.now(timezone.utc)
    return embed