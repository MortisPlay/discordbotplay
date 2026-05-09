import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import asyncio
from typing import Dict, Any, Optional, List

from config.settings import logger, DATA_DIR


class Database:
    """Универсальный менеджер JSON-базы данных"""

    def __init__(self, filename: str, default_data: Any = None):
        self.file_path = Path(DATA_DIR) / filename
        self.default_data = default_data or {}
        self.data: Dict = {}
        self._lock = asyncio.Lock()

    async def load(self) -> Dict:
        """Загрузка данных из файла"""
        async with self._lock:
            try:
                if self.file_path.exists() and self.file_path.stat().st_size > 0:
                    with open(self.file_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            self.data = json.loads(content)
                        else:
                            self.data = self.default_data.copy()
                    logger.debug(f"Загружено: {self.file_path.name}")
                else:
                    self.data = self.default_data.copy()
                    self._write_to_disk()
                    logger.info(f"Создан новый файл: {self.file_path.name}")
                return self.data
            except Exception as e:
                logger.error(f"Ошибка загрузки {self.file_path.name}: {e}")
                self.data = self.default_data.copy()
                return self.data

    async def save(self):
        """Сохранение данных в файл"""
        async with self._lock:
            self._write_to_disk()

    def _write_to_disk(self):
        """Внутренний метод записи (без Lock)"""
        try:
            temp_file = self.file_path.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            temp_file.replace(self.file_path)
        except Exception as e:
            logger.error(f"Ошибка записи {self.file_path.name}: {e}")

    # ====================== Методы данных ======================\

    def get_user(self, user_id: int | str) -> Dict[str, Any]:
        """Получает данные пользователя или создает новые с расширенными полями"""
        user_id = str(user_id)
        if user_id not in self.data:
            # ОБНОВЛЕННЫЙ ШАБЛОН:
            self.data[user_id] = {
                "balance": 0,            # Обычные монеты (с налогами и комиссией)
                "mortis_coins": 0,      # Элитная валюта (без комиссий)
                "is_verified": False,    # Пройдена ли верификация (для MortisCoin)
                "status": "Новичок 🍼",
                "inventory": [],
                "warnings": 0,           # Кол-во подозрений от античита
                "last_work": None,
                "last_daily": None,
                "created_at": datetime.now().isoformat() # Дата регистрации в экономике
            }
        return self.data[user_id]

    def update_user(self, user_id: int | str, data: Dict[str, Any] = None):
        """
        Обновляет данные пользователя. 
        Поддерживает два формата:
        1. update_user(user_dict) - если ID есть внутри словаря (как 'id' или ключ)
        2. update_user(user_id, data) - классический вариант
        """
        if data is None and isinstance(user_id, dict):
            # Если передан только словарь, пытаемся найти ID внутри него
            # Но так как в economy.py мы работаем со структурами без явного ID внутри,
            # лучше сделать метод универсальным:
            logger.error("Метод update_user требует user_id и data")
            return

        u_id = str(user_id)
        self.data[u_id] = data
        asyncio.create_task(self.save())

    async def add_to_user_list(self, user_id: int | str, list_key: str, item: Any):
        """
        Добавляет элемент в список (например, варны или инвентарь).
        Если списка нет, он будет создан автоматически.
        """
        user_data = self.get_user(user_id)
        
        # Проверяем, существует ли ключ и является ли он списком
        if list_key not in user_data or not isinstance(user_data[list_key], list):
            user_data[list_key] = []
            
        user_data[list_key].append(item)
        await self.save()

    def get_user_list(self, user_id: int | str, list_key: str) -> List:
        """Удобный метод для получения списка (например, всех варнов)"""
        user_data = self.get_user(user_id)
        return user_data.get(list_key, [])


# ====================== Экземпляры и Инициализация ======================\

economy_db = Database("economy.json", {})
warnings_db = Database("warnings.json", {})
cases_db = Database("cases.json", {})
faq_db = Database("faq.json", {"questions": []})
ticket_templates_db = Database("ticket_templates.json", {"templates": {}})

async def init_databases():
    os.makedirs(DATA_DIR, exist_ok=True)
    dbs = [
        ("Экономика", economy_db),
        ("Варны", warnings_db),
        ("Кейсы", cases_db),
        ("FAQ", faq_db),
        ("Шаблоны Тикетов", ticket_templates_db)
    ]
    
    for name, db in dbs:
        await db.load()
        logger.info(f"База данных [{name}] успешно инициализирована.")