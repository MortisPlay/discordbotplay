# config/shop.py
from datetime import date, datetime, timezone, timedelta

# Указываем дату события
EVENT_DATE = date(2026, 5, 9) 

CURRENT_EVENT = None  # События сейчас нет
PROMO_ROTATION_START = datetime.now(timezone.utc)

SHOP_CATEGORIES = {
    "бусты": {"name": "💰 Бусты доходов", "emoji": "💰", "description": "Увеличьте свои доходы на работе"},
    "предметы": {"name": "🎁 Предметы", "emoji": "🎁", "description": "Разные полезные вещи"},
    "ящики": {"name": "🎰 Удачные ящики", "emoji": "🎰", "description": "Лутбоксы с монетами"},
    "statuses": {"name": "🏷️ Статусы", "emoji": "🏷️", "description": "Ваш титул в профиле"},
    "battlepass": {"name": "🎫 Боевой пропуск", "emoji": "🎫", "description": "Активируйте премиум ветку Боевого Пропуска на сезон"},
    "luxury": {"name": "🏆 Роскошь", "emoji": "🏆", "description": "Очень дорогие коллекционные предметы"},
    "временные_акции": {"name": "⏰ ВРЕМЕННЫЕ АКЦИИ (БЕТА)", "emoji": "⏰", "description": "Эксклюзивные предметы с ограниченным сроком — 1-3 дня!"}
}

