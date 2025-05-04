import random

class BuffHandler:
    ATTRIBUTE_BUFF_KEYS = {
        "atk", "armor", "speed", "skill_damage", "precision", "block",
        "crit_rate", "crit_dmg", "armor_break", "control_immunity",
        "dr", "hd", "energy"
    }

    ATTRIBUTE_REDUCTION_KEYS = ATTRIBUTE_BUFF_KEYS.copy()

    ALIAS_MAP = {
        "control_immunity": "ctrl_immunity",
        "crit_damage": "crit_dmg",
        "crit_rate": "crit_rate",
        "dr": "DR",
        "adr": "ADR"
    }

    @staticmethod
    def is_attribute_buff(buff, strict=False):
        if buff.get("skill_buff", False):
            return False
        attr = buff.get("attribute")
        bonus = buff.get("bonus", 0)
        name = buff.get("name", "")
        if attr not in BuffHandler.ATTRIBUTE_BUFF_KEYS:
            return False
        if strict:
            if isinstance(bonus, (int, float)) and bonus < 0:
                return False
            if name.startswith("replicated_") or name.endswith("_down"):
                return False
        return True

    @staticmethod
    def is_attribute_reduction(debuff, strict=False):
        attr = debuff.get("attribute")
        bonus = debuff.get("bonus", 0)
        name = debuff.get("name", "")
        if attr not in BuffHandler.ATTRIBUTE_REDUCTION_KEYS:
            return False
        if strict:
            if isinstance(bonus, (int, float)) and bonus >= 0:
                return False
            if name.startswith("replicated_"):
                return False
        return True

    @staticmethod
    def _generate_unique_name(base_name, buffs):
        name = base_name
        while name in buffs:
            name = f"{base_name}_{random.randint(1000, 9999)}"
        return name
    
    @staticmethod
    def apply_buff(hero, buff_name, buff_data, boss=None, replace_existing=False):
        attr = buff_data.get("attribute")
        bonus = buff_data.get("bonus", 0)
        internal_attr = BuffHandler.ALIAS_MAP.get(attr, attr)

        # ✅ Curse of Decay offset routing to boss logic only
        if BuffHandler.is_attribute_buff(buff_data) and hero.curse_of_decay > 0:
            if boss and hasattr(boss, "boss_deal_damage_to_hero"):
                cod_dmg = int(boss.atk * 30 * hero.curse_of_decay)
                dealt_dmg = boss.boss_deal_damage_to_hero(hero, cod_dmg)
                msg = (
                    f"💀 Curse of Decay offsets {attr} buff on {hero.name}. "
                    f"Takes {dealt_dmg:,} damage. (1 layer removed)"
                )
                boss._round_curse_offsets.append(f"{hero.name}: {dealt_dmg // 1_000_000}M")
                hero.curse_of_decay -= 1
                return False, msg
            else:
                return False, f"💀 Curse of Decay offsets {attr} buff on {hero.name} (boss missing)."


        # Ensure unique buff name if stacking is allowed
        if not replace_existing:
            buff_name = BuffHandler._generate_unique_name(buff_name, hero.buffs)

        hero.buffs[buff_name] = buff_data

        # Special: shield hard cap
        if attr == "shield":
            amount = buff_data.get("shield", 0)
            hero.shield = min(hero.shield + amount, hero.max_hp)

        # Apply effect to stat
        try:
            if internal_attr == "all_damage_dealt":
                hero.all_damage_dealt += bonus
            elif internal_attr == "atk":
                hero.atk += bonus
            elif internal_attr == "armor":
                hero.armor += bonus
            elif internal_attr == "speed":
                hero.speed += bonus
            elif internal_attr == "skill_damage":
                hero.skill_damage += bonus
            elif internal_attr == "precision":
                hero.precision += bonus
            elif internal_attr == "block":
                hero.block += bonus
            elif internal_attr == "crit_rate":
                hero.crit_rate += bonus
            elif internal_attr == "crit_dmg":
                hero.crit_dmg += bonus
            elif internal_attr == "armor_break":
                hero.armor_break += bonus
            elif internal_attr == "ctrl_immunity":
                hero.ctrl_immunity = getattr(hero, "ctrl_immunity", 0) + bonus
            elif internal_attr == "DR":
                hero.DR = getattr(hero, "DR", 0) + bonus
            elif internal_attr == "HD":
                hero.hd += bonus
            elif internal_attr == "ADR":
                hero.ADR = getattr(hero, "ADR", 0) + bonus
            elif internal_attr == "energy":
                hero.energy += bonus
        except AttributeError:
            pass

        return True, None



    @staticmethod
    def apply_debuff(target, debuff_name, debuff_data, boss=None):
        # Route all debuff logic through apply_buff
        return BuffHandler.apply_buff(target, debuff_name, debuff_data, boss, replace_existing=False)

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
