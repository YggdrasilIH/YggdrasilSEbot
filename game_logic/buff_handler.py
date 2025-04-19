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
        if BuffHandler.is_attribute_buff(buff_data) and hero.curse_of_decay > 0:
            if boss:
                damage = int(boss.atk * 30)
                hero.hp -= damage
                msg = f"💀 Curse of Decay offsets {buff_data['attribute']} buff on {hero.name}. {hero.name} takes {damage / 1e6:.0f}M dmg."
            else:
                msg = f"💀 Curse of Decay offsets {buff_data['attribute']} buff on {hero.name}."
            hero.curse_of_decay -= 1
            return False, msg

        hero.buffs[buff_name] = buff_data
        return True, None  # Buff applied successfully

    @staticmethod
    def apply_debuff(target, debuff_name, debuff_data):
        if BuffHandler.is_attribute_reduction(debuff_data):
            target.buffs[debuff_name] = debuff_data
            attr = debuff_data.get('attribute', '')
            val = debuff_data.get('bonus', '')
            return [f"🔻 {target.name}: {val:+} {attr} ({debuff_data.get('rounds', '?')}r)"]
        else:
            target.buffs[debuff_name] = debuff_data
            return [f"🔻 {target.name}: {debuff_name} (skill effect)"]

    @staticmethod
    def cap_stats(hero):
        logs = []
        if hero.precision > 150:
            hero.precision = 150
            logs.append(f"📊 {hero.name}: Precision capped at 150")
        if hero.crit_dmg > 150:
            hero.crit_dmg = 150
            logs.append(f"📊 {hero.name}: Crit DMG capped at 150")
        return logs


def grant_energy(hero, amount: int) -> str:
    hero.energy += amount
    return f"⚡ {hero.name} gains +{amount} energy after using their skill."
