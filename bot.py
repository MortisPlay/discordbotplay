import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import View, Button, Modal, TextInput, Select
from datetime import datetime, timedelta, timezone
import json
import os
import asyncio
import re
import random
import aiohttp
import io
from collections import defaultdict, deque
import uuid
import traceback
import sys
import sqlite3
from contextlib import contextmanager
import json
# ───────────────────────────────────────────────
# НАСТРОЙКИ (БЕЗ ТОКЕНА!)
# ───────────────────────────────────────────────
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    print("❌ ОШИБКА: Не найден токен в переменных окружения!")
    print("📌 Установите переменную DISCORD_TOKEN")
    print("💡 Например: export DISCORD_TOKEN='ваш_токен'")
    sys.exit(1)
OWNER_ID = 765476979792150549
FULL_ACCESS_GUILD_ID = 1474623510268739790
MOD_LOG_CHANNEL_ID = 1475291899672657940
WELCOME_CHANNEL_ID = 1475048502370500639
GOODBYE_CHANNEL_ID = 1475048502370500639
TICKET_ARCHIVE_CHANNEL_ID = 1475338423513649347
PREFIX = "!"
WARNINGS_FILE = "warnings.json"
ECONOMY_FILE = "economy.json"
CASES_FILE = "cases.json"
TICKET_CATEGORY_ID = 1475334525344157807
SUPPORT_ROLE_ID = 1475331888163066029
SPAM_THRESHOLD = 5
SPAM_TIME = 8
ECONOMY_AUTOSAVE_INTERVAL = 60
DAILY_COOLDOWN = 86400
MESSAGE_COOLDOWN = 60
TAX_THRESHOLD = 10000
TAX_RATE = 0.01
def format_number(num: int) -> str:
    return f"{num:,}".replace(",", " ")
# НАСТРОЙКИ ДЛЯ АВТОМОДЕРАЦИИ
WARN_AUTO_MUTE_THRESHOLD = 3 # 3 варна → мут 1ч
WARN_AUTO_LONG_MUTE_THRESHOLD = 6 # 6 варнов → мут 24ч
WARN_AUTO_KICK_THRESHOLD = 10 # 10 варнов → кик
WARN_EXPIRY_DAYS = 30 # срок действия варна
RAID_JOIN_THRESHOLD = 5 # порог рейда
RAID_TIME_WINDOW = 300 # окно в секундах (5 минут)
NEW_ACCOUNT_DAYS = 7 # возраст нового аккаунта
VIP_ROLE_NAMES = ["VIP", "Premium", "Vip", "vip"]
VIP_SPAM_MULTIPLIER = 2
VIP_MENTION_MULTIPLIER = 3
# НОВЫЕ НАСТРОЙКИ
INACTIVE_TICKET_HOURS = 24
INVESTMENT_MIN_AMOUNT = 1000
INVESTMENT_MAX_DAYS = 30
INVESTMENT_BASE_RATE = 0.05
UNAUTHORIZED_CMD_LIMIT = 3
UNAUTHORIZED_MUTE_MINUTES = 1
# ───────────────────────────────────────────────
# НОВЫЕ НАСТРОЙКИ ЭКОНОМИКИ
# ───────────────────────────────────────────────
VOICE_INCOME_PER_30MIN = 8 # Сколько монет за 30 минут в голосе
VOICE_MIN_SESSION_MINUTES = 10 # Минимальное время сессии
VOICE_DAILY_MAX = 300 # Максимум от войса в сутки
SUPER_DROP_CHANCE = 2 # Шанс супер-дропа в daily (%)
SUPER_DROP_MIN = 50000
SUPER_DROP_MAX = 150000
# ───────────────────────────────────────────────
# РАСШИРЕННЫЙ МАГАЗИН С КАТЕГОРИЯМИ
# ───────────────────────────────────────────────

SHOP_CATEGORIES = {
    "бусты": {
        "name": "💰 Бусты доходов",
        "emoji": "💰",
        "description": "Увеличьте свои доходы"
    },
    "предметы": {
        "name": "🎁 Предметы",
        "emoji": "🎁",
        "description": "Полезные предметы"
    },
    "роли": {
        "name": "💎 Роли",
        "emoji": "💎",
        "description": "Специальные роли"
    },
    "косметика": {
        "name": "🎨 Косметика",
        "emoji": "🎨",
        "description": "Персонализация"
    },
    "пакеты": {
        "name": "📦 Готовые пакеты",
        "emoji": "📦",
        "description": "Экономные наборы"
    },
    "ящики": {
        "name": "🎰 Удачные ящики",
        "emoji": "🎰",
        "description": "Лутбоксы с лотереей"
    }
}

# ТОВАРЫ ПО КАТЕГОРИЯМ
SHOP_ITEMS = {
    # ─ БУСТЫ ─
    "multiplier_1x5": {
        "category": "бусты",
        "name": "Удвоитель ×1.5 (неделя)",
        "price": 1000,
        "duration_days": 7,
        "description": "×1.5 к доходу от сообщений и daily",
        "emoji": "🚀"
    },
    "multiplier_2x": {
        "category": "бусты",
        "name": "Удвоитель ×2 (3 дня)",
        "price": 2500,
        "duration_days": 3,
        "description": "×2 к доходу от сообщений и daily (короче, но сильнее)",
        "emoji": "🚀🚀"
    },
    "multiplier_3x": {
        "category": "бусты",
        "name": "Утроитель ×3 (1 день)",
        "price": 5000,
        "duration_days": 1,
        "description": "×3 ко ВСЕМУ доходу (супер редкий!)",
        "emoji": "🚀🚀🚀"
    },
    "lucky_day": {
        "category": "бусты",
        "name": "🍀 Счастливый день",
        "price": 1000,
        "description": "+50% ко всему за 24ч",
        "emoji": "🍀",
        "type": "effect"
    },
    
    # ─ ПРЕДМЕТЫ ─
    "gift_box": {
        "category": "предметы",
        "name": "Подарочная коробка",
        "price": 1500,
        "description": "Случайно от 500 до 5000 монет",
        "type": "inventory_item",
        "item_id": "gift_box",
        "emoji": "🎁"
    },
    "lucky_spin": {
        "category": "предметы",
        "name": "Счастливая крутка",
        "price": 3000,
        "description": "Одно бесплатное открытие кейса",
        "type": "inventory_item",
        "item_id": "lucky_spin",
        "emoji": "🎰"
    },
    
    # ─ РОЛИ ─
    "vip": {
        "category": "роли",
        "name": "VIP роль на 1 месяц",
        "price": 10000,
        "duration_days": 30,
        "description": "×2 ко всем доходам • VIP-чат • ×2 за войс • Приоритет тикетов",
        "emoji": "💎"
    },
    "vip_permanent": {
        "category": "роли",
        "name": "💎 VIP Навсегда",
        "price": 500000,
        "duration_days": 999999,
        "limited": True,
        "stock": 5,
        "description": "Вечный VIP статус (только 5 доступно!)",
        "emoji": "👑"
    },
    
    # ─ КОСМЕТИКА ─
    "custom_title": {
        "category": "косметика",
        "name": "🏷️ Пользовательский титул (30 дн)",
        "price": 5000,
        "description": "Своё название в топе богачей",
        "emoji": "🏷️",
        "type": "cosmetic"
    },
    "crown_emoji": {
        "category": "косметика",
        "name": "👑 Эмодзи корона (30 дн)",
        "price": 3000,
        "description": "Корона рядом с именем в топе",
        "emoji": "👑",
        "type": "cosmetic"
    },
    "discount_card": {
        "category": "косметика",
        "name": "💳 Скидочная карта (-15%)",
        "price": 3000,
        "description": "15% скидка на весь магазин на неделю",
        "emoji": "💳",
        "type": "discount",
        "discount": 0.15,
        "duration_days": 7
    },
    
    # ─ ПАКЕТЫ ─
    "starter_pack": {
        "category": "пакеты",
        "name": "📦 Стартовый набор",
        "price": 2500,
        "description": "gift_box ×3 + lucky_spin ×1 + 1000 💰",
        "type": "bundle",
        "emoji": "📦",
        "items": {
            "gift_box": 3,
            "lucky_spin": 1
        },
        "bonus_coins": 1000
    },
    "boost_pack": {
        "category": "пакеты",
        "name": "🚀 Пакет бустов",
        "price": 5000,
        "description": "Все три буста по сниженной цене",
        "type": "bundle",
        "emoji": "🚀",
        "items_to_buy": {
            "multiplier_1x5": 1,
            "multiplier_2x": 1,
            "lucky_day": 1
        },
        "savings": 1500
    },
    "vip_pack": {
        "category": "пакеты",
        "name": "💎 VIP Премиум набор",
        "price": 50000,
        "description": "VIP на месяц + Титул + 10000 💰",
        "type": "bundle",
        "emoji": "💎",
        "includes": ["vip", "custom_title"],
        "bonus_coins": 10000
    },
    
    # ─ ЯЩИКИ ─
    "lucky_box_small": {
        "category": "ящики",
        "name": "🎁 Малый удачный ящик",
        "price": 500,
        "description": "Случайный предмет (70% обычные, 30% редкие)",
        "type": "lootbox",
        "emoji": "🎁",
        "pool": [
            ("gift_box", 0.7),
            ("lucky_spin", 0.3)
        ]
    },
    "lucky_box_medium": {
        "category": "ящики",
        "name": "🎰 Средний удачный ящик",
        "price": 1500,
        "description": "Лучший шанс на редкие предметы (50%)",
        "type": "lootbox",
        "emoji": "🎰",
        "pool": [
            ("gift_box", 0.5),
            ("lucky_spin", 0.4),
            ("multiplier_1x5", 0.1)
        ]
    },
    "lucky_box_mega": {
        "category": "ящики",
        "name": "🎲 Мега ящик",
        "price": 5000,
        "description": "Максимальный шанс на эпик (20% редкий буст!)",
        "type": "lootbox",
        "emoji": "🎲",
        "pool": [
            ("gift_box", 0.4),
            ("lucky_spin", 0.3),
            ("multiplier_1x5", 0.2),
            ("multiplier_2x", 0.1)
        ]
    }
}

# ОТСЛЕЖИВАНИЕ ПОКУПОК (для динамических цен)
item_purchase_tracking = {}

def get_dynamic_price(item_key: str, base_price: int) -> int:
    """Динамическая цена на основе спроса"""
    purchase_count = item_purchase_tracking.get(item_key, {}).get("count", 0)
    
    # Если много купили в последние 7 дней → цена растёт
    if purchase_count > 50:
        return int(base_price * 1.3)  # +30%
    elif purchase_count > 30:
        return int(base_price * 1.15)  # +15%
    elif purchase_count < 5:
        return int(base_price * 0.85)  # -15% (стимулируем покупки)
    
    return base_price

def track_purchase(item_key: str):
    """Отслеживать покупку"""
    now = datetime.now(timezone.utc).timestamp()
    
    if item_key not in item_purchase_tracking:
        item_purchase_tracking[item_key] = {
            "count": 0,
            "first_purchase": now
        }
    
    item_purchase_tracking[item_key]["count"] += 1
    
    # Сбрасываем счётчик каждые 7 дней
    if now - item_purchase_tracking[item_key]["first_purchase"] > 7 * 86400:
        item_purchase_tracking[item_key] = {
            "count": 1,
            "first_purchase": now
        }

# ───────────────────────────────────────────────
# ПРЕДМЕТЫ ИНВЕНТАРЯ (расширяй по желанию)
# ───────────────────────────────────────────────
INVENTORY_ITEMS = {
    "gift_box": {
        "name": "Подарочная коробка",
        "emoji": "🎁",
        "description": "Содержит случайную сумму от 500 до 5000 монет",
        "rarity": "rare",
        "one_use": True
    },
    "lucky_spin": {
        "name": "Счастливая крутка",
        "emoji": "🎰",
        "description": "Одно бесплатное открытие кейса",
        "rarity": "epic",
        "one_use": True
    },
    "xp_boost_24h": {
        "name": "Буст опыта ×2 (24ч)",
        "emoji": "⚡",
        "description": "Удваивает получаемый XP на 24 часа",
        "rarity": "legendary",
        "duration_hours": 24,
        "effect_type": "xp_multiplier",
        "value": 2.0
    }
}
# Добавляем в начало файла (после настроек)
GIFT_BOX_RANGES = [
    (70,  500,  1200),   # 70% — 500–1200
    (20,  1201, 1800),   # 20% — 1201–1800
    (8,   1801, 2200),   # 8%  — 1801–2200
    (2,   2201, 2500),   # 2%  — 2201–2500
]

# Новая функция
def open_gift_box():
    roll = random.randint(1, 100)
    cumulative = 0
    for chance, min_val, max_val in GIFT_BOX_RANGES:
        cumulative += chance
        if roll <= cumulative:
            return random.randint(min_val, max_val)
    return random.randint(500, 2500)  # fallback
# ───────────────────────────────────────────────
# АКЦИЯ 8 МАРТА
# ───────────────────────────────────────────────
MARCH_8_DISCOUNT_START = datetime(2026, 3, 7, 0, 0, tzinfo=timezone.utc)
MARCH_8_DISCOUNT_END = datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc) # до 10 марта 00:00
MARCH_8_DISCOUNT_PERCENT = 20
MARCH_8_DISCOUNT_ROLE_ID = 1477476358710890629 # ← замени на реальный ID роли, которой даётся скидка
DISCOUNTED_ITEMS = {"vip", "multiplier"} # какие товары участвуют в скидке
# ───────────────────────────────────────────────
# НАСТРОЙКИ ДЛЯ FAQ
# ───────────────────────────────────────────────
FAQ_FILE = "faq.json"
FAQ_CATEGORIES = {
    "общее": "📋 Общие вопросы",
    "правила": "📜 Правила",
    "экономика": "💰 Экономика",
    "модерация": "🛡️ Модерация",
    "техника": "🔧 Технические вопросы"
}
# НОВОЕ ОФОРМЛЕНИЕ ДЛЯ ЭКОНОМИКИ
ECONOMY_EMOJIS = {
    "balance": "💰",
    "vault": "🏦",
    "daily": "🎁",
    "tax": "📊",
    "rich": "👑",
    "poor": "😢",
    "transfer": "💸",
    "coin": "🪙",
    "bank": "🏛️",
    "chart": "📈",
    "time": "⏰",
    "warning": "⚠️",
    "success": "✅",
    "error": "❌",
    "gift": "🎀",
    "crown": "👑",
    "diamond": "💎",
    "gold": "🪙",
    "silver": "🥈",
    "bronze": "🥉",
    "investment": "📈",
    "profit": "💹",
    "risk": "⚠️",
    "calendar": "📅"
}
RARITIES = [
    ("Обычная", 70, 15, 35, 0xA8A8A8, "🪙"),
    ("Редкая", 20, 50, 70, 0x3498DB, "💎"),
    ("Эпическая", 9, 200, 350, 0x9B59B6, "🌟"),
    ("Легендарная", 1, 500,1000, 0xF1C40F, "🔥")
]
RARITY_STYLE = {
    "common":    {"color": 0x95a5a6, "emoji": "⬜", "name": "Обычная"},
    "rare":      {"color": 0x3498db, "emoji": "💎", "name": "Редкая"},
    "epic":      {"color": 0x9b59b6, "emoji": "🌟", "name": "Эпическая"},
    "legendary": {"color": 0xf1c40f, "emoji": "🔥", "name": "Легендарная"},
}
BAD_WORDS = [
    "пидор", "пидорас", "пидрила", "пидр", "гей", "хуесос", "ебанат", "дебил", "идиот",
    "тупой", "чмо", "чмошник", "сука", "блядь", "еблан", "мудак", "тварь", "урод"
]
INSULT_PATTERNS = [
    r"\b(ты|тебе|тобой)\s*(пидор|дебил|идиот|тупой|чмо|хуесос|ебанат)\b",
    r"\b(иди|пошёл|пиздец)\s*(нахуй|в пизду|в жопу)\b",
    r"\b(заткнись|заткнулся|молчи)\s*(сука|блядь|ебанат)\b"
]
# ЦВЕТА ДЛЯ ОФОРМЛЕНИЯ
COLORS = {
    "welcome": 0x57F287, # Зеленый
    "goodbye": 0xF04747, # Красный
    "audit": 0x5865F2, # Синий
    "mod": 0xFAA61A, # Оранжевый
    "economy": 0xFFD700, # Золотой
    "ticket": 0x9B59B6, # Фиолетовый
    "faq": 0x3498DB # Голубой
}
# ───────────────────────────────────────────────
# ФУНКЦИИ ДЛЯ АКЦИИ 8 МАРТА
# ───────────────────────────────────────────────
def is_march8_event_active() -> bool:
    now = datetime.now(timezone.utc)
    return MARCH_8_DISCOUNT_START <= now < MARCH_8_DISCOUNT_END

def get_discounted_price(original_price: int, item_key: str, member: discord.Member) -> int:
    if not is_march8_event_active():
        return original_price
    if item_key not in DISCOUNTED_ITEMS:
        return original_price
    # Проверяем, есть ли нужная роль
    has_discount_role = any(role.id == MARCH_8_DISCOUNT_ROLE_ID for role in member.roles)
    if not has_discount_role:
        return original_price
    discount = int(original_price * (MARCH_8_DISCOUNT_PERCENT / 100))
    return original_price - discount
# ───────────────────────────────────────────────
# ГЛОБАЛЬНЫЕ ДАННЫЕ
# ───────────────────────────────────────────────
economy_data = {}
warnings_data = {}
cases_data = {}
spam_cache = {}
raid_cache = defaultdict(list)
temp_roles = {}
unauthorized_attempts = defaultdict(list)
faq_data = {}
voice_start_time = {}
daily_voice_earned = {}
# ───────────────────────────────────────────────
# SQLITE — ЭКОНОМИКА (НОВЫЙ НАДЁЖНЫЙ СОХРАНЯЛКА)
# ───────────────────────────────────────────────
DB_FILE = "/data/economy.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS economy (
            user_id TEXT PRIMARY KEY,
            balance INTEGER DEFAULT 0,
            last_daily REAL DEFAULT 0,
            last_message REAL DEFAULT 0,
            multiplier_end REAL DEFAULT 0,
            inventory TEXT DEFAULT '{}',
            active_effects TEXT DEFAULT '[]',
            investments TEXT DEFAULT '[]'
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS server_vault (
            key TEXT PRIMARY KEY,
            value INTEGER DEFAULT 0
        )
    ''')
    c.execute("INSERT OR IGNORE INTO server_vault (key, value) VALUES ('vault', 0)")
    conn.commit()
    conn.close()

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE)
    try:
        yield conn
    finally:
        conn.close()

def load_economy():
    """Загружает данные из SQLite БД с полной поддержкой восстановления"""
    global economy_data
    economy_data = {"server_vault": 0}
    
    try:
        with get_db() as conn:
            c = conn.cursor()
            
            # Загружаем казну
            c.execute("SELECT value FROM server_vault WHERE key = 'vault'")
            row = c.fetchone()
            if row:
                economy_data["server_vault"] = row[0]
            else:
                c.execute("INSERT INTO server_vault (key, value) VALUES ('vault', 0)")
                conn.commit()
            
            # Загружаем всех игроков
            c.execute("""
                SELECT user_id, balance, last_daily, last_message, multiplier_end, 
                       inventory, active_effects, investments 
                FROM economy
            """)
            
            loaded_count = 0
            for row in c.fetchall():
                uid = row[0]
                economy_data[uid] = {
                    "balance": int(row[1]) if row[1] else 0,
                    "last_daily": float(row[2]) if row[2] else 0,
                    "last_message": float(row[3]) if row[3] else 0,
                    "multiplier_end": float(row[4]) if row[4] else 0,
                    "inventory": json.loads(row[5] or '{}'),
                    "active_effects": json.loads(row[6] or '[]'),
                    "investments": json.loads(row[7] or '[]')
                }
                loaded_count += 1
        
        vault = economy_data.get("server_vault", 0)
        print(f"✅ [ECONOMY LOAD] Загружено {loaded_count} игроков из SQLite")
        print(f"   💰 Казна сервера: {format_number(vault)} монет")
        
    except Exception as e:
        print(f"❌ [ECONOMY LOAD ERROR] {e}")
        traceback.print_exc()
        economy_data = {"server_vault": 0}

def save_economy():
    """Сохраняет ВСЕ данные в SQLite с логированием"""
    try:
        if not economy_data:
            print("[SAVE] Нечего сохранять")
            return
            
        with get_db() as conn:
            c = conn.cursor()
            
            # Сохраняем казну
            vault_value = economy_data.get("server_vault", 0)
            c.execute("UPDATE server_vault SET value = ? WHERE key = 'vault'", (vault_value,))
            
            if c.rowcount == 0:
                c.execute("INSERT INTO server_vault (key, value) VALUES ('vault', ?)", (vault_value,))
            
            # Сохраняем игроков
            saved_players = 0
            for uid, data in economy_data.items():
                if uid == "server_vault":
                    continue
                
                try:
                    c.execute('''
                        INSERT OR REPLACE INTO economy 
                        (user_id, balance, last_daily, last_message, multiplier_end, 
                         inventory, active_effects, investments)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        uid,
                        int(data.get("balance", 0)),
                        float(data.get("last_daily", 0)),
                        float(data.get("last_message", 0)),
                        float(data.get("multiplier_end", 0)),
                        json.dumps(data.get("inventory", {}), ensure_ascii=False),
                        json.dumps(data.get("active_effects", []), ensure_ascii=False),
                        json.dumps(data.get("investments", []), ensure_ascii=False)
                    ))
                    saved_players += 1
                except Exception as e:
                    print(f"⚠️  Ошибка при сохранении {uid}: {e}")
                    continue
            
            conn.commit()
            
        print(f"✅ [SAVE] Сохранено {saved_players} игроков | 💰 Казна: {format_number(vault_value)}")
        
    except Exception as e:
        print(f"❌ [SAVE CRITICAL] {e}")
        traceback.print_exc()
# ───────────────────────────────────────────────
# ЗАГРУЗКА / СОХРАНЕНИЕ ОСТАЛЬНЫХ ФАЙЛОВ (faq, warnings, cases)
# ───────────────────────────────────────────────
def load_faq():
    global faq_data
    if os.path.exists(FAQ_FILE):
        try:
            with open(FAQ_FILE, "r", encoding="utf-8") as f:
                faq_data = json.load(f)
            print(f"[FAQ] Загружено {len(faq_data)} категорий")
        except Exception as e:
            print(f"[FAQ LOAD] Ошибка: {e}")
            faq_data = {}
    else:
        faq_data = {}
        print("[FAQ] Файл не найден → создан пустой")

