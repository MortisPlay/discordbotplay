import discord
from discord.ui import View, Button, Select
from discord import Interaction
from typing import Optional, Callable
import asyncio

from config.settings import logger


class ConfirmView(View):
    """Универсальное окно подтверждения (Да / Нет)"""
    
    def __init__(self, author_id: int, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value: Optional[bool] = None

    @discord.ui.button(label="✅ Подтвердить", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Это не твоё подтверждение.", ephemeral=True)
        
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="❌ Отмена", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Это не твоё подтверждение.", ephemeral=True)
        
        self.value = False
        self.stop()
        await interaction.response.defer()


class PaginationView(View):
    """Пагинация для длинных списков / эмбедов"""
    
    def __init__(self, embeds: list[discord.Embed], author_id: int, timeout: float = 120.0):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.author_id = author_id
        self.current_page = 0

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.gray)
    async def previous(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Это не твоя панель.", ephemeral=True)
        
        self.current_page = (self.current_page - 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.current_page])

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.gray)
    async def next(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Это не твоя панель.", ephemeral=True)
        
        self.current_page = (self.current_page + 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.current_page])

    @discord.ui.button(label="❌ Закрыть", style=discord.ButtonStyle.red, row=1)
    async def close(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Это не твоя панель.", ephemeral=True)
        await interaction.message.delete()
        self.stop()


class TicketActionView(View):
    """Общие кнопки для тикетов (можно использовать в tickets.py)"""
    
    def __init__(self, ticket_channel_id: int, author_id: int):
        super().__init__(timeout=None)
        self.ticket_channel_id = ticket_channel_id
        self.author_id = author_id

    @discord.ui.button(label="🔒 Закрыть", style=discord.ButtonStyle.red, emoji="🔒")
    async def close(self, interaction: Interaction, button: Button):
        # Можно импортировать логику закрытия из TicketsCog
        await interaction.response.send_message("Закрытие тикета...", ephemeral=True)
        # Дальше логика перенаправляется в cog

    @discord.ui.button(label="⏳ Продлить", style=discord.ButtonStyle.gray, emoji="⏰")
    async def extend(self, interaction: Interaction, button: Button):
        await interaction.response.send_message("⏳ Время тикета продлено на 24 часа.", ephemeral=True)


# ====================== Фабрики ======================

def create_confirm_view(author_id: int) -> ConfirmView:
    """Быстрое создание окна подтверждения"""
    return ConfirmView(author_id=author_id)


async def ask_confirmation(interaction: Interaction, text: str, timeout: float = 45.0) -> bool:
    """Удобная функция подтверждения"""
    embed = discord.Embed(title="Подтверждение", description=text, color=0xFFD700)
    view = ConfirmView(author_id=interaction.user.id, timeout=timeout)
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    await view.wait()
    return view.value is True