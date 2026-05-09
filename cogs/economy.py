import discord
from discord import app_commands
from discord.ext import commands
import random
from datetime import datetime, timedelta, timezone
from datetime import date
import asyncio
import string # Для генерации капчи

from config.settings import logger, format_number
from config.economy import ECONOMY_EMOJIS, JOBS, DAILY_COOLDOWN, get_item_price
from config.shop import SHOP_ITEMS, INVENTORY_ITEMS, SHOP_CATEGORIES
from utils.db import economy_db
from config.shop import CURRENT_EVENT, SHOP_ITEMS

def get_item_price(item_id: str, member: discord.Member) -> int:
    """Вычисляет цену товара с учетом текущих акций и скидок"""
    from config.shop import CURRENT_EVENT, SHOP_ITEMS # Импорт внутри для избежания ошибок
    
    item = SHOP_ITEMS.get(item_id)
    if not item:
        return 0
    
    base_price = item["price"]
    
    # Проверка даты: скидка работает ТОЛЬКО в указанный день
    today = date.today()
    event_date = CURRENT_EVENT.get("date") # Мы добавили это поле в shop.py
    
    if event_date and today == event_date:
        # Если сегодня 9 мая (или дата события), применяем скидку
        return int(base_price * CURRENT_EVENT.get("multiplier", 1.0))
    
    # В остальные дни цена обычная
    return base_price

