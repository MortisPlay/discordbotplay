from __future__ import annotations
import discord
from discord import app_commands
from discord.ext import commands
from config.settings import logger

class ErrorHandler(commands.Cog):
    """Глобальная обработка ошибок"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Привязываем обработчик к дереву слэш-команд
        bot.tree.on_error = self.on_app_command_error

    # ====================== ОБРАБОТКА СЛЭШ-КОМАНД (/) ======================

    async def on_app_command_error(self, interaction: "discord.Interaction", error: app_commands.AppCommandError):
        """Этот метод вызывается автоматически при ошибке в любой слэш-команде"""
        
        # Обработка Кулдауна (Ограничения по времени)
        if isinstance(error, app_commands.CommandOnCooldown):
            seconds = error.retry_after
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            remaining_seconds = int(seconds % 60)

            if hours > 0:
                time_str = f"**{hours} ч. {minutes} мин.**"
            elif minutes > 0:
                time_str = f"**{minutes} мин. {remaining_seconds} сек.**"
            else:
                time_str = f"**{remaining_seconds} сек.**"

            return await interaction.response.send_message(
                f"⏳ Ты уже забирал свою награду! Приходи через {time_str}.", 
                ephemeral=True
            )

        # Ошибка прав у пользователя
        if isinstance(error, app_commands.MissingPermissions):
            return await interaction.response.send_message(
                f"❌ У тебя недостаточно прав! Требуется: `{', '.join(error.missing_permissions)}`", 
                ephemeral=True
            )

        # Ошибка прав у бота
        if isinstance(error, app_commands.BotMissingPermissions):
            return await interaction.response.send_message(
                f"❌ Мне (боту) не хватает прав для этого: `{', '.join(error.missing_permissions)}`", 
                ephemeral=True
            )

        # Логирование всех остальных критических ошибок
        logger.error(f"Ошибка в слэш-команде {interaction.command.name if interaction.command else 'Unknown'}: {error}")
        
        # Пытаемся ответить пользователю, если еще не ответили
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Произошла внутренняя ошибка при выполнении команды.", ephemeral=True)
        except:
            pass

    # ====================== ОБРАБОТКА ОБЫЧНЫХ КОМАНД (!) ======================
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Команда на паузе. Подожди **{error.retry_after:.1f}** сек.", delete_after=5)
        elif isinstance(error, commands.CommandNotFound):
            pass # Игнорируем несуществующие команды на префикс
        else:
            logger.error(f"Ошибка префикс-команды: {error}")

async def setup(bot: commands.Bot):
    await bot.add_cog(ErrorHandler(bot))