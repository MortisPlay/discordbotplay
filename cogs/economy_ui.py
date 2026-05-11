# economy_ui.py
from __future__ import annotations
import discord
from discord.ui import View, Button, Select
from datetime import datetime
import asyncio
import random

from config.settings import logger, format_number
from config.economy import ECONOMY_EMOJIS
from config.shop import SHOP_ITEMS, SHOP_CATEGORIES, CURRENT_EVENT, INVENTORY_ITEMS
from utils.db import economy_db


# ====================== ПОДТВЕРЖДЕНИЕ ПОКУПКИ ======================
class ConfirmPurchaseView(View):
    def __init__(self, item_id: str, member: "discord.Member", final_price: int, user_id: int):
        super().__init__(timeout=60)
        self.item_id = item_id
        self.member = member
        self.final_price = final_price
        self.user_id = user_id

    @discord.ui.button(label="✅ Подтвердить", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: "discord.Interaction", button: Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)

        user = economy_db.get_user(self.member.id)
        if user.get("balance", 0) < self.final_price:
            return await interaction.response.send_message("❌ Недостаточно средств!", ephemeral=True)

        item = SHOP_ITEMS.get(self.item_id)
        if not item:
            return await interaction.response.send_message("❌ Предмет не найден.", ephemeral=True)

        user["balance"] -= self.final_price

        if item.get("category") == "statuses":
            user["status"] = f"{item['emoji']} {item['name']}"
            success_msg = f"✅ Статус успешно установлен: **{user['status']}**"
        else:
            inventory = user.setdefault("inventory", {})
            inventory[self.item_id] = inventory.get(self.item_id, 0) + 1
            success_msg = f"✅ Вы купили **{item['name']}** за **{format_number(self.final_price)}** {ECONOMY_EMOJIS['coin']}"

        economy_db.update_user(self.member.id, user)
        await interaction.response.edit_message(content=success_msg, embed=None, view=None)

    @discord.ui.button(label="❌ Отмена", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: "discord.Interaction", button: Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)
        await interaction.response.edit_message(content="🛒 Покупка отменена.", embed=None, view=None)


# ====================== ИНВЕНТАРЬ ======================
class InventoryView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.refresh_items()

    def refresh_items(self):
        self.clear_items()
        user = economy_db.get_user(self.user_id)
        inventory = user.get("inventory", {})

        usable_items = {k: v for k, v in inventory.items() if v > 0}

        if not usable_items:
            return

        options = []
        for iid, count in usable_items.items():
            info = SHOP_ITEMS.get(iid) or INVENTORY_ITEMS.get(iid)
            if not info:
                continue
            options.append(discord.SelectOption(
                label=f"{info['name']} ({count} шт.)",
                value=iid,
                emoji=info.get("emoji"),
                description=info.get("description", "")[:100]
            ))

        if options:
            select = Select(
                placeholder="Выберите предмет для использования...",
                options=options[:25]
            )
            select.callback = self.use_callback
            self.add_item(select)

    async def use_callback(self, interaction: "discord.Interaction"):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваш инвентарь!", ephemeral=True)

        item_id = interaction.data['values'][0]
        user = economy_db.get_user(self.user_id)
        inventory = user.setdefault("inventory", {})

        if inventory.get(item_id, 0) <= 0:
            return await interaction.response.send_message("❌ Предмета больше нет!", ephemeral=True)

        await interaction.response.edit_message(content="🔄 **Используем предмет...**", embed=None, view=None)

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
            for frame in ["🎰 Запуск рулетки...", "⏳ [ ❓ | ❓ | ❓ ]", "🎰 [ ✨ | ❓ | ✨ ]", "🚀 [ 💰 | ✨ | 💰 ]"]:
                await asyncio.sleep(0.6)
                await interaction.edit_original_response(content=frame)

            rewards, weights = case_rewards[item_id]
            win = random.choices(rewards, weights=weights)[0]
            user["balance"] = user.get("balance", 0) + win
            msg = f"🎊 **Выигрыш:** {format_number(win)} {ECONOMY_EMOJIS['coin']}"

        elif item_id == "energy_drink":
            inventory[item_id] -= 1
            user["work_boost"] = True
            msg = "🥤 Энергетик выпит! +50% к следующей работе."

        elif item_id == "gift_box":
            res = random.randint(500, 5000)
            inventory[item_id] -= 1
            user["balance"] = user.get("balance", 0) + res
            msg = f"🎁 В подарке было **{format_number(res)}** {ECONOMY_EMOJIS['coin']}"

        economy_db.update_user(self.user_id, user)
        self.refresh_items()

        embed = self.create_embed(user, interaction.user)
        await interaction.edit_original_response(content=f"✅ {msg}", embed=embed, view=self)

    @staticmethod
    def create_embed(user_data: dict, member: "discord.Member"):
        embed = discord.Embed(
            title=f"🎒 Инвентарь — {member.display_name}",
            color=0x1abc9c
        )
        inv = user_data.get("inventory", {})

        lines = []
        for iid, count in inv.items():
            if count <= 0:
                continue
            info = SHOP_ITEMS.get(iid) or INVENTORY_ITEMS.get(iid)
            if info:
                lines.append(f"{info.get('emoji', '📦')} **{info['name']}** — `{count}` шт.")
            else:
                lines.append(f"❓ **{iid}** — `{count}` шт.")

        if lines:
            embed.description = "\n".join(lines)
        else:
            embed.description = "*Инвентарь пуст...*\nПопробуйте `/shop`, `/work` или `/vault` для новых возможностей."

        job_name = user_data.get("job", "Безработный")
        boost_status = "Да" if user_data.get("work_boost") else "Нет"
        embed.add_field(
            name="⚙️ Статус",
            value=f"Работа: `{job_name.capitalize()}`\nЭнергетик: `{boost_status}`",
            inline=False
        )
        embed.set_footer(text=f"Баланс: {format_number(user_data.get('balance', 0))} {ECONOMY_EMOJIS['coin']} • /work /vault")
        embed.set_thumbnail(url=member.display_avatar.url)
        return embed


