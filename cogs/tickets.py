import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, Select
from datetime import datetime, timezone
import asyncio
import random
import io

from config.settings import logger, TICKET_CATEGORY_ID, TICKET_ARCHIVE_CHANNEL_ID, SUPPORT_ROLE_ID
from config.tickets import TICKET_CATEGORIES


class TicketsCog(commands.Cog):
    """Расширенная система тикетов"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_tickets = {}  # channel_id: {author_id, last_activity, ...}

    # ====================== ОСНОВНЫЕ КОМАНДЫ ======================

    @app_commands.command(name="panel", description="🎫 Создать панель тикетов")
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Система поддержки",
            description="Нажмите кнопку ниже, чтобы создать тикет.",
            color=0x9B59B6
        )
        view = ImprovedTicketPanelView(self.bot) # Передаем self.bot
        await interaction.response.send_message(embed=embed, view=view)

    # ====================== UI ======================

class ImprovedTicketPanelView(View):
    def __init__(self, bot: commands.Bot): # Добавили bot
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="🎫 Создать тикет", style=discord.ButtonStyle.green, emoji="📩")
    async def create_ticket(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="Выберите категорию",
            description="Пожалуйста, выберите категорию вашего обращения:",
            color=0x9B59B6
        )
        view = View(timeout=120)
        view.add_item(ImprovedTicketCategorySelect(self.bot)) # Передаем бота
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class ImprovedTicketCategorySelect(Select):
    def __init__(self, bot: commands.Bot): # Добавили bot
        self.bot = bot
        options = [
            discord.SelectOption(
                label=cat['name'],
                value=key,
                emoji=cat['emoji'],
                description=cat['description'][:100]
            )
            for key, cat in TICKET_CATEGORIES.items()
        ]
        super().__init__(
            placeholder="📋 Выберите категорию обращения...",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        # Передаем self.bot в модалку
        modal = TicketFormModal(self.values[0], self.bot)
        await interaction.response.send_modal(modal)


class TicketFormModal(Modal, title="Создание тикета"):
    def __init__(self, category_key: str, bot: commands.Bot): # Добавили bot
        super().__init__(timeout=300)
        self.category_key = category_key
        self.category = TICKET_CATEGORIES[category_key]
        self.bot = bot # Сохраняем бота в self

        for field in self.category["form_fields"]:
            style = discord.TextStyle.long if field["style"] == "long" else discord.TextStyle.short
            self.add_item(TextInput(
                label=field["label"],
                style=style,
                required=field.get("required", True),
                placeholder=field.get("placeholder", ""),
                max_length=1000 if field["style"] == "long" else 200
            ))

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        answers = {field["label"]: self.children[i].value 
                  for i, field in enumerate(self.category["form_fields"])}

        guild = interaction.guild
        category_channel = guild.get_channel(TICKET_CATEGORY_ID)

        if not category_channel or not isinstance(category_channel, discord.CategoryChannel):
            return await interaction.followup.send("❌ Категория тикетов не настроена корректно!", ephemeral=True)

        support_role = guild.get_role(self.category["support_role"])

        # Проверка на уже открытый тикет
        for channel in category_channel.text_channels:
            if channel.topic and str(interaction.user.id) in channel.topic:
                return await interaction.followup.send(
                    "❌ У вас уже есть открытый тикет! Закройте его сначала.", ephemeral=True
                )

        # Создание прав доступа
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            support_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        channel_name = f"{self.category['emoji']}-{interaction.user.name.lower()}-{random.randint(100, 999)}"
        
        ticket_channel = await category_channel.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            topic=f"Тикет от {interaction.user.id} | Категория: {self.category['name']}"
        )

        # ТЕПЕРЬ ОШИБКИ НЕ БУДЕТ: используем self.bot
        self.bot.get_cog("TicketsCog").active_tickets[ticket_channel.id] = {
            "author_id": interaction.user.id,
            "last_activity": datetime.now(timezone.utc).timestamp()
        }

        # Приветственное сообщение
        welcome = f"{interaction.user.mention} {support_role.mention if self.category.get('ping_role') else ''}\n\n"
        welcome += f"**Категория:** {self.category['name']}\n\n"
        welcome += "**Информация из формы:**\n"
        for q, a in answers.items():
            welcome += f"**{q}:** {a}\n"
        welcome += f"\n{self.category['auto_response']}\n\n**Управление тикетом:**"

        # Сюда тоже передаем бота для работы архивации
        view = ImprovedTicketControls(self.bot, ticket_channel.id, interaction.user.id)
        await ticket_channel.send(content=welcome, view=view)

        await interaction.followup.send(f"✅ Тикет создан: {ticket_channel.mention}", ephemeral=True)

        logger.info(f"Новый тикет создан: {ticket_channel.name} ({interaction.user})")


class ImprovedTicketControls(View):
    def __init__(self, bot: commands.Bot, channel_id: int, author_id: int):
        super().__init__(timeout=None)
        self.bot = bot # Добавили
        self.channel_id = channel_id
        self.author_id = author_id

    @discord.ui.button(label="🔒 Закрыть тикет", style=discord.ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        # Проверка прав (уже есть в вашем коде)
        if interaction.user.id != self.author_id and not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Только автор или модератор может закрыть тикет.", ephemeral=True)

        confirm_view = View(timeout=30)
        
        # Функции-обработчики
        async def confirm_callback(inter: discord.Interaction):
            # Сначала отвечаем Дискорду, что мы приняли нажатие
            await inter.response.defer() 
            # Затем запускаем долгий процесс архивации
            await self._archive_and_close(inter)
        
        async def cancel_callback(inter: discord.Interaction):
            await inter.response.edit_message(content="❌ Закрытие отменено.", view=None)

        # Создаем кнопку подтверждения
        btn_confirm = Button(label="✅ Да, закрыть", style=discord.ButtonStyle.green)
        btn_confirm.callback = confirm_callback # Назначаем callback отдельно
        
        # Создаем кнопку отмены
        btn_cancel = Button(label="❌ Отмена", style=discord.ButtonStyle.red)
        btn_cancel.callback = cancel_callback # Назначаем callback отдельно

        # Добавляем кнопки в представление
        confirm_view.add_item(btn_confirm)
        confirm_view.add_item(btn_cancel)

        await interaction.response.send_message("Вы уверены, что хотите закрыть тикет?", view=confirm_view, ephemeral=True)

    async def _archive_and_close(self, interaction: discord.Interaction):
        channel = interaction.channel
        transcript_lines = []
        
        async for msg in channel.history(limit=1000, oldest_first=True):
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            author = f"{msg.author} ({msg.author.id})"
            content = msg.content or "[пустое сообщение]"
            if msg.attachments:
                content += f" | 📎 {', '.join(a.url for a in msg.attachments)}"
            transcript_lines.append(f"[{timestamp}] {author}: {content}")

        transcript_text = "\n".join(transcript_lines) or "[Сообщений не было]"

        # Отправка в архив
        archive_ch = self.bot.get_channel(TICKET_ARCHIVE_CHANNEL_ID)
        if archive_ch:
            # Используем io.StringIO вместо discord.utils.IOStringIO
            file_data = io.StringIO(transcript_text) 
            file = discord.File(
                fp=file_data, 
                filename=f"transcript_{channel.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            emb = discord.Embed(
                title="📜 Тикет закрыт",
                description=f"**Канал:** `{channel.name}`\n**Закрыл:** {interaction.user.mention}",
                color=discord.Color.red(),
                timestamp=datetime.now()
            )
            
            await archive_ch.send(embed=emb, file=file)

        await interaction.channel.send("✅ Тикет заархивирован и будет удален через 5 секунд...")
        await asyncio.sleep(5)
        await channel.delete()

        if channel.id in self.bot.get_cog("TicketsCog").active_tickets:
            del self.bot.get_cog("TicketsCog").active_tickets[channel.id]


# ====================== SETUP ======================
async def setup(bot: commands.Bot):
    await bot.add_cog(TicketsCog(bot))
    logger.info("✅ TicketsCog успешно загружен")