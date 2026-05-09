import os
import logging
from dotenv import load_dotenv

# Загружаем .env файл
load_dotenv()

# ====================== ОСНОВНЫЕ НАСТРОЙКИ ======================
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN не найден в .env файле!")

OWNER_ID = 765476979792150549
FULL_ACCESS_GUILD_ID = 1474623510268739790

# Каналы и роли
MOD_LOG_CHANNEL_ID = 1475291899672657940
WELCOME_CHANNEL_ID = 1475048502370500639
GOODBYE_CHANNEL_ID = 1475048502370500639
TICKET_CATEGORY_ID = 1475334525344157807
TICKET_ARCHIVE_CHANNEL_ID = 1475338423513649347
SUPPORT_ROLE_ID = 1475331888163066029

# ====================== ПУТИ К ФАЙЛАМ ======================
DATA_DIR = "data"
ECONOMY_FILE = f"{DATA_DIR}/economy.json"
WARNINGS_FILE = f"{DATA_DIR}/warnings.json"
CASES_FILE = f"{DATA_DIR}/cases.json"
FAQ_FILE = f"{DATA_DIR}/faq.json"
TICKET_TEMPLATES_FILE = f"{DATA_DIR}/ticket_templates.json"

# ====================== ЭКОНОМИКА ======================
DAILY_COOLDOWN = 86400
MESSAGE_COOLDOWN = 60
TAX_THRESHOLD = 10000
TAX_RATE = 0.01
MORTIS_COIN_RATE = 2.0

# Автосохранение экономики (в секундах)
ECONOMY_AUTOSAVE_INTERVAL = 300  # 5 минут

# ====================== МОДЕРАЦИЯ ======================
WARN_AUTO_MUTE_THRESHOLD = 3
WARN_AUTO_LONG_MUTE_THRESHOLD = 6
WARN_AUTO_KICK_THRESHOLD = 10
WARN_EXPIRY_DAYS = 30

UNAUTHORIZED_CMD_LIMIT = 3
UNAUTHORIZED_MUTE_MINUTES = 1

# ====================== ТИКЕТЫ ======================
INACTIVE_TICKET_HOURS = 24

# ====================== ЛОГИРОВАНИЕ ======================
os.makedirs("logs", exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)   # ← Добавил создание папки data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8", mode="a"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MortisBot")

# ====================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ======================
def format_number(num: int | float) -> str:
    """Форматирует число с пробелами (1 000 000)"""
    return f"{int(num):,}".replace(",", " ")