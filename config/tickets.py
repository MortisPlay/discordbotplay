# config/tickets.py

TICKET_CATEGORIES = {
    "tech_support": {
        "name": "Техническая поддержка",
        "emoji": "🛠️",
        "description": "Проблемы с ботом, ошибки или предложения по функционалу.",
        "support_role": 1475331888163066029,  # ID роли техподдержки
        "ping_role": True,
        "auto_response": "Спасибо за обращение! Опишите вашу проблему максимально подробно, и наши специалисты скоро ответят.",
        "form_fields": [
            {"label": "Суть проблемы", "style": "short", "placeholder": "Например: не работает команда /work", "required": True},
            {"label": "Подробное описание", "style": "long", "placeholder": "Опишите, после чего возникла ошибка...", "required": True}
        ]
    },
    "report": {
        "name": "Жалоба на игрока",
        "emoji": "⚖️",
        "description": "Нарушение правил сервера другими пользователями.",
        "support_role": 1474689484393021442,  # ID роли модератора
        "ping_role": False,
        "auto_response": "Ваша жалоба принята. Пожалуйста, приложите скриншоты или видео нарушений, если вы еще этого не сделали.",
        "form_fields": [
            {"label": "Никнейм нарушителя", "style": "short", "placeholder": "User#0000", "required": True},
            {"label": "Нарушенное правило", "style": "short", "placeholder": "Например: Оскорбление", "required": True},
            {"label": "Обстоятельства", "style": "long", "placeholder": "Расскажите, что произошло...", "required": True}
        ]
    },
    "donation": {
        "name": "Вопрос по донату",
        "emoji": "💳",
        "description": "Вопросы по пополнению баланса или выдаче ролей.",
        "support_role": 1475294922948214925,  # ID роли администратора
        "ping_role": True,
        "auto_response": "Администрация свяжется с вами для уточнения деталей транзакции.",
        "form_fields": [
            {"label": "ID транзакции / Чек", "style": "short", "placeholder": "Введите номер чека", "required": True},
            {"label": "Ваш запрос", "style": "long", "placeholder": "Что именно вы приобрели или хотите узнать?", "required": True}
        ]
    }
}