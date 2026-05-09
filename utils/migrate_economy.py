import json
import os
import sys
from pathlib import Path
import glob

# Добавляем корень проекта в PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import logger, DATA_DIR, ECONOMY_FILE
from utils.db import economy_db


async def migrate_old_economy_to_new():
    """Миграция — ищет economy.json в корне проекта"""
    
    # 1. Основной файл в корне проекта
    root_economy = Path("economy.json")
    
    # 2. Также проверяем в data/
    data_economy = Path(DATA_DIR) / "economy.json"
    
    old_file = None
    if root_economy.exists() and root_economy.stat().st_size > 0:
        old_file = root_economy
        print(f"🔍 Найден economy.json в корне проекта")
    elif data_economy.exists() and data_economy.stat().st_size > 0:
        old_file = data_economy
        print(f"🔍 Найден economy.json в папке data/")
    else:
        # Ищем любые бэкапы
        for pattern in ["economy*.json", "economy_old*.json"]:
            files = list(glob.glob(pattern)) + list(glob.glob(str(Path(DATA_DIR)/pattern)))
            for f in files:
                p = Path(f)
                if p.exists() and p.stat().st_size > 0:
                    old_file = p
                    print(f"🔍 Найден бэкап: {p.name}")
                    break
            if old_file:
                break

    if not old_file:
        print("❌ Не найден economy.json ни в корне, ни в data/")
        return False

    print(f"🔄 Используем файл: {old_file}")

    try:
        with open(old_file, 'r', encoding='utf-8') as f:
            old_data = json.load(f)

        print(f"🔄 Начинаем миграцию {len(old_data)} записей...")

        migrated = 0

        for user_id, data in old_data.items():
            if user_id == "server_vault":
                economy_db.data["server_vault"] = data
                print(f"   ✓ server_vault = {data}")
                continue

            if not isinstance(data, dict):
                continue

            new_user = economy_db.get_user(user_id)
            
            new_user["balance"] = data.get("balance", 0)
            new_user["last_daily"] = data.get("last_daily", 0)
            new_user["last_message"] = data.get("last_message", 0)
            new_user["multiplier"] = data.get("multiplier", 1.0)
            new_user["multiplier_end"] = data.get("multiplier_end", 0)
            new_user["last_tax_time"] = data.get("last_tax_time", 0)
            new_user["inventory"] = data.get("inventory", {}).copy()
            new_user["investments"] = data.get("investments", []).copy()
            new_user["active_effects"] = data.get("active_effects", []).copy()
            new_user["active_discounts"] = data.get("active_discounts", []).copy()

            migrated += 1

        await economy_db.save()
        
        print(f"\n✅ Миграция успешно завершена! Перенесено: {migrated} пользователей")
        
        # Создаём бэкап
        backup_name = f"economy_migrated_backup_{int(os.path.getmtime(old_file))}.json"
        backup_path = old_file.with_name(backup_name)
        os.rename(old_file, backup_path)
        print(f"📦 Старый файл сохранён как: {backup_name}")

        return True

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False


if __name__ == "__main__":
    import asyncio
    asyncio.run(migrate_old_economy_to_new())