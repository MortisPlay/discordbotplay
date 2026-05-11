# config/economy.py
import discord
import random
from datetime import datetime
from config.settings import logger

# ====================== ОСНОВНЫЕ НАСТРОЙКИ ЭКОНОМИКИ ======================

MORTIS_COIN_RATE = 2.0
DAILY_COOLDOWN = 86400

# Эмодзи для системы
ECONOMY_EMOJIS = {
    "balance": "💰",
    "coin": "🪙",
    "daily": "🎁",
    "success": "✅",
    "error": "❌",
    "job": "🏢",
    "user": "👤",
    "stats": "📊"
}

# Роли для скидок
MALE_ROLE_ID = 1477476332714856561 

# ====================== НАСТРОЙКИ ГОЛОСОВОЙ АКТИВНОСТИ ======================
VOICE_INCOME_PER_MINUTE = 5       
VOICE_MIN_SESSION_MINUTES = 2    

# ====================== МАГАЗИН И КАТЕГОРИИ ======================

SHOP_CATEGORIES = {
    "бусты": {"name": "💰 Бусты доходов", "emoji": "💰", "description": "Увеличьте свои заработки"},
    "предметы": {"name": "🎁 Предметы", "emoji": "🎁", "description": "Расходные материалы и инструменты"},
    "luxury": {"name": "🏆 Статус", "emoji": "🏆", "description": "Предметы роскоши"},
    "роли": {"name": "💎 Роли", "emoji": "💎", "description": "Эксклюзивные статусы"},
    "ящики": {"name": "🎰 Удачные ящики", "emoji": "🎰", "description": "Лутбоксы с призами"}
}

SHOP_ITEMS = {
    # ─ БУСТЫ ─
    "multiplier_2x": {
        "category": "бусты",
        "name": "Удвоитель ×2 (3 дня)",
        "price": 2500,
        "description": "Удваивает доход в течение 3 дней.",
        "emoji": "🚀",
        "type": "multiplier"
    },
    "energy_drink": {
        "category": "бусты",
        "name": "Энергетик «Mortis Drive»",
        "price": 250,
        "description": "Дает +50% к следующей зарплате в /work.",
        "emoji": "🥤",
        "type": "inventory_item"
    },
    
    # ─ ЯЩИКИ ─
    "chainsaw_case": {
        "category": "ящики",
        "name": "Кейс «Семья Бензопил»",
        "price": 1000,
        "description": "Случайный куш от 200 до 5000 монет!",
        "emoji": "🎰",
        "type": "inventory_item"
    },

    # ─ ПРЕДМЕТЫ И ИНСТРУМЕНТЫ ─
    "gift_box": {
        "category": "предметы",
        "name": "Подарочная коробка",
        "price": 1500,
        "description": "Содержит от 500 до 5000 монет.",
        "emoji": "🎁",
        "type": "inventory_item"
    },
    "pro_tools": {
        "category": "предметы",
        "name": "Набор инструментов",
        "price": 2500,
        "description": "Постоянный бонус +20% к каждой смене /work.",
        "emoji": "🛠️",
        "type": "inventory_item"
    },

    # ─ СТАТУС (Luxury) ─
    "luxury_watch": {
        "category": "luxury",
        "name": "Золотые часы",
        "price": 15000,
        "description": "Символ вашего успеха.",
        "emoji": "⌚",
        "type": "inventory_item"
    },
    "mortis_car": {
        "category": "luxury",
        "name": "Личный спорткар",
        "price": 75000,
        "description": "Самый быстрый на сервере.",
        "emoji": "🏎️",
        "type": "inventory_item"
    },

    # ─ РОЛИ ─
    "vip": {
        "category": "роли",
        "name": "VIP статус (30 дней)",
        "price": 10000,
        "description": "• Уникальный цвет\n• Доступ в VIP-чат",
        "emoji": "💎",
        "type": "role",
        "role_id": 1477560387640754287,
        "duration_days": 30
    }
}

# ====================== ИНВЕНТАРЬ ======================

