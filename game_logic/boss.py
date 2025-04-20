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
        self.hd_bonus = 0
        self.all_damage_bonus = 0
        self.shield = 0
        self.curse_of_decay = 0
        self.abyssal_corruption = 0

    def apply_buff(self, buff_name, buff_data):
        self.buffs[buff_name] = buff_data

    def process_buffs(self):
        expired = []
        for buff in list(self.buffs.keys()):
            self.buffs[buff]["rounds"] -= 1
            if self.buffs[buff]["rounds"] <= 0:
                expired.append(buff)
        for buff_name in expired:
            buff = self.buffs[buff_name]
            if "hd_bonus" in buff:
                self.hd_bonus -= buff["hd_bonus"]
            if "all_damage_bonus" in buff:
                self.all_damage_bonus -= buff["all_damage_bonus"]
            del self.buffs[buff_name]

    def take_damage(self, dmg, source_hero=None, team=None):
        logs = []
        multiplier = 1.0
        if self.shrink_debuff:
            multiplier *= self.shrink_debuff["multiplier_received"]
        damage_bonus = 1 + (self.all_damage_bonus / 100)
        effective_dmg = dmg * multiplier * damage_bonus

        dr = min(getattr(self, "dr", 0), 0.75)
        effective_dmg *= (1 - dr)

        adr = min(getattr(self, "adr", 0), 0.75)
        effective_dmg *= (1 - adr)

        self.hp -= effective_dmg
        self.total_damage_taken += effective_dmg
        logs.append(stylize_log("damage", f"Boss takes {int(effective_dmg / 1e6):.0f}M damage."))
        return logs

    def counterattack(self, heroes):
        logs = []
        counter_lines = []
        calamity_targets = []

        for hero in heroes:
            if not hero.is_alive():
                continue
            effective_atk = self.atk
            if self.shrink_debuff:
                effective_atk *= self.shrink_debuff["multiplier_dealt"]
            damage = int(effective_atk * 15)
            absorbed = min(hero.shield, damage)
            hero.shield = max(0, hero.shield - damage)
            final_damage = max(0, damage - absorbed)
            hero.hp -= final_damage

            extras = []
            calamity_targets.append(hero)
            if random.random() < 0.5:
                hero.curse_of_decay += 1
                extras.append("+1 Curse")

            line = f"⚔️ {hero.name}: {final_damage} dmg"
            if absorbed:
                line += f" ({absorbed} absorbed)"
            if extras:
                line += ", " + ", ".join(extras)
            counter_lines.append(line)

        for hero in calamity_targets:
            add_calamity(hero, 1, logs, boss=self)

        if counter_lines:
            logs.append("⏱️ Boss counterattacks → " + " | ".join(counter_lines))
        return logs

    def process_control_buffs(self, heroes):
        logs = []
        buffs = []
        fear_count = sum(1 for h in heroes if h.has_fear)
        silence_count = sum(1 for h in heroes if h.has_silence)
        seal_count = sum(1 for h in heroes if h.has_seal_of_light)

        if fear_count:
            bonus = fear_count * 50
            BuffHandler.apply_buff(self, "fear_buff", {
                "attribute": "HD", "bonus": bonus, "rounds": 15
            })
            self.attribute_effects.append({
                "attribute": "HD",
                "value": bonus,
                "rounds": 15,
                "name": "HD buff (Fear)"
            })
            buffs.append(f"+{bonus} HD (Fear)")
        if silence_count:
            energy_gain = silence_count * 50
            self.energy += energy_gain
            buffs.append(f"+{energy_gain} ⚡ (Silence)")
        if seal_count:
            bonus = seal_count * 15
            BuffHandler.apply_buff(self, "seal_buff", {"attribute": "all_damage_bonus", "bonus": bonus, "rounds": 15})
            buffs.append(f"+{bonus}% DMG (Seal)")

        if buffs:
            logs.append("✨ Boss gains: " + ", ".join(buffs))
        return logs

    def process_poison_and_other_effects(self):
        msg = self.process_poison()
        return [msg] if msg else []

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
            logs.append(f"🌀 Drains {hero_high.name}: -100 ⚡, -40% ATK (2r), +3 Curse")

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

        logs.extend(self.process_control_buffs(heroes))
        self.process_buffs()
        return logs

    def get_status_description(self):
        status = f"{self.name} Status:  HP {self.hp:.1e} | ⚡ {self.energy} | 🔥 ATK {self.atk}"
        if self.all_damage_bonus:
            status += f" | +{self.all_damage_bonus}% DMG"
        if self.hd_bonus:
            status += f" | +{self.hd_bonus} HD"
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

    def active_skill(self, heroes, round_num):
        logs = []
        dmg_lines = []
        calamity_targets = []
        for hero in heroes:
            if not hero.is_alive():
                continue
            total_dmg = 0
            for _ in range(3):
                damage = int(self.atk * 30)
                hero.hp -= damage
                total_dmg += damage
            dmg_lines.append(f"{hero.name}: {total_dmg // 1_000_000}M")
            hero.apply_buff("armor_down", {"attribute": "armor", "bonus": -100, "rounds": 3})
            hero.apply_buff("atk_steal", {"attribute": "atk", "bonus": -int(hero.atk * 0.08), "rounds": 3})
            hero.curse_of_decay += 2
            calamity_targets.append(hero)
        if dmg_lines:
            for line in dmg_lines:
                logs.append(f"💥 Boss hits {line} with Active Skill.")
                logs.append("💀 Inflicts 2 Curse of Decay.")
        if calamity_targets:
            for hero in calamity_targets:
                add_calamity(hero, 2, logs, boss=self)
        return logs

    def basic_attack(self, heroes, round_num):
        logs = []
        dmg_lines = []
        calamity_targets = []
        for hero in heroes:
            if not hero.is_alive():
                continue
            total_dmg = 0
            for _ in range(3):
                damage = int(self.atk * 20)
                hero.hp -= damage
                total_dmg += damage
            dmg_lines.append(f"{hero.name}: {total_dmg // 1_000_000}M")
            hero.apply_buff("crit_down", {"attribute": "crit_rate", "bonus": -20, "rounds": 3})
            calamity_targets.append(hero)
        if dmg_lines:
            for line in dmg_lines:
                logs.append(f"💥 Boss hits {line} with Basic Attack.")
                logs.append("💀 Inflicts 1 Calamity (75% chance for +1 more).")
        for hero in calamity_targets:
            add_calamity(hero, 1, logs, boss=self)
            if random.random() < 0.75:
                add_calamity(hero, 1, logs, boss=self)
        return logs

    def is_alive(self):
        return self.hp > 0