# ====================== UI: ПОДТВЕРЖДЕНИЕ ПОКУПКИ ======================
class ConfirmPurchaseView(discord.ui.View):
    def __init__(self, item_id: str, member: discord.Member, final_price: int, user_id: int):
        super().__init__(timeout=30)
        self.item_id = item_id
        self.member = member
        self.final_price = final_price
        self.user_id = user_id

    @discord.ui.button(label="Подтвердить", style=discord.ButtonStyle.green, emoji="✅")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
        
        user = economy_db.get_user(self.member.id)
        if user.get("balance", 0) < self.final_price:
            return await interaction.response.send_message("❌ Недостаточно средств!", ephemeral=True)

        # Замени старый блок на этот:
        item = SHOP_ITEMS[self.item_id]
        user["balance"] -= self.final_price
        
        # Проверяем, является ли предмет статусом
        if item.get("category") == "statuses":
            # Устанавливаем статус напрямую пользователю
            user["status"] = f"{item['emoji']} {item['name']}"
            success_msg = f"✅ Вы успешно купили и установили статус: **{user['status']}**!"
        else:
            # Обычный предмет — добавляем в инвентарь
            inventory = user.get("inventory", {})
            inventory[self.item_id] = inventory.get(self.item_id, 0) + 1
            user["inventory"] = inventory
            success_msg = f"✅ Вы успешно купили **{item['name']}** за **{format_number(self.final_price)}** {ECONOMY_EMOJIS['coin']}!"
        
        # Сохраняем изменения
        economy_db.update_user(self.member.id, user)
        
        await interaction.response.edit_message(
            content=success_msg, 
            embed=None, 
            view=None
        )

    @discord.ui.button(label="Отмена", style=discord.ButtonStyle.red, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
        await interaction.response.edit_message(content="🛒 Покупка отменена.", embed=None, view=None)

# ====================== UI: ИНВЕНТАРЬ (ВМЕСТО /USE) ======================
class InventoryView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.refresh_items()

    def refresh_items(self):
        self.clear_items()
        user = economy_db.get_user(self.user_id)
        inventory = user.get("inventory", {})
        
        # Берем только те предметы, количество которых > 0
        usable_items = {k: v for k, v in inventory.items() if v > 0}
        
        if not usable_items:
            return

        options = []
        for iid, count in usable_items.items():
            # Ищем инфо в магазине или в списке спец. предметов
            info = SHOP_ITEMS.get(iid) or INVENTORY_ITEMS.get(iid)
            if not info: continue

            options.append(discord.SelectOption(
                label=f"{info['name']} ({count} шт.)",
                value=iid,
                emoji=info.get("emoji"),
                description=info.get("description", "Нажмите, чтобы использовать")[:100]
            ))

        if options:
            select = discord.ui.Select(placeholder="Выберите предмет для использования...", options=options)
            select.callback = self.use_callback
            self.add_item(select)

    async def use_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваш инвентарь!", ephemeral=True)

        item_id = interaction.data['values'][0]
        user = economy_db.get_user(self.user_id)
        inventory = user.get("inventory", {})

        if inventory.get(item_id, 0) <= 0:
            return await interaction.response.send_message("❌ Предмет закончился!", ephemeral=True)

        # Сразу редактируем сообщение, чтобы запустить процесс (первый ответ)
        await interaction.response.edit_message(content="🔄 Обработка...", view=None)

        msg = "Этот предмет нельзя использовать."
        
        case_rewards = {
            "low_box": ([50, 150, 300], [60, 30, 10]),
            "standard_case": ([400, 700, 1200], [50, 35, 15]),
            "military_crate": ([2000, 4000, 8000], [50, 35, 15]),
            "neon_pack": ([8000, 15000, 30000], [50, 35, 15]),
            "mortis_relic": ([40000, 80000, 200000], [50, 40, 10]),
            "chainsaw_case": ([200, 1000, 5000], [70, 25, 5])
        }

        if item_id in case_rewards:
            inventory[item_id] -= 1
            # Анимация через edit_original_response (последующие правки)
            for frame in ["🎰 **Запуск рулетки...**", "⏳ [ ❓ | ❓ | ❓ ]", "🎰 [ ✨ | ❓ | ✨ ]", "🚀 [ 💰 | ✨ | 💰 ]"]:
                await asyncio.sleep(0.7)
                await interaction.edit_original_response(content=frame)
            
            res_list, weights = case_rewards[item_id]
            win = random.choices(res_list, weights=weights)[0]
            user["balance"] += win
            msg = f"🎊 Выигрыш из кейса: **{format_number(win)}** {ECONOMY_EMOJIS['coin']}!"
        
        elif item_id == "energy_drink":
            inventory[item_id] -= 1
            user["work_boost"] = True
            msg = "🥤 Энергетик выпит! Бонус к следующей работе активирован."
        
        elif item_id == "gift_box":
            res = random.randint(500, 5000)
            inventory[item_id] -= 1
            user["balance"] += res
            msg = f"🎁 Внутри подарка было **{format_number(res)}** {ECONOMY_EMOJIS['coin']}!"

        # Сохраняем и обновляем UI
        economy_db.update_user(self.user_id, user)
        self.refresh_items()
        
        new_embed = self.create_embed(user, interaction.user)
        
        # ВАЖНО: Используем edit_original_response, так как на взаимодействие уже ответили
        await interaction.edit_original_response(content=f"✅ {msg}", embed=new_embed, view=self)

    @staticmethod
    def create_embed(user_data, member):
        embed = discord.Embed(title=f"🎒 Инвентарь {member.display_name}", color=0x3498db)
        inv = user_data.get("inventory", {})
        
        lines = []
        for iid, count in inv.items():
            if count <= 0: continue
            info = SHOP_ITEMS.get(iid) or INVENTORY_ITEMS.get(iid)
            if info:
                lines.append(f"{info.get('emoji')} **{info['name']}** — `{count} шт.`")
        
        embed.description = "\n".join(lines) if lines else "*Пусто... Купите что-нибудь в магазине!*"
        embed.set_footer(text=f"Баланс: {format_number(user_data.get('balance', 0))} монет")
        return embed

# ====================== UI: МАГАЗИН С КАТЕГОРИЯМИ ======================
class ShopView(discord.ui.View):
    def __init__(self, user_id: int, member: discord.Member):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.member = member
        self.current_category = None

        # Создаем начальный список категорий
        options = [
            discord.SelectOption(
                label=data["name"], 
                value=cid, 
                emoji=data.get("emoji"), 
                description=data.get("description", "")[:100]
            ) for cid, data in SHOP_CATEGORIES.items()
        ]
        
        self.select_cat = discord.ui.Select(
            placeholder="Выберите категорию товаров...", 
            options=options, 
            custom_id="shop_cat"
        )
        self.select_cat.callback = self.category_callback
        self.add_item(self.select_cat)

    async def category_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
        
        self.current_category = self.select_cat.values[0]
        await self.update_shop_embed(interaction)

    async def update_shop_embed(self, interaction: discord.Interaction):
        # Импортируем данные события для актуальности
        from config.shop import CURRENT_EVENT, SHOP_CATEGORIES, SHOP_ITEMS
        
        cat_data = SHOP_CATEGORIES.get(self.current_category, {})
        
        # Формируем блок информации о событии (причина скидок)
        event_text = ""
        if CURRENT_EVENT and CURRENT_EVENT.get("name"):
            event_text = f"🎊 **СОБЫТИЕ: {CURRENT_EVENT['name']}**\n"
            event_text += f"💡 *{CURRENT_EVENT['reason']}*\n\n"

        embed = discord.Embed(
            title=f"{cat_data.get('emoji')} Категория: {cat_data.get('name')}",
            description=f"{event_text}*{cat_data.get('description', 'Предметы представлены ниже')}*\n\n",
            color=0x9B59B6
        )

        # Фильтруем предметы по выбранной категории
        items = {k: v for k, v in SHOP_ITEMS.items() if v.get('category') == self.current_category}
        
        if not items:
            embed.description += "В этой категории пока пусто."
        else:
            item_options = []
            for iid, info in items.items():
                old_p = info['price']
                cur_p = get_item_price(iid, self.member)
                
                price_text = f"**Цена:** {format_number(cur_p)} {ECONOMY_EMOJIS['coin']}"
                # Если цена со скидкой меньше базовой, показываем это красиво
                if cur_p < old_p:
                    price_text = f"**Цена:** ~~{format_number(old_p)}~~ → **{format_number(cur_p)}** {ECONOMY_EMOJIS['coin']} 🔥"

                embed.add_field(
                    name=f"{info.get('emoji')} {info['name']}", 
                    value=f"{price_text}\n{info.get('description', '')}", 
                    inline=False
                )
                item_options.append(discord.SelectOption(label=info['name'], value=iid, emoji=info.get('emoji')))

            # Удаляем старый селектор предметов (если он был), чтобы заменить на новый
            for child in self.children[:]:
                if isinstance(child, discord.ui.Select) and child.custom_id != "shop_cat":
                    self.remove_item(child)

            # Добавляем выпадающий список для выбора товара
            item_select = discord.ui.Select(placeholder="Выберите товар для покупки...", options=item_options)
            item_select.callback = self.initiate_purchase
            self.add_item(item_select)
        
        # Защита от ошибки InteractionResponded
        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.edit_original_response(embed=embed, view=self)

    async def initiate_purchase(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id: 
            return await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
        
        item_id = interaction.data['values'][0]
        item = SHOP_ITEMS[item_id]
        
        old_price = item["price"]
        current_price = get_item_price(item_id, self.member)
        discount = old_price - current_price

        confirm_embed = discord.Embed(title="💳 Подтверждение покупки", color=0x2ecc71)
        confirm_embed.set_thumbnail(url=self.member.display_avatar.url)
        
        msg = f"Вы выбрали: **{item['emoji']} {item['name']}**\n\n"
        if discount > 0:
            msg += f"💰 Обычная цена: ~~{format_number(old_price)}~~\n"
            msg += f"🔥 **Цена для вас: {format_number(current_price)}**\n"
            msg += f"✨ Экономия: {format_number(discount)} {ECONOMY_EMOJIS['coin']}"
        else:
            msg += f"К оплате: **{format_number(current_price)}** {ECONOMY_EMOJIS['coin']}"
        
        confirm_embed.description = msg

        await interaction.response.send_message(
            embed=confirm_embed, 
            view=ConfirmPurchaseView(item_id, self.member, current_price, self.user_id), 
            ephemeral=True
        )
# ====================== ОСНОВНОЙ COG ======================
class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="shop", description="🛒 Открыть магазин MortisPlay")
    async def shop(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🛒 Магазин MortisPlay",
            description="Выберите категорию товаров ниже.\nЦены обновляются автоматически!",
            color=0x2b2d31
        )
        view = ShopView(interaction.user.id, interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        # Добавьте это внутрь класса EconomyCog в economy.py
    def add_balance(self, user_id: int, amount: int):
        user = economy_db.get_user(user_id)
        user["balance"] = user.get("balance", 0) + amount
        economy_db.update_user(user_id, user)
        return user["balance"]

# ====================== ПРЕДМЕТЫ ИЗ ИНВЕНТАРЯ (INVENTORY ITEMS) ======================

    # Обработчик автозаполнения для предметов
    async def item_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        user = economy_db.get_user(interaction.user.id)
        inventory = user.get("inventory", {})
        
        choices = []
        for iid, count in inventory.items():
            if count <= 0: continue
            info = SHOP_ITEMS.get(iid) or INVENTORY_ITEMS.get(iid)
            if not info: continue
            
            name = f"{info['name']} (у вас {count} шт.)"
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=iid))
        
        return choices[:25] # Лимит Discord — 25 вариантов

    @app_commands.command(name="pay", description="💸 Передать валюту или предметы другому игроку")
    @app_commands.autocomplete(item_id=item_autocomplete)
    @app_commands.describe(
        member="Кому передаем?",
        amount="Количество (необязательно)",
        currency="Тип валюты (Монеты или MortisCoin)",
        item_id="Предмет из инвентаря (необязательно)"
    )
    @app_commands.choices(currency=[
        app_commands.Choice(name="🪙 Обычные монеты (Комиссия 5%)", value="balance"),
        app_commands.Choice(name="💎 MortisCoin (Без комиссии, нужна верификация)", value="mortis_coins")
    ])
    async def pay(
        self, 
        interaction: discord.Interaction, 
        member: discord.Member, 
        amount: int = 0, 
        currency: str = "balance", # По умолчанию обычные монеты
        item_id: str = None
    ):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Нельзя передавать что-то самому себе!", ephemeral=True)
        
        if member.bot:
            return await interaction.response.send_message("❌ Ботам не нужны ваши подарки.", ephemeral=True)

        if amount <= 0 and item_id is None:
            return await interaction.response.send_message("❌ Укажите сумму или выберите предмет.", ephemeral=True)

        sender_data = economy_db.get_user(interaction.user.id)
        receiver_data = economy_db.get_user(member.id)
        
        # --- АНТИЧИТ: Проверка возраста аккаунта (минимум 3 дня) ---
        account_age = datetime.now(interaction.user.created_at.tzinfo) - interaction.user.created_at
        if account_age.days < 3:
            return await interaction.response.send_message("❌ **Античит:** Ваш аккаунт слишком новый для передачи активов.", ephemeral=True)

        msg_parts = []

        # Логика передачи валюты
        if amount > 0:
            # Проверка верификации для MortisCoin
            if currency == "mortis_coins" and not sender_data.get("is_verified", False):
                return await interaction.response.send_message("❌ Вы не можете передавать **MortisCoin**, так как не прошли верификацию! (/verify)", ephemeral=True)

            if sender_data.get(currency, 0) < amount:
                currency_name = "монет" if currency == "balance" else "MortisCoin"
                return await interaction.response.send_message(f"❌ У вас недостаточно {currency_name}!", ephemeral=True)
            
            # РАСЧЕТ КОМИССИИ
            if currency == "balance":
                commission = int(amount * 0.05) # 5% комиссия
                receive_amount = amount - commission
                display_emoji = ECONOMY_EMOJIS['coin']
                comm_text = f" (Комиссия: {commission} {display_emoji})"
            else:
                receive_amount = amount # Для MortisCoin комиссия 0%
                display_emoji = "💎"
                comm_text = ""

            sender_data[currency] -= amount
            receiver_data[currency] = receiver_data.get(currency, 0) + receive_amount
            msg_parts.append(f"**{format_number(receive_amount)}** {display_emoji}{comm_text}")

        # Логика передачи предмета (остается без изменений)
        if item_id:
            sender_inv = sender_data.get("inventory", {})
            # Проверка: если инвентарь - список, а не словарь, фиксим на ходу
            if isinstance(sender_inv, list): 
                 return await interaction.response.send_message("❌ Ошибка инвентаря. Свяжитесь с админом.", ephemeral=True)

            if sender_inv.get(item_id, 0) <= 0:
                return await interaction.response.send_message("❌ У вас нет этого предмета!", ephemeral=True)
            
            item_info = SHOP_ITEMS.get(item_id) or INVENTORY_ITEMS.get(item_id)
            sender_inv[item_id] -= 1
            receiver_inv = receiver_data.get("inventory", {})
            receiver_inv[item_id] = receiver_inv.get(item_id, 0) + 1
            
            sender_data["inventory"] = sender_inv
            receiver_data["inventory"] = receiver_inv
            msg_parts.append(f"**{item_info['emoji']} {item_info['name']}**")

        economy_db.update_user(interaction.user.id, sender_data)
        economy_db.update_user(member.id, receiver_data)

        res_msg = " и ".join(msg_parts)
        await interaction.response.send_message(f"✅ {interaction.user.mention} передал {member.mention}: {res_msg}")    

    @app_commands.command(name="inventory", description="🎒 Посмотреть свои вещи")
    async def inventory(self, interaction: discord.Interaction):
        user = economy_db.get_user(interaction.user.id)
        inventory = user.get("inventory", {})

        # ПРОВЕРКА: Если инвентарь вдруг оказался списком, превращаем его в пустой словарь
        if isinstance(inventory, list):
            inventory = {}
            user["inventory"] = {}
            economy_db.update_user(interaction.user.id, user)

        if not inventory:
            return await interaction.response.send_message("🎒 Ваш инвентарь пуст.", ephemeral=True)

        emb = discord.Embed(title=f"Инвентарь {interaction.user.display_name}", color=0x3498db)
        
        inv_text = ""
        for iid, amt in inventory.items(): # Теперь .items() не вызовет ошибку
            if amt > 0:
                item = SHOP_ITEMS.get(iid) or INVENTORY_ITEMS.get(iid)
                if item:
                    inv_text += f"{item['emoji']} **{item['name']}** — {amt} шт.\n"
                else:
                    inv_text += f"❓ **{iid}** — {amt} шт.\n"

        emb.description = inv_text or "Тут пока ничего нет."
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="balance", description="💰 Проверить состояние счета")
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        user_data = economy_db.get_user(target.id)
        balance = user_data.get("balance", 0)
        
        # Создаем красивый Embed
        embed = discord.Embed(
            title=f"Финансы — {target.display_name}",
            color=0x2ecc71 if balance > 0 else 0xe74c3c, # Зеленый если есть деньги, красный если 0
            timestamp=datetime.now()
        )
        
        # Добавляем аватар пользователя сбоку
        embed.set_thumbnail(url=target.display_avatar.url)
        
        # Основное поле с балансом
        embed.add_field(
            name="Текущий счет", 
            value=f"```fix\n{format_number(balance)} {ECONOMY_EMOJIS['coin']}```", 
            inline=False
        )

        # Добавляем статус из профиля для красоты
        status = user_data.get("status", "Новичок 🍼")
        embed.add_field(name="Ранг", value=status, inline=True)
        
        # Инфо о том, чей это баланс в футере
        footer_text = "Ваш личный счет" if target == interaction.user else f"Счет пользователя {target.name}"
        embed.set_footer(text=footer_text)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    @app_commands.command(name="vault", description="🏦 Центробанк: курсы валют и налоги")
    async def vault(self, interaction: discord.Interaction):
        # В будущем rate можно сделать динамическим
        rate = 500 
        
        emb = discord.Embed(
            title="🏦 Центральное Хранилище Mortis", 
            description="Управляйте своими активами и следите за налогами.",
            color=0xf1c40f
        )
        emb.add_field(
            name="🪙 Обычные Монеты", 
            value="• Комиссия на перевод: **5%**\n• Налог (если >10к): **2% в сутки**\n• Доступно: **Всем**", 
            inline=False
        )
        emb.add_field(
            name="💎 MortisCoin", 
            value=f"• Курс: **1 💎 = {rate} 🪙**\n• Комиссия: **0%**\n• Налоги: **Нет**\n• Доступно: **После верификации**", 
            inline=False
        )
        emb.set_footer(text="Mortis Economy System • Справедливость для каждого")
        
        await interaction.response.send_message(embed=emb)     

    @app_commands.command(name="work", description="⚒️ Отправиться на работу")
    async def work(self, interaction: discord.Interaction):
        user = economy_db.get_user(interaction.user.id)
        
        # --- [ АНТИЧИТ: ПРОВЕРКА ВОЗРАСТА АККАУНТА ] ---
        # Если аккаунту меньше 3 дней, работать нельзя
        now = datetime.now(timezone.utc)
        account_age = now - interaction.user.created_at
        if account_age.days < 3:
            return await interaction.response.send_message(
                f"❌ **Античит:** Ваш аккаунт слишком новый (создан {account_age.days} дн. назад).\n"
                f"Для участия в экономике аккаунту должно быть минимум **3 дня**.", 
                ephemeral=True
            )

        # --- [ АНТИЧИТ: ПРОВЕРКА КУЛДАУНА ] ---
        # Предположим, работать можно раз в 30 минут (1800 секунд)
        WORK_COOLDOWN = 1800 
        last_work_str = user.get("last_work")
        
        if last_work_str:
            last_work_time = datetime.fromisoformat(last_work_str)
            if now < last_work_time + timedelta(seconds=WORK_COOLDOWN):
                remaining = (last_work_time + timedelta(seconds=WORK_COOLDOWN)) - now
                minutes, seconds = divmod(int(remaining.total_seconds()), 60)
                return await interaction.response.send_message(
                    f"⌛ Вы слишком устали! Отдохните еще **{minutes}м. {seconds}с.**", 
                    ephemeral=True
                )

        # --- [ ЛОГИКА РАБОТЫ ] ---
        job_id = user.get("job", "unemployed")
        if job_id == "unemployed":
            return await interaction.response.send_message("❌ Сначала устройтесь на работу!", ephemeral=True)

        job_info = JOBS.get(job_id)
        reward = random.randint(job_info["min_salary"], job_info["max_salary"])
        
        # Применение бонусов
        bonus = 1.0
        bonus_text = ""
        inventory = user.get("inventory", {})
        
        if inventory.get("pro_tools", 0) > 0:
            bonus += 0.2
            bonus_text += " (+20% 🛠️)"
            
        if user.get("work_boost"):
            bonus += 0.5
            user["work_boost"] = False 
            bonus_text += " (+50% 🥤)"

        final_reward = int(reward * bonus)
        
        # --- [ АНТИЧИТ: ПРОВЕРКА ПОДОЗРИТЕЛЬНЫХ ВЫПЛАТ ] ---
        # Если награда превышает максимально возможную с учетом всех бустов
        max_possible = int(job_info["max_salary"] * 1.7) # 1.7 это 100% + 20% + 50%
        if final_reward > max_possible + 10: # +10 для запаса на округление
            user["warnings"] = user.get("warnings", 0) + 1
            economy_db.update_user(interaction.user.id, user)
            return await interaction.response.send_message(
                "⚠️ **Античит:** Обнаружена попытка накрутки баланса. Ваше действие отклонено, администрация уведомлена.", 
                ephemeral=True
            )

        # Обновление данных
        user["balance"] = user.get("balance", 0) + final_reward
        user["last_work"] = now.isoformat() # Сохраняем время работы
        
        economy_db.update_user(interaction.user.id, user)
        
        await interaction.response.send_message(
            f"⚒️ Вы поработали и получили **{format_number(final_reward)}** {ECONOMY_EMOJIS['coin']}{bonus_text}", 
            ephemeral=True
        )
    @app_commands.command(name="verify", description="🔐 Пройти верификацию для доступа к MortisCoin")
    async def verify(self, interaction: discord.Interaction):
        user = economy_db.get_user(interaction.user.id)
        
        if user.get("is_verified"):
            return await interaction.response.send_message("✅ Вы уже прошли верификацию и имеете доступ к MortisCoin!", ephemeral=True)

        # --- ЭТАП 1: МАТЕМАТИКА ---
        a, b = random.randint(15, 60), random.randint(15, 60)
        math_result = a + b
        
        await interaction.response.send_message(
            f"🛡️ **Верификация: Этап 1 из 2**\n\nРешите пример: Сколько будет **{a} + {b}**?\n"
            f"*У вас 20 секунд. Напишите ответ прямо в этот чат.*", 
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            # Ждем ответ на математику
            msg = await self.bot.wait_for("message", check=check, timeout=20.0)
            
            if msg.content.strip() != str(math_result):
                return await interaction.followup.send("❌ Неверно! Верификация провалена. Попробуйте позже.", ephemeral=True)
            
            # Удаляем сообщение пользователя, чтобы не засорять чат (если есть права)
            try: await msg.delete() 
            except: pass

            # --- ЭТАП 2: КАПЧА ---
            captcha = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            await interaction.followup.send(
                f"✅ Верно! **Этап 2 из 2**\n\nВведите код с картинки (регистр важен):\n"
                f"# ` {captcha} `\n"
                f"*У вас 20 секунд.*", 
                ephemeral=True
            )

            msg_captcha = await self.bot.wait_for("message", check=check, timeout=20.0)

            if msg_captcha.content.strip() == captcha:
                # Успех! Обновляем базу
                user["is_verified"] = True
                economy_db.update_user(interaction.user.id, user)
                
                # Дарим небольшой бонус за прохождение
                user["mortis_coins"] = user.get("mortis_coins", 0) + 1
                
                await interaction.followup.send(
                    "🎉 **Поздравляем!**\nВы успешно подтвердили свою личность.\n"
                    "• Вам доступна валюта **MortisCoin**.\n"
                    "• Налоги и комиссии при переводах отключены.\n"
                    "• Вам начислен бонус: **1 💎 MortisCoin**!", 
                    ephemeral=True
                )
                try: await msg_captcha.delete() 
                except: pass
            else:
                await interaction.followup.send("❌ Неверный код капчи! Попробуйте снова через команду.", ephemeral=True)

        except asyncio.TimeoutError:
            await interaction.followup.send("⏱️ Время вышло! Вы не успели пройти проверку.", ephemeral=True)    

    @app_commands.command(name="daily", description="🎁 Ежедневная награда")
    async def daily(self, interaction: discord.Interaction):
        user = economy_db.get_user(interaction.user.id)
        now = datetime.now()
        last_daily = user.get("last_daily")
        
        if isinstance(last_daily, str):
            try:
                last_dt = datetime.fromisoformat(last_daily)
                if now < last_dt + timedelta(seconds=DAILY_COOLDOWN):
                    delta = (last_dt + timedelta(seconds=DAILY_COOLDOWN)) - now
                    hours, remainder = divmod(int(delta.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)
                    return await interaction.response.send_message(
                        f"❌ Вы уже забирали бонус. Приходите через **{hours}ч. {minutes}м.**", 
                        ephemeral=True
                    )
            except ValueError:
                pass

        reward = random.randint(10, 50)
        user["balance"] = user.get("balance", 0) + reward
        user["last_daily"] = now.isoformat()
        
        economy_db.update_user(interaction.user.id, user)
        await interaction.response.send_message(f"🎁 Вы забрали награду: **{reward}** {ECONOMY_EMOJIS['coin']}!", ephemeral=True)

    @app_commands.command(name="profile", description="👤 Посмотреть свой профиль и статус")
    async def profile(self, interaction: discord.Interaction, member: discord.Member = None):
        target = member or interaction.user
        u = economy_db.get_user(target.id)
        
        # Выбираем цвет: золотой для верифицированных, зеленый для обычных
        is_verified = u.get("is_verified", False)
        emb_color = 0xf1c40f if is_verified else 0x2ecc71
        
        # Добавляем галочку к имени, если верифицирован
        verify_badge = " ✅" if is_verified else ""
        emb = discord.Embed(title=f"Профиль {target.display_name}{verify_badge}", color=emb_color)
        
        status = u.get("status", "Новичок 🍼")
        emb.add_field(name="🏷️ Статус", value=f"**{status}**", inline=False)
        
        # Отображаем обе валюты (используем .get чтобы избежать ошибок)
        coins = format_number(u.get('balance', 0))
        m_coins = format_number(u.get('mortis_coins', 0))
        
        emb.add_field(name="🪙 Баланс", value=f"{coins} {ECONOMY_EMOJIS['coin']}", inline=True)
        emb.add_field(name="💎 MortisCoin", value=f"{m_coins} 💎", inline=True)
        
        # --- БЕЗОПАСНЫЙ ИНВЕНТАРЬ ---
        inventory = u.get("inventory", {})
        inv_list = []
        
        if isinstance(inventory, dict):
            for iid, amt in inventory.items():
                if amt > 0:
                    # Ищем информацию о предмете в магазине или списке инвентаря
                    item_info = SHOP_ITEMS.get(iid) or INVENTORY_ITEMS.get(iid)
                    if item_info:
                        inv_list.append(f"{item_info['emoji']} {item_info['name']}: {amt}")
                    else:
                        # Если предмета 'lucky_day' нет в коде, бот просто выведет его ID
                        # Это предотвращает KeyError
                        inv_list.append(f"❓ {iid}: {amt}")

        inv_text = "\n".join(inv_list) if inv_list else "Пусто"
        emb.add_field(name="🎒 Инвентарь", value=inv_text, inline=False)

        emb.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=emb, ephemeral=True)

    @app_commands.command(name="exchange", description="💱 Обменять обычные монеты на MortisCoin")
    @app_commands.describe(amount_coins="Сколько обычных монет вы отдаете?")
    async def exchange(self, interaction: discord.Interaction, amount_coins: int):
        if amount_coins < 500:
            return await interaction.response.send_message("❌ Минимальная сумма для обмена — **500** 🪙", ephemeral=True)
            
        user = economy_db.get_user(interaction.user.id)
        
        if not user.get("is_verified"):
            return await interaction.response.send_message("❌ Обмен доступен только после верификации! (/verify)", ephemeral=True)
            
        if user.get("balance", 0) < amount_coins:
            return await interaction.response.send_message("❌ У вас недостаточно монет для обмена!", ephemeral=True)
            
        # Курс: 500 монет = 1 MortisCoin
        rate = 500
        m_coins_to_receive = amount_coins // rate
        final_coins_spent = m_coins_to_receive * rate # Тратим только кратное курсу
        
        if m_coins_to_receive <= 0:
            return await interaction.response.send_message(f"❌ Этой суммы недостаточно даже для 1 💎 (нужно {rate} 🪙)", ephemeral=True)
            
        user["balance"] -= final_coins_spent
        user["mortis_coins"] = user.get("mortis_coins", 0) + m_coins_to_receive
        
        economy_db.update_user(interaction.user.id, user)
        
        await interaction.response.send_message(
            f"✅ Успешный обмен!\nОтдано: **{format_number(final_coins_spent)}** 🪙\n"
            f"Получено: **{format_number(m_coins_to_receive)}** 💎"
        )    

async def setup(bot: commands.Bot):
    await bot.add_cog(EconomyCog(bot))