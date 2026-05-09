# config/shop.py
from datetime import date

# Указываем дату события
EVENT_DATE = date(2026, 5, 9) 

CURRENT_EVENT = {
    "name": "Праздник Победы",
    "reason": "В честь 9 мая на все товары действует праздничная скидка 15%!",
    "multiplier": 0.85,
    "date": date(2026, 5, 9) # Добавьте эту строку!
}

SHOP_CATEGORIES = {
    "бусты": {"name": "💰 Бусты доходов", "emoji": "💰", "description": "Увеличьте свои доходы на работе"},
    "предметы": {"name": "🎁 Предметы", "emoji": "🎁", "description": "Разные полезные вещи"},
    "ящики": {"name": "🎰 Удачные ящики", "emoji": "🎰", "description": "Лутбоксы с монетами"},
    "statuses": {"name": "🏷️ Статусы", "emoji": "🏷️", "description": "Ваш титул в профиле"},
    "luxury": {"name": "🏆 Роскошь", "emoji": "🏆", "description": "Очень дорогие коллекционные предметы"}
}

SHOP_ITEMS = {
    # --- БУСТЫ ---
    "pro_tools": {"category": "бусты", "name": "Набор инструментов", "price": 1000, "description": "Постоянный бонус +20% к зарплате.", "emoji": "🛠️"},
    "energy_drink": {"category": "бусты", "name": "Энергетик", "price": 250, "description": "Разовый буст +50% к следующей работе.", "emoji": "🥤"},
    "coffee_machine": {"category": "бусты", "name": "Кофемашина", "price": 5000, "description": "Увеличивает минимальную зарплату навсегда.", "emoji": "☕"},

    # --- ПРЕДМЕТЫ ---
    "gift_box": {"category": "предметы", "name": "Подарочная коробка", "price": 500, "description": "Можно передать другу или открыть самому.", "emoji": "🎁"},
    "lucky_coin": {"category": "предметы", "name": "Счастливая монета", "price": 1200, "description": "Немного удачи в профиль.", "emoji": "🪙"},
    "repair_kit": {"category": "предметы", "name": "Ремкомплект", "price": 300, "description": "Пригодится для будущих систем.", "emoji": "🔧"},

    # --- КЕЙСЫ ---
    "low_box": {"category": "ящики", "name": "Потертая коробка", "price": 150, "description": "Дешево и сердито.", "emoji": "📦"},
    "standard_case": {"category": "ящики", "name": "Обычный кейс", "price": 500, "description": "Стандартный набор призов.", "emoji": "💼"},
    "chainsaw_case": {"category": "ящики", "name": "Кейс «Семья Бензопил»", "price": 1000, "description": "Классика жанра.", "emoji": "🎰"},
    "military_crate": {"category": "ящики", "name": "Армейский ящик", "price": 2500, "description": "Серьезные призы.", "emoji": "📦"},
    "neon_pack": {"category": "ящики", "name": "Неоновый пакет", "price": 10000, "description": "Высокие ставки!", "emoji": "🛍️"},
    "mortis_relic": {"category": "ящики", "name": "Реликвия Мортиса", "price": 50000, "description": "Легендарный артефакт.", "emoji": "🔱"},

    # --- СТАТУСЫ ---
    "st_worker": {"category": "statuses", "name": "Работяга", "price": 100, "description": "Труд крут!", "emoji": "🛠️"},
    "st_streamer": {"category": "statuses", "name": "Ютубер", "price": 150, "description": "Подпишись!", "emoji": "🎥"},
    "st_lethal": {"category": "statuses", "name": "Сотрудник Компании", "price": 200, "description": "Сбор лома — это жизнь.", "emoji": "🧤"},
    "st_rich": {"category": "statuses", "name": "Мажор", "price": 1000, "description": "Деньги есть.", "emoji": "💰"},
    "st_legend": {"category": "statuses", "name": "Легенда", "price": 5000, "description": "О вас слагают мифы.", "emoji": "👑"},

    # --- LUXURY ---
    "golden_throne": {"category": "luxury", "name": "Золотой трон", "price": 100000, "description": "Символ безграничной власти.", "emoji": "💺"},
    "private_jet": {"category": "luxury", "name": "Личный самолет", "price": 500000, "description": "Для тех, кто ценит время.", "emoji": "🛩️"},
    "diamond_crown": {"category": "luxury", "name": "Алмазная корона", "price": 1000000, "description": "Самый дорогой предмет в мире.", "emoji": "💎"},
}

# Предметы, которые могут лежать в инвентаре
INVENTORY_ITEMS = {
    "pro_tools": {"name": "Набор инструментов", "emoji": "🛠️", "one_use": False},
    "energy_drink": {"name": "Энергетик", "emoji": "🥤", "one_use": True},
    "gift_box": {"name": "Подарочная коробка", "emoji": "🎁", "one_use": True},
    "low_box": {"name": "Потертая коробка", "emoji": "📦", "one_use": True},
    "standard_case": {"name": "Обычный кейс", "emoji": "💼", "one_use": True},
    "chainsaw_case": {"name": "Кейс «Семья Бензопил»", "emoji": "🎰", "one_use": True},
    "military_crate": {"name": "Армейский ящик", "emoji": "📦", "one_use": True},
    "neon_pack": {"name": "Неоновый пакет", "emoji": "🛍️", "one_use": True},
    "mortis_relic": {"name": "Реликвия Мортиса", "emoji": "🔱", "one_use": True},
}