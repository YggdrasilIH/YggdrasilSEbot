class BuffHandler:
    ATTRIBUTE_BUFF_KEYS = {
        "atk", "armor", "speed", "skill_damage", "precision", "block",
        "crit_rate", "crit_dmg", "armor_break", "control_immunity",
        "dr", "hd", "energy"
    }

    ATTRIBUTE_REDUCTION_KEYS = ATTRIBUTE_BUFF_KEYS.copy()

    @staticmethod
    def is_attribute_buff(buff, strict=False):
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
    def apply_buff(hero, buff_name, buff_data, boss=None):
        attr = buff_data.get("attribute")

        # Check if offsettable by Curse of Decay
        if BuffHandler.is_attribute_buff(buff_data) and hero.curse_of_decay > 0:
            if boss and hasattr(boss, "apply_curse_of_decay_damage"):
                cod_logs = []
                boss.apply_curse_of_decay_damage(hero, cod_logs)
                msg = f"💀 Curse of Decay offsets {buff_data['attribute']} buff on {hero.name}. " + " ".join(cod_logs)
            else:
                damage = int(boss.atk * 30) if boss else 0
                hero.hp -= damage
                msg = f"💀 Curse of Decay offsets {buff_data['attribute']} buff on {hero.name}. {hero.name} takes {damage / 1e6:.0f}M dmg."
            hero.curse_of_decay -= 1
            return False, msg

        # --- Stacking Logic ---
        if buff_name in hero.buffs:
            existing = hero.buffs[buff_name]
            # If both old and new buffs have 'bonus', add them
            if "bonus" in existing and "bonus" in buff_data:
                existing["bonus"] += buff_data["bonus"]
            # If both have 'heal_amount', add them
            if "heal_amount" in existing and "heal_amount" in buff_data:
                existing["heal_amount"] += buff_data["heal_amount"]
            # If both have 'shield', add them
            if "shield" in existing and "shield" in buff_data:
                existing["shield"] += buff_data["shield"]
            # Extend duration if incoming buff has longer remaining rounds
            if "rounds" in existing and "rounds" in buff_data:
                existing["rounds"] = max(existing["rounds"], buff_data["rounds"])
        else:
            hero.buffs[buff_name] = buff_data

        # Apply immediate impact for all_damage_dealt
        if attr == "all_damage_dealt":
            hero.all_damage_dealt += buff_data.get("bonus", 0)

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
