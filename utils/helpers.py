import discord
from datetime import datetime, timezone
import random

from config.settings import logger


def format_duration(seconds: int) -> str:
    """Преобразует секунды в читаемый формат (1d 12h 30m)"""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    minutes = minutes % 60
    if hours < 24:
        return f"{hours}h {minutes}m" if minutes else f"{hours}h"
    days = hours // 24
    hours = hours % 24
    if days < 30:
        return f"{days}d {hours}h" if hours else f"{days}d"
    months = days // 30
    days = days % 30
    if months < 12:
        if days and hours:
            return f"{months}mo {days}d {hours}h"
        if days:
            return f"{months}mo {days}d"
        if hours:
            return f"{months}mo {hours}h"
        return f"{months}mo"
    years = months // 12
    months = months % 12
    if months and days:
        return f"{years}y {months}mo {days}d"
    if months:
        return f"{years}y {months}mo"
    return f"{years}y"


def parse_duration(duration_str: str) -> int | None:
    """Преобразует 1h30m, 2d, 45m в секунды"""
    if not duration_str:
        return None
    
    duration_str = duration_str.lower().replace(" ", "")
    total = 0
    current = ""
    
    for char in duration_str:
        if char.isdigit():
            current += char
        else:
            if not current:
                return None
            value = int(current)
            if char == 'd':
                total += value * 86400
            elif char == 'h':
                total += value * 3600
            elif char == 'm':
                total += value * 60
            elif char == 's':
                total += value
            else:
                return None
            current = ""
    
    return total if total > 0 else None


def generate_color() -> int:
    """Генерирует случайный цвет для embed"""
    return random.randint(0, 0xFFFFFF)


async def send_log(channel: discord.TextChannel, message: str, title: str = "Лог"):
    """Удобная отправка лога в канал"""
    embed = discord.Embed(title=title, description=message, color=0x5865F2, timestamp=datetime.now(timezone.utc))
    try:
        await channel.send(embed=embed)
    except:
        pass