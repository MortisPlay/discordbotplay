# modules/economy_bp/bp_core.py

from utils.db import economy_db
from .bp_config import BP_SETTINGS, BP_REWARDS, get_level_by_xp

class BPCore:
    @staticmethod
    def setup_user_bp(user_data: dict) -> dict:
        """Инициализирует данные БП в профиле игрока, если их нет"""
        changed = False
        if "bp_xp" not in user_data:
            user_data["bp_xp"] = 0
            changed = True
        if "bp_premium" not in user_data:
            user_data["bp_premium"] = False
            changed = True
        if "bp_claimed" not in user_data:
            user_data["bp_claimed"] = [] # Список уже забранных уровней
            changed = True
        return user_data, changed

    @staticmethod
    def add_xp(user_id: int, amount: int):
        """Начисляет опыт БП пользователю"""
        user = economy_db.get_user(user_id)
        user, _ = BPCore.setup_user_bp(user)
        
        # Не даем опыта больше, чем на макс. уровень
        max_xp = BP_SETTINGS["MAX_LEVEL"] * BP_SETTINGS["XP_PER_LEVEL"]
        if user["bp_xp"] < max_xp:
            user["bp_xp"] += amount
            economy_db.update_user(user_id, user)
            return True
        return False

    @staticmethod
    def claim_level_reward(user_id: int, level: int):
        """Выдает награду за конкретный уровень"""
        user = economy_db.get_user(user_id)
        user, _ = BPCore.setup_user_bp(user)
        
        if level in user["bp_claimed"]:
            return False, "Награда уже получена!"
        
        current_lvl = get_level_by_xp(user["bp_xp"])
        if level > current_lvl:
            return False, "Уровень еще не достигнут!"

        # Собираем награды (бесплатную и, если есть премиум, платную)
        rewards_to_give = [BP_REWARDS[level]["free"]]
        if user["bp_premium"]:
            rewards_to_give.append(BP_REWARDS[level]["premium"])

        for reward in rewards_to_give:
            if reward["type"] == "coins":
                user["balance"] = user.get("balance", 0) + reward["amount"]
            
            elif reward["type"] == "mcoins":
                user["mortis_coins"] = user.get("mortis_coins", 0) + reward["amount"]
            
            elif reward["type"] == "item":
                inventory = user.get("inventory", {})
                item_id = reward["id"]
                inventory[item_id] = inventory.get(item_id, 0) + reward["amount"]
                user["inventory"] = inventory
            
            elif reward["type"] == "status":
                # Добавляем статус в список достижений или меняем поле status
                user["status"] = reward["label"]

        user["bp_claimed"].append(level)
        economy_db.update_user(user_id, user)
        return True, "Успешно!"