SHOP_ITEMS = {
    # --- БУСТЫ ---
    "pro_tools": {"category": "бусты", "name": "Набор инструментов", "price": 1000, "description": "Постоянный бонус +20% к зарплате.", "emoji": "🛠️", "passive": True},
    "energy_drink": {"category": "бусты", "name": "Энергетик", "price": 250, "description": "Разовый буст +50% к следующей работе.", "emoji": "🥤"},
    "coffee_machine": {"category": "бусты", "name": "Кофемашина", "price": 5000, "description": "Увеличивает минимальную зарплату навсегда.", "emoji": "☕"},
    "work_amplifier": {"category": "бусты", "name": "Аналитический усилитель", "price": 1800, "description": "Следующая работа принесёт +35% дохода.", "emoji": "🧠"},

    # --- ПРЕДМЕТЫ ---
    "gift_box": {"category": "предметы", "name": "Подарочная коробка", "price": 500, "description": "Можно передать другу или открыть самому.", "emoji": "🎁"},
    "lucky_coin": {"category": "предметы", "name": "Счастливая монета", "price": 1200, "description": "Немного удачи в профиль.", "emoji": "🪙"},
    "repair_kit": {"category": "предметы", "name": "Ремкомплект", "price": 300, "description": "Пригодится для будущих систем.", "emoji": "🔧"},
    "fortune_cookie": {"category": "предметы", "name": "Печенье удачи", "price": 900, "description": "Повышает шанс получить редкий приз в следующем кейсе.", "emoji": "🍪"},

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
    "premium_pass": {"category": "battlepass", "name": "Premium Pass", "price": 10, "currency": "mortis_coins", "description": "Активирует премиум ветку Боевого Пропуска за MortisCoin.", "emoji": "🎟️", "bp_premium": True},

    # --- LUXURY ---
    "golden_throne": {"category": "luxury", "name": "Золотой трон", "price": 100000, "description": "Символ безграничной власти.", "emoji": "💺"},
    "private_jet": {"category": "luxury", "name": "Личный самолет", "price": 500000, "description": "Для тех, кто ценит время.", "emoji": "🛩️"},
    "diamond_crown": {"category": "luxury", "name": "Алмазная корона", "price": 1000000, "description": "Самый дорогой предмет в мире.", "emoji": "💎"},
    "royal_mansion": {"category": "luxury", "name": "Королевское поместье", "price": 300000, "description": "Роскошное владение для настоящих аристократов.", "emoji": "🏰"},
    
    # --- ВРЕМЕННЫЕ АКЦИИ (ротация) ---
    # Эти предметы появляются на 1-3 дня и затем заменяются другими
    "акция_vip_24h": {"category": "временные_акции", "name": "💎 VIP-статус (24 часа)", "price": 500, "description": "⏰ Эксклюзивное предложение! Действует только 1 день!", "emoji": "💎", "exclusive": True, "duration_hours": 24},
    "акция_x3_boost": {"category": "временные_акции", "name": "🚀 Тройной бонус (3 смены)", "price": 750, "description": "⏰ Действует 2 дня! +300% к следующим 3 сменам.", "emoji": "🚀", "exclusive": False, "duration_hours": 48},
    "акция_mysterybox": {"category": "временные_акции", "name": "🎁 Мистическая коробка", "price": 1500, "description": "⏰ Действует 3 дня! Случайный набор предметов.", "emoji": "🎁", "exclusive": False, "duration_hours": 72},
    "акция_premium_25off": {"category": "временные_акции", "name": "🎟️ Premium Pass (-25% скидка)", "price": 7, "currency": "mortis_coins", "description": "⏰ Спешите! Скидка 25% только 1 день!", "emoji": "🎟️", "bp_premium": True, "exclusive": True, "duration_hours": 24},
    "акция_multiplier_x2": {"category": "временные_акции", "name": "💰 Удвоитель заработков (48ч)", "price": 1200, "description": "⏰ Удвоит все заработки на 2 дня! Очень редкая акция!", "emoji": "💰", "exclusive": True, "duration_hours": 48},
    "акция_golden_case": {"category": "временные_акции", "name": "👑 Золотой кейс (ЛЕГЕНДАРНЫЙ)", "price": 3000, "description": "⏰ Только 1 день! Гарантирован куш от 5000+ монет!", "emoji": "👑", "exclusive": True, "duration_hours": 24},
    "акция_super_combo": {"category": "временные_акции", "name": "⚡ Суперкомбо-набор", "price": 2000, "description": "⏰ Действует 3 дня! Набор из 5 энергетиков + 2 ящика.", "emoji": "⚡", "exclusive": False, "duration_hours": 72},
    "акция_instant_500k": {"category": "временные_акции", "name": "💸 Премиум-пакет помощи", "price": 4500, "description": "⏰ Только 1 день! Получите пакет ресурсов и монет.", "emoji": "💸", "exclusive": True, "duration_hours": 24},
    "акция_pro_tools_50off": {"category": "временные_акции", "name": "🛠️ Инструменты (скидка -50%)", "price": 500, "description": "⏰ Действует 2 дня! Набор инструментов со скидкой 50%!", "emoji": "🛠️", "exclusive": False, "duration_hours": 48},
    "акция_vip_week": {"category": "временные_акции", "name": "👑 VIP на неделю", "price": 1800, "description": "⏰ Только 2 дня! VIP-статус на 7 дней со скидкой!", "emoji": "👑", "exclusive": False, "duration_hours": 48},
    "акция_elite_box": {"category": "временные_акции", "name": "🎖️ Элитный ящик (72ч)", "price": 2500, "description": "⏰ Действует 3 дня! Премиум кейс с лучшими награами!", "emoji": "🎖️", "exclusive": False, "duration_hours": 72},
    "акция_rolemaster": {"category": "временные_акции", "name": "🎭 Роль Мастер (НОВАЯ)", "price": 800, "description": "⏰ Спешите! Только 1 день! Получите новую роль на сервере!", "emoji": "🎭", "exclusive": True, "duration_hours": 24},
    "акция_double_earn": {"category": "временные_акции", "name": "⚡ Двойной заработок (48ч)", "price": 1200, "description": "⏰ Только 2 дня! Ваши следующие работы принесут +100% дохода.", "emoji": "⚡", "exclusive": True, "duration_hours": 48},
    "акция_luxury_flash": {"category": "временные_акции", "name": "✨ Люксовый Flash-сейл", "price": 2200, "description": "⏰ Эксклюзивно 24 часа! Бонус на коллекцию роскоши.", "emoji": "✨", "exclusive": True, "duration_hours": 24},
    "акция_seasonal_elite": {"category": "временные_акции", "name": "🌟 Сезонная элита", "price": 3500, "description": "⏰ Будет доступна после старта сезона. Эксклюзивное предложение!", "emoji": "🌟", "exclusive": True, "duration_hours": 72, "seasonal": True},
}



# Предметы, которые могут лежать в инвентаре
INVENTORY_ITEMS = {
    "pro_tools": {"name": "Набор инструментов", "emoji": "🛠️", "one_use": False, "passive": True},
    "energy_drink": {"name": "Энергетик", "emoji": "🥤", "one_use": True},
    "gift_box": {"name": "Подарочная коробка", "emoji": "🎁", "one_use": True},
    "fortune_cookie": {"name": "Печенье удачи", "emoji": "🍪", "one_use": True},
    "work_amplifier": {"name": "Аналитический усилитель", "emoji": "🧠", "one_use": True},
    "low_box": {"name": "Потертая коробка", "emoji": "📦", "one_use": True},
    "standard_case": {"name": "Обычный кейс", "emoji": "💼", "one_use": True},
    "chainsaw_case": {"name": "Кейс «Семья Бензопил»", "emoji": "🎰", "one_use": True},
    "military_crate": {"name": "Армейский ящик", "emoji": "📦", "one_use": True},
    "neon_pack": {"name": "Неоновый пакет", "emoji": "🛍️", "one_use": True},
    "mortis_relic": {"name": "Реликвия Мортиса", "emoji": "🔱", "one_use": True},
}