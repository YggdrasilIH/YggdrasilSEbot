# game_logic/foresight.py
from game_logic.buff_handler import BuffHandler

def apply_foresight(hero, source):
    logs = []

    if hero.has_seal_of_light:
        logs.append(f"❌ {hero.name}'s Foresight is blocked by Seal of Light.")
        return logs

    if source == "basic":
        # Create a new unique buff name for each trigger to avoid overwriting
        buff_key = f"foresight_basic_{len([b for b in hero.buffs if b.startswith('foresight_basic')]) + 1}"

        BuffHandler.apply_buff(hero, buff_key, {
            "attribute": "all_damage_dealt",
            "bonus": 30,
            "rounds": 15,
            "skill_buff": True  # Mark as skill_buff to avoid Curse
        })

        BuffHandler.apply_buff(hero, f"{buff_key}_energy", {
            "attribute": "energy",
            "bonus": 50,
            "rounds": 0,  # immediate energy grant
            "skill_buff": True
        })

        logs.append(f"🧿 {hero.name} gains Foresight (Basic): +30% All Damage for 15 rounds and +50 Energy.")

    elif source == "active":
        buff_key = f"foresight_active_{len([b for b in hero.buffs if b.startswith('foresight_active')]) + 1}"

        BuffHandler.apply_buff(hero, buff_key, {
            "crit_rate_increase": 30,
            "crit_dmg_increase": 100,
            "rounds": 2,
            "skill_buff": True
        })

        hero.crit_rate += 30
        hero.crit_dmg += 100

        logs.append(f"🎯 {hero.name} gains Foresight (Active): +30% Crit Rate, +100% Crit DMG for 2 rounds.")

    return logs