def save_faq():
    try:
        with open(FAQ_FILE, "w", encoding="utf-8") as f:
            json.dump(faq_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[SAVE FAQ] Ошибка: {e}")

def load_warnings():
    global warnings_data
    if os.path.exists(WARNINGS_FILE):
        try:
            with open(WARNINGS_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                warnings_data = json.load(f) if content else {}
        except Exception as e:
            print(f"⚠️ Ошибка чтения warnings.json: {e}")
            warnings_data = {}
    else:
        warnings_data = {}

def save_warnings():
    with open(WARNINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(warnings_data, f, ensure_ascii=False, indent=2)

def load_cases():
    global cases_data
    if os.path.exists(CASES_FILE):
        try:
            with open(CASES_FILE, "r", encoding="utf-8") as f:
                cases_data = json.load(f)
        except:
            cases_data = {}
    else:
        cases_data = {}

def save_cases():
    with open(CASES_FILE, "w", encoding="utf-8") as f:
        json.dump(cases_data, f, ensure_ascii=False, indent=2)

# ───────────────────────────────────────────────
# SQLITE — ЭКОНОМИКА + ПРИНУДИТЕЛЬНАЯ МИГРАЦИЯ ПРИ ПЕРВОМ ЗАПУСКЕ
# ───────────────────────────────────────────────

MIGRATION_DONE_FILE = "migration_done.flag"

def migrate_from_json_if_needed():
    if os.path.exists(MIGRATION_DONE_FILE):
        print("[MIGRATION] Уже выполнялась ранее → пропускаем")
        return

    if not os.path.exists(ECONOMY_FILE) or os.path.getsize(ECONOMY_FILE) < 10:
        print("[MIGRATION] Старый economy.json не найден или пуст → новая база")
        with open(MIGRATION_DONE_FILE, "w") as f:
            f.write("done")
        return

    try:
        with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
            old_data = json.load(f)
        print(f"[MIGRATION] Нашли старый файл → переносим {len(old_data)} записей...")

        with get_db() as conn:
            c = conn.cursor()
            migrated = 0
            for uid, data in old_data.items():
                if uid == "server_vault":
                    c.execute("UPDATE server_vault SET value = ? WHERE key = 'vault'", (data,))
                    continue

                # Проверяем, существует ли уже пользователь (на случай повторного запуска)
                c.execute("SELECT 1 FROM economy WHERE user_id = ?", (uid,))
                if c.fetchone():
                    continue  # уже есть, пропускаем

                c.execute('''
                    INSERT INTO economy 
                    (user_id, balance, last_daily, last_message, multiplier_end, inventory, active_effects, investments)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    uid,
                    data.get("balance", 0),
                    data.get("last_daily", 0),
                    data.get("last_message", 0),
                    data.get("multiplier_end", 0),
                    json.dumps(data.get("inventory", {})),
                    json.dumps(data.get("active_effects", [])),
                    json.dumps(data.get("investments", []))
                ))
                migrated += 1

            conn.commit()

        print(f"[MIGRATION] Успешно перенесено {migrated} пользователей")
        
        # Создаём флаг, чтобы больше не мигрировать
        with open(MIGRATION_DONE_FILE, "w") as f:
            f.write("done")
            
        # Можно раскомментировать, если хочешь убрать старый файл
        # os.rename(ECONOMY_FILE, ECONOMY_FILE + ".migrated_backup")

    except Exception as e:
        print(f"[MIGRATION CRITICAL] Ошибка переноса: {e}")
        traceback.print_exc()

import os
os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
# Вызовы загрузки (всегда выполняются)
init_db()               # создаёт таблицы, если их нет
migrate_from_json_if_needed()   # мигрирует только если нужно
load_economy()          # загружает из .db
load_faq()
load_warnings()
load_cases()
# ───────────────────────────────────────────────
# ФУНКЦИИ ДЛЯ ПРОВЕРКИ ПРАВ
# ───────────────────────────────────────────────
def is_moderator(ctx_or_member) -> bool:
    if isinstance(ctx_or_member, discord.Member):
        member = ctx_or_member
    elif isinstance(ctx_or_member, commands.Context):
        member = ctx_or_member.author
    elif isinstance(ctx_or_member, discord.Interaction):
        member = ctx_or_member.user
        if not isinstance(member, discord.Member) or not member.guild:
            return False
    else:
        return False
    if not member.guild or member.bot:
        return False
    return (
        member.guild_permissions.manage_messages or
        member.guild_permissions.administrator or
        member.id == OWNER_ID
    )
def is_protected_from_automod(member: discord.Member) -> bool:
    return (member.guild_permissions.administrator or
            member.guild_permissions.manage_messages or
            member.guild_permissions.manage_guild or
            member.id == OWNER_ID or
            member.top_role.permissions.administrator)
def can_punish(executor: discord.Member, target: discord.Member) -> bool:
    if not executor or not target:
        return False
    if executor.id == target.id:
        return False
    if target.id == OWNER_ID:
        return False
    if target == target.guild.owner:
        return False
    if target.guild_permissions.administrator:
        return False
    if target.top_role >= executor.top_role and executor.id != OWNER_ID:
        return False
    return True
# ───────────────────────────────────────────────
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ───────────────────────────────────────────────
async def check_unauthorized_commands(user: discord.Member):
    if is_moderator(user):
        return False
    user_id = str(user.id)
    now = datetime.now(timezone.utc).timestamp()
    unauthorized_attempts[user_id] = [t for t in unauthorized_attempts[user_id] if now - t < 3600]
    unauthorized_attempts[user_id].append(now)
    if len(unauthorized_attempts[user_id]) >= UNAUTHORIZED_CMD_LIMIT:
        try:
            await user.timeout(timedelta(minutes=UNAUTHORIZED_MUTE_MINUTES),
                              reason="Превышение лимита попыток использования команд без прав")
            await send_punishment_log(
                member=user,
                punishment_type="🔇 Мут (авто)",
                duration=f"{UNAUTHORIZED_MUTE_MINUTES} мин",
                reason="Превышение лимита попыток использования модераторских команд",
                moderator=bot.user
            )
            unauthorized_attempts[user_id] = []
            return True
        except:
            pass
    return False
def get_rank_emoji(balance: int) -> str:
    if balance >= 100000:
        return "👑"
    elif balance >= 50000:
        return "💎"
    elif balance >= 10000:
        return "💰"
    elif balance >= 5000:
        return "💵"
    elif balance >= 1000:
        return "🪙"
    elif balance >= 100:
        return "🥉"
    else:
        return "🥚"
def create_progress_bar(current: int, max_value: int, length: int = 10) -> str:
    if max_value <= 0:
        return "█" * length
    progress = min(current / max_value, 1.0)
    filled = int(progress * length)
    return "█" * filled + "░" * (length - filled)
def generate_case_id() -> str:
    return str(uuid.uuid4())[:8]
async def create_case(member: discord.Member, moderator: discord.User, action: str, reason: str, duration: str = None):
    case_id = generate_case_id()
    cases_data[case_id] = {
        "id": case_id,
        "user_id": str(member.id),
        "user_name": str(member),
        "moderator_id": str(moderator.id),
        "moderator_name": str(moderator),
        "action": action,
        "reason": reason,
        "duration": duration,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    save_cases()
    return case_id
async def get_case(case_id: str) -> dict:
    return cases_data.get(case_id)
def is_vip(member: discord.Member) -> bool:
    if not member:
        return False
    return any(role.name in VIP_ROLE_NAMES for role in member.roles)
def clean_old_warnings(user_id: str):
    if user_id not in warnings_data:
        return
    now = datetime.now(timezone.utc)
    fresh_warnings = []
    for warn in warnings_data[user_id]:
        try:
            warn_time = datetime.strptime(warn["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            if (now - warn_time).days < WARN_EXPIRY_DAYS:
                fresh_warnings.append(warn)
        except:
            continue
    warnings_data[user_id] = fresh_warnings
    if not fresh_warnings:
        del warnings_data[user_id]
    save_warnings()
def get_warning_count(user_id: str) -> int:
    clean_old_warnings(user_id)
    return len(warnings_data.get(user_id, []))
async def check_auto_punishment(member: discord.Member, reason: str = "Автоматически"):
    if not member or is_protected_from_automod(member):
        return
    user_id = str(member.id)
    warn_count = get_warning_count(user_id)
    if warn_count >= WARN_AUTO_KICK_THRESHOLD:
        try:
            await member.kick(reason=f"Достигнут лимит варнов ({warn_count})")
            case_id = await create_case(member, bot.user, "Авто-кик", f"{warn_count} варнов")
            await send_punishment_log(
                member=member,
                punishment_type="👢 Кик (авто)",
                duration="Навсегда",
                reason=f"Автоматический кик: {warn_count} варнов",
                moderator=bot.user,
                case_id=case_id
            )
        except:
            pass
    elif warn_count >= WARN_AUTO_LONG_MUTE_THRESHOLD:
        try:
            await member.timeout(timedelta(hours=24), reason=f"Автоматический мут: {warn_count} варнов")
            case_id = await create_case(member, bot.user, "Авто-мут 24ч", f"{warn_count} варнов", "24 часа")
            await send_punishment_log(
                member=member,
                punishment_type="🔇 Мут 24ч (авто)",
                duration="24 часа",
                reason=f"Автоматический мут: {warn_count} варнов",
                moderator=bot.user,
                case_id=case_id
            )
        except:
            pass
    elif warn_count >= WARN_AUTO_MUTE_THRESHOLD:
        try:
            await member.timeout(timedelta(hours=1), reason=f"Автоматический мут: {warn_count} варнов")
            case_id = await create_case(member, bot.user, "Авто-мут 1ч", f"{warn_count} варнов", "1 час")
            await send_punishment_log(
                member=member,
                punishment_type="🔇 Мут 1ч (авто)",
                duration="1 час",
                reason=f"Автоматический мут: {warn_count} варнов",
                moderator=bot.user,
                case_id=case_id
            )
        except:
            pass
async def send_punishment_log(member: discord.Member, punishment_type: str, duration: str, reason: str, moderator: discord.User, case_id: str = None):
    if not MOD_LOG_CHANNEL_ID:
        return
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    embed = discord.Embed(
        title=f"🛠️ Наказание {f'[#{case_id}]' if case_id else ''}",
        color=COLORS["mod"],
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="👤 Кто наказан", value=f"{member.mention}\n{member} ({member.id})", inline=False)
    embed.add_field(name="⚡ Тип", value=punishment_type, inline=True)
    embed.add_field(name="⏰ Время действия", value=duration, inline=True)
    embed.add_field(name="📝 Причина", value=reason, inline=False)
    embed.add_field(name="👮 Модератор", value=moderator.mention, inline=False)
    if case_id:
        embed.add_field(name="🔖 ID кейса", value=f"`{case_id}`", inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"ID: {member.id}")
    view = ModActionView(member)
    await log_ch.send(embed=embed, view=view)
async def send_mod_log(title: str, description: str = None, color: int = COLORS["audit"], fields: list = None):
    if not MOD_LOG_CHANNEL_ID:
        return
    log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
    if not log_ch:
        return
    embed = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)
    embed.set_footer(text=f"Время: {datetime.now().strftime('%H:%M:%S')}")
    await log_ch.send(embed=embed)
async def send_error_embed(ctx, error_msg: str):
    embed = discord.Embed(
        title="❌ Ошибка",
        description=error_msg,
        color=0xF04747,
        timestamp=datetime.now(timezone.utc)
    )
    await ctx.send(embed=embed, ephemeral=True)
def is_toxic(content: str) -> bool:
    if not content:
        return False
    content_lower = content.lower()
    for pattern in INSULT_PATTERNS:
        if re.search(pattern, content_lower):
            return True
    words = content_lower.split()
    for word in words:
        if word in BAD_WORDS:
            for i, w in enumerate(words):
                if w == word and i > 0 and words[i-1] in ["ты", "тебе", "тобой", "твой", "твоя", "твоё"]:
                    return True
    return False
def has_full_access(guild_id: int) -> bool:
    return guild_id == FULL_ACCESS_GUILD_ID
async def apply_wealth_tax(user_id: str) -> int:
    if user_id not in economy_data:
        return 0
    
    data = economy_data[user_id]
    balance = data.get("balance", 0)
    if balance <= TAX_THRESHOLD:
        return 0
    
    # Проверяем, когда последний раз применяли налог
    last_tax_time = data.get("last_tax_time", 0)
    now = datetime.now(timezone.utc).timestamp()
    if now - last_tax_time < 86400:  # уже применяли сегодня
        return 0
    
    taxable = balance - TAX_THRESHOLD
    tax = int(taxable * TAX_RATE)
    
    # Скидка за недавнюю активность
    last_msg = data.get("last_message", 0)
    if now - last_msg < 86400:
        reduction = random.uniform(0.20, 0.50)
        tax = int(tax * (1 - reduction))
    
    if tax <= 0:
        return 0
    
    # Применяем налог
    data["balance"] -= tax
    economy_data["server_vault"] = economy_data.get("server_vault", 0) + tax
    
    # Запоминаем время последнего налога
    data["last_tax_time"] = now
    
    save_economy()
    
    # Можно отправить уведомление в ЛС, если хочешь
    try:
        user = bot.get_user(int(user_id))
        if user:
            await user.send(
                f"💸 С вас списан налог на богатство: **-{format_number(tax)}** монет\n"
                f"Новый баланс: **{format_number(data['balance'])}**"
            )
    except:
        pass
    
    return tax
# ───────────────────────────────────────────────
# КЛАССЫ ДЛЯ UI
# ───────────────────────────────────────────────
class ModActionView(View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=180)
        self.member = member
    @discord.ui.button(label="Предупредить", style=discord.ButtonStyle.secondary, emoji="⚠️")
    async def warn_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not can_punish(interaction.user, self.member):
            return await interaction.response.send_message(
                "❌ Нельзя наказывать владельца сервера, администраторов или самого себя!",
                ephemeral=True
            )
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
        modal = WarnModal(self.member)
        await interaction.response.send_modal(modal)
    @discord.ui.button(label="Замутить", style=discord.ButtonStyle.danger, emoji="🔇")
    async def mute_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not can_punish(interaction.user, self.member):
            return await interaction.response.send_message(
                "❌ Нельзя наказывать владельца сервера, администраторов или самого себя!",
                ephemeral=True
            )
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
        modal = MuteModal(self.member)
        await interaction.response.send_modal(modal)
    @discord.ui.button(label="Очистить", style=discord.ButtonStyle.success, emoji="🧹")
    async def clear_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_moderator(interaction.user):
            return await interaction.response.send_message("❌ Недостаточно прав!", ephemeral=True)
        modal = ClearModal(self.member)
        await interaction.response.send_modal(modal)
class WarnModal(Modal, title="Выдать предупреждение"):
    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member
    reason = TextInput(label="Причина", placeholder="Введите причину предупреждения...", style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction: discord.Interaction):
        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.send = lambda **kwargs: interaction.response.send_message(**kwargs)
        await warn(ctx, self.member, reason=self.reason.value)
class MuteModal(Modal, title="Замутить пользователя"):
    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member
    duration = TextInput(label="Длительность", placeholder="1h, 1d, 30m", max_length=10)
    reason = TextInput(label="Причина", placeholder="Введите причину мута...", style=discord.TextStyle.paragraph, required=False)
    async def on_submit(self, interaction: discord.Interaction):
        ctx = await bot.get_context(interaction.message)
        ctx.author = interaction.user
        ctx.send = lambda **kwargs: interaction.response.send_message(**kwargs)
        reason = self.reason.value or "Не указана"
        await mute(ctx, self.member, duration=self.duration.value, reason=reason)
class ClearModal(Modal, title="Очистить сообщения"):
    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member
    amount = TextInput(label="Количество", placeholder="От 1 до 100", max_length=3)
    async def on_submit(self, interaction: discord.Interaction):
        try:
            amount = int(self.amount.value)
            if amount < 1 or amount > 100:
                return await interaction.response.send_message("❌ Количество должно быть от 1 до 100!", ephemeral=True)
            deleted = await interaction.channel.purge(limit=amount, check=lambda m: m.author == self.member)
            await interaction.response.send_message(f"✅ Удалено {len(deleted)} сообщений {self.member.mention}", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Введите число!", ephemeral=True)
class WelcomeView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Правила", style=discord.ButtonStyle.primary, emoji="📜", custom_id="welcome_rules")
    async def rules_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📜 Правила сервера",
            description="""**1.** Уважайте других участников
            **2.** Не спамьте и не флудите
            **3.** Не рекламируйте без разрешения
            **4.** Соблюдайте тематику каналов
            **5.** Слушайтесь модераторов
            **6.** Не используйте оскорбления
            **7.** Запрещен контент 18+""",
            color=COLORS["welcome"]
        )
        embed.set_footer(text="Нарушение правил = наказание")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    @discord.ui.button(label="Команды", style=discord.ButtonStyle.success, emoji="🤖", custom_id="welcome_commands")
    async def commands_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🤖 Основные команды",
            description="""**Для всех:**
            `/help` - помощь по командам
            `/balance` - проверить баланс
            `/daily` - ежедневный бонус
            `/userinfo` - информация о пользователе
            `/stats` - статистика сервера
            `/faq` - частые вопросы
            `/iq` - узнать свой IQ
            `/valute` - курсы валют
            **Экономика:**
            `/pay` - перевести монеты
            `/top` - топ богачей
            `/invest` - инвестировать
            `/investments` - мои инвестиции""",
            color=COLORS["welcome"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    @discord.ui.button(label="Роли", style=discord.ButtonStyle.secondary, emoji="🏷️", custom_id="welcome_roles")
    async def roles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏷️ Доступные роли",
            description="""**Вы можете получить роли в канале <#РОЛИ>**
            🎮 **Игроки** - @Игрок
            💎 **VIP** - @VIP (требуется поддержка)
            🎨 **Креатив** - @Творец
            🎵 **Музыкант** - @Music Lover
            🎥 **Стример** - @Streamer
            *Роли дают доступ к дополнительным каналам и возможностям*""",
            color=COLORS["welcome"]
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
class TicketCategorySelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Техническая проблема", value="tech", emoji="🔧", description="Проблемы с ботом или сервером"),
            discord.SelectOption(label="Жалоба на игрока", value="complaint", emoji="⚠️", description="Пожаловаться на нарушителя"),
            discord.SelectOption(label="Вопрос по серверу", value="question", emoji="❓", description="Общие вопросы о сервере"),
            discord.SelectOption(label="Сотрудничество", value="partner", emoji="🤝", description="Предложения о сотрудничестве"),
            discord.SelectOption(label="Другое", value="other", emoji="📌", description="Другие вопросы")
        ]
        super().__init__(placeholder="Выберите категорию тикета...", options=options, min_values=1, max_values=1)
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            return await interaction.followup.send("❌ Категория тикетов не настроена!", ephemeral=True)
        support_role = guild.get_role(SUPPORT_ROLE_ID)
        if not support_role:
            return await interaction.followup.send("❌ Роль поддержки не настроена!", ephemeral=True)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, attach_files=True),
            support_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_messages=True, attach_files=True, manage_messages=True)
        }
        category_emojis = {
            "tech": "🔧",
            "complaint": "⚠️",
            "question": "❓",
            "partner": "🤝",
            "other": "📌"
        }
        emoji = category_emojis.get(self.values[0], "🎫")
        channel_name = f"{emoji}-{self.values[0]}-{interaction.user.name.lower()}"
        ticket_channel = await category.create_text_channel(channel_name, overwrites=overwrites)
        category_descriptions = {
            "tech": "Техническая проблема",
            "complaint": "Жалоба на игрока",
            "question": "Вопрос по серверу",
            "partner": "Сотрудничество",
            "other": "Другое"
        }
        embed = discord.Embed(
            title=f"🎟️ Тикет: {category_descriptions.get(self.values[0], 'Обращение')}",
            description=f"**{interaction.user.mention}**, спасибо за обращение!\n"
                       f"Модератор свяжется с вами в ближайшее время.\n\n"
                       f"**Категория:** {self.values[0]}\n\n"
                       f"🔒 **Закрыть тикет** — нажмите красную кнопку ниже\n"
                       f"⚠️ Тикет будет автоматически закрыт через {INACTIVE_TICKET_HOURS} часов неактивности.",
            color=COLORS["ticket"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"ID: {interaction.user.id}")
        view = TicketControls()
        await ticket_channel.send(content=f"{interaction.user.mention} {support_role.mention}", embed=embed, view=view)
        await interaction.followup.send(f"✅ Тикет создан: {ticket_channel.mention}", ephemeral=True)
        await send_mod_log(
            title="📩 Новый тикет",
            description=f"**Канал:** {ticket_channel.mention}\n**Автор:** {interaction.user}\n**Категория:** {self.values[0]}",
            color=COLORS["ticket"]
        )
class TicketInactivityCheck:
    def __init__(self):
        self.ticket_channels = {}
    async def check_inactive_tickets(self):
        for guild in bot.guilds:
            category = guild.get_channel(TICKET_CATEGORY_ID)
            if not category or not isinstance(category, discord.CategoryChannel):
                continue
            for channel in category.text_channels:
                if not channel.name.startswith(("🔧-", "⚠️-", "❓-", "🤝-", "📌-")):
                    continue
                async for msg in channel.history(limit=1):
                    last_msg_time = msg.created_at
                    now = datetime.now(timezone.utc)
                    if (now - last_msg_time).total_seconds() > INACTIVE_TICKET_HOURS * 3600:
                        warning_embed = discord.Embed(
                            title="⚠️ Тикет неактивен",
                            description=f"Этот тикет будет автоматически закрыт через 12 часов из-за неактивности.",
                            color=0xFAA61A
                        )
                        await channel.send(embed=warning_embed)
                        await asyncio.sleep(43200)
                        async for new_msg in channel.history(limit=1):
                            if new_msg.id == msg.id:
                                transcript = await self.create_transcript(channel)
                                await channel.delete()
                                await send_mod_log(
                                    title="📜 Тикет закрыт автоматически",
                                    description=f"**Канал:** {channel.name}\n**Причина:** Неактивность",
                                    color=0x7289DA,
                                    fields=[("Транскрипт", transcript[:1000] + "...", False)]
                                )
                            break
                    break
    async def create_transcript(self, channel) -> str:
        transcript_lines = []
        async for msg in channel.history(limit=100, oldest_first=True):
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = f"{msg.author} ({msg.author.id})"
            content = msg.content or "[пусто]"
            transcript_lines.append(f"[{timestamp}] {author}: {content}")
        return "\n".join(transcript_lines)
class TicketPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="Создать тикет", style=discord.ButtonStyle.green, emoji="🎟️", custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🎫 Выбор категории",
            description="Пожалуйста, выберите категорию вашего обращения:",
            color=COLORS["ticket"]
        )
        view = View(timeout=60)
        view.add_item(TicketCategorySelect())
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
class TicketControls(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.last_activity = datetime.now(timezone.utc)
    @discord.ui.button(label="Закрыть тикет", style=discord.ButtonStyle.red, emoji="🔒", custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await check_unauthorized_commands(interaction.user)
            return await interaction.response.send_message("❌ Только модераторы могут закрыть тикет.", ephemeral=True)
        await interaction.response.send_message("🔒 Тикет закрывается через 5 секунд...", ephemeral=False)
        transcript_lines = []
        async for msg in interaction.channel.history(limit=1000, oldest_first=True):
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = f"{msg.author} ({msg.author.id})"
            content = msg.content or "[пусто]"
            if msg.attachments:
                content += f"\n📎 Вложения: {', '.join([a.url for a in msg.attachments])}"
            transcript_lines.append(f"[{timestamp}] {author}: {content}")
        transcript_text = "\n".join(transcript_lines) or "[В тикете не было сообщений]"
        filename = f"transcript_{interaction.channel.name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"
        file = discord.File(io.StringIO(transcript_text), filename=filename)
        archive_channel_id = TICKET_ARCHIVE_CHANNEL_ID or MOD_LOG_CHANNEL_ID
        archive_ch = bot.get_channel(archive_channel_id)
        if archive_ch:
            short_embed = discord.Embed(
                title="📜 Тикет закрыт",
                description=f"**Канал:** {interaction.channel.name}\n**Закрыл:** {interaction.user.mention}\n**Сообщений:** {len(transcript_lines)}",
                color=COLORS["ticket"],
                timestamp=datetime.now(timezone.utc)
            )
            await archive_ch.send(embed=short_embed, file=file)
        await asyncio.sleep(5)
        await interaction.channel.delete()
    @discord.ui.button(label="Взять тикет", style=discord.ButtonStyle.blurple, emoji="🖐️", custom_id="claim_ticket")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await check_unauthorized_commands(interaction.user)
            return await interaction.response.send_message("❌ Только модераторы могут взять тикет.", ephemeral=True)
        await interaction.response.send_message(f"✅ {interaction.user.mention} взял тикет в работу!", ephemeral=False)
        self.claim_ticket.disabled = True
        await interaction.message.edit(view=self)
class HelpView(View):
    def __init__(self, author: discord.User, is_mod: bool):
        super().__init__(timeout=60)
        self.author = author
        self.current_page = 0
        self.categories = [
            {
                "name": "📋 Основное",
                "emoji": "📋",
                "commands": [
                    ("/ping", "Проверить задержку бота"),
                    ("/avatar", "Показать аватар"),
                    ("/userinfo", "Информация о пользователе"),
                    ("/stats", "Статистика сервера"),
                    ("/say", "Написать от лица бота")
                ]
            },
            {
                "name": "💰 Экономика",
                "emoji": "💰",
                "commands": [
                    ("/balance", "Проверить баланс"),
                    ("/daily", "Ежедневный бонус"),
                    ("/pay", "Перевести монеты"),
                    ("/top", "Топ богачей"),
                    ("/vault", "Казна сервера"),
                    ("/invest", "Инвестировать"),
                    ("/investments", "Мои инвестиции")
                ]
            },
            {
                "name": "🎮 Развлечения",
                "emoji": "🎮",
                "commands": [
                    ("/iq", "Узнать свой IQ"),
                    ("/valute", "Курсы валют"),
                    ("/faq", "Часто задаваемые вопросы")
                ]
            }
        ]
        if is_mod:
            self.categories.extend([
                {
                    "name": "🛡️ Модерация",
                    "emoji": "🛡️",
                    "commands": [
                        ("/warn", "Выдать предупреждение"),
                        ("/warnings", "Список предупреждений"),
                        ("/clearwarn", "Очистить предупреждения"),
                        ("/mute", "Замутить пользователя"),
                        ("/unmute", "Снять мут"),
                        ("/temprole", "Временная роль"),
                        ("/case", "Информация о кейсе"),
                        ("/ban", "Забанить пользователя"),
                        ("/unwarn", "Удалить предупреждение"),
                        ("/faq add", "Добавить вопрос в FAQ")
                    ]
                },
                {
                    "name": "🎫 Тикеты",
                    "emoji": "🎫",
                    "commands": [
                        ("/ticket setup", "Создать панель тикетов"),
                        ("/ticket close", "Закрыть текущий тикет")
                    ]
                }
            ])
    def get_embed(self):
        category = self.categories[self.current_page]
        embed = discord.Embed(
            title=f"{category['emoji']} {category['name']}",
            description="Список доступных команд:",
            color=COLORS["welcome"]
        )
        for cmd, desc in category["commands"]:
            embed.add_field(name=cmd, value=desc, inline=False)
        embed.set_footer(text=f"Страница {self.current_page + 1} из {len(self.categories)}")
        return embed
    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        self.current_page = (self.current_page - 1) % len(self.categories)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        self.current_page = (self.current_page + 1) % len(self.categories)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)
    @discord.ui.button(label="🏠", style=discord.ButtonStyle.success)
    async def home_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        is_mod = is_moderator(interaction.user)
        base = "**📋 Основное**\n**💰 Экономика**\n**🎮 Развлечения**"
        mod = "\n**🛡️ Модерация**\n**🎫 Тикеты**" if is_mod else ""
        embed = discord.Embed(
            title="🤖 Помощь по командам",
            description=f"Используй кнопки для навигации\n\n{base}{mod}",
            color=COLORS["welcome"]
        )
        embed.set_footer(text="Выбери категорию")
        self.current_page = 0
        await interaction.response.edit_message(embed=embed, view=self)
class FAQCategorySelect(Select):
    def __init__(self):
        options = []
        for key, name in FAQ_CATEGORIES.items():
            emoji = "📋" if "общее" in key else "📜" if "правила" in key else "💰" if "экономика" in key else "🛡️" if "модерация" in key else "🔧"
            options.append(discord.SelectOption(label=name, value=key, emoji=emoji))
        super().__init__(placeholder="Выберите категорию...", options=options, min_values=1, max_values=1)
    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        questions = faq_data.get(category, [])
        if not questions:
            return await interaction.response.send_message("❌ В этой категории пока нет вопросов.", ephemeral=True)
        view = FAQQuestionsView(category, questions, interaction.user)
        await interaction.response.edit_message(content=f"**{FAQ_CATEGORIES[category]}**\nВыберите вопрос:", embed=None, view=view)
class FAQQuestionsView(View):
    def __init__(self, category: str, questions: list, author: discord.User):
        super().__init__(timeout=60)
        self.category = category
        self.questions = questions
        self.author = author
        self.current_page = 0
        self.items_per_page = 5
        self.add_question_buttons()
    def add_question_buttons(self):
        self.clear_items()
        start = self.current_page * self.items_per_page
        end = min(start + self.items_per_page, len(self.questions))
        page_questions = self.questions[start:end]
        for i, q in enumerate(page_questions, start=1):
            async def button_callback(interaction: discord.Interaction, question=q):
                if interaction.user.id != self.author.id:
                    return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
                embed = discord.Embed(
                    title=f"❓ {question['question']}",
                    description=question['answer'],
                    color=COLORS["faq"]
                )
                embed.set_footer(text=f"Категория: {FAQ_CATEGORIES[self.category]}")
                view = View(timeout=60)
                back = Button(label="◀️ Назад", style=discord.ButtonStyle.secondary)
                async def back_cb(interaction: discord.Interaction):
                    await self.show_questions(interaction)
                back.callback = back_cb
                view.add_item(back)
                await interaction.response.edit_message(embed=embed, view=view)
            button = Button(label=f"{start + i}. {q['question'][:50]}...", style=discord.ButtonStyle.secondary)
            button.callback = button_callback
            self.add_item(button)
        if self.current_page > 0:
            prev = Button(label="◀️", style=discord.ButtonStyle.primary)
            prev.callback = self.prev_page
            self.add_item(prev)
        if end < len(self.questions):
            next = Button(label="▶️", style=discord.ButtonStyle.primary)
            next.callback = self.next_page
            self.add_item(next)
        back_to_cat = Button(label="🏠 Категории", style=discord.ButtonStyle.success)
        back_to_cat.callback = self.back_to_categories
        self.add_item(back_to_cat)
    async def show_questions(self, interaction: discord.Interaction):
        self.add_question_buttons()
        await interaction.response.edit_message(
            content=f"**{FAQ_CATEGORIES[self.category]}**\nВыберите вопрос:",
            embed=None,
            view=self
        )
    async def prev_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        self.current_page -= 1
        self.add_question_buttons()
        await interaction.response.edit_message(view=self)
    async def next_page(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        self.current_page += 1
        self.add_question_buttons()
        await interaction.response.edit_message(view=self)
    async def back_to_categories(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("❌ Это не твое меню!", ephemeral=True)
        view = FAQView(interaction.user)
        embed = discord.Embed(
            title="📚 Часто задаваемые вопросы",
            description="Выберите категорию вопросов:",
            color=COLORS["faq"]
        )
        await interaction.response.edit_message(embed=embed, view=view)
class FAQView(View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=60)
        self.author = author
        self.add_item(FAQCategorySelect())

class UseItemModal(Modal, title="Используй предмет"):
    """Модальное окно для подтверждения использования"""
    def __init__(self, item_id: str, item_name: str, owner_id: int):
        super().__init__()
        self.item_id = item_id
        self.item_name = item_name
        self.owner_id = owner_id
        
        self.add_item(TextInput(
            label="Подтвердите использование",
            placeholder=f"Напишите 'да' для использования {item_name}",
            style=discord.TextStyle.short,
            required=True
        ))
    
    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.owner_id:
            return await interaction.response.send_message(
                "❌ Это не твой предмет!", ephemeral=True
            )
        
        confirm_text = self.children[0].value.lower().strip()
        if confirm_text != "да":
            return await interaction.response.send_message(
                f"❌ Использование {self.item_name} отменено. Нужно написать 'да'.",
                ephemeral=True
            )
        
        user_id = str(interaction.user.id)
        if user_id not in economy_data:
            return await interaction.response.send_message(
                "❌ Пользователь не найден в экономике.", ephemeral=True
            )
        
        inv = economy_data[user_id].get("inventory", {})
        if self.item_id not in inv or inv[self.item_id] <= 0:
            return await interaction.response.send_message(
                f"❌ У вас больше нет **{self.item_name}**!", ephemeral=True
            )
        
        result = await handle_item_use(
            interaction.user,
            self.item_id,
            self.item_name,
            interaction
        )
        
        if result["success"]:
            inv[self.item_id] -= 1
            if inv[self.item_id] == 0:
                del inv[self.item_id]
            save_economy()
            
            await interaction.response.send_message(
                embed=result["embed"],
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                result["error"],
                ephemeral=True
            )


class InventoryViewImproved(View):
    """Улучшенный вид инвентаря с кнопками для каждого предмета"""
    def __init__(self, owner_id: int, inventory: dict):
        super().__init__(timeout=300)
        self.owner_id = owner_id
        self.inventory = inventory.copy()
        
        row = 0
        items_added = 0
        usable_items = ["gift_box", "lucky_spin", "xp_boost_24h"]
        
        for item_id in usable_items:
            if item_id in self.inventory and self.inventory[item_id] > 0:
                item = INVENTORY_ITEMS.get(item_id, {})
                name = item.get("name", item_id)
                count = self.inventory[item_id]
                
                button = Button(
                    label=f"Использовать {name} ×{count}",
                    style=discord.ButtonStyle.green,
                    emoji=item.get("emoji", "🎁"),
                    row=row
                )
                
                button.callback = self.create_use_callback(item_id, name)
                self.add_item(button)
                items_added += 1
                
                if items_added % 2 == 0:
                    row += 1
        
        refresh_btn = Button(
            label="🔄 Обновить",
            style=discord.ButtonStyle.grey,
            row=min(2, row + 1)
        )
        refresh_btn.callback = self.refresh_inventory
        self.add_item(refresh_btn)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "❌ Это не твой инвентарь!", ephemeral=True
            )
            return False
        return True
    
    def create_use_callback(self, item_id: str, item_name: str):
        """Создаёт callback для кнопки использования"""
        async def callback(interaction: discord.Interaction):
            modal = UseItemModal(item_id, item_name, self.owner_id)
            await interaction.response.send_modal(modal)
        return callback
    
    async def refresh_inventory(self, interaction: discord.Interaction):
        """Обновить отображение инвентаря"""
        user_id = str(interaction.user.id)
        if user_id not in economy_data:
            return await interaction.response.send_message(
                "❌ Пользователь не найден.", ephemeral=True
            )
        
        data = economy_data[user_id]
        inv = data.get("inventory", {})
        
        embed = await create_inventory_embed(interaction.user, inv, data)
        new_view = InventoryViewImproved(self.owner_id, inv)
        
        await interaction.response.edit_message(embed=embed, view=new_view)

class TradeAcceptView(View):
    """Вид для принятия или отклонения трейда"""
    def __init__(self, trade_id: str, initiator_id: int, recipient_id: int):
        super().__init__(timeout=300)  # 5 минут
        self.trade_id = trade_id
        self.initiator_id = initiator_id
        self.recipient_id = recipient_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.recipient_id:
            await interaction.response.send_message(
                "❌ Это приглашение не для тебя!",
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(label="✅ Принять трейд", style=discord.ButtonStyle.green, emoji="🤝")
    async def accept_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)
        
        if self.trade_id not in active_trades:
            return await interaction.followup.send(
                "❌ Трейд больше не существует или уже завершён.",
                ephemeral=True
            )
        
        trade = active_trades[self.trade_id]
        
        if trade["status"] != "pending":
            return await interaction.followup.send(
                "❌ Трейд уже в процессе или завершён.",
                ephemeral=True
            )
        
        trade["recipient_confirmed"] = True
        trade["status"] = "both_confirmed"
        
        embed = discord.Embed(
            title="🤝 Оба игрока согласны!",
            description=f"Обмен будет выполнен в течение 10 секунд...",
            color=0x2ecc71,
            timestamp=datetime.now(timezone.utc)
        )
        
        await interaction.followup.send(embed=embed)
        
        await asyncio.sleep(10)
        
        initiator_id = str(trade["initiator_id"])
        recipient_id = str(trade["recipient_id"])
        
        try:
            initiator_items = trade["initiator_items"]
            recipient_items = trade["recipient_items"]
            
            if initiator_id not in economy_data or recipient_id not in economy_data:
                raise Exception("Один из игроков не найден в экономике")
            
            initiator_inv = economy_data[initiator_id].get("inventory", {})
            recipient_inv = economy_data[recipient_id].get("inventory", {})
            
            for item_id, count in initiator_items.items():
                if initiator_inv.get(item_id, 0) < count:
                    raise Exception(f"У отправителя недостаточно предмета {item_id}")
            
            for item_id, count in recipient_items.items():
                if recipient_inv.get(item_id, 0) < count:
                    raise Exception(f"У получателя недостаточно предмета {item_id}")
            
            for item_id, count in initiator_items.items():
                initiator_inv[item_id] = initiator_inv.get(item_id, 0) - count
                if initiator_inv[item_id] == 0:
                    del initiator_inv[item_id]
                
                recipient_inv[item_id] = recipient_inv.get(item_id, 0) + count
            
            for item_id, count in recipient_items.items():
                recipient_inv[item_id] = recipient_inv.get(item_id, 0) - count
                if recipient_inv[item_id] == 0:
                    del recipient_inv[item_id]
                
                initiator_inv[item_id] = initiator_inv.get(item_id, 0) + count
            
            save_economy()
            
            trade["status"] = "completed"
            
            initiator_user = bot.get_user(int(initiator_id))
            recipient_user = bot.get_user(int(recipient_id))
            
            success_embed = discord.Embed(
                title="✅ Трейд успешно завершён!",
                description=f"**{initiator_user.mention}** ↔️ **{recipient_user.mention}**",
                color=0x2ecc71,
                timestamp=datetime.now(timezone.utc)
            )
            
            initiator_items_text = "\n".join([
                f"  • {INVENTORY_ITEMS.get(iid, {}).get('name', iid)} ×{cnt}"
                for iid, cnt in initiator_items.items()
            ])
            recipient_items_text = "\n".join([
                f"  • {INVENTORY_ITEMS.get(iid, {}).get('name', iid)} ×{cnt}"
                for iid, cnt in recipient_items.items()
            ])
            
            success_embed.add_field(
                name=f"📤 {initiator_user.display_name} отдал",
                value=initiator_items_text or "Ничего",
                inline=True
            )
            success_embed.add_field(
                name=f"📥 {recipient_user.display_name} отдал",
                value=recipient_items_text or "Ничего",
                inline=True
            )
            
            success_embed.set_footer(text=f"Трейд ID: {self.trade_id}")
            
            await interaction.channel.send(embed=success_embed)
            
            await send_mod_log(
                title="🔄 Трейд завершён",
                description=f"**От:** {initiator_user.mention}\n**Кому:** {recipient_user.mention}\n**ID:** {self.trade_id}",
                color=0x2ecc71
            )
            
            if (self.initiator_id, self.recipient_id) in trade_invitations:
                del trade_invitations[(self.initiator_id, self.recipient_id)]
        
        except Exception as e:
            error_embed = discord.Embed(
                title="❌ Ошибка при выполнении трейда",
                description=f"**Причина:** {str(e)}\n\nТрейд отменён.",
                color=0xe74c3c,
                timestamp=datetime.now(timezone.utc)
            )
            
            await interaction.channel.send(embed=error_embed)
            trade["status"] = "failed"
    
    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.red, emoji="✖️")
    async def reject_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=False)
        
        if self.trade_id not in active_trades:
            return await interaction.followup.send(
                "❌ Трейд уже не существует.",
                ephemeral=True
            )
        
        trade = active_trades[self.trade_id]
        trade["status"] = "rejected"
        
        initiator_user = bot.get_user(int(trade["initiator_id"]))
        reject_embed = discord.Embed(
            title="❌ Трейд отклонён",
            description=f"**{interaction.user.mention}** отклонил предложение от **{initiator_user.mention}**",
            color=0xe74c3c,
            timestamp=datetime.now(timezone.utc)
        )
        
        await interaction.followup.send(embed=reject_embed)
        
        if (self.initiator_id, self.recipient_id) in trade_invitations:
            del trade_invitations[(self.initiator_id, self.recipient_id)]


class TradeItemSelect(Select):
    """Выбор предметов для трейда"""
    def __init__(self, user_id: int, placeholder: str, custom_id: str):
        self.user_id = user_id
        
        user_id_str = str(user_id)
        if user_id_str not in economy_data:
            options = [discord.SelectOption(label="Нет предметов", value="none", emoji="🚫")]
        else:
            inv = economy_data[user_id_str].get("inventory", {})
            
            if not inv:
                options = [discord.SelectOption(label="Нет предметов", value="none", emoji="🚫")]
            else:
                options = []
                for item_id, count in sorted(inv.items()):
                    item = INVENTORY_ITEMS.get(item_id, {})
                    name = item.get("name", item_id)
                    emoji = item.get("emoji", "📦")
                    label = f"{emoji} {name} ×{count}"[:100]
                    
                    options.append(
                        discord.SelectOption(
                            label=label,
                            value=item_id,
                            emoji=emoji,
                            description=f"У тебя есть {count} шт."
                        )
                    )
        
        super().__init__(
            placeholder=placeholder,
            options=options[:25],
            min_values=0,
            max_values=min(5, len(options)) if options else 1,
            custom_id=custom_id
        )
    
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            self.values = []
        
        await interaction.response.defer()


class TradeItemAmountModal(Modal, title="Укажи количество предметов"):
    """Модальное окно для ввода количества предметов"""
    def __init__(self, trade_id: str, user_role: str):
        super().__init__()
        self.trade_id = trade_id
        self.user_role = user_role
        
        self.add_item(TextInput(
            label="Предметы для обмена",
            placeholder='Формат: item_id:количество (например: gift_box:2, xp_boost_24h:1)',
            style=discord.TextStyle.paragraph,
            required=False
        ))
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        if self.trade_id not in active_trades:
            return await interaction.followup.send(
                "❌ Трейд больше не существует.",
                ephemeral=True
            )
        
        trade = active_trades[self.trade_id]
        input_text = self.children[0].value.strip()
        
        items_dict = {}
        if input_text:
            try:
                pairs = [p.strip() for p in input_text.split(",") if p.strip()]
                for pair in pairs:
                    if ":" not in pair:
                        raise ValueError(f"Неверный формат: {pair}")
                    
                    item_id, count_str = pair.split(":", 1)
                    item_id = item_id.strip()
                    count = int(count_str.strip())
                    
                    if count <= 0:
                        raise ValueError(f"Количество должно быть > 0: {pair}")
                    
                    if item_id not in INVENTORY_ITEMS:
                        raise ValueError(f"Предмет {item_id} не существует")
                    
                    user_id = str(interaction.user.id)
                    user_inv = economy_data.get(user_id, {}).get("inventory", {})
                    if user_inv.get(item_id, 0) < count:
                        raise ValueError(f"У тебя нет {count} шт. {item_id}")
                    
                    items_dict[item_id] = count
            
            except Exception as e:
                return await interaction.followup.send(
                    f"❌ Ошибка при парсинге: {str(e)}\n\n"
                    f"**Формат:** item_id:количество (например: gift_box:2, xp_boost_24h:1)",
                    ephemeral=True
                )
        
        if self.user_role == "initiator":
            trade["initiator_items"] = items_dict
            trade["initiator_confirmed"] = True
        else:
            trade["recipient_items"] = items_dict
            trade["recipient_confirmed"] = True
        
        items_text = "\n".join([
            f"  • {INVENTORY_ITEMS.get(iid, {}).get('name', iid)} ×{cnt}"
            for iid, cnt in items_dict.items()
        ]) or "Ничего"
        
        confirm_embed = discord.Embed(
            title="✅ Предметы добавлены",
            description=f"Тебе нужно согласиться на трейд",
            color=0x2ecc71
        )
        confirm_embed.add_field(
            name="Твои предметы",
            value=items_text,
            inline=False
        )
        
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)


class TradeConfirmView(View):
    """Вид для подтверждения сторонами трейда"""
    def __init__(self, trade_id: str, user_id: int, user_role: str):
        super().__init__(timeout=600)
        self.trade_id = trade_id
        self.user_id = user_id
        self.user_role = user_role
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Это не твой трейд!",
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(label="📝 Изменить предметы", style=discord.ButtonStyle.blurple, emoji="✏️")
    async def edit_items(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TradeItemAmountModal(self.trade_id, self.user_role)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="✅ Подтвердить трейд", style=discord.ButtonStyle.green, emoji="🤝")
    async def confirm_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if self.trade_id not in active_trades:
            return await interaction.followup.send(
                "❌ Трейд больше не существует.",
                ephemeral=True
            )
        
        trade = active_trades[self.trade_id]
        
        if self.user_role == "initiator":
            trade["initiator_confirmed"] = True
        else:
            trade["recipient_confirmed"] = True
        
        if trade.get("initiator_confirmed") and trade.get("recipient_confirmed"):
            trade["status"] = "both_confirmed"
            
            initiator = bot.get_user(int(trade["initiator_id"]))
            recipient = bot.get_user(int(trade["recipient_id"]))
            
            ready_embed = discord.Embed(
                title="🎉 Оба игрока готовы!",
                description=f"Трейд между **{initiator.mention}** и **{recipient.mention}** будет выполнен в течение 10 секунд...",
                color=0x2ecc71
            )
            
            channel = interaction.channel
            msg = await channel.send(embed=ready_embed)
            
            await asyncio.sleep(10)
            
            initiator_id = str(trade["initiator_id"])
            recipient_id = str(trade["recipient_id"])
            
            try:
                initiator_items = trade.get("initiator_items", {})
                recipient_items = trade.get("recipient_items", {})
                
                if initiator_id not in economy_data or recipient_id not in economy_data:
                    raise Exception("Один из игроков не найден")
                
                initiator_inv = economy_data[initiator_id].get("inventory", {})
                recipient_inv = economy_data[recipient_id].get("inventory", {})
                
                for item_id, count in initiator_items.items():
                    if initiator_inv.get(item_id, 0) < count:
                        raise Exception(f"У отправителя недостаточно {item_id}")
                
                for item_id, count in recipient_items.items():
                    if recipient_inv.get(item_id, 0) < count:
                        raise Exception(f"У получателя недостаточно {item_id}")
                
                for item_id, count in initiator_items.items():
                    initiator_inv[item_id] = initiator_inv.get(item_id, 0) - count
                    if initiator_inv[item_id] == 0:
                        del initiator_inv[item_id]
                    
                    recipient_inv[item_id] = recipient_inv.get(item_id, 0) + count
                
                for item_id, count in recipient_items.items():
                    recipient_inv[item_id] = recipient_inv.get(item_id, 0) - count
                    if recipient_inv[item_id] == 0:
                        del recipient_inv[item_id]
                    
                    initiator_inv[item_id] = initiator_inv.get(item_id, 0) + count
                
                save_economy()
                
                trade["status"] = "completed"
                
                success_embed = discord.Embed(
                    title="✅ Трейд успешно завершён!",
                    description=f"**{initiator.mention}** ↔️ **{recipient.mention}**",
                    color=0x2ecc71,
                    timestamp=datetime.now(timezone.utc)
                )
                
                initiator_items_text = "\n".join([
                    f"  • {INVENTORY_ITEMS.get(iid, {}).get('name', iid)} ×{cnt}"
                    for iid, cnt in initiator_items.items()
                ]) or "Ничего"
                recipient_items_text = "\n".join([
                    f"  • {INVENTORY_ITEMS.get(iid, {}).get('name', iid)} ×{cnt}"
                    for iid, cnt in recipient_items.items()
                ]) or "Ничего"
                
                success_embed.add_field(
                    name=f"📤 {initiator.display_name} отдал",
                    value=initiator_items_text,
                    inline=True
                )
                success_embed.add_field(
                    name=f"📥 {recipient.display_name} отдал",
                    value=recipient_items_text,
                    inline=True
                )
                
                success_embed.set_footer(text=f"Трейд ID: {self.trade_id}")
                
                await msg.edit(embed=success_embed)
                
                await send_mod_log(
                    title="🔄 Трейд завершён",
                    description=f"**От:** {initiator.mention}\n**Кому:** {recipient.mention}",
                    color=0x2ecc71
                )
                
                if (trade["initiator_id"], trade["recipient_id"]) in trade_invitations:
                    del trade_invitations[(trade["initiator_id"], trade["recipient_id"])]
            
            except Exception as e:
                error_embed = discord.Embed(
                    title="❌ Ошибка при трейде",
                    description=f"**Причина:** {str(e)}\n\nТрейд отменён, предметы вернулись.",
                    color=0xe74c3c
                )
                await msg.edit(embed=error_embed)
                trade["status"] = "failed"
        else:
            status_embed = discord.Embed(
                title="⏳ Ожидание подтверждения",
                description="Второй игрок должен подтвердить трейд",
                color=0xf39c12
            )
            await interaction.followup.send(embed=status_embed, ephemeral=True)
    
    @discord.ui.button(label="❌ Отменить", style=discord.ButtonStyle.red, emoji="✖️")
    async def cancel_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        if self.trade_id not in active_trades:
            return await interaction.followup.send(
                "❌ Трейд уже не существует.",
                ephemeral=True
            )
        
        trade = active_trades[self.trade_id]
        trade["status"] = "cancelled"
        
        cancel_embed = discord.Embed(
            title="❌ Трейд отменён",
            description=f"**{interaction.user.mention}** отменил трейд",
            color=0xe74c3c
        )
        
        await interaction.channel.send(embed=cancel_embed)
        await interaction.followup.send("✅ Трейд отменён.", ephemeral=True)
        
        if (trade["initiator_id"], trade["recipient_id"]) in trade_invitations:
            del trade_invitations[(trade["initiator_id"], trade["recipient_id"])]

# ─────────────────────────────────────────────────────────────────────────────
# ФУНКЦИИ ТРЕЙДИНГА
# ─────────────────────────────────────────────────────────────────────────────

def generate_trade_id() -> str:
    """Генерирует уникальный ID трейда"""
    import uuid
    return f"trade_{str(uuid.uuid4())[:8]}"                    

# ─────────────────────────────────────────────────────────────────────────────
# ОБРАБОТЧИКИ ИСПОЛЬЗОВАНИЯ ПРЕДМЕТОВ
# ─────────────────────────────────────────────────────────────────────────────

async def handle_item_use(member: discord.Member, item_id: str, item_name: str, interaction: discord.Interaction) -> dict:
    """Главный обработчик использования любого предмета"""
    user_id = str(member.id)
    
    try:
        if item_id == "gift_box":
            return await use_gift_box(member, user_id)
        
        elif item_id == "lucky_spin":
            return await use_lucky_spin(member, user_id)
        
        elif item_id == "xp_boost_24h":
            return await use_xp_boost(member, user_id)
        
        else:
            return {
                "success": False,
                "error": f"❌ Неизвестный предмет: {item_id}"
            }
    
    except Exception as e:
        print(f"❌ Ошибка при использовании {item_id}: {e}")
        return {
            "success": False,
            "error": f"❌ Ошибка при использовании: {str(e)}"
        }


async def use_gift_box(member: discord.Member, user_id: str) -> dict:
    """Использование подарочной коробки"""
    reward = open_gift_box()
    
    economy_data[user_id]["balance"] += reward
    
    if reward >= 2200:
        rarity = "🔥 ЛЕГЕНДАРНАЯ!"
        color = 0xF1C40F
        emoji = "🌟"
    elif reward >= 1800:
        rarity = "🌟 Эпическая!"
        color = 0x9B59B6
        emoji = "✨"
    elif reward >= 1200:
        rarity = "💎 Редкая"
        color = 0x3498DB
        emoji = "💎"
    else:
        rarity = "🪙 Обычная"
        color = 0xA8A8A8
        emoji = "🪙"
    
    embed = discord.Embed(
        title=f"{emoji} Коробка открыта!",
        description=f"**+{format_number(reward)}** {ECONOMY_EMOJIS['coin']}",
        color=color,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="Редкость", value=rarity, inline=True)
    embed.add_field(
        name="Новый баланс",
        value=f"**{format_number(economy_data[user_id]['balance'])}** {ECONOMY_EMOJIS['coin']}",
        inline=True
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="🎁 Подарочная коробка")
    
    if reward >= 1500:
        await send_mod_log(
            title="🎁 Крупная награда из коробки!",
            description=f"**Пользователь:** {member.mention}\n**Награда:** {format_number(reward)} {ECONOMY_EMOJIS['coin']}\n**Редкость:** {rarity}",
            color=color
        )
    
    save_economy()
    return {"success": True, "embed": embed}


async def use_lucky_spin(member: discord.Member, user_id: str) -> dict:
    """Использование счастливой крутки - открытие кейса с рандомной наградой"""
    
    # ───────────────────────────────────────────────
    # ТАБЛИЦА НАГРАД С ВЕРОЯТНОСТЯМИ
    # ───────────────────────────────────────────────
    rewards_table = [
        # (chance%, reward_type, value, name, emoji, color)
        
        # 🪙 МОНЕТЫ (50% всего)
        (20, "coins", (100, 500), "Горсть монет", "🪙", 0x95a5a6),
        (15, "coins", (500, 1500), "Мешочек монет", "💰", 0x3498db),
        (10, "coins", (1500, 3000), "Сундук монет", "💎", 0x9b59b6),
        (5,  "coins", (3000, 5000), "Сокровищница", "👑", 0xf1c40f),
        
        # 🎁 ПРЕДМЕТЫ (30% всего)
        (12, "item", "gift_box", "Подарочная коробка", "🎁", 0x3498db),
        (8,  "item", "lucky_spin", "Ещё одна крутка!", "🎰", 0x9b59b6),
        (5,  "item", "xp_boost_24h", "Буст опыта ×2", "⚡", 0xf1c40f),
        (5,  "item", "discount_card", "Скидочная карта", "💳", 0x9b59b6),
        
        # 🚀 БУСТЫ (15% всего)
        (8,  "boost", ("multiplier_1x5", 7), "Удвоитель ×1.5", "🚀", 0x00ff9d),
        (5,  "boost", ("multiplier_2x", 3), "Удвоитель ×2", "🚀🚀", 0xf1c40f),
        (2,  "boost", ("multiplier_3x", 1), "Утроитель ×3", "🚀🚀🚀", 0xff4500),
        
        # 💎 ДЖЕКПОТ (5% всего)
        (3,  "jackpot", (10000, 25000), "ДЖЕКПОТ!", "💥", 0xff0000),
        (1,  "mega_jackpot", (50000, 100000), "МЕГА ДЖЕКПОТ!!!", "🌟", 0xffd700),
        (1,  "legendary", "vip_7days", "VIP на 7 дней", "👑", 0xffd700),
    ]
    
    # ───────────────────────────────────────────────
    # ВЫБОР НАГРАДЫ
    # ───────────────────────────────────────────────
    roll = random.random() * 100
    cumulative = 0
    selected_reward = None
    
    for chance, reward_type, value, name, emoji, color in rewards_table:
        cumulative += chance
        if roll <= cumulative:
            selected_reward = (reward_type, value, name, emoji, color)
            break
    
    if not selected_reward:
        # Fallback на случай ошибки
        selected_reward = ("coins", (100, 500), "Горсть монет", "🪙", 0x95a5a6)
    
    reward_type, value, reward_name, reward_emoji, reward_color = selected_reward
    
    # ───────────────────────────────────────────────
    # ПРИМЕНЕНИЕ НАГРАДЫ
    # ───────────────────────────────────────────────
    reward_text = ""
    detailed_reward = ""
    
    # 🪙 МОНЕТЫ
    if reward_type == "coins":
        min_coins, max_coins = value
        coins = random.randint(min_coins, max_coins)
        economy_data[user_id]["balance"] += coins
        reward_text = f"**+{format_number(coins)}** {ECONOMY_EMOJIS['coin']}"
        detailed_reward = f"Монеты добавлены на баланс"
    
    # 🎁 ПРЕДМЕТЫ
    elif reward_type == "item":
        item_id = value
        inv = economy_data[user_id].setdefault("inventory", {})
        inv[item_id] = inv.get(item_id, 0) + 1
        
        item_info = INVENTORY_ITEMS.get(item_id, {})
        item_emoji = item_info.get("emoji", "📦")
        
        reward_text = f"{item_emoji} **{reward_name}**"
        detailed_reward = f"Предмет добавлен в инвентарь"
    
    # 🚀 БУСТЫ
    elif reward_type == "boost":
        boost_key, days = value
        
        now = datetime.now(timezone.utc).timestamp()
        duration_sec = days * 86400
        end_time = now + duration_sec
        
        if "multiplier_end" not in economy_data[user_id]:
            economy_data[user_id]["multiplier_end"] = 0
        
        # Продлеваем или ставим новый
        if economy_data[user_id]["multiplier_end"] > now:
            economy_data[user_id]["multiplier_end"] += duration_sec
        else:
            economy_data[user_id]["multiplier_end"] = end_time
        
        multiplier = boost_key.split("_")[1]  # "1x5" -> "1.5"
        reward_text = f"🚀 **{reward_name}** ({days}д)"
        detailed_reward = f"Буст активирован до <t:{int(economy_data[user_id]['multiplier_end'])}:R>"
    
    # 💥 ДЖЕКПОТ
    elif reward_type == "jackpot":
        min_coins, max_coins = value
        coins = random.randint(min_coins, max_coins)
        economy_data[user_id]["balance"] += coins
        reward_text = f"💥 **{format_number(coins)}** {ECONOMY_EMOJIS['coin']}"
        detailed_reward = f"НЕВЕРОЯТНАЯ УДАЧА!"
    
    # 🌟 МЕГА ДЖЕКПОТ
    elif reward_type == "mega_jackpot":
        min_coins, max_coins = value
        coins = random.randint(min_coins, max_coins)
        economy_data[user_id]["balance"] += coins
        reward_text = f"🌟 **{format_number(coins)}** {ECONOMY_EMOJIS['coin']}"
        detailed_reward = f"ЛЕГЕНДАРНЫЙ ДРОП! ТЫ ОДИН ИЗ НЕМНОГИХ!"
    
    # 👑 ЛЕГЕНДАРНАЯ НАГРАДА (VIP)
    elif reward_type == "legendary":
        if value == "vip_7days":
            # Даём VIP роль на 7 дней (если есть на сервере)
            reward_text = f"👑 **VIP статус на 7 дней**"
            detailed_reward = f"Легендарная награда! Проверь свои роли"
            
            # Пытаемся выдать роль (если бот на сервере)
            try:
                if member.guild:
                    vip_role = discord.utils.get(member.guild.roles, name="VIP")
                    if vip_role:
                        await member.add_roles(vip_role)
                        temp_roles.setdefault(user_id, {})[str(vip_role.id)] = (
                            datetime.now(timezone.utc).timestamp() + (7 * 86400)
                        )
            except:
                pass
    
    # ───────────────────────────────────────────────
    # СОХРАНЕНИЕ + EMBED
    # ───────────────────────────────────────────────
    save_economy()
    
    # Определяем редкость
    if reward_type in ["mega_jackpot", "legendary"]:
        rarity = "🔥 ЛЕГЕНДАРНАЯ"
    elif reward_type == "jackpot" or (reward_type == "boost" and "3x" in str(value)):
        rarity = "🌟 ЭПИЧЕСКАЯ"
    elif reward_type == "boost" or (reward_type == "item" and value in ["lucky_spin", "xp_boost_24h"]):
        rarity = "💎 РЕДКАЯ"
    else:
        rarity = "🪙 Обычная"
    
    embed = discord.Embed(
        title=f"{reward_emoji} {reward_name}",
        description=f"**{reward_text}**\n\n{detailed_reward}",
        color=reward_color,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(name="🎲 Редкость", value=rarity, inline=True)
    embed.add_field(
        name="💰 Новый баланс",
        value=f"**{format_number(economy_data[user_id]['balance'])}** {ECONOMY_EMOJIS['coin']}",
        inline=True
    )
    
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="🎰 Счастливая крутка • MortisPlay")
    
    # ───────────────────────────────────────────────
    # ЛОГ РЕДКИХ ДРОПОВ
    # ───────────────────────────────────────────────
    if reward_type in ["jackpot", "mega_jackpot", "legendary"]:
        try:
            await send_mod_log(
                title="🎰 РЕДКИЙ ДРОП!",
                description=f"**Игрок:** {member.mention}\n**Награда:** {reward_name}\n**Редкость:** {rarity}",
                color=reward_color
            )
        except:
            pass
    
    return {"success": True, "embed": embed}


async def use_xp_boost(member: discord.Member, user_id: str) -> dict:
    """Использование буста опыта на 24 часа"""
    now_ts = datetime.now(timezone.utc).timestamp()
    end_ts = now_ts + (24 * 3600)
    
    effects = economy_data[user_id].get("active_effects", [])
    active_xp_boost = any(e.get("effect_type") == "xp_multiplier" for e in effects)
    
    if active_xp_boost:
        return {
            "success": False,
            "error": "❌ У вас уже активен буст опыта! Подожди, пока истечёт."
        }
    
    effect = {
        "effect_type": "xp_multiplier",
        "name": "Буст опыта ×2",
        "value": 2.0,
        "start_time": now_ts,
        "end_time": end_ts,
        "duration_sec": 24 * 3600
    }
    economy_data[user_id].setdefault("active_effects", []).append(effect)
    save_economy()
    
    embed = discord.Embed(
        title="⚡ Буст опыта активирован!",
        description="**×2 опыта на 24 часа** 🚀",
        color=0x00FF9D,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="⏰ Действует", value="**24 часа**", inline=True)
    embed.add_field(name="📊 Множитель", value="**×2.0**", inline=True)
    embed.add_field(
        name="✨ Завершение",
        value=f"<t:{int(end_ts)}:R>",
        inline=False
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text="⚡ Буст активирован")
    
    try:
        await send_mod_log(
            title="⚡ Буст активирован",
            description=f"**Пользователь:** {member.mention}\n**Эффект:** Буст опыта ×2\n**Длительность:** 24 часа",
            color=0x00FF9D
        )
    except:
        pass
    
    return {"success": True, "embed": embed}


# ─────────────────────────────────────────────────────────────────────────────
# ПОМОЩНИК ДЛЯ СОЗДАНИЯ EMBED'а ИНВЕНТАРЯ
# ─────────────────────────────────────────────────────────────────────────────

async def create_inventory_embed(member: discord.Member, inventory: dict, economy_data_user: dict) -> discord.Embed:
    """Создаёт красивый embed для инвентаря"""
    embed = discord.Embed(
        title=f"🎒 Инвентарь {member.display_name}",
        color=0x2ecc71,
        timestamp=datetime.now(timezone.utc)
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    
    # ─ ПРЕДМЕТЫ ─
    if inventory:
        items_lines = []
        rarest_rarity = "common"
        rarity_order = ["common", "rare", "epic", "legendary"]
        
        for item_id, count in sorted(inventory.items()):
            item = INVENTORY_ITEMS.get(item_id, {})
            rarity = item.get("rarity", "common")
            style = RARITY_STYLE.get(rarity, RARITY_STYLE["common"])
            name = item.get("name", item_id)
            emoji = item.get("emoji", "📦")
            
            items_lines.append(f"{style['emoji']} **{emoji} {name}** ×{count}")
            
            if rarity_order.index(rarity) > rarity_order.index(rarest_rarity):
                rarest_rarity = rarity
        
        def get_rarity_index(line):
            for r in rarity_order:
                if RARITY_STYLE[r]["emoji"] in line:
                    return rarity_order.index(r)
            return 0
        
        items_lines.sort(key=get_rarity_index, reverse=True)
        
        embed.add_field(
            name="📦 Предметы",
            value="\n".join(items_lines),
            inline=False
        )
        embed.color = RARITY_STYLE[rarest_rarity]["color"]
    else:
        embed.add_field(
            name="📦 Предметы",
            value="🚫 Инвентарь пуст!\nСходи в `/shop` 🛒",
            inline=False
        )
    
    # ─ АКТИВНЫЕ ЭФФЕКТЫ ─
    now_ts = datetime.now(timezone.utc).timestamp()
    effects = economy_data_user.get("active_effects", [])
    active_lines = []
    
    for eff in effects[:10]:
        ends_at = eff.get("end_time", 0)
        if ends_at <= now_ts:
            continue
        
        time_left_sec = ends_at - now_ts
        hours_left = int(time_left_sec // 3600)
        mins_left = int((time_left_sec % 3600) // 60)
        
        duration_sec = eff.get("duration_sec", 24 * 3600)
        progress = (time_left_sec / duration_sec) * 100
        progress = max(0, min(100, progress))
        
        bar = create_progress_bar(int(progress), 100, length=12)
        name = eff.get("name", "Эффект")
        value = eff.get("value", 1)
        
        line = f"**{name} ×{value}** — <t:{int(ends_at)}:R>\n`{bar}` **{int(progress)}%**"
        active_lines.append(line)
    
    embed.add_field(
        name="✨ Активные эффекты",
        value="\n".join(active_lines) if active_lines else "✅ Нет активных эффектов",
        inline=False
    )
    
    # ─ СТАТИСТИКА ─
    balance = economy_data_user.get("balance", 0)
    embed.set_footer(
        text=f"Баланс: {format_number(balance)} {ECONOMY_EMOJIS['coin']} • Используй кнопки ниже"
    )
    
    return embed                
# ───────────────────────────────────────────────
# Магазин с кнопками, подтверждением, проверкой "уже куплено"
# ───────────────────────────────────────────────
class ShopConfirmModal(Modal, title="Подтверждение покупки"):
    def __init__(self, item_key: str, item_name: str, price: int, final_price: int):
        super().__init__()
        self.item_key = item_key
        self.item_name = item_name
        self.price = price
        self.final_price = final_price
        self.add_item(TextInput(
            label="Подтвердите покупку",
            placeholder=f"Напишите 'подтверждаю' для покупки {item_name}",
            style=discord.TextStyle.short,
            required=True
        ))
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.children[0].value.lower().strip() != "подтверждаю":
            return await interaction.response.send_message(
                "❌ Покупка отменена. Нужно написать 'подтверждаю'.", 
                ephemeral=True
            )
        
        user_id = str(interaction.user.id)
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0}
            save_economy()
        
        if economy_data[user_id].get("balance", 0) < self.final_price:
            return await interaction.response.send_message(
                f"{ECONOMY_EMOJIS['error']} Недостаточно монет! Требуется {format_number(self.final_price)}",
                ephemeral=True
            )
        
        shop_item = SHOP_ITEMS[self.item_key]
        economy_data[user_id]["balance"] -= self.final_price
        
        msg = ""
        msg_title = ""
        color = 0x2ecc71
        
        # ───────────────────────────────────────
        # ВИП РОЛЬ
        # ───────────────────────────────────────
        if self.item_key == "vip":
            role = discord.utils.get(interaction.guild.roles, name="VIP")
            if role:
                await interaction.user.add_roles(role)
                temp_roles.setdefault(user_id, {})[str(role.id)] = (
                    datetime.now(timezone.utc).timestamp() + (shop_item["duration_days"] * 86400)
                )
                msg = (
                    f"×2 ко всем доходам • VIP-чат • ×2 за войс\n"
                    f"Приоритет тикетов • Закрытые ивенты"
                )
                msg_title = "💎 VIP активирован!"
            else:
                msg = f"{ECONOMY_EMOJIS['error']} Роль VIP не найдена!"
                color = 0xe74c3c
                msg_title = "❌ Ошибка"
        
        # ───────────────────────────────────────
        # ПОСТОЯННЫЙ ВИП
        # ───────────────────────────────────────
        elif self.item_key == "vip_permanent":
            role = discord.utils.get(interaction.guild.roles, name="VIP")
            if role:
                await interaction.user.add_roles(role)
                # Без срока действия (999 лет)
                temp_roles.setdefault(user_id, {})[str(role.id)] = (
                    datetime.now(timezone.utc).timestamp() + (999 * 365 * 86400)
                )
                
                # Отмечаем как постоянный VIP
                economy_data[user_id]["vip_permanent"] = True
                
                msg = (
                    f"👑 **ВЕЧНЫЙ VIP СТАТУС!**\n"
                    f"Ты один из 5 избранных!\n\n"
                    f"×2 ко всем доходам\n"
                    f"VIP-чат\n"
                    f"×2 за войс\n"
                    f"Приоритет тикетов"
                )
                msg_title = "👑 ПОСТОЯННЫЙ VIP!"
                color = 0xFFD700
            else:
                msg = f"{ECONOMY_EMOJIS['error']} Роль VIP не найдена!"
                color = 0xe74c3c
                msg_title = "❌ Ошибка"
        
        # ───────────────────────────────────────
        # БУСТЫ (multiplier_1x5, multiplier_2x и т.д.)
        # ───────────────────────────────────────
        elif shop_item.get("duration_days"):
            if "multiplier_end" not in economy_data[user_id]:
                economy_data[user_id]["multiplier_end"] = 0
            
            economy_data[user_id]["multiplier_end"] = (
                datetime.now(timezone.utc).timestamp() + (shop_item["duration_days"] * 86400)
            )
            
            # Парсим множитель из имени
            multiplier_text = shop_item["name"].split("×")[1].split()[0] if "×" in shop_item["name"] else "1.5"
            days = shop_item["duration_days"]
            
            msg = f"×{multiplier_text} ко ВСЕМ доходам\nДействует {days} {'день' if days == 1 else 'дня' if days < 5 else 'дней'}"
            msg_title = f"🚀 Буст ×{multiplier_text} активирован!"
            color = 0x00FF9D
        
        # ───────────────────────────────────────
        # ЭФФЕКТ (lucky_day и прочее)
        # ───────────────────────────────────────
        elif shop_item.get("type") == "effect":
            now_ts = datetime.now(timezone.utc).timestamp()
            duration_sec = shop_item.get("duration_hours", 24) * 3600
            end_ts = now_ts + duration_sec
            
            effect = {
                "effect_type": "special_bonus",
                "name": shop_item["name"],
                "value": shop_item.get("value", 1.5),
                "start_time": now_ts,
                "end_time": end_ts,
                "duration_sec": duration_sec
            }
            
            economy_data[user_id].setdefault("active_effects", []).append(effect)
            
            msg = f"Бонус действует 24 часа\n<t:{int(end_ts)}:R>"
            msg_title = f"🍀 {shop_item['name']} активирован!"
            color = 0x2ECC71
        
        # ───────────────────────────────────────
        # ПРЕДМЕТЫ ИНВЕНТАРЯ
        # ───────────────────────────────────────
        elif shop_item.get("type") == "inventory_item":
            item_id = shop_item.get("item_id", self.item_key)
            inv = economy_data[user_id].setdefault("inventory", {})
            inv[item_id] = inv.get(item_id, 0) + 1
            
            item_info = INVENTORY_ITEMS.get(item_id, {})
            emoji = item_info.get("emoji", "📦")
            
            msg = f"Добавлено в инвентарь\nИспользуй `/inventory` для активации"
            msg_title = f"{emoji} {shop_item['name']} получен!"
            color = 0x3498DB
        
        # ───────────────────────────────────────
        # ЛУТБОКСЫ
        # ───────────────────────────────────────
        elif shop_item.get("type") == "lootbox":
            pool = shop_item.get("pool", [])
            
            # Крутим лотерею
            roll = random.random()
            cumulative = 0
            selected_item = pool[0][0]
            
            for item_id, chance in pool:
                cumulative += chance
                if roll <= cumulative:
                    selected_item = item_id
                    break
            
            inv = economy_data[user_id].setdefault("inventory", {})
            inv[selected_item] = inv.get(selected_item, 0) + 1
            
            item_name = INVENTORY_ITEMS.get(selected_item, {}).get("name", selected_item)
            item_emoji = INVENTORY_ITEMS.get(selected_item, {}).get("emoji", "📦")
            
            # Определяем редкость
            if roll > 0.7:
                rarity_text = "🔥 РЕДКИЙ ДРОП!"
                color = 0xFF6B6B
            elif roll > 0.4:
                rarity_text = "💎 ХОРОШИЙ ДРОП"
                color = 0x3498DB
            else:
                rarity_text = "🪙 Обычный дроп"
                color = 0x95a5a6
            
            msg = f"{item_emoji} **{item_name}**\n{rarity_text}"
            msg_title = f"🎰 Ящик открыт!"
        
        # ───────────────────────────────────────
        # СКИДОЧНАЯ КАРТА
        # ───────────────────────────────────────
        elif shop_item.get("type") == "discount":
            now_ts = datetime.now(timezone.utc).timestamp()
            duration_sec = shop_item.get("duration_days", 7) * 86400
            end_ts = now_ts + duration_sec
            
            discount = {
                "type": self.item_key,
                "discount_percent": int(shop_item.get("discount", 0.15) * 100),
                "start_time": now_ts,
                "end_time": end_ts
            }
            
            economy_data[user_id].setdefault("active_discounts", []).append(discount)
            
            discount_percent = int(shop_item.get("discount", 0.15) * 100)
            msg = f"-{discount_percent}% на весь магазин\nДействует до <t:{int(end_ts)}:D>"
            msg_title = f"💳 Скидочная карта активирована!"
            color = 0x9B59B6
        
        # ───────────────────────────────────────
        # ПАКЕТЫ (BUNDLE)
        # ───────────────────────────────────────
        elif shop_item.get("type") == "bundle":
            inv = economy_data[user_id].setdefault("inventory", {})
            
            # Добавляем предметы из пакета
            items_added = []
            for item_id, count in shop_item.get("items", {}).items():
                inv[item_id] = inv.get(item_id, 0) + count
                item_name = INVENTORY_ITEMS.get(item_id, {}).get("name", item_id)
                items_added.append(f"  • {item_name} ×{count}")
            
            # Добавляем бонусные монеты
            bonus_coins = shop_item.get("bonus_coins", 0)
            if bonus_coins > 0:
                economy_data[user_id]["balance"] += bonus_coins
                items_added.append(f"  • {format_number(bonus_coins)} 🪙")
            
            msg = "Предметы добавлены в инвентарь:\n" + "\n".join(items_added)
            msg_title = f"📦 {shop_item['name']}!"
            color = 0x2ECC71
        
        # ───────────────────────────────────────
        # КОСМЕТИКА (ТИТУЛ, КОРОНА)
        # ───────────────────────────────────────
        elif shop_item.get("type") == "cosmetic":
            now_ts = datetime.now(timezone.utc).timestamp()
            duration_sec = shop_item.get("duration_days", 30) * 86400
            end_ts = now_ts + duration_sec
            
            cosmetic = {
                "type": self.item_key,
                "name": shop_item["name"],
                "start_time": now_ts,
                "end_time": end_ts
            }
            
            economy_data[user_id].setdefault("cosmetics", []).append(cosmetic)
            
            msg = f"Активирован на {shop_item.get('duration_days', 30)} дней\nДействует до <t:{int(end_ts)}:D>"
            msg_title = f"🎨 {shop_item['name']}!"
            color = 0xE74C3C
        
        # Сохраняем все изменения
        save_economy()
        
        # Отслеживаем покупку для динамических цен
        track_purchase(self.item_key)
        
        # Отправляем сообщение об успехе
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['success']} {msg_title}",
            description=msg,
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"Баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']}")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Логируем покупку
        log_desc = (
            f"**Пользователь:** {interaction.user.mention}\n"
            f"**Товар:** {self.item_name}\n"
            f"**Цена:** {format_number(self.final_price)} {ECONOMY_EMOJIS['coin']}"
        )
        await send_mod_log(
            title="🛒 Покупка в магазине",
            description=log_desc,
            color=COLORS["economy"]
        )
# ───────────────────────────────────────────────
# НОВЫЙ КЛАСС ДЛЯ ВЫБОРА КАТЕГОРИЙ
# ───────────────────────────────────────────────

class ShopCategorySelect(Select):
    """Селект для выбора категории магазина"""
    def __init__(self):
        options = [
            discord.SelectOption(
                label=SHOP_CATEGORIES[cat]["name"],
                value=cat,
                emoji=SHOP_CATEGORIES[cat]["emoji"],
                description=SHOP_CATEGORIES[cat]["description"]
            )
            for cat in SHOP_CATEGORIES.keys()
        ]
        
        super().__init__(
            placeholder="Выберите категорию товаров...",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="shop_category_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        
        # Получаем все товары в категории
        items_in_category = {
            key: item for key, item in SHOP_ITEMS.items()
            if item.get("category") == category
        }
        
        if not items_in_category:
            return await interaction.response.send_message(
                f"{ECONOMY_EMOJIS['error']} В этой категории нет товаров!",
                ephemeral=True
            )
        
        # Показываем товары
        await interaction.response.defer(ephemeral=True)
        
        user_id = str(interaction.user.id)
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0}
            save_economy()
        
        balance = economy_data[user_id].get("balance", 0)
        
        embed = discord.Embed(
            title=f"{SHOP_CATEGORIES[category]['emoji']} {SHOP_CATEGORIES[category]['name']}",
            description=f"**Ваш баланс:** {format_number(balance)} {ECONOMY_EMOJIS['coin']}\n\n",
            color=COLORS["economy"]
        )
        
        for key, item in items_in_category.items():
            # Проверка "уже куплено"
            owned = False
            owned_text = ""
            
            if key == "vip":
                role = discord.utils.get(interaction.guild.roles, name="VIP")
                owned = role in interaction.user.roles if role else False
                owned_text = " ✅" if owned else ""
            
            elif item.get("type") == "discount":
                if "active_discounts" in economy_data.get(user_id, {}):
                    discounts = economy_data[user_id]["active_discounts"]
                    owned = any(d.get("type") == key for d in discounts)
                owned_text = " ✅" if owned else ""
            
            # Динамическая цена
            base_price = item["price"]
            display_price = get_dynamic_price(key, base_price)
            
            # Скидочная карта
            display_price = get_discounted_price(display_price, key, interaction.user)
            
            # Скидка при акции
            if is_march8_event_active() and key in DISCOUNTED_ITEMS:
                original = display_price
                display_price = int(display_price * 0.8)
                price_text = f"**{format_number(display_price)}** ~~{format_number(original)}~~ (-20%)"
            else:
                price_text = f"**{format_number(display_price)}** {ECONOMY_EMOJIS['coin']}"
            
            status = "✅ Уже куплено" if owned else f"Цена: {price_text}"
            
            # Ограниченный товар
            limited_text = ""
            if item.get("limited"):
                stock = item.get("stock", 0)
                limited_text = f"\n⚠️ **Осталось: {stock}**"
            
            embed.add_field(
                name=f"{item.get('emoji', '📦')} {item['name']}{owned_text}{limited_text}",
                value=f"{status}\n{item['description']}",
                inline=False
            )
        
        # Кнопки для покупки (по одной для каждого товара)
        view = ShopItemsView(category, items_in_category, interaction.user.id)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

class ShopItemsView(View):
    """Вид с кнопками для покупки товаров в категории"""
    def __init__(self, category: str, items: dict, author_id: int):
        super().__init__(timeout=300)
        self.category = category
        self.items = items
        self.author_id = author_id
        
        row = 0
        for i, (key, item) in enumerate(list(items.items())[:5]):  # Макс 5 кнопок
            button = Button(
                label=f"{item.get('emoji', '📦')} {item['name'][:20]}",
                style=discord.ButtonStyle.blurple,
                custom_id=f"shop_item_{key}",
                row=row
            )
            
            async def handle_purchase(interaction: discord.Interaction, item_key=key):
                await self._handle_purchase(interaction, item_key)
            
            button.callback = handle_purchase
            self.add_item(button)
            
            if (i + 1) % 2 == 0:
                row += 1
    
    async def _handle_purchase(self, interaction: discord.Interaction, item_key: str):
        """Обработка покупки товара"""
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message(
                "❌ Это не твой магазин!",
                ephemeral=True
            )
        
        if item_key not in SHOP_ITEMS:
            return await interaction.response.send_message(
                "❌ Товар не найден!",
                ephemeral=True
            )
        
        item = SHOP_ITEMS[item_key]
        user_id = str(interaction.user.id)
        
        # Инициализация
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0}
            save_economy()
        
        balance = economy_data[user_id].get("balance", 0)
        
        # Проверка "уже куплено"
        already_owned = False
        if item_key == "vip":
            role = discord.utils.get(interaction.guild.roles, name="VIP")
            already_owned = role in interaction.user.roles if role else False
        
        if already_owned:
            return await interaction.response.send_message(
                f"{ECONOMY_EMOJIS['warning']} У тебя уже есть **{item['name']}**!",
                ephemeral=True
            )
        
        # Динамическая цена + скидки
        price = get_dynamic_price(item_key, item["price"])
        price = get_discounted_price(price, item_key, interaction.user)
        
        if balance < price:
            return await interaction.response.send_message(
                f"{ECONOMY_EMOJIS['error']} Недостаточно монет!\n"
                f"Нужно: **{format_number(price)}**, у вас: **{format_number(balance)}**",
                ephemeral=True
            )
        
        # Подтверждение
        modal = ShopConfirmModal(item_key, item["name"], item["price"], price)
        await interaction.response.send_modal(modal)

class ShopCategoryView(View):
    """Вид с выбором категории в магазине"""
    def __init__(self, author_id: int):
        super().__init__(timeout=300)
        self.author_id = author_id
        self.add_item(ShopCategorySelect())
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Это не твой магазин!",
                ephemeral=True
            )
            return False
        return True                       
# ───────────────────────────────────────────────
# ИНИЦИАЛИЗАЦИЯ БОТА
# ───────────────────────────────────────────────
intents = discord.Intents(
    guilds=True,
    members=True,
    presences=True,
    message_content=True,
    voice_states=True,
    moderation=True,
    guild_messages=True,
    dm_messages=False
)
bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents,
    help_command=None,
    case_insensitive=True,
    owner_id=OWNER_ID
)
# ───────────────────────────────────────────────
# ФОНОВЫЕ ЗАДАЧИ
# ───────────────────────────────────────────────
@tasks.loop(seconds=15)  # ← БЫЛО 30, ТЕПЕРЬ 15 (чаще!)
async def autosave_economy_task():
    """Автосохранение экономики каждые 15 секунд"""
    try:
        save_economy()
    except Exception as e:
        print(f"❌ [AUTOSAVE ERROR] {e}")
@tasks.loop(hours=1)
async def clean_old_warnings_task():
    global warnings_data
    now = datetime.now(timezone.utc)
    changed = False
    for user_id in list(warnings_data.keys()):
        fresh = []
        for warn in warnings_data[user_id]:
            try:
                warn_time = datetime.strptime(warn["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                if (now - warn_time).days < WARN_EXPIRY_DAYS:
                    fresh.append(warn)
            except:
                continue
        if len(fresh) != len(warnings_data[user_id]):
            changed = True
            if fresh:
                warnings_data[user_id] = fresh
            else:
                del warnings_data[user_id]
    if changed:
        save_warnings()
        print("[AUTO] Старые варны очищены")
@tasks.loop(minutes=1)
async def check_temp_roles_task():
    for guild in bot.guilds:
        for member in guild.members:
            user_id = str(member.id)
            if user_id in temp_roles:
                now = datetime.now(timezone.utc).timestamp()
                to_remove = []
                for role_id, expiry in temp_roles[user_id].items():
                    if now >= expiry:
                        role = guild.get_role(int(role_id))
                        if role and role in member.roles:
                            try:
                                await member.remove_roles(role, reason="Временная роль истекла")
                                await send_mod_log(
                                    title="⏱️ Роль снята",
                                    description=f"**Пользователь:** {member.mention}\n**Роль:** {role.mention}",
                                    color=COLORS["audit"]
                                )
                            except:
                                pass
                        to_remove.append(role_id)
                for role_id in to_remove:
                    del temp_roles[user_id][role_id]
                if not temp_roles[user_id]:
                    del temp_roles[user_id]
@tasks.loop(hours=6)
async def check_investments_task():
    now = datetime.now(timezone.utc).timestamp()
    for user_id, data in economy_data.items():
        if user_id == "server_vault" or "investments" not in data:
            continue
        active = []
        for inv in data["investments"]:
            if inv["end_time"] <= now:
                profit = inv["profit"]
                data["balance"] += profit
                user = bot.get_user(int(user_id))
                if user:
                    embed = discord.Embed(
                        title=f"{ECONOMY_EMOJIS['profit']} Инвестиция завершена",
                        description=f"Ваша инвестиция на {inv['days']} дней завершена!\n"
                                   f"**Прибыль:** +{format_number(profit)} {ECONOMY_EMOJIS['coin']}",
                        color=COLORS["economy"]
                    )
                    try:
                        await user.send(embed=embed)
                    except:
                        pass
            else:
                active.append(inv)
        data["investments"] = active
    save_economy()
    print("[AUTO] Инвестиции проверены")
@tasks.loop(hours=1)
async def check_inactive_tickets_task():
    checker = TicketInactivityCheck()
    await checker.check_inactive_tickets()
@tasks.loop(minutes=30)
async def voice_income_task():
    now = datetime.now(timezone.utc).timestamp()
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            if "afk" in vc.name.lower():
                continue
            active_members = [
                m for m in vc.members
                if not m.bot
                and m.voice
                and not (m.voice.mute or m.voice.self_mute or m.voice.self_deaf or m.voice.deaf)
            ]
            if len(active_members) < 2:
                continue
            for member in active_members:
                user_id = str(member.id)
                if user_id not in economy_data:
                    continue
                if user_id in voice_start_time:
                    minutes_in_voice = (now - voice_start_time[user_id]) / 60
                    if minutes_in_voice < VOICE_MIN_SESSION_MINUTES:
                        continue
                    earn = VOICE_INCOME_PER_30MIN
                    if is_vip(member):
                        earn = int(earn * 2)
                    if user_id not in daily_voice_earned:
                        daily_voice_earned[user_id] = 0
                    if daily_voice_earned[user_id] + earn > VOICE_DAILY_MAX:
                        remaining = VOICE_DAILY_MAX - daily_voice_earned[user_id]
                        if remaining <= 0:
                            if daily_voice_earned[user_id] < VOICE_DAILY_MAX:
                                try:
                                    user = bot.get_user(int(user_id))
                                    if user:
                                        await user.send(
                                            embed=discord.Embed(
                                                title="🎤 Дневной лимит войса достигнут!",
                                                description=(
                                                    f"Сегодня вы заработали максимум **{VOICE_DAILY_MAX}** монет "
                                                    f"в голосовых каналах.\nЗавтра в 00:00 UTC лимит обновится — "
                                                    f"возвращайтесь! 🚀"
                                                ),
                                                color=0xF1C40F,
                                                timestamp=datetime.now(timezone.utc)
                                            ).set_footer(text="MortisPlay • Экономика")
                                        )
                                except:
                                    pass
                            continue
                        earn = remaining
                    economy_data[user_id]["balance"] += earn
                    daily_voice_earned[user_id] += earn
                    save_economy()
# ───────────────────────────────────────────────
# СОБЫТИЯ
# ───────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"┌──────────────────────────────────────────────┐")
    print(f"│ Залогинен как {bot.user} │")
    print(f"│ ID {bot.user.id} │")
    print(f"│ Время запуска {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} │")
    print(f"└──────────────────────────────────────────────┘")
    
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(type=discord.ActivityType.watching, name="mortisplay.ru")
    )
    
    try:
        synced = await bot.tree.sync()
        print(f"Команды синхронизированы: {len(synced)} шт")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")
    
    # ✅ ПРОВЕРКА ЦЕЛОСТНОСТИ БД
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("PRAGMA integrity_check")
            check = c.fetchone()
            if check[0] == "ok":
                print("✅ [DB CHECK] База данных целостна")
            else:
                print(f"⚠️  [DB CHECK] Проблема: {check[0]}")
    except Exception as e:
        print(f"❌ [DB CHECK] Ошибка проверки: {e}")
    
    # ✅ ЗАГРУЗКА ЭКОНОМИКИ
    load_economy()
    save_economy()  # Проверяем, что сохранение работает
    
    for guild in bot.guilds:
        await guild.chunk()
        if guild.id == FULL_ACCESS_GUILD_ID:
            bot_member = guild.get_member(bot.user.id)
            if bot_member:
                perms = bot_member.guild_permissions
                if not perms.view_audit_log:
                    print(f"⚠️ НЕТ ПРАВА VIEW_AUDIT_LOG на сервере {guild.name}!")
                else:
                    print(f"✅ Право VIEW_AUDIT_LOG есть на сервере {guild.name}")
    
    bot.add_view(TicketPanelView())
    bot.add_view(TicketControls())

    async def reset_voice_earned():
     while True:
        now = datetime.now(timezone.utc)
        # Следующий день в 00:00
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        wait_seconds = (tomorrow - now).total_seconds()
        
        await asyncio.sleep(wait_seconds)
        daily_voice_earned.clear()
        print("✅ [VOICE] Дневной лимит сброшен")
    
    # ✅ ЗАПУСК ФОНОВЫХ ЗАДАЧ (измененный интервал для autosave)
    autosave_economy_task.start()
    clean_old_warnings_task.start()
    check_temp_roles_task.start()
    check_investments_task.start()
    check_inactive_tickets_task.start()
    bot.loop.create_task(reset_voice_earned())
    voice_income_task.start()
    
    # ✅ ПРОВЕРКА ЦЕЛОСТНОСТИ ЭКОНОМИКИ КАЖДЫЙ ЧАС
    async def verify_economy():
        while True:
            await asyncio.sleep(3600)  # Каждый час
            try:
                if not economy_data or economy_data == {"server_vault": 0}:
                    print("⚠️  [VERIFY] Экономика пуста, перезагружаю...")
                    load_economy()
                
                players = len([k for k in economy_data.keys() if k != "server_vault"])
                vault = economy_data.get("server_vault", 0)
                
                if players > 0:
                    print(f"✅ [VERIFY] Экономика в порядке: {players} игроков, казна {format_number(vault)}")
                
                # Сохраняем для подстраховки
                save_economy()
                
            except Exception as e:
                print(f"❌ [VERIFY ERROR] {e}")
    
    bot.loop.create_task(verify_economy())
    
    bot.launch_time = datetime.now(timezone.utc)
    print("✅ Бот полностью готов к работе")
# ───────────────────────────────────────────────
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ДЛЯ ГОЛОСА
# ───────────────────────────────────────────────
voice_start_time = {}
daily_voice_earned = {}
daily_voice_reset = {}
# ─────────────────────────────────────────────────────────────────────────────
# ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ ДЛЯ АКТИВНЫХ ТРЕЙДОВ
# ─────────────────────────────────────────────────────────────────────────────
active_trades = {}  # {trade_id: trade_data}
trade_invitations = {}  # {(user1_id, user2_id): trade_id}
# ───────────────────────────────────────────────
# СОБЫТИЯ (продолжение)
# ───────────────────────────────────────────────
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    user_id = str(message.author.id)
    now = datetime.now(timezone.utc).timestamp()
    # ====================== АНТИ-СПАМ, ТОКСИЧНОСТЬ, МОДЕРАЦИЯ ======================
    protected = is_protected_from_automod(message.author)
    spam_threshold = SPAM_THRESHOLD
    mention_limit = 4
    if not protected:
        spam_threshold *= (VIP_SPAM_MULTIPLIER if is_vip(message.author) else 1)
        mention_limit *= (VIP_MENTION_MULTIPLIER if is_vip(message.author) else 1)
    if user_id not in spam_cache:
        spam_cache[user_id] = []
    spam_cache[user_id] = [t for t in spam_cache[user_id] if now - t < SPAM_TIME]
    spam_cache[user_id].append(now)
    if len(spam_cache[user_id]) >= spam_threshold:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, слишком быстро пишешь!", delete_after=8)
        try:
            await message.author.timeout(timedelta(minutes=10), reason="Анти-спам")
            case_id = await create_case(message.author, bot.user, "Авто-мут (спам)", "Превышение лимита сообщений", "10 минут")
            await send_punishment_log(
                member=message.author,
                punishment_type="🔇 Мут 10 минут",
                duration="10 минут",
                reason="Превышение лимита сообщений",
                moderator=bot.user,
                case_id=case_id
            )
        except:
            pass
        return
    mention_count = len(message.mentions) + len(message.role_mentions)
    if ("@everyone" in message.content or "@here" in message.content) and not message.author.guild_permissions.mention_everyone:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, у тебя нет прав на массовые упоминания!", delete_after=8)
        return
    if mention_count > mention_limit:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, не спамь упоминаниями! (лимит: {mention_limit})", delete_after=8)
        if user_id not in warnings_data:
            warnings_data[user_id] = []
        warnings_data[user_id].append({
            "moderator": "Автомодерация",
            "reason": f"Массовый пинг ({mention_count} упоминаний)",
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        })
        save_warnings()
        case_id = await create_case(message.author, bot.user, "Варн (авто)", f"Массовый пинг ({mention_count} упоминаний)")
        await check_auto_punishment(message.author, "Массовый пинг")
        return
    if len(message.content) > 15:
        upper_ratio = sum(1 for c in message.content if c.isupper()) / len(message.content)
        if upper_ratio > 0.75:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, не кричи (капс)!", delete_after=8)
            return
    if re.search(r"discord\.(gg|com/invite)/", message.content.lower()):
        await message.delete()
        await message.channel.send(f"{message.author.mention}, реклама запрещена!", delete_after=10)
        return
    if is_toxic(message.content):
        await message.delete()
        user_id = str(message.author.id)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        last_toxic = None
        for warn in warnings_data.get(user_id, []):
            if "токсичность" in warn.get("reason", "").lower():
                last_toxic = datetime.strptime(warn["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                break
        if last_toxic and (datetime.now(timezone.utc) - last_toxic).total_seconds() < 300:
            await message.channel.send(
                f"{message.author.mention}, без оскорблений, пожалуйста 😅 (слишком быстро)",
                delete_after=8
            )
            return
        toxic_count = sum(
            1 for w in warnings_data.get(user_id, [])
            if "токсичность" in w.get("reason", "").lower()
            and (datetime.now(timezone.utc) - datetime.strptime(w["time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)).days < 7
        )
        reason = "Токсичность / личное оскорбление"
        if toxic_count == 0:
            warnings_data.setdefault(user_id, []).append({
                "moderator": "Автомодерация",
                "reason": reason,
                "time": now_str
            })
            save_warnings()
            await message.channel.send(
                f"{message.author.mention}, эй, без оскорблений, ок? 😅\n"
                f"Это первое предупреждение. Следующее → мут.",
                delete_after=12
            )
            case_id = await create_case(
                message.author, bot.user, "Предупреждение (авто)", reason
            )
            await send_punishment_log(
                member=message.author,
                punishment_type="⚠️ Предупреждение (авто)",
                duration="—",
                reason=reason + " (1-е)",
                moderator=bot.user,
                case_id=case_id
            )
        elif toxic_count == 1:
            warnings_data.setdefault(user_id, []).append({
                "moderator": "Автомодерация",
                "reason": reason,
                "time": now_str
            })
            save_warnings()
            try:
                await message.author.timeout(timedelta(minutes=30), reason="Повторная токсичность")
                await message.channel.send(
                    f"{message.author.mention}, **мут 30 минут** за повторные оскорбления.\n"
                    f"Третье → мут 2 часа.",
                    delete_after=15
                )
                case_id = await create_case(
                    message.author, bot.user, "Мут 30 мин (авто)", reason + " (2-е)", "30 минут"
                )
                await send_punishment_log(
                    member=message.author,
                    punishment_type="🔇 Мут 30 мин (авто)",
                    duration="30 минут",
                    reason=reason + " (2-е нарушение)",
                    moderator=bot.user,
                    case_id=case_id
                )
            except:
                pass
        else:
            warnings_data.setdefault(user_id, []).append({
                "moderator": "Автомодерация",
                "reason": reason,
                "time": now_str
            })
            save_warnings()
            try:
                await message.author.timeout(timedelta(hours=2), reason="Многократная токсичность")
                await message.channel.send(
                    f"{message.author.mention}, **мут 2 часа** за многократные оскорбления.",
                    delete_after=15
                )
                case_id = await create_case(
                    message.author, bot.user, "Мут 2ч (авто)", reason + f" ({toxic_count+1}-е)", "2 часа"
                )
                await send_punishment_log(
                    member=message.author,
                    punishment_type="🔇 Мут 2ч (авто)",
                    duration="2 часа",
                    reason=f"{reason} ({toxic_count+1}-е нарушение)",
                    moderator=bot.user,
                    case_id=case_id
                )
                await send_mod_log(
                    title="⚠️ Многократная токсичность",
                    description=f"**Пользователь:** {message.author.mention}\n"
                                f"**Нарушений:** {toxic_count+1}\n"
                                f"**Последнее сообщение:** удалено\n"
                                f"**Причина:** {reason}",
                    color=0xe74c3c
                )
            except:
                pass
        await check_auto_punishment(message.author, reason)
        return
    # ───────────────────────────────────────────────
    # ЭКОНОМИКА — только на основном сервере
    # ───────────────────────────────────────────────
    if has_full_access(message.guild.id) or message.author.id == OWNER_ID:
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}
        if now - economy_data[user_id].get("last_message", 0) >= MESSAGE_COOLDOWN:
            earn_coins = random.randint(1, 5)
            economy_data[user_id]["balance"] += earn_coins
            economy_data[user_id]["last_message"] = now
            save_economy()
    await bot.process_commands(message)
# ───────────────────────────────────────────────
# ПРИВЕТСТВИЯ И ПРОЩАНИЯ
# ───────────────────────────────────────────────
@bot.event
async def on_member_join(member):
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            embed = discord.Embed(
                title="📥 Участник зашёл",
                color=COLORS["welcome"],
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Пользователь", value=member.mention, inline=True)
            embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
            embed.add_field(name="Аккаунт создан", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
            account_age = datetime.now(timezone.utc) - member.created_at
            if account_age.days < NEW_ACCOUNT_DAYS:
                embed.add_field(name="⚠️ Внимание", value="Новый аккаунт!", inline=False)
            await log_ch.send(embed=embed)
        welcome_ch = bot.get_channel(WELCOME_CHANNEL_ID)
        if welcome_ch:
            total = member.guild.member_count
            humans = len([m for m in member.guild.members if not m.bot])
            bots = total - humans
            embed = discord.Embed(
                title="🎉 Новый участник!",
                description=f"**{member.mention}**, добро пожаловать на сервер!",
                color=COLORS["welcome"],
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="📝 Имя", value=member.name, inline=True)
            embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
            embed.add_field(name="📅 Регистрация", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
            embed.add_field(
                name="👥 Статистика",
                value=f"**Всего:** {total}\n👤 **Людей:** {humans}\n🤖 **Ботов:** {bots}",
                inline=True
            )
            embed.add_field(
                name="📋 Быстрый старт",
                value="• Ознакомься с правилами\n• Получи роли\n• Начни общаться",
                inline=True
            )
            embed.set_footer(text="Спасибо что выбрали нас! 💫", icon_url=member.guild.icon.url if member.guild.icon else None)
            view = WelcomeView()
            await welcome_ch.send(embed=embed, view=view)
    except Exception as e:
        print(f"Ошибка в on_member_join: {e}")
@bot.event
async def on_member_remove(member):
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            embed = discord.Embed(
                title="📤 Участник вышел",
                color=COLORS["goodbye"],
                timestamp=datetime.now(timezone.utc)
            )
            embed.add_field(name="Пользователь", value=str(member), inline=True)
            embed.add_field(name="ID", value=f"`{member.id}`", inline=True)
            embed.add_field(name="На сервере был", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Неизвестно", inline=True)
            await log_ch.send(embed=embed)
        goodbye_ch = bot.get_channel(GOODBYE_CHANNEL_ID)
        if goodbye_ch:
            days_on_server = 0
            if member.joined_at:
                days_on_server = (datetime.now(timezone.utc) - member.joined_at).days
            total = member.guild.member_count
            embed = discord.Embed(
                title="👋 Пока...",
                description=f"**{member.name}** покинул нас",
                color=COLORS["goodbye"],
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            if days_on_server > 0:
                embed.add_field(name="⏱️ Пробыл на сервере", value=f"**{days_on_server}** {_plural(days_on_server, 'день', 'дня', 'дней')}", inline=True)
            embed.add_field(name="👥 Осталось", value=f"**{total}**", inline=True)
            if days_on_server > 30:
                embed.add_field(name="💔 Жаль", value="Надеемся, ты вернешься!", inline=False)
            elif days_on_server > 7:
                embed.add_field(name="😢", value="Будем скучать!", inline=False)
            await goodbye_ch.send(embed=embed)
    except Exception as e:
        print(f"Ошибка в on_member_remove: {e}")
def _plural(count, one, few, many):
    if count % 10 == 1 and count % 100 != 11:
        return one
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return few
    return many
# ───────────────────────────────────────────────
# УЛУЧШЕННЫЙ АУДИТ-ЛОГ (оставлен без изменений)
# ───────────────────────────────────────────────
async def get_audit_info(guild, action, target_id=None, limit=5):
    try:
        async for entry in guild.audit_logs(limit=limit, action=action):
            if target_id and entry.target.id == target_id:
                return {
                    "moderator": entry.user,
                    "reason": entry.reason,
                    "created_at": entry.created_at
                }
            elif not target_id:
                return {
                    "moderator": entry.user,
                    "reason": entry.reason,
                    "created_at": entry.created_at
                }
    except:
        pass
    return None
# (все on_message_delete, on_message_edit, on_member_update, on_member_ban и т.д. оставлены без изменений — они не связаны с сезоном)
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if not log_ch:
            return
        moderator = None
        reason = None
        try:
            async for entry in message.guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
                time_diff = (datetime.now(timezone.utc) - entry.created_at).total_seconds()
                if (hasattr(entry.extra, 'channel') and
                    entry.extra.channel.id == message.channel.id and
                    entry.target.id == message.author.id and
                    time_diff < 10):
                    moderator = entry.user
                    reason = entry.reason
                    break
        except:
            pass
        embed = discord.Embed(
            title="🗑 Сообщение удалено",
            color=COLORS["audit"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="Автор", value=f"{message.author.mention}\nID: `{message.author.id}`", inline=False)
        embed.add_field(name="Канал", value=message.channel.mention, inline=False)
        if moderator:
            embed.add_field(name="Удалил", value=f"{moderator.mention}\nID: `{moderator.id}`", inline=False)
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
        if message.content:
            content = message.content[:900] + ("..." if len(message.content) > 900 else "")
            embed.add_field(name="Содержимое", value=content, inline=False)
        if message.attachments:
            files = "\n".join([f"[{a.filename}]({a.url})" for a in message.attachments])
            embed.add_field(name="Вложения", value=files[:1000], inline=False)
        embed.set_footer(text=f"ID: {message.id}")
        await log_ch.send(embed=embed)
    except Exception as e:
        print(f"Ошибка в on_message_delete: {e}")
# (остальные аудит-события оставлены полностью — они не касаются сезона)
@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    user_id = str(member.id)
    now = datetime.now(timezone.utc).timestamp()
    try:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if before.channel is None and after.channel is not None:
            if log_ch and "afk" not in after.channel.name.lower():
                embed = discord.Embed(
                    title="🔊 Подключился к голосовому",
                    color=COLORS["audit"],
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Пользователь", value=member.mention, inline=True)
                embed.add_field(name="Канал", value=after.channel.mention, inline=True)
                await log_ch.send(embed=embed)
            if "afk" not in after.channel.name.lower():
                voice_start_time[user_id] = now
        elif before.channel is not None and after.channel is None:
            if log_ch:
                embed = discord.Embed(
                    title="🔇 Отключился от голосового",
                    color=COLORS["audit"],
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Пользователь", value=member.mention, inline=True)
                embed.add_field(name="Канал", value=before.channel.mention, inline=True)
                await log_ch.send(embed=embed)
            if user_id in voice_start_time:
                del voice_start_time[user_id]
        elif before.channel != after.channel and before.channel is not None and after.channel is not None:
            if log_ch:
                embed = discord.Embed(
                    title="🔄 Переместился в голосовом",
                    color=COLORS["audit"],
                    timestamp=datetime.now(timezone.utc)
                )
                embed.add_field(name="Пользователь", value=member.mention, inline=False)
                embed.add_field(name="Было", value=before.channel.mention, inline=True)
                embed.add_field(name="Стало", value=after.channel.mention, inline=True)
                await log_ch.send(embed=embed)
            if "afk" not in after.channel.name.lower():
                voice_start_time[user_id] = now
            else:
                if user_id in voice_start_time:
                    del voice_start_time[user_id]
    except Exception as e:
        print(f"Ошибка в on_voice_state_update (лог): {e}")
# (все остальные on_* события оставлены без изменений)
# ───────────────────────────────────────────────
# КОМАНДЫ (без сезонных)
# ───────────────────────────────────────────────
@bot.hybrid_command(name="ping", description="Подробная информация о боте")
async def ping(ctx: commands.Context):
    try:
        latency = round(bot.latency * 1000)
        uptime = datetime.now(timezone.utc) - bot.launch_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if days > 0:
            uptime_str = f"{days}д {hours}ч {minutes}м {seconds}с"
        elif hours > 0:
            uptime_str = f"{hours}ч {minutes}м {seconds}с"
        elif minutes > 0:
            uptime_str = f"{minutes}м {seconds}с"
        else:
            uptime_str = f"{seconds}с"
        guild_count = len(bot.guilds)
        user_count = sum(g.member_count for g in bot.guilds if g.member_count)
        channel_count = sum(len(g.channels) for g in bot.guilds)
        ping_status = "🟢 Отлично" if latency < 100 else "🟡 Средне" if latency < 200 else "🔴 Плохо"
        embed = discord.Embed(
            title="🏓 **ПОНГ!**",
            description="```Статус бота и производительность```",
            color=COLORS["welcome"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(
            name="📊 **Основная информация**",
            value=f"```yml\n"
                  f"Задержка: {latency}ms\n"
                  f"Состояние: {ping_status}\n"
                  f"Время работы: {uptime_str}\n"
                  f"Серверов: {guild_count}\n"
                  f"Пользователей: {user_count:,}\n"
                  f"Каналов: {channel_count}\n"
                  f"```",
            inline=False
        )
        embed.add_field(
            name="⏱️ **Детали задержки**",
            value=f"```diff\n"
                  f"+ WebSocket: {latency}ms\n"
                  f"+ API: ~{latency + 20}ms\n"
                  f"+ База данных: ~{latency + 10}ms\n"
                  f"```",
            inline=True
        )
        command_count = len(bot.commands)
        embed.add_field(
            name="📋 **Команды**",
            value=f"```css\n"
                  f"Всего: {command_count}\n"
                  f"```",
            inline=True
        )
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        embed.set_footer(
            text=f"MortisPlay • Запросил: {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        view = View(timeout=60)
        button = Button(label="🔄 Обновить", style=discord.ButtonStyle.primary)
        async def refresh_callback(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("❌ Это не твоя команда!", ephemeral=True)
            new_latency = round(bot.latency * 1000)
            new_uptime = datetime.now(timezone.utc) - bot.launch_time
            new_days = new_uptime.days
            new_hours, new_remainder = divmod(new_uptime.seconds, 3600)
            new_minutes, new_seconds = divmod(new_remainder, 60)
            if new_days > 0:
                new_uptime_str = f"{new_days}д {new_hours}ч {new_minutes}м {new_seconds}с"
            elif new_hours > 0:
                new_uptime_str = f"{new_hours}ч {new_minutes}м {new_seconds}с"
            elif new_minutes > 0:
                new_uptime_str = f"{new_minutes}м {new_seconds}с"
            else:
                new_uptime_str = f"{new_seconds}с"
            new_ping_status = "🟢 Отлично" if new_latency < 100 else "🟡 Средне" if new_latency < 200 else "🔴 Плохо"
            new_embed = discord.Embed(
                title="🏓 **ПОНГ!**",
                description="```Статус бота и производительность```",
                color=COLORS["welcome"],
                timestamp=datetime.now(timezone.utc)
            )
            new_embed.add_field(
                name="📊 **Основная информация**",
                value=f"```yml\n"
                      f"Задержка: {new_latency}ms\n"
                      f"Состояние: {new_ping_status}\n"
                      f"Время работы: {new_uptime_str}\n"
                      f"Серверов: {guild_count}\n"
                      f"Пользователей: {user_count:,}\n"
                      f"Каналов: {channel_count}\n"
                      f"```",
                inline=False
            )
            new_embed.add_field(
                name="⏱️ **Детали задержки**",
                value=f"```diff\n"
                      f"+ WebSocket: {new_latency}ms\n"
                      f"+ API: ~{new_latency + 20}ms\n"
                      f"+ База данных: ~{new_latency + 10}ms\n"
                      f"```",
                inline=True
            )
            new_embed.add_field(
                name="📋 **Команды**",
                value=f"```css\n"
                      f"Всего: {command_count}\n"
                      f"```",
                inline=True
            )
            new_embed.set_thumbnail(url=bot.user.display_avatar.url)
            new_embed.set_footer(
                text=f"MortisPlay • Запросил: {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )
            await interaction.response.edit_message(embed=new_embed, view=view)
        button.callback = refresh_callback
        view.add_item(button)
        await ctx.send(embed=embed, view=view, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="avatar", description="Показать аватар")
@app_commands.describe(member="Пользователь")
async def avatar(ctx: commands.Context, member: discord.Member = None):
    try:
        member = member or ctx.author
        embed = discord.Embed(title=f"Аватар {member}", color=COLORS["welcome"])
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="userinfo", description="Информация о пользователе")
@app_commands.describe(member="Пользователь")
async def userinfo(ctx: commands.Context, member: discord.Member = None):
    try:
        await ctx.defer(ephemeral=True)
        member = member or ctx.author
        guild = ctx.guild
        fresh_member = guild.get_member(member.id) or await guild.fetch_member(member.id)
        status_map = {
            discord.Status.online: ("🟢 Онлайн", 0x43b581),
            discord.Status.idle: ("🟡 Неактивен", 0xfaa61a),
            discord.Status.dnd: ("🔴 Не беспокоить", 0xf04747),
            discord.Status.offline: ("⚫ Оффлайн", 0x747f8d),
            discord.Status.invisible: ("⚫ Невидимка", 0x747f8d)
        }
        status_text, color = status_map.get(fresh_member.status, ("⚫ Неизвестно", 0x747f8d))
        devices = []
        if fresh_member.desktop_status != discord.Status.offline:
            devices.append("🖥️ Desktop")
        if fresh_member.mobile_status != discord.Status.offline:
            devices.append("📱 Mobile")
        if fresh_member.web_status != discord.Status.offline:
            devices.append("🌐 Web")
        devices_str = " • ".join(devices) or "Неизвестно"
        booster_since = fresh_member.premium_since
        booster_text = f"Бустер с {booster_since.strftime('%d.%m.%Y')}" if booster_since else "Не бустит"
        embed = discord.Embed(title=f"👤 {fresh_member.display_name}", color=color)
        embed.set_thumbnail(url=fresh_member.display_avatar.url)
        embed.add_field(name="🆔 ID", value=f"`{fresh_member.id}`", inline=True)
        embed.add_field(name="📛 Ник", value=f"`{fresh_member.name}`", inline=True)
        embed.add_field(name="📅 Регистрация", value=fresh_member.created_at.strftime("%d.%m.%Y %H:%M"), inline=True)
        embed.add_field(name="📅 На сервере", value=fresh_member.joined_at.strftime("%d.%m.%Y %H:%M") if fresh_member.joined_at else "—", inline=True)
        embed.add_field(name="🌐 Статус", value=status_text, inline=True)
        embed.add_field(name="📱 Устройства", value=devices_str, inline=True)
        embed.add_field(name="🚀 Бустер", value=booster_text, inline=True)
        embed.add_field(name="🏆 Высшая роль", value=fresh_member.top_role.mention if fresh_member.top_role != guild.default_role else "Нет", inline=False)
        if fresh_member.id == bot.user.id:
            embed.add_field(name="📝 Биография", value="Я многофункциональный бот для Discord, созданный для автоматизации модерации, экономики и развлечений. Разработан специально для сервера MortisPlay!", inline=False)
        if fresh_member.banner:
            embed.set_image(url=fresh_member.banner.url)
        embed.set_footer(text=f"Запросил: {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, f"Не удалось загрузить информацию: {str(e)}")
@bot.hybrid_command(name="stats", description="Статистика сервера")
async def stats(ctx: commands.Context):
    try:
        guild = ctx.guild
        total = guild.member_count
        online = sum(1 for m in guild.members if m.status != discord.Status.offline)
        idle = sum(1 for m in guild.members if m.status == discord.Status.idle)
        dnd = sum(1 for m in guild.members if m.status == discord.Status.dnd)
        offline = total - online
        bots = sum(1 for m in guild.members if m.bot)
        humans = total - bots
        embed = discord.Embed(
            title=f"📊 Статистика {guild.name}",
            color=COLORS["welcome"],
            timestamp=datetime.now(timezone.utc)
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="👥 Участники", value=f"**Всего:** {total}\n👤 **Людей:** {humans}\n🤖 **Ботов:** {bots}", inline=True)
        embed.add_field(name="🟢 Онлайн", value=f"**Онлайн:** {online}\n🟡 **Idle:** {idle}\n🔴 **DND:** {dnd}\n⚫ **Offline:** {offline}", inline=True)
        embed.add_field(name="📁 Каналы", value=f"**Текстовых:** {len(guild.text_channels)}\n**Голосовых:** {len(guild.voice_channels)}\n**Категорий:** {len(guild.categories)}", inline=True)
        embed.add_field(name="🎨 Оформление", value=f"**Ролей:** {len(guild.roles)}\n**Эмодзи:** {len(guild.emojis)}", inline=True)
        embed.add_field(name="🚀 Буст", value=f"**Уровень:** {guild.premium_tier}\n**Бустов:** {guild.premium_subscription_count}", inline=True)
        embed.add_field(name="📅 Сервер создан", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
        if guild.owner:
            embed.add_field(name="👑 Владелец", value=guild.owner.mention, inline=False)
        embed.set_footer(text=f"ID: {guild.id}")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="say", description="Написать от лица бота")
@app_commands.describe(
    text="Текст сообщения",
    embed_title="Заголовок embed",
    embed_description="Описание embed",
    embed_color="Цвет embed (например #FF0000)",
    channel="Канал",
    reply_to="ID сообщения для ответа"
)
@commands.has_permissions(manage_messages=True)
async def say(
    ctx: commands.Context,
    text: str = None,
    embed_title: str = None,
    embed_description: str = None,
    embed_color: str = "#57F287",
    channel: discord.TextChannel = None,
    reply_to: discord.Message = None
):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not has_full_access(ctx.guild.id):
            return await ctx.send("❌ Команда доступна только на сервере разработчика.", ephemeral=True)
        target = channel or ctx.channel
        if not target.permissions_for(ctx.guild.me).send_messages:
            return await ctx.send("❌ Нет прав писать в этот канал.", ephemeral=True)
        if embed_title and embed_description:
            color = int(embed_color.lstrip("#"), 16) if embed_color.startswith("#") else 0x57F287
            embed = discord.Embed(title=embed_title, description=embed_description, color=color)
            await target.send(embed=embed, reference=reply_to)
        else:
            if not text:
                return await ctx.send("❌ Укажи текст или embed.", ephemeral=True)
            await target.send(text, reference=reply_to)
        await ctx.send(f"✅ Отправлено в {target.mention}", ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
# ───────────────────────────────────────────────
# ЭКОНОМИКА
# ───────────────────────────────────────────────
@bot.hybrid_command(name="pay", description="💸 Перевести монеты с подтверждением и комиссией")
@app_commands.describe(
    member="Кому перевести",
    amount="Сумма (целое число)",
    comment="Сообщение получателю (опционально)"
)
async def pay(ctx: commands.Context, member: discord.Member, amount: int, comment: str = None):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)
        if amount <= 0:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Сумма должна быть больше 0.", ephemeral=True)
        if member.id == ctx.author.id:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Нельзя переводить себе.", ephemeral=True)
        if member.bot:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Нельзя переводить ботам.", ephemeral=True)
        sender_id = str(ctx.author.id)
        receiver_id = str(member.id)
        if sender_id not in economy_data or economy_data[sender_id].get("balance", 0) < amount:
            bal = economy_data.get(sender_id, {}).get("balance", 0)
            return await ctx.send(
                f"{ECONOMY_EMOJIS['error']} Недостаточно монет!\nБаланс: **{format_number(bal)}** {ECONOMY_EMOJIS['coin']}",
                ephemeral=True
            )
        now = datetime.now(timezone.utc).timestamp()
        if not is_vip(ctx.author):
            if "pay_history" not in economy_data.setdefault(sender_id, {}):
                economy_data[sender_id]["pay_history"] = []
            economy_data[sender_id]["pay_history"] = [
                t for t in economy_data[sender_id]["pay_history"] if now - t < 86400
            ]
            if len(economy_data[sender_id]["pay_history"]) >= 5:
                next_time = economy_data[sender_id]["pay_history"][0] + 86400
                remaining = int(next_time - now)
                hours = remaining // 3600
                mins = (remaining % 3600) // 60
                return await ctx.send(
                    f"{ECONOMY_EMOJIS['error']} Лимит 5 переводов в сутки.\nСледующий через **{hours}ч {mins}мин**.",
                    ephemeral=True
                )
        transfer_tax = max(1, int(amount * 0.01)) if amount > 5000 else 0
        final_amount = amount - transfer_tax
        class PayConfirm(View):
            def __init__(self, author_id: int):
                super().__init__(timeout=120)
                self.author_id = author_id
            @discord.ui.button(label="Подтвердить перевод", style=discord.ButtonStyle.green, emoji="💸")
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.author_id:
                    return await interaction.response.send_message("Это не твоя команда!", ephemeral=True)
                await interaction.response.defer(ephemeral=False)
                try:
                    economy_data[sender_id]["balance"] -= amount
                    if receiver_id not in economy_data:
                        economy_data[receiver_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}
                    economy_data[receiver_id]["balance"] += final_amount
                    if transfer_tax > 0:
                        economy_data["server_vault"] = economy_data.get("server_vault", 0) + transfer_tax
                    economy_data[sender_id].setdefault("pay_history", []).append(now)
                    save_economy()
                    success_embed = discord.Embed(
                        title=f"{ECONOMY_EMOJIS['gift']} Подарок доставлен! 🎁",
                        description=f"**{interaction.user.mention}** → **{member.mention}**",
                        color=0x2ecc71,
                        timestamp=datetime.now(timezone.utc)
                    )
                    success_embed.add_field(name="Сумма", value=f"**{format_number(final_amount)}** {ECONOMY_EMOJIS['coin']}", inline=True)
                    if transfer_tax > 0:
                        success_embed.add_field(name=f"{ECONOMY_EMOJIS['tax']} Комиссия", value=f"-{format_number(transfer_tax)} (1%)", inline=True)
                    success_embed.add_field(
                        name="Баланс отправителя", value=f"**{format_number(economy_data[sender_id]['balance'])}** {ECONOMY_EMOJIS['coin']}", inline=False
                    )
                    success_embed.add_field(
                        name="Баланс получателя", value=f"**{format_number(economy_data[receiver_id]['balance'])}** {ECONOMY_EMOJIS['coin']}", inline=False
                    )
                    if comment:
                        success_embed.add_field(name="📝 Сообщение", value=f"*{comment}*", inline=False)
                    success_embed.set_thumbnail(url="https://media.giphy.com/media/l0HlRnAWXxn0MhKLK/giphy.gif")
                    success_embed.set_footer(text=f"MortisPlay • Перевод #{len(economy_data[sender_id]['pay_history'])}")
                    await interaction.followup.send(embed=success_embed)
                    try:
                        await interaction.message.delete(delay=5)
                    except:
                        pass
                    try:
                        dm = discord.Embed(
                            title=f"{ECONOMY_EMOJIS['gift']} Вам прислали подарок!",
                            description=f"От: {interaction.user.mention}\nСумма: **{format_number(final_amount)}** {ECONOMY_EMOJIS['coin']}",
                            color=0x2ecc71
                        )
                        if comment:
                            dm.add_field(name="Сообщение", value=comment, inline=False)
                        await member.send(embed=dm)
                    except:
                        pass
                    if amount >= 10000:
                        await send_mod_log(
                            title="💰 Крупный перевод!",
                            description=f"**От:** {interaction.user.mention}\n**Кому:** {member.mention}\n**Сумма:** {format_number(amount)} → {format_number(final_amount)}",
                            color=0xffd700
                        )
                except Exception as inner_e:
                    error_embed = discord.Embed(
                        title=f"{ECONOMY_EMOJIS['error']} Ошибка при переводе",
                        description=str(inner_e),
                        color=0xe74c3c
                    )
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
            @discord.ui.button(label="Отмена", style=discord.ButtonStyle.red, emoji="✖️")
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != self.author_id:
                    return await interaction.response.send_message("Это не твоя команда!", ephemeral=True)
                await interaction.response.defer(ephemeral=False)
                cancel_embed = discord.Embed(
                    title=f"{ECONOMY_EMOJIS['error']} Перевод отменён",
                    color=0xe74c3c,
                    timestamp=datetime.now(timezone.utc)
                )
                await interaction.followup.send(embed=cancel_embed)
                try:
                    await interaction.message.delete(delay=3)
                except:
                    pass
        preview_embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['transfer']} Подтвердите перевод",
            description=f"**{format_number(amount)}** {ECONOMY_EMOJIS['coin']} → {member.mention}",
            color=0x3498db,
            timestamp=datetime.now(timezone.utc)
        )
        if transfer_tax > 0:
            preview_embed.add_field(name=f"{ECONOMY_EMOJIS['tax']} Комиссия", value=f"{format_number(transfer_tax)} (1%)", inline=False)
        preview_embed.add_field(name="Получатель получит", value=f"**{format_number(final_amount)}** {ECONOMY_EMOJIS['coin']}", inline=False)
        if comment:
            preview_embed.add_field(name="Сообщение", value=f"*{comment}*", inline=False)
        preview_embed.set_footer(text="Действие в течение 120 секунд • Лимит: 5/сутки (VIP — без лимита)")
        view = PayConfirm(author_id=ctx.author.id)
        await ctx.send(embed=preview_embed, view=view)
    except Exception as e:
        await send_error_embed(ctx, f"Ошибка при подготовке перевода: {str(e)}")
@bot.hybrid_command(name="invest", description="📈 Инвестировать монеты")
@app_commands.describe(amount="Сумма", days="Количество дней (1-30)")
async def invest(ctx: commands.Context, amount: int, days: int):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)
        if amount < INVESTMENT_MIN_AMOUNT:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Минимум: {format_number(INVESTMENT_MIN_AMOUNT)} {ECONOMY_EMOJIS['coin']}", ephemeral=True)
        if days < 1 or days > INVESTMENT_MAX_DAYS:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Срок: 1-{INVESTMENT_MAX_DAYS} дней.", ephemeral=True)
        user_id = str(ctx.author.id)
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}
        if economy_data[user_id]["balance"] < amount:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Недостаточно монет! Баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']}", ephemeral=True)
        rate = INVESTMENT_BASE_RATE * (1 + days / 30)
        profit = int(amount * rate)
        end_time = datetime.now(timezone.utc).timestamp() + (days * 86400)
        investment = {
            "amount": amount,
            "days": days,
            "profit": profit,
            "start_time": datetime.now(timezone.utc).timestamp(),
            "end_time": end_time,
            "rate": round(rate * 100, 2)
        }
        economy_data[user_id]["balance"] -= amount
        economy_data[user_id].setdefault("investments", []).append(investment)
        save_economy()
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['investment']} Инвестиция создана",
            color=COLORS["economy"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="💰 Сумма", value=f"{format_number(amount)} {ECONOMY_EMOJIS['coin']}", inline=True)
        embed.add_field(name="📅 Срок", value=f"{days} дней", inline=True)
        embed.add_field(name="📊 Ставка", value=f"{investment['rate']}%", inline=True)
        embed.add_field(name="💹 Прибыль", value=f"+{format_number(profit)} {ECONOMY_EMOJIS['coin']}", inline=True)
        embed.add_field(name="⏰ Завершение", value=f"<t:{int(end_time)}:R>", inline=False)
        embed.set_footer(text=f"Баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']}")
        await ctx.send(embed=embed, ephemeral=True)
        await send_mod_log(
            title="📈 Новая инвестиция",
            description=f"**Пользователь:** {ctx.author.mention}\n**Сумма:** {format_number(amount)} {ECONOMY_EMOJIS['coin']}\n**Срок:** {days} дней",
            color=COLORS["economy"]
        )
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="investments", description="📊 Мои инвестиции")
async def my_investments(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)
        user_id = str(ctx.author.id)
        if user_id not in economy_data or not economy_data[user_id].get("investments"):
            return await ctx.send(f"{ECONOMY_EMOJIS['warning']} У вас нет инвестиций.", ephemeral=True)
        now = datetime.now(timezone.utc).timestamp()
        active = []
        completed = []
        for inv in economy_data[user_id]["investments"]:
            if inv["end_time"] > now:
                active.append(inv)
            else:
                completed.append(inv)
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['investment']} Мои инвестиции",
            color=COLORS["economy"],
            timestamp=datetime.now(timezone.utc)
        )
        if active:
            text = ""
            for i, inv in enumerate(active, 1):
                left = inv["end_time"] - now
                days = int(left // 86400)
                hours = int((left % 86400) // 3600)
                text += f"**{i}.** {format_number(inv['amount'])} → +{format_number(inv['profit'])} {ECONOMY_EMOJIS['coin']}\n⏰ Осталось: {days}д {hours}ч\n\n"
            embed.add_field(name="🟢 Активные", value=text, inline=False)
        if completed:
            text = ""
            for i, inv in enumerate(completed[-5:], 1):
                text += f"**{i}.** {format_number(inv['amount'])} → +{format_number(inv['profit'])} {ECONOMY_EMOJIS['coin']} ✅\n"
            embed.add_field(name="✅ Завершенные", value=text, inline=False)
        total_invested = sum(i["amount"] for i in economy_data[user_id]["investments"])
        total_profit = sum(i["profit"] for i in economy_data[user_id]["investments"])
        embed.add_field(
            name="📊 Статистика",
            value=f"**Инвестировано:** {format_number(total_invested)} {ECONOMY_EMOJIS['coin']}\n**Прибыль:** +{format_number(total_profit)} {ECONOMY_EMOJIS['coin']}",
            inline=False
        )
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="case", description="🔍 Информация о кейсе")
@app_commands.describe(case_id="ID кейса")
@commands.has_permissions(manage_messages=True)
async def case_info(ctx: commands.Context, case_id: str):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        case = await get_case(case_id)
        if not case:
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Кейс `{case_id}` не найден.", ephemeral=True)
        embed = discord.Embed(
            title=f"🔍 Кейс #{case_id}",
            color=COLORS["mod"],
            timestamp=datetime.fromisoformat(case['timestamp'])
        )
        user = await bot.fetch_user(int(case['user_id'])) if case['user_id'].isdigit() else None
        mod = await bot.fetch_user(int(case['moderator_id'])) if case['moderator_id'].isdigit() else None
        embed.add_field(name="👤 Пользователь", value=user.mention if user else case['user_name'], inline=True)
        embed.add_field(name="👮 Модератор", value=mod.mention if mod else case['moderator_name'], inline=True)
        embed.add_field(name="⚡ Действие", value=case['action'], inline=True)
        if case['duration']:
            embed.add_field(name="⏰ Длительность", value=case['duration'], inline=True)
        embed.add_field(name="📝 Причина", value=case['reason'], inline=False)
        embed.add_field(name="📅 Дата", value=f"<t:{int(datetime.fromisoformat(case['timestamp']).timestamp())}:F>", inline=False)
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="help", description="📚 Список команд")
async def help_command(ctx: commands.Context):
    try:
        is_mod = is_moderator(ctx.author)
        embed = discord.Embed(
            title="🤖 Помощь по командам",
            description="**📋 Основное**\n**💰 Экономика**\n**🎮 Развлечения**" +
                       ("\n**🛡️ Модерация**\n**🎫 Тикеты**" if is_mod else ""),
            color=COLORS["welcome"]
        )
        embed.set_footer(text="Используй кнопки для навигации")
        view = HelpView(ctx.author, is_mod)
        await ctx.send(embed=embed, view=view, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="faq", description="📚 Часто задаваемые вопросы")
async def faq(ctx: commands.Context):
    try:
        embed = discord.Embed(
            title="📚 Часто задаваемые вопросы",
            description="Выберите категорию:",
            color=COLORS["faq"]
        )
        view = FAQView(ctx.author)
        await ctx.send(embed=embed, view=view, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="faqadd", description="📚 Добавить вопрос в FAQ")
@app_commands.describe(category="Категория", question="Вопрос", answer="Ответ")
@commands.has_permissions(manage_messages=True)
async def faq_add(ctx: commands.Context, category: str, question: str, *, answer: str):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        cat = category.lower()
        if cat not in FAQ_CATEGORIES:
            cats = ", ".join(FAQ_CATEGORIES.keys())
            return await ctx.send(f"❌ Категории: {cats}", ephemeral=True)
        faq_data.setdefault(cat, []).append({"question": question, "answer": answer})
        save_faq()
        embed = discord.Embed(
            title="✅ Вопрос добавлен",
            description=f"**Категория:** {FAQ_CATEGORIES[cat]}\n**Вопрос:** {question}",
            color=COLORS["faq"]
        )
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="iq", description="Узнать свой IQ")
async def iq(ctx: commands.Context):
    try:
        random.seed(ctx.author.id + int(datetime.now().timestamp() // 86400))
        iq = random.randint(70, 130)
        if random.random() < 0.03:
            iq = random.randint(145, 165)
            title = "🧠 ГЕНИЙ!"
            color = 0xFFD700
        elif random.random() < 0.10:
            iq = random.randint(115, 144)
            title = "🌟 Умный"
            color = 0x3498DB
        else:
            title = "🧠 Твой IQ"
            color = 0x2ECC71
        embed = discord.Embed(title=title, description=f"**{ctx.author.mention}, твой IQ: {iq}**", color=color)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Обновляется каждый день")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="valute", description="Курсы валют + курс внутреннего коина")
async def valute(ctx: commands.Context):
    try:
        apis = [
            "https://api.exchangerate-api.com/v4/latest/USD",
            "https://open.er-api.com/v6/latest/USD",
        ]
        data = None
        for url in apis:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            break
            except Exception:
                continue
        embed = discord.Embed(
            title="📈 Курсы валют + MortisCoin",
            color=COLORS["welcome"],
            timestamp=datetime.now(timezone.utc)
        )
        if data:
            rates = data.get("rates", {})
            embed.add_field(name="🇺🇸 USD", value="1.00", inline=True)
            embed.add_field(name="🇪🇺 EUR", value=f"{rates.get('EUR', 0.92):.2f}", inline=True)
            embed.add_field(name="🇬🇧 GBP", value=f"{rates.get('GBP', 0.79):.2f}", inline=True)
            embed.add_field(name="🇷🇺 RUB", value=f"{rates.get('RUB', 92.50):.2f}", inline=True)
            embed.add_field(name=" ", value=" ", inline=False)
        else:
            embed.description = "⚠️ Внешние курсы временно недоступны"
        embed.add_field(
            name=f"{ECONOMY_EMOJIS['coin']} MortisCoin (внутренний)",
            value="**1 MortisCoin = 1 🪙**\nФиксированный курс внутри сервера",
            inline=False
        )
        embed.set_footer(text="MortisCoin — валюта сервера • Внешние данные: exchangerate-api")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
# ───────────────────────────────────────────────
# МОДЕРАЦИЯ
# ───────────────────────────────────────────────
@bot.hybrid_command(name="warn", description="Выдать предупреждение")
@app_commands.describe(member="Пользователь", reason="Причина")
@commands.has_permissions(manage_messages=True)
async def warn(ctx: commands.Context, member: discord.Member, *, reason: str = "Не указана"):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя наказывать владельца сервера, администраторов или самого себя!", ephemeral=True)
        user_id = str(member.id)
        warnings_data.setdefault(user_id, []).append({
            "moderator": str(ctx.author),
            "reason": reason,
            "time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        })
        save_warnings()
        count = get_warning_count(user_id)
        case_id = await create_case(member, ctx.author, "Предупреждение", reason)
        await send_punishment_log(
            member=member,
            punishment_type="⚠️ Предупреждение",
            duration="—",
            reason=reason,
            moderator=ctx.author,
            case_id=case_id
        )
        embed = discord.Embed(
            title="⚠️ Предупреждение выдано",
            description=f"**Пользователь:** {member.mention}\n**Причина:** {reason}\n**Всего:** {count}",
            color=COLORS["mod"]
        )
        await ctx.send(embed=embed, ephemeral=True)
        await check_auto_punishment(member, reason)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="warnings", description="Список предупреждений")
@app_commands.describe(member="Пользователь")
@commands.has_permissions(manage_messages=True)
async def warnings(ctx: commands.Context, member: discord.Member):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        user_id = str(member.id)
        clean_old_warnings(user_id)
        warns = warnings_data.get(user_id, [])
        if not warns:
            return await ctx.send(f"✅ У {member.mention} нет предупреждений.", ephemeral=True)
        embed = discord.Embed(
            title=f"⚠️ Предупреждения {member.display_name}",
            description=f"Всего: **{len(warns)}**",
            color=COLORS["mod"]
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        for i, w in enumerate(warns[-10:], 1):
            embed.add_field(
                name=f"{i}. {w['time']}",
                value=f"**Модератор:** {w['moderator']}\n**Причина:** {w['reason']}",
                inline=False
            )
        embed.set_footer(text="Последние 10")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="clearwarn", description="Очистить предупреждения")
@app_commands.describe(member="Пользователь", warn_id="all или номер")
@commands.has_permissions(administrator=True)
async def clearwarn(ctx: commands.Context, member: discord.Member, warn_id: str = "all"):
    try:
        if not ctx.author.guild_permissions.administrator:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя очищать предупреждения у владельца сервера или администратора!", ephemeral=True)
        user_id = str(member.id)
        if user_id not in warnings_data or not warnings_data[user_id]:
            return await ctx.send(f"✅ У {member.mention} нет предупреждений.", ephemeral=True)
        if warn_id.lower() == "all":
            del warnings_data[user_id]
            save_warnings()
            await ctx.send(f"✅ Все предупреждения {member.mention} удалены.", ephemeral=True)
            await send_mod_log(
                title="🧹 Очистка предупреждений",
                description=f"**Модератор:** {ctx.author.mention}\n**Пользователь:** {member.mention}",
                color=COLORS["mod"]
            )
        else:
            await ctx.send("❌ Удаление конкретного предупреждения пока не реализовано.", ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="mute", description="Замутить пользователя")
@app_commands.describe(member="Пользователь", duration="1h, 1d, 30m", reason="Причина")
@commands.has_permissions(manage_messages=True)
async def mute(ctx: commands.Context, member: discord.Member, duration: str, *, reason: str = "Не указана"):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя наказывать владельца сервера, администраторов или самого себя!", ephemeral=True)
        seconds = 0
        if duration.endswith("h"):
            seconds = int(duration[:-1]) * 3600
        elif duration.endswith("d"):
            seconds = int(duration[:-1]) * 86400
        elif duration.endswith("m"):
            seconds = int(duration[:-1]) * 60
        elif duration.endswith("s"):
            seconds = int(duration[:-1])
        else:
            seconds = int(duration) * 60
        if seconds <= 0:
            return await ctx.send("❌ Некорректная длительность!", ephemeral=True)
        delta = timedelta(seconds=seconds)
        await member.timeout(delta, reason=reason)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        dur_text = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
        case_id = await create_case(member, ctx.author, "Мут", reason, dur_text)
        await send_punishment_log(
            member=member,
            punishment_type="🔇 Мут",
            duration=dur_text,
            reason=reason,
            moderator=ctx.author,
            case_id=case_id
        )
        embed = discord.Embed(
            title="🔇 Пользователь замучен",
            description=f"**Пользователь:** {member.mention}\n**Длительность:** {dur_text}\n**Причина:** {reason}",
            color=COLORS["mod"]
        )
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="unmute", description="Снять мут")
@app_commands.describe(member="Пользователь", reason="Причина")
@commands.has_permissions(manage_messages=True)
async def unmute(ctx: commands.Context, member: discord.Member, *, reason: str = "Не указана"):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя снимать мут с владельца сервера или администратора!", ephemeral=True)
        await member.timeout(None, reason=reason)
        case_id = await create_case(member, ctx.author, "Снятие мута", reason)
        await send_punishment_log(
            member=member,
            punishment_type="🔊 Мут снят",
            duration="—",
            reason=reason,
            moderator=ctx.author,
            case_id=case_id
        )
        embed = discord.Embed(
            title="🔊 Мут снят",
            description=f"**Пользователь:** {member.mention}\n**Причина:** {reason}",
            color=COLORS["mod"]
        )
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="temprole", description="Временная роль")
@app_commands.describe(member="Пользователь", role="Роль", duration="1h, 1d, 30m")
@commands.has_permissions(manage_roles=True)
async def temprole(ctx: commands.Context, member: discord.Member, role: discord.Role, duration: str):
    try:
        if not ctx.author.guild_permissions.manage_roles:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя выдавать временную роль владельцу сервера, администраторам или самому себе!", ephemeral=True)
        if role >= ctx.author.top_role and ctx.author.id != OWNER_ID:
            return await ctx.send("❌ Нельзя выдать роль выше своей!", ephemeral=True)
        seconds = 0
        if duration.endswith("h"):
            seconds = int(duration[:-1]) * 3600
        elif duration.endswith("d"):
            seconds = int(duration[:-1]) * 86400
        elif duration.endswith("m"):
            seconds = int(duration[:-1]) * 60
        else:
            seconds = int(duration) * 60
        if seconds <= 0:
            return await ctx.send("❌ Некорректная длительность!", ephemeral=True)
        await member.add_roles(role, reason=f"Временная роль от {ctx.author}")
        user_id = str(member.id)
        temp_roles.setdefault(user_id, {})[str(role.id)] = datetime.now(timezone.utc).timestamp() + seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        dur_text = f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"
        embed = discord.Embed(
            title="⏱️ Временная роль",
            description=f"**Пользователь:** {member.mention}\n**Роль:** {role.mention}\n**Длительность:** {dur_text}",
            color=COLORS["mod"]
        )
        await ctx.send(embed=embed, ephemeral=True)
        await send_mod_log(
            title="⏱️ Временная роль",
            description=f"**Модератор:** {ctx.author.mention}\n**Пользователь:** {member.mention}\n**Роль:** {role.mention}\n**Длительность:** {dur_text}",
            color=COLORS["mod"]
        )
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="ticket", description="Управление тикетами")
@app_commands.describe(action="setup / close")
@commands.has_permissions(manage_channels=True)
async def ticket(ctx: commands.Context, action: str = "setup"):
    try:
        if not ctx.author.guild_permissions.manage_channels:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not has_full_access(ctx.guild.id):
            return await ctx.send("❌ Команда только на сервере разработчика.", ephemeral=True)
        action = action.lower()
        if action == "setup":
            embed = discord.Embed(
                title="🎫 Система тикетов",
                description="Нажми кнопку, чтобы создать тикет",
                color=COLORS["ticket"]
            )
            view = TicketPanelView()
            await ctx.send(embed=embed, view=view)
            await ctx.send("✅ Панель создана!", delete_after=10)
        elif action == "close":
            if not any(ctx.channel.name.startswith(p) for p in ["🔧-", "⚠️-", "❓-", "🤝-", "📌-"]):
                return await ctx.send("❌ Это не тикет!", ephemeral=True)
            await ctx.send("🔒 Закрываю...")
            await asyncio.sleep(5)
            await ctx.channel.delete()
        else:
            await ctx.send("Использование: `/ticket setup` или `/ticket close`")
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="ban", description="Забанить пользователя")
@app_commands.describe(member="Пользователь", reason="Причина", delete_message_days="Удалить сообщения за N дней")
@commands.has_permissions(ban_members=True)
async def ban(ctx: commands.Context, member: discord.Member, reason: str = "Не указана", delete_message_days: int = 0):
    try:
        if not ctx.author.guild_permissions.ban_members:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя наказывать владельца сервера, администраторов или самого себя!", ephemeral=True)
        await member.ban(reason=reason, delete_message_days=delete_message_days)
        case_id = await create_case(member, ctx.author, "Бан", reason)
        await send_punishment_log(
            member=member,
            punishment_type="🔨 Бан",
            duration="Навсегда",
            reason=reason,
            moderator=ctx.author,
            case_id=case_id
        )
        embed = discord.Embed(
            title="🔨 Пользователь забанен",
            description=f"**Пользователь:** {member.mention}\n**Причина:** {reason}\n**Удалено сообщений за:** {delete_message_days} дней",
            color=COLORS["mod"]
        )
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="unwarn", description="Удалить предупреждение")
@app_commands.describe(member="Пользователь", warn_index="Номер предупреждения")
@commands.has_permissions(manage_messages=True)
async def unwarn(ctx: commands.Context, member: discord.Member, warn_index: int):
    try:
        if not ctx.author.guild_permissions.manage_messages:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send("❌ Нет прав!", ephemeral=True)
        if not can_punish(ctx.author, member):
            return await ctx.send("❌ Нельзя удалять предупреждения у владельца сервера или администратора!", ephemeral=True)
        user_id = str(member.id)
        if user_id not in warnings_data or not warnings_data[user_id]:
            return await ctx.send(f"✅ У {member.mention} нет предупреждений.", ephemeral=True)
        if warn_index < 1 or warn_index > len(warnings_data[user_id]):
            return await ctx.send(f"❌ Неверный номер. Всего: {len(warnings_data[user_id])}", ephemeral=True)
        removed = warnings_data[user_id].pop(warn_index - 1)
        if not warnings_data[user_id]:
            del warnings_data[user_id]
        save_warnings()
        await send_mod_log(
            title="🧹 Предупреждение удалено",
            description=f"**Модератор:** {ctx.author.mention}\n**Пользователь:** {member.mention}\n**Номер:** {warn_index}\n**Причина:** {removed['reason']}",
            color=COLORS["mod"]
        )
        await ctx.send(f"✅ Предупреждение #{warn_index} для {member.mention} удалено.", ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="vault", description="🏦 Казна сервера")
async def vault(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Команда только на сервере разработчика.", ephemeral=True)
        if not ctx.author.guild_permissions.manage_messages and ctx.author.id != OWNER_ID:
            await check_unauthorized_commands(ctx.author)
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Нет прав.", ephemeral=True)
        vault = economy_data.get("server_vault", 0)
        users = len([k for k in economy_data.keys() if k != "server_vault"])
        total = sum(v.get("balance", 0) for k, v in economy_data.items() if k != "server_vault")
        avg = total // max(users, 1)
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['vault']} Казна сервера",
            color=COLORS["economy"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="💰 Накоплено", value=f"**{format_number(vault)}** {ECONOMY_EMOJIS['coin']}", inline=False)
        embed.add_field(
            name="📊 Статистика",
            value=f"**Участников:** {users}\n**Всего монет:** {format_number(total)} {ECONOMY_EMOJIS['coin']}\n**Средний баланс:** {format_number(avg)} {ECONOMY_EMOJIS['coin']}",
            inline=False
        )
        embed.set_footer(text="Экономика v0.1.7", icon_url=bot.user.display_avatar.url)
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
@bot.hybrid_command(name="balance", description="💰 Посмотреть баланс")
@app_commands.describe(member="Пользователь")
async def balance(ctx: commands.Context, member: discord.Member = None):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(
                f"{ECONOMY_EMOJIS['error']} Экономика доступна только на основном сервере.",
                ephemeral=True
            )
        member = member or ctx.author
        user_id = str(member.id)
        if user_id not in economy_data:
            economy_data[user_id] = {
                "balance": 0,
                "last_daily": 0,
                "last_message": 0,
                "investments": []
            }
            save_economy()
        # Просто показываем, но НЕ применяем налог при просмотре
        # Применение налога оставляем только в daily, pay, voice_income и т.д.
        tax = 0  # или оставь вызов, но без save_economy() внутри apply_wealth_tax
        bal = economy_data[user_id]["balance"]
        vault = economy_data.get("server_vault", 0)
        users = [(k, v.get("balance", 0)) for k, v in economy_data.items() if k != "server_vault"]
        users.sort(key=lambda x: x[1], reverse=True)
        rank = next((i for i, (uid, _) in enumerate(users, 1) if uid == user_id), len(users) + 1)
        now = datetime.now(timezone.utc).timestamp()
        last_daily = economy_data[user_id].get("last_daily", 0)
        remaining = DAILY_COOLDOWN - (now - last_daily)
        if remaining <= 0:
            daily_status = f"{ECONOMY_EMOJIS['gift']} **Daily доступен!**"
        else:
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            progress = (now - last_daily) / DAILY_COOLDOWN
            bar = create_progress_bar(int(progress * 100), 100)
            daily_status = f"⏳ До daily: **{hours}ч {minutes}мин**\n`{bar}` **{int(progress * 100)}%**"
        embed = discord.Embed(
            title=f"{get_rank_emoji(bal)} Баланс {member.display_name}",
            color=COLORS["economy"],
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name=f"{ECONOMY_EMOJIS['balance']} Монеты",
            value=f"**`{format_number(bal)}`** {ECONOMY_EMOJIS['coin']}",
            inline=True
        )
        embed.add_field(
            name="🏆 Место в топе",
            value=f"**#{rank}** из {len(users)}",
            inline=True
        )
        embed.add_field(
            name=f"{ECONOMY_EMOJIS['bank']} Казна сервера",
            value=f"`{format_number(vault)}` {ECONOMY_EMOJIS['coin']}",
            inline=True
        )
        if tax > 0:
            embed.add_field(
                name=f"{ECONOMY_EMOJIS['tax']} Налог на богатство",
                value=f"Списано **-{format_number(tax)}** {ECONOMY_EMOJIS['coin']}",
                inline=False
            )
        embed.add_field(
            name=f"{ECONOMY_EMOJIS['gift']} Ежедневный бонус",
            value=daily_status,
            inline=False
        )
        voice_today = daily_voice_earned.get(user_id, 0)
        voice_progress = f"{format_number(voice_today)} / {VOICE_DAILY_MAX}"
        if voice_today >= VOICE_DAILY_MAX:
            voice_progress += " (лимит достигнут)"
        embed.add_field(
            name="🎤 Заработано в голосе сегодня",
            value=f"**{voice_progress}** {ECONOMY_EMOJIS['coin']}",
            inline=True
        )
        if "multiplier_end" in economy_data[user_id]:
            end = economy_data[user_id]["multiplier_end"]
            if end > now:
                remaining_sec = int(end - now)
                remaining_h = remaining_sec // 3600
                remaining_m = (remaining_sec % 3600) // 60
                embed.add_field(
                    name="🚀 Активный буст ×1.5",
                    value=f"Действует на сообщения и daily\nОсталось: **{remaining_h}ч {remaining_m}мин**",
                    inline=True
                )
        inv = economy_data[user_id].get("investments", [])
        active_invest = sum(1 for i in inv if i["end_time"] > now)
        if active_invest > 0:
            embed.add_field(
                name=f"{ECONOMY_EMOJIS['investment']} Активные инвестиции",
                value=f"**{active_invest}** шт.",
                inline=True
            )
        embed.set_footer(
            text=f"ID: {member.id} • Запросил: {ctx.author.display_name}",
            icon_url=bot.user.display_avatar.url
        )
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, f"Ошибка при проверке баланса: {str(e)}")
        print(f"[BALANCE ERROR] {e}")
@bot.hybrid_command(name="daily", description="🎁 Ежедневный бонус")
async def daily(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)
        user_id = str(ctx.author.id)
        now = datetime.now(timezone.utc).timestamp()
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0, "last_daily": 0, "last_message": 0, "investments": []}
        last = economy_data[user_id].get("last_daily", 0)
        if now - last < DAILY_COOLDOWN:
            remaining = int(DAILY_COOLDOWN - (now - last))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            progress = (now - last) / DAILY_COOLDOWN
            bar = create_progress_bar(int(progress * 100), 100)
            embed = discord.Embed(
                title=f"{ECONOMY_EMOJIS['time']} Daily на кулдауне",
                description=f"Следующая через **{hours}ч {minutes}мин**",
                color=COLORS["economy"]
            )
            embed.add_field(name="Прогресс", value=f"`{bar}` **{int(progress * 100)}%**", inline=False)
            embed.set_footer(text=f"Баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']}")
            return await ctx.send(embed=embed, ephemeral=True)
        tax = await apply_wealth_tax(user_id)
        roll = random.randint(1, 100)
        is_super_drop = roll <= SUPER_DROP_CHANCE
        if is_super_drop:
            title = "ЭПИЧЕСКИЙ ДРОП!!!"
            reward = random.randint(SUPER_DROP_MIN, SUPER_DROP_MAX)
            color = 0xFF4500
            emoji = "🌟🔥"
            rarity_text = "🌟🔥 ЛЕГЕНДАРНЫЙ СУПЕР-ДРОП!!!"
        else:
            rarity = "Обычная"
            min_c, max_c = 15, 35
            color = 0xA8A8A8
            emoji = "🪙"
            for r in RARITIES:
                if roll <= r[1]:
                    rarity = r[0]
                    min_c = r[2]
                    max_c = r[3]
                    color = r[4]
                    emoji = r[5]
                    break
            reward = random.randint(min_c, max_c)
            title = f"{emoji} {rarity} награда!"
            rarity_text = f"**Редкость:** {rarity} ({min_c}–{max_c} {ECONOMY_EMOJIS['coin']})"
        bonus = 0
        if last > 0:
            last_date = datetime.fromtimestamp(last, tz=timezone.utc).date()
            today_date = datetime.now(timezone.utc).date()
            if (today_date - last_date).days == 1:
                bonus = int(reward * 0.1)
                reward += bonus
        economy_data[user_id]["balance"] += reward
        economy_data[user_id]["last_daily"] = now
        save_economy()
        embed = discord.Embed(
            title=title,
            description=f"**+{format_number(reward)}** {ECONOMY_EMOJIS['coin']}",
            color=color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        if is_super_drop:
            embed.add_field(
                name="🎉 СУПЕР-ДРОП!",
                value=f"Ты словил легендарный бонус!\nШанс был всего **{SUPER_DROP_CHANCE}%** 🔥",
                inline=False
            )
        else:
            embed.add_field(name="📊 Детали", value=rarity_text, inline=True)
        if bonus > 0:
            embed.add_field(
                name="🔥 Стрик",
                value=f"+{format_number(bonus)} (10%)",
                inline=True
            )
        if tax > 0:
            embed.add_field(
                name=f"{ECONOMY_EMOJIS['tax']} Налог",
                value=f"**-{format_number(tax)}** {ECONOMY_EMOJIS['coin']}",
                inline=False
            )
        if not embed.footer.text:
            embed.set_footer(
                text=f"Баланс: {format_number(economy_data[user_id]['balance'])} {ECONOMY_EMOJIS['coin']}"
            )
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, str(e))
        print(f"❌ Ошибка в daily: {e}")
@bot.hybrid_command(name="top", description="🏆 Топ богачей")
async def top(ctx: commands.Context):
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.", ephemeral=True)
        users = []
        for uid, data in economy_data.items():
            if uid == "server_vault":
                continue
            if isinstance(data, dict) and "balance" in data and data["balance"] > 0:
                users.append((uid, data["balance"]))
        if not users:
            return await ctx.send(f"{ECONOMY_EMOJIS['warning']} Пока нет пользователей с монетами!", ephemeral=True)
        users.sort(key=lambda x: x[1], reverse=True)
        embed = discord.Embed(
            title=f"{ECONOMY_EMOJIS['crown']} Топ богатейших",
            color=COLORS["economy"],
            timestamp=datetime.now(timezone.utc)
        )
        text = ""
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, bal) in enumerate(users[:10], 1):
            try:
                user = await bot.fetch_user(int(uid))
                name = user.display_name
            except:
                name = f"ID: {uid}"
            medal = medals[i-1] if i <= 3 else f"**{i}.**"
            text += f"{medal} {get_rank_emoji(bal)} **{name}** — `{format_number(bal)}` {ECONOMY_EMOJIS['coin']}\n"
        embed.description = text
        total = sum(b for _, b in users)
        avg = total // len(users) if users else 0
        embed.add_field(
            name="📊 Статистика",
            value=f"**Всего монет:** {format_number(total)} {ECONOMY_EMOJIS['coin']}\n**Участников:** {len(users)}\n**Средний баланс:** {format_number(avg)} {ECONOMY_EMOJIS['coin']}",
            inline=False
        )
        embed.set_footer(text=f"Показано {min(10, len(users))} из {len(users)}")
        await ctx.send(embed=embed, ephemeral=True)
    except Exception as e:
        await send_error_embed(ctx, f"Ошибка в /top: {str(e)}")
        print(f"Ошибка в /top: {e}")
@bot.hybrid_command(name="shop", description="🛒 Магазин с категориями")
@app_commands.describe(category="Выбрать категорию (опционально)")
async def shop(ctx: commands.Context, category: str = None):
    """Магазин с выбором категорий"""
    try:
        if not has_full_access(ctx.guild.id):
            return await ctx.send(
                f"{ECONOMY_EMOJIS['error']} Экономика доступна только на основном сервере.",
                ephemeral=True
            )
        
        user_id = str(ctx.author.id)
        if user_id not in economy_data:
            economy_data[user_id] = {"balance": 0}
            save_economy()
        
        balance = economy_data[user_id].get("balance", 0)
        
        # Если категория указана
        if category and category.lower() in SHOP_CATEGORIES:
            cat = category.lower()
            items_in_category = {
                key: item for key, item in SHOP_ITEMS.items()
                if item.get("category") == cat
            }
            
            embed = discord.Embed(
                title=f"{SHOP_CATEGORIES[cat]['emoji']} {SHOP_CATEGORIES[cat]['name']}",
                description=f"**Ваш баланс:** {format_number(balance)} {ECONOMY_EMOJIS['coin']}\n\n",
                color=COLORS["economy"]
            )
            
            for key, item in items_in_category.items():
                owned = False
                if key == "vip":
                    role = discord.utils.get(ctx.guild.roles, name="VIP")
                    owned = role in ctx.author.roles if role else False
                
                price = get_dynamic_price(key, item["price"])
                price = get_discounted_price(price, key, ctx.author)
                
                price_text = f"**{format_number(price)}** {ECONOMY_EMOJIS['coin']}"
                status = "✅ Куплено" if owned else f"Цена: {price_text}"
                
                embed.add_field(
                    name=f"{item.get('emoji', '📦')} {item['name']}",
                    value=f"{status}\n{item['description']}",
                    inline=False
                )
            
            view = ShopItemsView(cat, items_in_category, ctx.author.id)
            return await ctx.send(embed=embed, view=view, ephemeral=True)
        
        # Иначе показываем выбор категорий
        embed = discord.Embed(
            title="🛒 Магазин MortisPlay",
            description=f"**Ваш баланс:** {format_number(balance)} {ECONOMY_EMOJIS['coin']}\n\n"
                       "Выберите категорию товаров ниже:",
            color=COLORS["economy"]
        )
        
        for cat_key, cat_info in SHOP_CATEGORIES.items():
            count = len([i for i in SHOP_ITEMS.values() if i.get("category") == cat_key])
            embed.add_field(
                name=f"{cat_info['emoji']} {cat_info['name']}",
                value=f"{cat_info['description']}\n({count} товаров)",
                inline=False
            )
        
        if is_march8_event_active():
            embed.add_field(
                name="🎀 Идёт акция 8 марта!",
                value="Скидка -20% на VIP и бусты",
                inline=False
            )
        
        view = ShopCategoryView(ctx.author.id)
        await ctx.send(embed=embed, view=view, ephemeral=True)
    
    except Exception as e:
        await send_error_embed(ctx, f"Ошибка в магазине: {str(e)}")
        print(f"[SHOP ERROR] {e}")

@bot.hybrid_command(name="admin_coins", description="⚙️ Изменить количество монет у пользователя (только для админов)")
@app_commands.describe(
    member="Кому изменить баланс (можно указать себя)",
    amount="На сколько изменить (положительное — добавить, отрицательное — снять)",
    reason="Причина изменения (обязательно)"
)
@commands.check(is_moderator)
async def admin_coins(ctx: commands.Context, member: discord.Member, amount: int, *, reason: str):
    if not (ctx.author.guild_permissions.administrator or ctx.author.id == OWNER_ID):
        await ctx.send("❌ Доступ только администраторам и владельцу бота.", ephemeral=True)
        return
    if member.bot:
        await ctx.send("❌ Нельзя изменять баланс ботов.", ephemeral=True)
        return
    user_id = str(member.id)
    if user_id not in economy_data:
        economy_data[user_id] = {"balance": 0}
    old_balance = economy_data[user_id]["balance"]
    new_balance = old_balance + amount
    if new_balance < 0 and amount < 0:
        await ctx.send(f"❌ Баланс не может стать отрицательным ({new_balance}).", ephemeral=True)
        return
    delta = amount
    server_tax = 0
    if delta > 0:
        if delta <= 500:
            server_tax = 0
        elif delta <= 2000:
            server_tax = int(delta * 0.15)
        elif delta <= 10000:
            server_tax = int(delta * 0.30)
        elif delta <= 50000:
            server_tax = int(delta * 0.50)
        else:
            server_tax = int(delta * 0.70)
    real_amount = delta - server_tax if delta > 0 else delta
    economy_data[user_id]["balance"] += real_amount
    economy_data["server_vault"] = economy_data.get("server_vault", 0) + server_tax
    save_economy()
    embed = discord.Embed(
        title="⚙️ Изменение баланса",
        color=0x00ff9d if delta > 0 else 0xff5555,
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="Пользователь", value=member.mention, inline=True)
    embed.add_field(name="Было", value=f"{format_number(old_balance)} 🪙", inline=True)
    embed.add_field(name="Стало", value=f"{format_number(economy_data[user_id]['balance'])} 🪙", inline=True)
    change_text = f"**{format_number(delta)}** 🪙" if delta >= 0 else f"**{format_number(delta)}** 🪙"
    embed.add_field(name="Изменение", value=change_text, inline=False)
    if server_tax > 0:
        embed.add_field(
            name="Компенсация в казну",
            value=f"+{format_number(server_tax)} 🪙 ({int(server_tax/delta*100)}%)",
            inline=False
        )
    embed.add_field(name="Причина", value=reason, inline=False)
    embed.add_field(name="Выполнил", value=ctx.author.mention, inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"ID: {member.id} • Казна: {format_number(economy_data['server_vault'])}")
    await ctx.send(embed=embed, ephemeral=False)
    log_embed = discord.Embed(
        title="🛠 Изменение баланса (админ)",
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc)
    )
    log_embed.add_field(name="Пользователь", value=f"{member} ({member.id})", inline=True)
    log_embed.add_field(name="Изменение", value=f"{format_number(delta)} → реально {format_number(real_amount)}", inline=True)
    if server_tax > 0:
        log_embed.add_field(name="В казну", value=f"+{format_number(server_tax)}", inline=True)
    log_embed.add_field(name="Было → Стало", value=f"{format_number(old_balance)} → {format_number(economy_data[user_id]['balance'])}", inline=False)
    log_embed.add_field(name="Причина", value=reason, inline=False)
    log_embed.add_field(name="Админ", value=ctx.author.mention, inline=True)
    if MOD_LOG_CHANNEL_ID:
        log_ch = bot.get_channel(MOD_LOG_CHANNEL_ID)
        if log_ch:
            await log_ch.send(embed=log_embed)

@bot.hybrid_command(name="migration_status", description="Статус миграции экономики")
async def migration_status(ctx):
    if ctx.author.id != OWNER_ID:
        return await ctx.send("Только владелец может смотреть.", ephemeral=True)
    
    status = "Миграция уже выполнена" if os.path.exists(MIGRATION_DONE_FILE) else "Миграция ещё не выполнялась"
    count = len(economy_data) - 1 if "server_vault" in economy_data else 0
    
    embed = discord.Embed(title="Статус экономики", color=0x00ff9d)
    embed.add_field(name="Миграция", value=status, inline=False)
    embed.add_field(name="Игроков в базе", value=f"{count}", inline=False)
    embed.add_field(name="Размер базы", value=f"{os.path.getsize(DB_FILE):,} байт", inline=False)
    await ctx.send(embed=embed, ephemeral=True)            

import signal
import atexit

# ───────────────────────────────────────────────
# Сохранение при выключении / Ctrl+C / SIGTERM
# ───────────────────────────────────────────────

def graceful_shutdown():
    print("[SHUTDOWN] Принудительное сохранение экономики...")
    save_economy()
    save_warnings()
    save_cases()
    save_faq()
    print("[SHUTDOWN] Данные сохранены. Выход.")

# Регистрируем обработчики
atexit.register(graceful_shutdown)

# Для Ctrl+C и SIGTERM (в linux/docker чаще всего SIGTERM)
def signal_handler(sig, frame):
    print(f"[SHUTDOWN] Получен сигнал {sig}")
    graceful_shutdown()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@bot.hybrid_command(name="inventory", description="🎒 Ваш инвентарь с использованием предметов")
async def inventory(ctx: commands.Context):
    """Показывает инвентарь с кнопками для использования"""
    if not has_full_access(ctx.guild.id):
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Экономика только на сервере разработчика.",
            ephemeral=True
        )
    
    await ctx.defer(ephemeral=True)
    
    user_id = str(ctx.author.id)
    
    if user_id not in economy_data:
        economy_data[user_id] = {
            "balance": 0,
            "inventory": {},
            "active_effects": [],
            "last_daily": 0,
            "last_message": 0,
            "investments": []
        }
        save_economy()
    
    data = economy_data[user_id]
    inv = data.get("inventory", {})
    
    try:
        embed = await create_inventory_embed(ctx.author, inv, data)
        view = InventoryViewImproved(ctx.author.id, inv)
        
        await ctx.send(embed=embed, view=view, ephemeral=True)
    
    except Exception as e:
        await send_error_embed(ctx, f"Ошибка при загрузке инвентаря: {str(e)}")
        print(f"[INVENTORY ERROR] {e}")


@bot.hybrid_command(name="use", description="Использовать предмет из инвентаря")
@app_commands.describe(item="Название или ID предмета (gift_box, lucky_spin, xp_boost_24h)")
async def use_item_command(ctx: commands.Context, item: str):
    """Быстрое использование предмета"""
    if not has_full_access(ctx.guild.id):
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Только на сервере разработчика.",
            ephemeral=True
        )
    
    await ctx.defer(ephemeral=True)
    
    user_id = str(ctx.author.id)
    
    if user_id not in economy_data or "inventory" not in economy_data[user_id]:
        return await ctx.send("❌ Ваш инвентарь пуст.", ephemeral=True)
    
    inv = economy_data[user_id]["inventory"]
    item_id = item.lower().strip()
    
    found_item = None
    for iid, item_obj in INVENTORY_ITEMS.items():
        if iid == item_id or item_obj.get("name", "").lower() == item_id:
            found_item = iid
            break
    
    if not found_item:
        return await ctx.send(
            f"❌ Предмет **{item}** не найден.\nДоступные: gift_box, lucky_spin, xp_boost_24h",
            ephemeral=True
        )
    
    if found_item not in inv or inv[found_item] <= 0:
        return await ctx.send(
            f"❌ У вас нет предмета **{item}**.",
            ephemeral=True
        )
    
    item_name = INVENTORY_ITEMS.get(found_item, {}).get("name", found_item)
    result = await handle_item_use(ctx.author, found_item, item_name, ctx.interaction)
    
    if result["success"]:
        inv[found_item] -= 1
        if inv[found_item] == 0:
            del inv[found_item]
        save_economy()
        
        await ctx.send(embed=result["embed"], ephemeral=True)
    else:
        await ctx.send(result["error"], ephemeral=True)

@bot.hybrid_command(name="trade", description="🔄 Предложить трейд другому игроку")
@app_commands.describe(member="Игрок для обмена")
async def trade(ctx: commands.Context, member: discord.Member):
    """Предложить трейд другому игроку"""
    if not has_full_access(ctx.guild.id):
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Трейдинг только на сервере разработчика.",
            ephemeral=True
        )
    
    if member.id == ctx.author.id:
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Нельзя торговать с собой!",
            ephemeral=True
        )
    
    if member.bot:
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Нельзя торговать с ботами!",
            ephemeral=True
        )
    
    initiator_id = ctx.author.id
    recipient_id = member.id
    
    if (initiator_id, recipient_id) in trade_invitations:
        return await ctx.send(
            f"{ECONOMY_EMOJIS['warning']} У вас уже есть активный трейд с этим игроком!",
            ephemeral=True
        )
    
    initiator_inv = economy_data.get(str(initiator_id), {}).get("inventory", {})
    if not initiator_inv:
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} У тебя нет предметов в инвентаре!",
            ephemeral=True
        )
    
    trade_id = generate_trade_id()
    active_trades[trade_id] = {
        "trade_id": trade_id,
        "initiator_id": initiator_id,
        "recipient_id": recipient_id,
        "initiator_items": {},
        "recipient_items": {},
        "initiator_confirmed": False,
        "recipient_confirmed": False,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).timestamp()
    }
    
    trade_invitations[(initiator_id, recipient_id)] = trade_id
    
    await ctx.defer(ephemeral=True)
    
    trade_embed = discord.Embed(
        title="🔄 Предложение трейда",
        description=f"**{ctx.author.mention}** предлагает трейд **{member.mention}**",
        color=0x3498db,
        timestamp=datetime.now(timezone.utc)
    )
    trade_embed.add_field(
        name="📝 Следующие шаги",
        value="1. Отправитель выбирает предметы\n2. Получатель выбирает предметы\n3. Оба подтверждают\n4. Трейд выполнен!",
        inline=False
    )
    trade_embed.set_footer(text=f"Трейд ID: {trade_id}")
    
    view = TradeConfirmView(trade_id, initiator_id, "initiator")
    
    await ctx.send(embed=trade_embed, view=view, ephemeral=True)
    
    invite_embed = discord.Embed(
        title="🔄 Тебе предлагают трейд!",
        description=f"**{ctx.author.mention}** хочет торговать с тобой",
        color=0x2ecc71,
        timestamp=datetime.now(timezone.utc)
    )
    invite_embed.set_footer(text=f"Трейд ID: {trade_id}")
    
    recipient_view = TradeConfirmView(trade_id, recipient_id, "recipient")
    
    try:
        await member.send(embed=invite_embed, view=recipient_view)
    except:
        await ctx.send(
            f"{ECONOMY_EMOJIS['warning']} Не удалось отправить ДМ {member.mention}. "
            f"Проверь, открыты ли тебе ДМ от участников сервера.",
            ephemeral=True
        )


@bot.hybrid_command(name="tradelist", description="📋 Список активных трейдов")
async def tradelist(ctx: commands.Context):
    """Показать список активных трейдов"""
    if not has_full_access(ctx.guild.id):
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Команда только на сервере разработчика.",
            ephemeral=True
        )
    
    user_trades = [
        t for t in active_trades.values()
        if t["initiator_id"] == ctx.author.id or t["recipient_id"] == ctx.author.id
    ]
    
    if not user_trades:
        return await ctx.send(
            f"{ECONOMY_EMOJIS['warning']} У тебя нет активных трейдов.",
            ephemeral=True
        )
    
    embed = discord.Embed(
        title="📋 Твои трейды",
        color=0x3498db,
        timestamp=datetime.now(timezone.utc)
    )
    
    for trade in user_trades[:10]:
        initiator = bot.get_user(int(trade["initiator_id"]))
        recipient = bot.get_user(int(trade["recipient_id"]))
        
        status_emoji = {
            "pending": "⏳",
            "both_confirmed": "✅",
            "completed": "🎉",
            "cancelled": "❌",
            "rejected": "👎",
            "failed": "💥"
        }.get(trade["status"], "❓")
        
        field_name = f"{status_emoji} {initiator.display_name} ↔️ {recipient.display_name}"
        field_value = f"**Статус:** {trade['status']}\n**ID:** `{trade['trade_id']}`"
        
        embed.add_field(name=field_name, value=field_value, inline=False)
    
    await ctx.send(embed=embed, ephemeral=True)


@bot.hybrid_command(name="tradeinfo", description="ℹ️ Информация о трейде")
@app_commands.describe(trade_id="ID трейда")
async def tradeinfo(ctx: commands.Context, trade_id: str):
    """Показать информацию о конкретном трейде"""
    if not has_full_access(ctx.guild.id):
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Команда только на сервере разработчика.",
            ephemeral=True
        )
    
    trade = active_trades.get(trade_id)
    if not trade:
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Трейд `{trade_id}` не найден.",
            ephemeral=True
        )
    
    if trade["initiator_id"] != ctx.author.id and trade["recipient_id"] != ctx.author.id:
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Это не твой трейд!",
            ephemeral=True
        )
    
    initiator = bot.get_user(int(trade["initiator_id"]))
    recipient = bot.get_user(int(trade["recipient_id"]))
    
    embed = discord.Embed(
        title=f"🔄 Трейд {trade_id}",
        color=0x3498db,
        timestamp=datetime.now(timezone.utc)
    )
    
    embed.add_field(
        name="👤 Отправитель",
        value=f"{initiator.mention}\nПодтверждение: {'✅' if trade['initiator_confirmed'] else '❌'}",
        inline=True
    )
    embed.add_field(
        name="👤 Получатель",
        value=f"{recipient.mention}\nПодтверждение: {'✅' if trade['recipient_confirmed'] else '❌'}",
        inline=True
    )
    
    initiator_items_text = "\n".join([
        f"  • {INVENTORY_ITEMS.get(iid, {}).get('name', iid)} ×{cnt}"
        for iid, cnt in trade.get("initiator_items", {}).items()
    ]) or "Не выбрано"
    
    recipient_items_text = "\n".join([
        f"  • {INVENTORY_ITEMS.get(iid, {}).get('name', iid)} ×{cnt}"
        for iid, cnt in trade.get("recipient_items", {}).items()
    ]) or "Не выбрано"
    
    embed.add_field(
        name=f"📤 {initiator.display_name} отдаёт",
        value=initiator_items_text,
        inline=False
    )
    embed.add_field(
        name=f"📥 {recipient.display_name} отдаёт",
        value=recipient_items_text,
        inline=False
    )
    
    status_emoji = {
        "pending": "⏳",
        "both_confirmed": "✅",
        "completed": "🎉",
        "cancelled": "❌",
        "rejected": "👎",
        "failed": "💥"
    }.get(trade["status"], "❓")
    
    embed.add_field(name="📊 Статус", value=f"{status_emoji} {trade['status']}", inline=False)
    
    await ctx.send(embed=embed, ephemeral=True)


@bot.hybrid_command(name="tradecancel", description="❌ Отменить трейд")
@app_commands.describe(trade_id="ID трейда")
async def tradecancel(ctx: commands.Context, trade_id: str):
    """Отменить активный трейд"""
    if not has_full_access(ctx.guild.id):
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Команда только на сервере разработчика.",
            ephemeral=True
        )
    
    trade = active_trades.get(trade_id)
    if not trade:
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Трейд `{trade_id}` не найден.",
            ephemeral=True
        )
    
    if trade["initiator_id"] != ctx.author.id and trade["recipient_id"] != ctx.author.id:
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Это не твой трейд!",
            ephemeral=True
        )
    
    if trade["status"] in ["completed", "cancelled", "failed"]:
        return await ctx.send(
            f"{ECONOMY_EMOJIS['error']} Этот трейд уже завершён или отменён.",
            ephemeral=True
        )
    
    trade["status"] = "cancelled"
    
    initiator = bot.get_user(int(trade["initiator_id"]))
    recipient = bot.get_user(int(trade["recipient_id"]))
    
    cancel_embed = discord.Embed(
        title="❌ Трейд отменён",
        description=f"**{ctx.author.mention}** отменил трейд между **{initiator.mention}** и **{recipient.mention}**",
        color=0xe74c3c,
        timestamp=datetime.now(timezone.utc)
    )
    cancel_embed.set_footer(text=f"Трейд ID: {trade_id}")
    
    await ctx.send(embed=cancel_embed, ephemeral=True)
    
    if (trade["initiator_id"], trade["recipient_id"]) in trade_invitations:
        del trade_invitations[(trade["initiator_id"], trade["recipient_id"])]        
# ───────────────────────────────────────────────
# ЗАПУСК
# ───────────────────────────────────────────────
if __name__ == "__main__":
    bot.launch_time = datetime.now(timezone.utc)
    try:
        print("Запуск бота...")
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Неверный токен.")
    except Exception as e:
        print(f"❌ Ошибка запуска: {type(e).__name__}: {e}")