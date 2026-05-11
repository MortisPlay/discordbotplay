import discord
from discord.ext import commands
from datetime import timedelta
import re
from typing import Optional


class DurationConverter(commands.Converter):
    """Конвертер длительности: 1h, 30m, 2d, 45m30s и т.д."""
    
    async def convert(self, ctx: commands.Context, argument: str) -> timedelta:
        """
        Примеры:
        - 1h → 1 час
        - 30m → 30 минут
        - 2d → 2 дня
        - 1h30m → 1.5 часа
        - 45s → 45 секунд
        """
        argument = argument.lower().replace(" ", "")
        
        if not argument:
            raise commands.BadArgument("Укажи длительность (например: 1h, 30m, 2d)")

        # Регулярка для разбора
        pattern = re.compile(r'(\d+)([dhms])')
        matches = pattern.findall(argument)

        if not matches:
            raise commands.BadArgument(f"Неверный формат длительности: `{argument}`")

        total_seconds = 0
        time_units = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}

        for value, unit in matches:
            total_seconds += int(value) * time_units[unit]

        if total_seconds <= 0:
            raise commands.BadArgument("Длительность должна быть больше 0")

        if total_seconds > 31536000:  # 1 год
            raise commands.BadArgument("Максимальная длительность — 1 год")

        return timedelta(seconds=total_seconds)


class PositiveIntConverter(commands.Converter):
    """Конвертер положительного целого числа (для экономики и т.д.)"""
    
    async def convert(self, ctx: commands.Context, argument: str) -> int:
        try:
            number = int(argument)
            if number <= 0:
                raise commands.BadArgument("Число должно быть положительным (> 0)")
            if number > 100_000_000:  # защита от слишком больших чисел
                raise commands.BadArgument("Слишком большое число!")
            return number
        except ValueError:
            raise commands.BadArgument("Ожидалось целое положительное число.")


class MemberOrIDConverter(commands.Converter):
    """Конвертер: принимает Member или ID пользователя"""
    
    async def convert(self, ctx: commands.Context, argument: str) -> discord.Member | int:
        # Пробуем найти по упоминанию / имени
        try:
            member = await commands.MemberConverter().convert(ctx, argument)
            return member
        except commands.MemberNotFound:
            pass
        
        # Пробуем как ID
        if argument.isdigit():
            user_id = int(argument)
            member = ctx.guild.get_member(user_id)
            if member:
                return member
            return user_id  # возвращаем ID, если участника нет на сервере
        
        raise commands.BadArgument(f"Не удалось найти пользователя: `{argument}`")


# ====================== Регистрация конвертеров ======================

# Можно использовать в командах так:
# @app_commands.describe(duration="Длительность (1h, 30m, 2d)")
# async def mute(self, interaction: "discord.Interaction", member: "discord.Member", duration: DurationConverter):