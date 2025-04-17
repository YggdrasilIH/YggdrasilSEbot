
# game_logic/foresight.py

def apply_foresight(hero, source):
    logs = []
    if source == "basic":
        hero.all_damage_dealt += 30
        hero.energy += 50
        hero.apply_buff("foresight_basic", {"attribute": "all_damage_dealt", "bonus": 30, "rounds": 15})
        logs.append(f"{hero.name} gains Foresight (Basic): +30% damage for 15 rounds and +50 energy.")
    elif source == "active":
        hero.crit_rate += 30
        hero.crit_dmg += 100
        hero.apply_buff("foresight_active", {"crit_rate_increase": 30, "crit_dmg_increase": 100, "rounds": 2})
        logs.append(f"{hero.name} gains Foresight (Active): +30% crit rate, +100% crit dmg.")
    return logs

