# game_logic/foresight.py

import random
from game_logic.buff_handler import BuffHandler

def apply_foresight(hero, source):
    logs = []

    if hero.has_seal_of_light:
        logs.append(f"❌ {hero.name}'s Foresight is blocked by Seal of Light.")
        return logs

    if source == "basic":
        hero.energy += 50
        key = f"foresight_basic_{random.randint(1000, 9999)}"
        BuffHandler.apply_buff(hero, key, {
            "attribute": "all_damage_dealt",
            "bonus": 30,
            "rounds": 15
        })
        logs.append(f"{hero.name} gains Foresight (Basic): +30% All Damage Dealt (15 rounds) and +50 Energy.")

    elif source == "active":
        BuffHandler.apply_buff(hero, "foresight_active_crit_rate", {
            "attribute": "crit_rate",
            "bonus": 30,
            "rounds": 2
        })
        BuffHandler.apply_buff(hero, "foresight_active_crit_dmg", {
            "attribute": "crit_dmg",
            "bonus": 100,
            "rounds": 2
        })
        logs.append(f"{hero.name} gains Foresight (Active): +30% Crit Rate and +100% Crit Damage (2 rounds).")

    return logs
