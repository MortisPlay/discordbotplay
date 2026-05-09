import discord
from discord.ext import commands
import time
from datetime import datetime
from config.economy import VOICE_INCOME_PER_MINUTE, VOICE_MIN_SESSION_MINUTES, ECONOMY_EMOJIS
from utils.db import economy_db
from config.settings import logger

class VoiceEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_times = {} # Храним время захода пользователей

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot: return

        # Пользователь зашел в канал (был не в канале, стал в канале)
        if before.channel is None and after.channel is not None:
            self.voice_times[member.id] = time.time()
            logger.info(f"🎙️ {member.display_name} зашел в голосовой канал")

        # Пользователь вышел из канала (был в канале, стал не в канале)
        elif before.channel is not None and after.channel is None:
            start_time = self.voice_times.pop(member.id, None)
            
            if start_time:
                duration_seconds = int(time.time() - start_time)
                duration_minutes = duration_seconds // 60
                
                if duration_minutes >= VOICE_MIN_SESSION_MINUTES:
                    reward = duration_minutes * VOICE_INCOME_PER_MINUTE
                    
                    # Начисляем монеты
                    user_data = economy_db.get_user(member.id)
                    user_data["balance"] = user_data.get("balance", 0) + reward
                    await economy_db.save()
                    
                    # Отправляем красивое уведомление в ЛС (по желанию)
                    try:
                        embed = discord.Embed(
                            title="🎙️ Голосовая активность",
                            description=(
                                f"Вы провели в канале **{duration_minutes}** мин.\n"
                                f"Ваша награда: **{reward}** {ECONOMY_EMOJIS['coin']}"
                            ),
                            color=0x2ECC71
                        )
                        embed.set_footer(text="Семья Бензопил • MortisPlay")
                        await member.send(embed=embed)
                    except discord.Forbidden:
                        # Если ЛС закрыты, просто логируем
                        logger.info(f"💰 {member.display_name} получил {reward} за войс (ЛС закрыты)")
                else:
                    logger.info(f"⏳ {member.display_name} пробыл в войсе слишком мало для награды")

async def setup(bot):
    await bot.add_cog(VoiceEvents(bot))