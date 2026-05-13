# modules/economy_bp/bp_main.py

import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from utils.db import economy_db
from .bp_core import BPCore
from .bp_view import BattlePassView
from .bp_config import BP_SETTINGS
from utils.helpers import format_duration

class BattlePassCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pass", description="🎫 Открыть Боевой Пропуск")
    async def bp_command(self, interaction: discord.Interaction):
        now = datetime.now(timezone.utc)
        season_start = BP_SETTINGS["SEASON_START"]
        
        # Проверка: сезон ещё не начался
        if now < season_start:
            time_until = format_duration(int((season_start - now).total_seconds()))
            embed = discord.Embed(
                title="⏳ Сезон ещё не начался",
                description=f"Сезон '{BP_SETTINGS['SEASON_NAME']}' начнётся через:\n**{time_until}**",
                color=0xe74c3c
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        
        user_id = interaction.user.id
        user_data = economy_db.get_user(user_id)
        
        # Инициализируем данные БП, если это новый игрок
        user_data, changed = BPCore.setup_user_bp(user_data)
        if changed:
            economy_db.update_user(user_id, user_data)

        view = BattlePassView(user_id, user_data)
        await interaction.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(BattlePassCog(bot))