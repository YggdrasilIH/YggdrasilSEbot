class BuffHandler:
    ATTRIBUTE_BUFF_KEYS = {
        "atk", "armor", "speed", "skill_damage", "precision", "block",
        "crit_rate", "crit_dmg", "armor_break", "control_immunity",
        "dr", "hd", "energy"
    }

    ATTRIBUTE_REDUCTION_KEYS = ATTRIBUTE_BUFF_KEYS.copy()

    @staticmethod
    def is_attribute_buff(buff, strict=False):
        # 🚨 New addition: If it's a skill_buff, treat it as NOT attribute buff
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

        # --- Stacking Logic with safety ---
        if buff_name in hero.buffs:
            existing = hero.buffs[buff_name]
            # If merging same attribute
            if "attribute" in existing and "attribute" in buff_data and existing["attribute"] == attr:
                # Merge bonuses carefully
                existing_bonus = existing.get("bonus", 0)
                incoming_bonus = buff_data.get("bonus", 0)
                existing["bonus"] = existing_bonus + incoming_bonus
            else:
                # Otherwise, overwrite safely
                hero.buffs[buff_name] = buff_data

            # Heal stacking
            if "heal_amount" in existing and "heal_amount" in buff_data:
                existing["heal_amount"] += buff_data["heal_amount"]

            # Shield stacking
            if "shield" in existing and "shield" in buff_data:
                existing["shield"] += buff_data["shield"]

            # Extend rounds if needed
            if "rounds" in existing and "rounds" in buff_data:
                existing["rounds"] = max(existing["rounds"], buff_data["rounds"])
        else:
            hero.buffs[buff_name] = buff_data

        # Apply immediate impact to hero stats if attribute matches
        bonus = buff_data.get("bonus", 0)
        if attr == "all_damage_dealt":
            hero.all_damage_dealt += bonus
        elif attr == "atk":
            hero.atk += bonus
        elif attr == "armor":
            hero.armor += bonus
        elif attr == "speed":
            hero.speed += bonus
        elif attr == "skill_damage":
            hero.skill_damage += bonus
        elif attr == "precision":
            hero.precision += bonus
        elif attr == "block":
            hero.block += bonus
        elif attr == "crit_rate":
            hero.crit_rate += bonus
        elif attr == "crit_dmg":
            hero.crit_dmg += bonus
        elif attr == "armor_break":
            hero.armor_break += bonus
        elif attr == "control_immunity":
            hero.control_immunity += bonus
        elif attr == "dr":
            hero.dr += bonus
        elif attr == "hd":
            hero.hd += bonus
        elif attr == "adr":
            hero.ADR += bonus
        elif attr == "energy":
            hero.energy += bonus

        return True, None


    @staticmethod
    def apply_debuff(target, debuff_name, debuff_data):
        if BuffHandler.is_attribute_reduction(debuff_data):
            target.buffs[debuff_name] = debuff_data

            # Apply immediate impact to hero stats if attribute matches
            bonus = debuff_data.get("bonus", 0)
            attr = debuff_data.get("attribute")

            if attr == "atk":
                target.atk += bonus
            elif attr == "armor":
                target.armor += bonus
            elif attr == "speed":
                target.speed += bonus
            elif attr == "skill_damage":
                target.skill_damage += bonus
            elif attr == "precision":
                target.precision += bonus
            elif attr == "block":
                target.block += bonus
            elif attr == "crit_rate":
                target.crit_rate += bonus
            elif attr == "crit_dmg":
                target.crit_dmg += bonus
            elif attr == "armor_break":
                target.armor_break += bonus
            elif attr == "control_immunity":
                target.control_immunity += bonus
            elif attr == "dr":
                target.dr += bonus
            elif attr == "hd":
                target.hd += bonus
            elif attr == "adr":
                target.ADR += bonus
            elif attr == "energy":
                target.energy += bonus

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