# ====================== МАГАЗИН (ИСПРАВЛЕНО) ======================
class ShopView(View):
    def __init__(self, user_id: int, member: "discord.Member"):
        super().__init__(timeout=300)
        self.user_id = user_id
        self.member = member
        self.current_category = None

        options = [
            discord.SelectOption(
                label=data["name"],
                value=cid,
                emoji=data.get("emoji"),
                description=data.get("description", "")[:100]
            )
            for cid, data in SHOP_CATEGORIES.items()
        ]

        select_cat = Select(
            placeholder="📂 Выберите категорию...",
            options=options
        )
        select_cat.callback = self.category_callback
        self.add_item(select_cat)

    async def category_callback(self, interaction: "discord.Interaction"):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)

        self.current_category = interaction.data['values'][0]
        await self.update_shop_embed(interaction)

    async def update_shop_embed(self, interaction: "discord.Interaction"):
        cat_data = SHOP_CATEGORIES.get(self.current_category, {})
        
        event_text = ""
        if CURRENT_EVENT and CURRENT_EVENT.get("name"):
            event_text = f"🎊 **{CURRENT_EVENT['name']}**\n{CURRENT_EVENT.get('reason', '')}\n\n"

        embed = discord.Embed(
            title=f"{cat_data.get('emoji', '🛒')} {cat_data.get('name', 'Магазин')}",
            description=event_text + cat_data.get("description", ""),
            color=0x9B59B6
        )

        items = {k: v for k, v in SHOP_ITEMS.items() if v.get('category') == self.current_category}

        item_options = []
        for iid, info in items.items():
            price = get_item_price(iid, self.member)
            old_price = info["price"]

            price_text = f"**Цена:** {format_number(price)} {ECONOMY_EMOJIS['coin']}"
            if price < old_price:
                price_text = f"**Цена:** ~~{format_number(old_price)}~~ → **{format_number(price)}** 🔥"

            embed.add_field(
                name=f"{info.get('emoji', '')} {info['name']}",
                value=f"{price_text}\n{info.get('description', '')}",
                inline=False
            )

            item_options.append(discord.SelectOption(
                label=info['name'],
                value=iid,
                emoji=info.get('emoji')
            ))

        # Удаляем старый селект товаров
        for child in self.children[:]:
            if isinstance(child, Select) and child.placeholder != "📂 Выберите категорию...":
                self.remove_item(child)

        if item_options:
            item_select = Select(placeholder="🛍️ Выберите товар...", options=item_options[:25])
            item_select.callback = self.initiate_purchase
            self.add_item(item_select)

        # === ИСПРАВЛЕНИЕ ОШИБКИ Unknown Webhook ===
        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        except discord.errors.NotFound:
            # Если сообщение уже удалено или недоступно
            await interaction.followup.send("❌ Сессия магазина устарела. Используйте `/shop` заново.", ephemeral=True)
        except Exception as e:
            logger.error(f"Ошибка обновления магазина: {e}")
            await interaction.followup.send("❌ Произошла ошибка при обновлении магазина.", ephemeral=True)

    async def initiate_purchase(self, interaction: "discord.Interaction"):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваше меню!", ephemeral=True)

        item_id = interaction.data['values'][0]
        item = SHOP_ITEMS[item_id]
        final_price = get_item_price(item_id, self.member)

        confirm_embed = discord.Embed(title="💳 Подтверждение покупки", color=0x2ecc71)
        confirm_embed.description = f"**{item.get('emoji', '')} {item['name']}**\nЦена: **{format_number(final_price)}** {ECONOMY_EMOJIS['coin']}"

        await interaction.response.send_message(
            embed=confirm_embed,
            view=ConfirmPurchaseView(item_id, self.member, final_price, self.user_id),
            ephemeral=True
        )


