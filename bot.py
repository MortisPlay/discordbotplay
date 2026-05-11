import discord
from discord.ext import commands, tasks
import asyncio
import os
import traceback
from config.settings import TOKEN, logger, OWNER_ID, DATA_DIR, FULL_ACCESS_GUILD_ID
from utils.db import init_databases

# ====================== НАСТРОЙКИ ======================
intents = discord.Intents(
    guilds=True,
    members=True,
    presences=True,
    message_content=True,
    voice_states=True,
    moderation=True,
    guild_messages=True
)

class MortisBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
            owner_id=OWNER_ID,
            status=discord.Status.dnd,
            activity=discord.Activity(type=discord.ActivityType.watching, name="mortisplay.ru")
        )

    async def setup_hook(self):
        """Выполняется перед запуском бота"""
        print(">>> [0/4] Загрузка cogs...")
        
        COGS = [
            "cogs.fun",
            "cogs.moderation",
            "cogs.tickets",
            "cogs.economy",      # ← Главный экономический модуль
            "cogs.errors",
            "cogs.admin",
            "cogs.utility",
            "cogs.voice_events",
            "cogs.casino",
        ]
        
        for cog in COGS:
            try:
                await self.load_extension(cog)
                print(f"    ✅ {cog} загружен")
            except Exception as e:
                print(f"    ❌ ОШИБКА загрузки {cog}:")
                traceback.print_exc()

        print(">>> Все cog'и обработаны.")

# ====================== БОТ ======================
bot = MortisBot()

# ====================== СТАТУС ======================
@tasks.loop(minutes=30)
async def keep_status():
    try:
        activity = discord.Activity(type=discord.ActivityType.watching, name="mortisplay.ru")
        await bot.change_presence(status=discord.Status.dnd, activity=activity)
        logger.info("🔄 Статус обновлён")
    except Exception as e:
        logger.error(f"❌ Ошибка в keep_status: {e}")

@keep_status.before_loop
async def before_keep_status():
    await bot.wait_until_ready()

# ====================== СОБЫТИЯ ======================
@bot.event
async def on_ready():
    print("=" * 50)
    print(f">>> {bot.user} ОНЛАЙН")
    print("=" * 50)

    # 1. Инициализация БД
    print(">>> [1/4] Проверка БД...")
    try:
        await asyncio.wait_for(init_databases(), timeout=15.0)
        print(">>> [1/4] БД готова")
    except Exception as e:
        print(f">>> [1/4] ОШИБКА БД: {e}")

    # 2. Синхронизация команд
    print(f">>> [2/4] Синхронизация команд на сервер {FULL_ACCESS_GUILD_ID}...")
    await asyncio.sleep(5)
    try:
        guild = discord.Object(id=FULL_ACCESS_GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f">>> [2/4] OK: {len(synced)} команд синхронизировано")
    except Exception as e:
        print(f">>> [2/4] ОШИБКА синхронизации: {e}")

    print("=" * 50)
    print(">>> БОТ ПОЛНОСТЬЮ РАБОТАЕТ")
    print("=" * 50)

# ====================== ЗАПУСК ======================
async def main():
    async with bot:
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            await bot.start(TOKEN)
        except Exception as e:
            print(f"❌ КРИТИЧНО: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("⏹️ Остановлено.")