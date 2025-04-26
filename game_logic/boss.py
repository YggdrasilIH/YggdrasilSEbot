import random
from game_logic.buff_handler import BuffHandler
from game_logic.control_effects import add_calamity
from utils.log_utils import stylize_log

class Boss:
    def __init__(self):
        self.name = "Boss"
        self.max_hp = 20_000_000_000_000
        self.hp = self.max_hp
        self.atk = 100_000
        self.dr = 0
        self.ADR = 0
        self.armor = 3000
        self.speed = 0
        self.crit_rate = 0
        self.crit_dmg = 0
        self.hd = 0
        self.total_damage_taken = 0
        self.attribute_effects = []
        self.energy = 0
        self.poison_effects = []
        self.shrink_debuff = None
        self.non_skill_debuffs = []
        self.buffs = {}
        self.all_damage_bonus = 0
        self.shield = 0
        self.curse_of_decay = 0
        self.abyssal_corruption = 0
        self._round_curse_offsets = []
        self._round_passive_bonuses = {"HD": 0, "Energy": 0, "ADD": 0}
        self._round_curse_gains = []
        self._round_calamity_gains = []
        self._pending_counterattack = []


    def apply_buff(self, buff_name, buff_data):
        self.buffs[buff_name] = buff_data

    def take_damage(self, dmg, source_hero=None, team=None, real_attack=False):
        logs = []
        multiplier = 1.0
        if self.shrink_debuff:
            multiplier *= self.shrink_debuff.get("multiplier_received", 1)
        damage_bonus = 1 + (self.all_damage_bonus / 100)
        effective_dmg = dmg * multiplier * damage_bonus

        dr = min(getattr(self, "dr", 0), 0.75)
        effective_dmg *= (1 - dr)

        adr = min(getattr(self, "adr", 0), 0.75)
        effective_dmg *= (1 - adr)

        self.hp -= effective_dmg
        self.total_damage_taken += effective_dmg
        logs.append(stylize_log("damage", f"Boss takes {int(effective_dmg / 1e6):.0f}M damage."))

        if source_hero and source_hero.is_alive() and getattr(source_hero, '_using_real_attack', False):
            self._pending_counterattack_needed = True

        return logs
    
    def flush_counterattacks(self, heroes):
        if not getattr(self, '_pending_counterattack_needed', False):
            return []

        logs = []
        damage_lines = []
        curse_heroes = []
        curse_totals = []
        calamity_heroes = []
        calamity_totals = []

        heroes_to_add_calamity = []

        # Step 1: Deal counterattack damage first
        for hero in heroes:
            if not hero.is_alive():
                continue
            counter_damage = int(self.atk * 15)
            final_damage = self.calculate_damage_to_hero(hero, counter_damage)
            damage_lines.append(f"{hero.name} ({final_damage // 1_000_000}M)")

            if hero.is_alive():
                heroes_to_add_calamity.append(hero)

        if damage_lines:
            logs.append(f"⏱️ Boss counterattacks→ {', '.join(damage_lines)}")

        # Step 2: After all damage, apply Calamity and potential Curse
        for hero in heroes_to_add_calamity:
            previous_calamity = hero.calamity
            self.add_calamity_with_tracking(hero, 1, logs, boss=self)
            calamity_heroes.append(hero.name)
            calamity_totals.append(str(hero.calamity))

            if random.random() < 0.5:
                hero.curse_of_decay += 1
                curse_heroes.append(hero.name)
                curse_totals.append(str(hero.curse_of_decay))

        if curse_heroes:
            logs.append(f"💀 {', '.join(curse_heroes)} gained 1 layer of Curse (Totals: {', '.join(curse_totals)})")
        if calamity_heroes:
            logs.append(f"☠️ {', '.join(calamity_heroes)} gained 1 layer of Calamity (Totals: {', '.join(calamity_totals)})")

        self._pending_counterattack_needed = False
        return logs




    def calculate_damage_to_hero(self, hero, base_damage):
        if not hero.is_alive():
            return 0
        damage = base_damage

        if self.shrink_debuff:
            damage *= self.shrink_debuff.get("multiplier_dealt", 1)

        armor = hero.armor
        armor_reduction = min(armor / (100 * 20 + 180), 0.75)
        damage *= (1 - armor_reduction)

        dr = min(getattr(hero, "DR", 0) / 100, 0.75)
        damage *= (1 - dr)

        adr = min(getattr(hero, "ADR", 0) / 100, 0.75)
        damage *= (1 - adr)

        damage = max(0, int(damage))

        if hero.shield > 0:
            absorbed = min(hero.shield, damage)
            hero.shield -= absorbed
            damage -= absorbed

        if hasattr(hero, "trait_enable") and hasattr(hero.trait_enable, "prevent_death"):
            if hero.trait_enable.prevent_death(hero, damage):
                damage = hero.hp - 1

        hero.hp -= damage
        hero.hp = max(hero.hp, 0)

        return damage

    def boss_deal_damage_to_hero(self, hero, base_damage):
        return self.calculate_damage_to_hero(hero, base_damage)

    def add_calamity_with_tracking(self, hero, amount, logs, boss=None):
        previous = hero.calamity
        hero.calamity += amount
        self._round_calamity_gains.append(f"{hero.name} +{amount} (Total: {hero.calamity})")
        if previous < 5 and hero.calamity >= 5:
            from game_logic.control_effects import apply_control_effect
            for effect in ["silence", "fear", "seal_of_light"]:
                if hero.immune_control_effect == effect:
                    continue
                else:
                    apply_control_effect(hero, effect, boss=boss, team=hero.team if hasattr(hero, 'team') else None)
            hero.calamity = 0

    def boss_action(self, heroes, round_num):
        logs = []
        if self.energy >= 100:
            logs += self.active_skill(heroes, round_num)
            self.energy -= 100
        else:
            logs += self.basic_attack(heroes, round_num)
        logs += self.counterattack(heroes)
        return logs

    def active_skill(self, heroes, round_num):
        logs = []
        damage_lines = []
        curse_names = []
        curse_totals = []
        calamity_names = []
        calamity_totals = []

        for hero in heroes:
            if not hero.is_alive():
                continue
            total_damage = 0
            for _ in range(3):
                total_damage += self.boss_deal_damage_to_hero(hero, int(self.atk * 30))
            damage_lines.append(f"{hero.name} ({total_damage // 1_000_000}M)")

            # Apply debuffs silently
            hero.apply_buff("armor_down", {"attribute": "armor", "bonus": -1.0, "rounds": 3, "is_percent": True})
            hero.apply_buff("atk_steal", {"attribute": "atk", "bonus": -int(hero.atk * 0.08), "rounds": 3})

            # Apply Curse
            hero.curse_of_decay += 2
            curse_names.append(hero.name)
            curse_totals.append(str(hero.curse_of_decay))

            # Apply Calamity
            previous_calamity = hero.calamity
            self.add_calamity_with_tracking(hero, 2, logs, boss=self)
            calamity_names.append(hero.name)
            calamity_totals.append(str(hero.calamity))

        if curse_names:
            logs.append(f"💀 {', '.join(curse_names)} gained 2 layers of Curse (Totals: {', '.join(curse_totals)})")
        if calamity_names:
            logs.append(f"☠️ {', '.join(calamity_names)} gained 2 layers of Calamity (Totals: {', '.join(calamity_totals)})")

        if damage_lines:
            logs.append(f"💥 Boss active hits→ {', '.join(damage_lines)}")
        return logs

    def basic_attack(self, heroes, round_num):
        logs = []
        damage_lines = []
        calamity_names = []
        calamity_totals = []

        for hero in heroes:
            if not hero.is_alive():
                continue
            total_damage = 0
            for _ in range(3):
                total_damage += self.boss_deal_damage_to_hero(hero, int(self.atk * 20))
            damage_lines.append(f"{hero.name} ({total_damage // 1_000_000}M)")

            # Apply debuff silently
            hero.apply_buff("crit_down", {"attribute": "crit_rate", "bonus": -20, "rounds": 3})

            # Apply Calamity
            previous_calamity = hero.calamity
            self.add_calamity_with_tracking(hero, 1, logs, boss=self)

            if random.random() < 0.75:
                previous_calamity = hero.calamity
                self.add_calamity_with_tracking(hero, 1, logs, boss=self)

            calamity_names.append(hero.name)
            calamity_totals.append(str(hero.calamity))

        if calamity_names:
            logs.append(f"☠️ {', '.join(calamity_names)} gained Calamity (Totals: {', '.join(calamity_totals)})")

        if damage_lines:
            logs.append(f"💥 Boss basic hits→ {', '.join(damage_lines)}")
        return logs


    
    def process_buffs(self):
        expired = []
        for buff in list(self.buffs.keys()):
            self.buffs[buff]["rounds"] -= 1
            if self.buffs[buff]["rounds"] <= 0:
                expired.append(buff)
        for buff_name in expired:
            buff = self.buffs[buff_name]
            attr = buff.get("attribute")
            bonus = buff.get("bonus", 0)
            if attr == "HD":
                self.hd -= bonus
            elif attr == "all_damage_bonus":
                self.all_damage_bonus -= bonus
            elif attr == "atk":
                self.atk -= bonus
            del self.buffs[buff_name]

    def on_hero_controlled(self, hero, effect):
        if effect == "fear":
            self.hd += 50
            BuffHandler.apply_buff(self, "fear_buff", {"attribute": "HD", "bonus": 50, "rounds": 15})
            self.attribute_effects.append({
                "attribute": "HD",
                "value": 50,
                "rounds": 15,
                "name": "HD buff (Fear)"
            })
            self._round_passive_bonuses["HD"] += 50
        elif effect == "seal_of_light":
            BuffHandler.apply_buff(self, "seal_buff", {"attribute": "all_damage_bonus", "bonus": 15, "rounds": 15})
            self._round_passive_bonuses["ADD"] += 15
        elif effect == "silence":
            self.energy += 50
            self._round_passive_bonuses["Energy"] += 50

    def process_control_buffs(self, heroes):
        for h in heroes:
            if h.has_fear:
                self.on_hero_controlled(h, "fear")
            if h.has_silence:
                self.on_hero_controlled(h, "silence")
            if h.has_seal_of_light:
                self.on_hero_controlled(h, "seal_of_light")
        return []

    def process_poison(self):
        total_poison = 0
        for effect in list(self.poison_effects):
            total_poison += effect["damage"]
            effect["rounds"] -= 1
            if effect["rounds"] <= 0:
                self.poison_effects.remove(effect)
        if total_poison > 0:
            self.hp -= total_poison
            self.hp = max(self.hp, 0)
            return f"☠️ {self.name}: {total_poison / 1e6:.0f}M Poison"
        return ""

    def process_poison_and_other_effects(self):
        msg = self.process_poison()
        return [msg] if msg else []

    def end_of_round_effects(self, heroes, round_num):
        logs = [f"🔄 Boss end-of-round (Round {round_num})"]
        logs.extend(self.process_poison_and_other_effects())

        if self.shrink_debuff:
            self.shrink_debuff["rounds"] -= 1
            if self.shrink_debuff["rounds"] <= 0:
                self.shrink_debuff = None
                logs.append("🌀 Shrink expired.")

        if self.non_skill_debuffs:
            removed = self.non_skill_debuffs.pop(0)
            logs.append(f"🧹 Removed debuff: {removed}")

        alive_heroes = [h for h in heroes if h.is_alive()]
        if alive_heroes:
            hero_high = max(alive_heroes, key=lambda h: h.atk)
            hero_high.energy = max(hero_high.energy - 100, 0)
            hero_high.apply_buff("boss_attack_debuff", {"attack_multiplier": 0.60, "rounds": 2})
            hero_high.curse_of_decay += 3
            logs.append(f"🌀 Drains {hero_high.name}: -100 energy, -40% ATK, +3 Curse")

        bonus = int(self.atk * 0.15)
        BuffHandler.apply_buff(self, "end_of_round_atk_buff", {
            "attribute": "atk", "bonus": bonus, "rounds": 9999
        })
        self.attribute_effects.append({
            "attribute": "atk",
            "value": bonus,
            "rounds": 9999,
            "name": "ATK buff"
        })
        logs.append(f"📈 Boss +{bonus} ATK")

        if alive_heroes:
            highest_atk = max(alive_heroes, key=lambda h: h.atk)
            if highest_atk.calamity > 0:
                attr_buffs = [k for k, v in highest_atk.buffs.items() if isinstance(v, dict) and v.get("attribute") in BuffHandler.ATTRIBUTE_BUFF_KEYS]
                if attr_buffs:
                    to_remove = random.choice(attr_buffs)
                    del highest_atk.buffs[to_remove]
                    logs.append(f"Boss removes attribute buff '{to_remove}' from {highest_atk.name}")

        for hero in alive_heroes:
            if hero.calamity == 0:
                hero.calamity += 1  # Silent +1 Calamity


        if self._round_curse_offsets:
            logs.append(f"💀 Curse offset damage this round: {', '.join(self._round_curse_offsets)}")
            self._round_curse_offsets.clear()

        self._round_curse_gains.clear()
        self._round_calamity_gains.clear()

        bonuses = []
        if self._round_passive_bonuses["HD"]:
            bonuses.append(f"+{self._round_passive_bonuses['HD']} HD")
        if self._round_passive_bonuses["Energy"]:
            bonuses.append(f"+{self._round_passive_bonuses['Energy']} Energy")
        if self._round_passive_bonuses["ADD"]:
            bonuses.append(f"+{self._round_passive_bonuses['ADD']}% ADD")
        if bonuses:
            logs.append(f"✨ Boss gained {', '.join(bonuses)} passively.")
            self._round_passive_bonuses = {"HD": 0, "Energy": 0, "ADD": 0}

        self.process_buffs()
        return logs
    
    def counterattack(self, heroes):
        logs = self.flush_counterattacks(heroes)
        return logs

    def get_status_description(self):
        status = f"{self.name} Status:  HP {self.hp:.1e} | ⚡ {self.energy} | 🔥 ATK {self.atk}"
        if self.all_damage_bonus:
            status += f" | +{self.all_damage_bonus}% DMG"
        if self.hd:
            status += f" | +{self.hd} HD"
        if self.dr:
            status += f" | DR {int(self.dr * 100)}%"
        if self.ADR:
            status += f" | ADR {int(self.ADR * 100)}%"
        if self.abyssal_corruption:
            status += f" | 🧿 Abyssal Corruption: {self.abyssal_corruption}"
        if self.curse_of_decay:
            status += f" | 💀 Curse: {self.curse_of_decay}"
        if self.shrink_debuff:
            rounds = self.shrink_debuff.get("rounds", 0)
            status += f" | 🌀 Shrink ({rounds}r)"
        return status
    
    def is_alive(self):
        return self.hp > 0