INVENTORY_ITEMS = {
    "gift_box": {
        "name": "Подарочная коробка",
        "emoji": "🎁",
        "description": "Дает случайную сумму монет.",
        "one_use": True
    },
    "chainsaw_case": {
        "name": "Кейс «Семья Бензопил»",
        "emoji": "🎰",
        "description": "Шанс выиграть огромный куш.",
        "one_use": True
    },
    "energy_drink": {
        "name": "Энергетик «Mortis Drive»",
        "emoji": "🥤",
        "description": "Разовый буст к работе.",
        "one_use": True
    },
    "pro_tools": {
        "name": "Рабочий инвентарь",
        "emoji": "🛠️",
        "description": "Пассивный бонус +20% к зарплате.",
        "one_use": False
    },
    "luxury_watch": {
        "name": "Золотые часы",
        "emoji": "⌚",
        "description": "Предмет роскоши.",
        "one_use": False
    },
    "mortis_car": {
        "name": "Личный спорткар",
        "emoji": "🏎️",
        "description": "Премиальный транспорт.",
        "one_use": False
    },
    "vip": {
        "name": "Свиток VIP",
        "emoji": "💎",
        "description": "Активирует VIP статус на 30 дней.",
        "one_use": True
    }
}

# ====================== РАБОТА (JOBS) ======================

# ВАЖНО: Название именно JOBS, чтобы cogs/economy.py не выдавал ImportError
JOBS = {
    "unemployed": {
        "name": "Безработный",
        "min_salary": 0,
        "max_salary": 0,
        "description": "У вас нет работы"
    },
    "cleaner": {
        "name": "Уборщик",
        "min_salary": 50,
        "max_salary": 100,
        "description": "Тяжелая работа на складе.",
        "emoji": "📦"
    },
    "barista": {
        "name": "Бариста",
        "min_salary": 120,
        "max_salary": 180,
        "description": "Варишь кофе в центре.",
        "emoji": "☕",
        "requirements": {
            "min_balance": 200,
            "min_account_age_days": 3
        }
    },
    "manager": {
        "name": "Менеджер",
        "min_salary": 200,
        "max_salary": 350,
        "description": "Руководишь проектами.",
        "emoji": "💼",
        "requirements": {
            "min_balance": 1000,
            "requires_verified": True,
            "min_account_age_days": 5
        }
    },
    "programmer": {
        "name": "Разработчик",
        "min_salary": 400,
        "max_salary": 600,
        "description": "Пишешь код для MortisPlay.",
        "emoji": "💻",
        "requirements": {
            "min_balance": 2500,
            "requires_verified": True,
            "min_account_age_days": 7
        }
    },
    "security_guard": {
        "name": "Охранник",
        "min_salary": 150,
        "max_salary": 250,
        "description": "Охраняешь важные объекты.",
        "emoji": "👮",
        "requirements": {
            "min_balance": 500,
            "min_account_age_days": 2
        }
    },
    "delivery_man": {
        "name": "Курьер",
        "min_salary": 100,
        "max_salary": 180,
        "description": "Доставляешь посылки по городу.",
        "emoji": "📮",
        "requirements": {
            "min_account_age_days": 1
        }
    },
    "chef": {
        "name": "Шеф-повар",
        "min_salary": 250,
        "max_salary": 400,
        "description": "Готовишь деликатесы в ресторане.",
        "emoji": "👨‍🍳",
        "requirements": {
            "min_balance": 800,
            "min_account_age_days": 4
        }
    },
    "designer": {
        "name": "Дизайнер",
        "min_salary": 350,
        "max_salary": 550,
        "description": "Создаёшь красивый визуал.",
        "emoji": "🎨",
        "requirements": {
            "min_balance": 1500,
            "requires_verified": True,
            "min_account_age_days": 6
        }
    },
    "ceo": {
        "name": "Генеральный директор",
        "min_salary": 600,
        "max_salary": 1000,
        "description": "Руководишь всей компанией.",
        "emoji": "🤵",
        "requirements": {
            "min_balance": 5000,
            "requires_verified": True,
            "min_account_age_days": 14
        }
    }
}

# ====================== ФУНКЦИИ ЛОГИКИ ======================

def get_item_price(item_id, member):
    from config.shop import SHOP_ITEMS, CURRENT_EVENT
    base_price = SHOP_ITEMS[item_id]["price"]
    
    # Применяем скидку события, если оно активно
    if CURRENT_EVENT and "multiplier" in CURRENT_EVENT:
        base_price = int(base_price * CURRENT_EVENT["multiplier"])
        
    return base_price

def open_gift_box() -> int:
    roll = random.randint(1, 100)
    if roll <= 70: return random.randint(500, 1200)
    if roll <= 90: return random.randint(1201, 1800)
    if roll <= 98: return random.randint(1801, 2200)
    return random.randint(2201, 2500)