# ====================== ПЕРЕКЛЮЧАТЕЛЬ ВАЛЮТ ======================
class CurrencySwitchView(View):
    def __init__(self):
        super().__init__(timeout=240)

    @discord.ui.button(label="🪙 Серверная валюта", style=discord.ButtonStyle.blurple, emoji="🪙")
    async def server_val(self, interaction: "discord.Interaction", button: Button):
        embed = discord.Embed(
            title="🪙 Монеты MortisPlay",
            description=(
                "• Основная внутриигровая валюта\n"
                "• Получается через работу, daily и кейсы\n"
                "• Переводы: 5% комиссия\n"
                "• Используйте в магазине и переводах"
            ),
            color=0x3498db
        )
        embed.add_field(name="Использование", value="`/work`, `/shop`, `/pay`, `/vault`", inline=False)
        embed.set_footer(text="Внутренняя валюта сервера")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="💎 MortisCoin", style=discord.ButtonStyle.green, emoji="💎")
    async def real_val(self, interaction: "discord.Interaction", button: Button):
        embed = discord.Embed(
            title="💎 MortisCoin",
            description=(
                "• Премиальная внутренняя валюта\n"
                "• Без комиссии при переводах\n"
                "• Получается через верификацию и обмен\n"
                "• 500 🪙 = 1 💎"
            ),
            color=0x00c292
        )
        embed.add_field(name="Требования", value="Нужна верификация: `/verify`", inline=False)
        embed.set_footer(text="Премиум валюта сервера")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🌍 Валюты", style=discord.ButtonStyle.gray, emoji="🌐")
    async def fiat_val(self, interaction: "discord.Interaction", button: Button):
        embed = discord.Embed(
            title="🌍 Фиатные валюты",
            description="Показатели настоящих валют, адаптированные для внутреннего баланса MortisPlay.",
            color=0x9b59b6
        )
        embed.add_field(name="🇷🇺 Рубли", value="1 ₽ = 1.4 🪙\n100 ₽ = 140 🪙", inline=False)
        embed.add_field(name="🇺🇸 Доллары", value="1 $ = 82 🪙\n5 $ = 410 🪙", inline=False)
        embed.add_field(name="🇪🇺 Евро", value="1 € = 92 🪙\n5 € = 460 🪙", inline=False)
        embed.add_field(name="💎 MortisCoin", value="1 💎 = 500 🪙\nПремиум валюта без комиссии", inline=False)
        embed.set_footer(text="Курсы ориентировочные и используются только внутри бота.")
        await interaction.response.edit_message(embed=embed, view=self)


# ====================== ЦЕНООБРАЗОВАНИЕ ======================
def get_item_price(item_id: str, member: "discord.Member") -> int:
    """Вычисляет цену с учетом событий"""
    from config.shop import CURRENT_EVENT, SHOP_ITEMS
    item = SHOP_ITEMS.get(item_id)
    if not item:
        return 0
    
    base_price = item["price"]
    today = datetime.now().date()
    event_date = CURRENT_EVENT.get("date")
    
    if event_date and today == event_date:
        return int(base_price * CURRENT_EVENT.get("multiplier", 1.0))
    return base_price