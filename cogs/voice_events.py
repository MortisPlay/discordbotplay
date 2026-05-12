from __future__ import annotations
import discord
from discord.ext import commands
import time
from datetime import datetime
from config.economy import VOICE_INCOME_PER_HOUR, VOICE_MIN_SESSION_MINUTES, ECONOMY_EMOJIS
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

        # Пользователь вышел из канала или переключился на другой канал
        elif before.channel is not None and before.channel != after.channel:
            start_time = self.voice_times.pop(member.id, None)
            
            if start_time:
                duration_seconds = int(time.time() - start_time)
                duration_minutes = duration_seconds // 60
                
                if duration_minutes >= VOICE_MIN_SESSION_MINUTES:
                    members_in_channel = [m for m in before.channel.members if not m.bot]
                    if member not in members_in_channel:
                        members_in_channel.append(member)

                    if len(members_in_channel) >= 2:
                        reward_hours = duration_minutes // 60
                        reward = reward_hours * VOICE_INCOME_PER_HOUR

                        if reward > 0:
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
                            logger.info(f"⏳ {member.display_name} провёл в войсе {duration_minutes} мин., но не набрал полный час для награды")
                    else:
                        logger.info(f"🚫 {member.display_name} не получил награду: в канале было меньше 2 человек")
                else:
                    logger.info(f"⏳ {member.display_name} пробыл в войсе слишком мало для награды")

async def setup(bot):
    await bot.add_cog(VoiceEvents(bot))