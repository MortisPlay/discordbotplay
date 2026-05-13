# modules/economy_bp/bp_config.py
from datetime import datetime, timezone

BP_SETTINGS = {
    "SEASON_NAME": "Сезон Бензопилы 10 ⛓️",
    "MAX_LEVEL": 10,
    "XP_PER_LEVEL": 500,  # Опыта на каждый уровень
    "PREMIUM_ITEM_ID": "premium_pass", # ID товара в магазине для активации платной ветки
    "SEASON_START": datetime(2026, 5, 26, 7, 0, 0, tzinfo=timezone.utc),  # 26 мая 10:00 MSK = 07:00 UTC
    "SEASON_DURATION_DAYS": 60,
    "EMOJI_FREE": "⚪",
    "EMOJI_PREMIUM": "🟡",
    "COLOR_FREE": 0x95a5a6,
    "COLOR_PREMIUM": 0xffd700
}

# Типы наград: 
# "coins" - обычные монеты
# "mcoins" - MortisCoins (премиум валюта)
# "item" - предмет из SHOP_ITEMS или INVENTORY_ITEMS
# "status" - текстовый статус/роль в профиле

BP_REWARDS = {
    1: {
        "free": {"type": "coins", "amount": 250, "label": "250 🪙"},
        "premium": {"type": "coins", "amount": 1000, "label": "1000 🪙 + Статус 'Новичок+'"}
    },
    2: {
        "free": {"type": "item", "id": "low_box", "amount": 1, "label": "📦 Кейс новичка"},
        "premium": {"type": "item", "id": "low_box", "amount": 3, "label": "📦 3 Кейса новичка"}
    },
    3: {
        "free": {"type": "coins", "amount": 500, "label": "500 🪙"},
        "premium": {"type": "mcoins", "amount": 1, "label": "💎 1 MortisCoin"}
    },
    4: {
        "free": {"type": "item", "id": "energy_drink", "amount": 1, "label": "⚡ Энергетик"},
        "premium": {"type": "item", "id": "energy_drink", "amount": 3, "label": "⚡ 3 Энергетика"}
    },
    5: {
        "free": {"type": "item", "id": "chainsaw_case", "amount": 1, "label": "🪚 Кейс Бензопилы"},
        "premium": {"type": "item", "id": "pro_tools", "amount": 1, "label": "🛠️ Набор инструментов"}
    },
    6: {
        "free": {"type": "coins", "amount": 1000, "label": "1000 🪙"},
        "premium": {"type": "coins", "amount": 5000, "label": "5000 🪙"}
    },
    7: {
        "free": {"type": "item", "id": "standard_case", "amount": 1, "label": "📦 Стандартный кейс"},
        "premium": {"type": "mcoins", "amount": 2, "label": "💎 2 MortisCoins"}
    },
    8: {
        "free": {"type": "item", "id": "energy_drink", "amount": 2, "label": "⚡ 2 Энергетика"},
        "premium": {"type": "item", "id": "military_crate", "amount": 1, "label": "🎖️ Военный кейс"}
    },
    9: {
        "free": {"type": "coins", "amount": 2000, "label": "2000 🪙"},
        "premium": {"type": "mcoins", "amount": 5, "label": "💎 5 MortisCoins"}
    },
    10: {
        "free": {"type": "status", "id": "veteran", "label": "🏆 Статус 'Ветеран'"},
        "premium": {"type": "status", "id": "chainsaw_man", "label": "⛓️ Статус 'Человек-бензопила'"}
    }
}

def get_level_by_xp(xp: int) -> int:
    """Вычисляет текущий уровень на основе опыта"""
    lvl = xp // BP_SETTINGS["XP_PER_LEVEL"]
    return min(lvl, BP_SETTINGS["MAX_LEVEL"])

def get_xp_progress(xp: int) -> int:
    """Возвращает остаток опыта до следующего уровня"""
    if xp >= BP_SETTINGS["MAX_LEVEL"] * BP_SETTINGS["XP_PER_LEVEL"]:
        return BP_SETTINGS["XP_PER_LEVEL"]
    return xp % BP_SETTINGS["XP_PER_LEVEL"]