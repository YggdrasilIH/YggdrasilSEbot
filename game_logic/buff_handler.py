# game_logic/buff_handler.py

class BuffHandler:
    ATTRIBUTE_BUFF_KEYS = {
        "atk", "armor", "speed", "skill_damage", "precision", "block",
        "crit_rate", "crit_dmg", "armor_break", "control_immunity",
        "DR", "HD", "energy"
    }

    ATTRIBUTE_REDUCTION_KEYS = {
        "atk", "armor", "speed", "skill_damage", "precision", "block",
        "crit_rate", "crit_dmg", "armor_break", "control_immunity",
        "DR", "HD", "energy"
    }

    @staticmethod
    def is_attribute_buff(buff):
        return buff.get("attribute") in BuffHandler.ATTRIBUTE_BUFF_KEYS

    @staticmethod
    def is_attribute_reduction(debuff):
        return debuff.get("attribute") in BuffHandler.ATTRIBUTE_REDUCTION_KEYS

    @staticmethod
    def apply_buff(hero, buff_name, buff_data, boss=None):
        logs = []
        if BuffHandler.is_attribute_buff(buff_data) and hero.curse_of_decay > 0:
            damage = int(boss.atk * 30) if boss else 0
            hero.hp -= damage
            hero.curse_of_decay -= 1
            logs.append(f"{hero.name} offsets {buff_data['attribute']} buff with Curse of Decay, taking {damage} damage.")
        else:
            hero.buffs[buff_name] = buff_data
            logs.append(f"{hero.name} gains buff '{buff_name}' with data: {buff_data}")
        return logs

    @staticmethod
    def apply_debuff(target, debuff_name, debuff_data):
        if BuffHandler.is_attribute_reduction(debuff_data):
            target.buffs[debuff_name] = debuff_data
            return [f"{target.name} receives attribute reduction '{debuff_name}': {debuff_data}"]
        else:
            target.buffs[debuff_name] = debuff_data
            return [f"{target.name} receives skill effect or general debuff '{debuff_name}': {debuff_data}"]

    @staticmethod
    def cap_stats(hero):
        logs = []
        if hero.precision > 150:
            hero.precision = 150
            logs.append(f"{hero.name}'s precision capped at 150.")
        if hero.crit_dmg > 150:
            hero.crit_dmg = 150
            logs.append(f"{hero.name}'s crit damage capped at 150.")
        return logs


def grant_energy(hero, amount: int) -> str:
    hero.energy += amount
    return f"⚡ {hero.name} gains +{amount} energy after using their skill."
