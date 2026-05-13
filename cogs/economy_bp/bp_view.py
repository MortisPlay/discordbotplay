# modules/economy_bp/bp_view.py

import discord
from discord.ui import View, Button
from datetime import datetime, timezone, timedelta
from .bp_config import BP_SETTINGS, BP_REWARDS, get_level_by_xp, get_xp_progress
from .bp_core import BPCore
from utils.db import economy_db
from utils.helpers import format_duration


def create_timer_display(remaining_seconds: int) -> str:
    if remaining_seconds <= 0:
        return "⏰ Действие завершено!"
    days = remaining_seconds // 86400
    hours = (remaining_seconds % 86400) // 3600
    minutes = (remaining_seconds % 3600) // 60
    seconds = remaining_seconds % 60

    if days > 0:
        return f"⏰ `{days}д {hours}ч {minutes}м`"
    elif hours > 0:
        return f"⏰ `{hours}ч {minutes}м {seconds}с`"
    elif minutes > 0:
        return f"⏰ `{minutes}м {seconds}с`"
    return f"⏰ `{seconds}с`"


def create_progress_bar(value: int, total: int, length: int = 10) -> str:
    progress = min(max(value / max(total, 1), 0), 1)
    filled = int(progress * length)
    bar = "🟩" * filled + "⬛" * (length - filled)
    return f"{bar} {int(progress * 100)}%"

class BattlePassView(View):
    def __init__(self, user_id: int, user_data: dict):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.user_data = user_data

    def create_embed(self):
        xp = self.user_data.get("bp_xp", 0)
        is_premium = self.user_data.get("bp_premium", False)
        current_lvl = get_level_by_xp(xp)
        xp_on_level = get_xp_progress(xp)
        
        # Генерация полоски прогресса
        filled_blocks = int((xp_on_level / BP_SETTINGS["XP_PER_LEVEL"]) * 10)
        progress_bar = "🟩" * filled_blocks + "⬛" * (10 - filled_blocks)
        
        color = BP_SETTINGS["COLOR_PREMIUM"] if is_premium else BP_SETTINGS["COLOR_FREE"]
        now = datetime.now(timezone.utc)
        season_start = BP_SETTINGS["SEASON_START"]
        season_end = season_start + timedelta(days=BP_SETTINGS["SEASON_DURATION_DAYS"])
        season_remaining = season_end - now

        if now < season_start:
            season_text = f"⏳ Сезон начнётся через {create_timer_display(int((season_start - now).total_seconds()))}"
        elif season_remaining.total_seconds() > 0:
            season_text = f"⏳ До конца сезона: {create_timer_display(int(season_remaining.total_seconds()))}"
        else:
            season_text = "⏳ Сезон завершён. Следующий начнётся скоро."
        
        embed = discord.Embed(
            title=f"{BP_SETTINGS['SEASON_NAME']}",
            description=(
                f"👤 **Игрок:** <@{self.user_id}>\n"
                f"📊 **Уровень:** `{current_lvl} / {BP_SETTINGS['MAX_LEVEL']}`\n"
                f"✨ **Опыт:** `{xp_on_level} / {BP_SETTINGS['XP_PER_LEVEL']}`\n"
                f"{progress_bar} {int((xp_on_level / BP_SETTINGS['XP_PER_LEVEL']) * 100)}%\n"
                f"{season_text}\n"
            ),
            color=color
        )

        status_text = "💎 **PREMIUM АКТИВИРОВАН**" if is_premium else "⚪ **БЕСПЛАТНАЯ ВЕТКА** (Купите Premium в `/shop`)"
        embed.add_field(name="Статус пропуска", value=status_text, inline=False)

        embed.add_field(
            name="FAQ — как работает BP",
            value=(
                "🎫 `/pass` показывает ваш Боевой Пропуск и ближайшие награды.\n"
                "🔼 Для перехода на новый уровень нужно набрать полный опыт текущей шкалы: "
                f"`{BP_SETTINGS['XP_PER_LEVEL']}` XP на уровень.\n"
                "💎 Premium Pass покупается в `/shop` и открывает премиум-наградную ветку.\n"
                "⚒️ Чтобы получить больше XP, чаще выполняйте `/work`, участвуйте в активностях и собирайте награды.\n"
                "✨ Чем больше вы играете, тем быстрее повышаетесь и забираете уровни."
            ),
            inline=False
        )

        # Список ближайших наград (показываем текущий, прошлый и следующий уровни)
        rewards_preview = ""
        for lvl in range(max(1, current_lvl), min(current_lvl + 3, BP_SETTINGS["MAX_LEVEL"] + 1)):
            mark = "🎁" if lvl <= current_lvl else "🔒"
            free_gift = BP_REWARDS[lvl]["free"]["label"]
            prem_gift = BP_REWARDS[lvl]["premium"]["label"]
            
            claimed_status = "✅" if lvl in self.user_data.get("bp_claimed", []) else ""
            
            rewards_preview += f"**Ур. {lvl}** {mark} {claimed_status}\n"
            rewards_preview += f"├ Free: {free_gift}\n"
            rewards_preview += f"└ Prem: {prem_gift}\n\n"
        
        embed.add_field(name="Ближайшие награды", value=rewards_preview or "Вы достигли максимума!", inline=False)
        embed.set_footer(text="Нажимайте кнопку ниже, чтобы забрать доступные призы!")
        
        return embed

    @discord.ui.button(label="Забрать награды", style=discord.ButtonStyle.green, emoji="🎁")
    async def claim_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваш пропуск!", ephemeral=True)

        xp = self.user_data.get("bp_xp", 0)
        current_lvl = get_level_by_xp(xp)
        claimed = self.user_data.get("bp_claimed", [])
        
        new_rewards_count = 0
        for lvl in range(1, current_lvl + 1):
            if lvl not in claimed:
                success, _ = BPCore.claim_level_reward(self.user_id, lvl)
                if success:
                    new_rewards_count += 1

        if new_rewards_count > 0:
            # Обновляем данные для отображения
            from utils.db import economy_db
            self.user_data = economy_db.get_user(self.user_id)
            await interaction.response.edit_message(embed=self.create_embed(), view=self)
            await interaction.followup.send(f"✅ Успешно получено наград за {new_rewards_count} ур.!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ У вас нет доступных наград для получения.", ephemeral=True)

    @discord.ui.button(label="🔄 Обновить", style=discord.ButtonStyle.secondary, emoji="🔁")
    async def refresh_btn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Это не ваш пропуск!", ephemeral=True)
        self.user_data = economy_db.get_user(self.user_id)
        await interaction.response.edit_message(embed=self.create_embed(), view=self)
