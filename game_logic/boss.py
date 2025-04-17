import random
from game_logic.buff_handler import BuffHandler

class Boss:
    def __init__(self):
        self.name = "Boss"
        self.max_hp = 20_000_000_000_000
        self.hp = self.max_hp
        self.atk = 100_000
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
        multiplier = 1.0
        if self.shrink_debuff:
            multiplier *= self.shrink_debuff["multiplier_received"]
        damage_bonus = 1 + (self.all_damage_bonus / 100)
        effective_dmg = dmg * multiplier * damage_bonus
        self.hp -= effective_dmg
        self.total_damage_taken += effective_dmg
        print(f"[DEBUG] Boss takes {int(effective_dmg)} damage (Base: {dmg}, Shrink: {multiplier}, Bonus: {damage_bonus})")

    def is_alive(self):
        return self.hp > 0

    def process_poison(self):
        total_poison = 0
        for effect in list(self.poison_effects):
            total_poison += effect["damage"]
            effect["rounds"] -= 1
            if effect["rounds"] <= 0:
                self.poison_effects.remove(effect)
        if total_poison > 0:
            self.hp -= total_poison
            return f"☠️ Boss takes {total_poison} poison damage."
        return ""

    def active_skill(self, heroes, round_num):
        logs = ["🔥 Boss uses active skill."]
        for hero in heroes:
            if not hero.is_alive():
                continue
            effective_atk = self.atk
            if self.shrink_debuff:
                effective_atk *= self.shrink_debuff["multiplier_dealt"]
            for i in range(3):
                damage = int(effective_atk * 30)
                hero.hp -= damage
                logs.append(f"💥 Boss hits {hero.name} for {damage} damage.")
            hero.armor_debuff = {"rounds": 3, "reduction": 1.0}
            hero.atk_debuff = {"rounds": 3, "reduction": 0.08}
            hero.calamity += 2
            hero.curse_of_decay += 2
            logs.append(f"🔻 Boss applies debuffs: -100% Armor, -8% ATK, +2 Calamity, +2 Curse of Decay to {hero.name}.")
        self.energy += 50
        logs.append(f"🔋 Boss gains 50 energy for performing an active skill.")
        self.counterattack(heroes)
        return logs

    def basic_attack(self, heroes, round_num):
        logs = ["⚔️ Boss uses basic attack."]
        for hero in heroes:
            if not hero.is_alive():
                continue
            effective_atk = self.atk
            if self.shrink_debuff:
                effective_atk *= self.shrink_debuff["multiplier_dealt"]
            for i in range(3):
                damage = int(effective_atk * 20)
                hero.hp -= damage
                logs.append(f"💥 Boss hits {hero.name} for {damage} damage.")
            hero.crit_rate_debuff = {"rounds": 3, "reduction": hero.crit_rate}
            hero.calamity += 1
            logs.append(f"🔻 {hero.name} receives -Crit Rate and +1 Calamity.")
            if random.random() < 0.75:
                hero.curse_of_decay += 1
                logs.append(f"💀 Boss adds an extra layer of Curse of Decay to {hero.name}.")
        self.energy += 50
        logs.append(f"🔋 Boss gains 50 energy for performing a basic attack.")
        self.counterattack(heroes)
        return logs

    def counterattack(self, heroes):
        logs = ["⏱️ Boss triggers counterattack."]
        for hero in heroes:
            if not hero.is_alive():
                continue
            effective_atk = self.atk
            if self.shrink_debuff:
                effective_atk *= self.shrink_debuff["multiplier_dealt"]
            damage = int(effective_atk * 15)
            if hero.shield > 0:
                if hero.shield >= damage:
                    hero.shield -= damage
                    logs.append(f"🛡️ {hero.name}'s shield absorbs {damage} damage.")
                    damage = 0
                else:
                    logs.append(f"🛡️ {hero.name}'s shield absorbs {hero.shield} damage.")
                    damage -= hero.shield
                    hero.shield = 0
            hero.hp -= damage
            logs.append(f"⚔️ Boss counterattacks {hero.name} for {damage} damage.")
            hero.calamity += 1
            logs.append(f"💀 {hero.name} gains 1 Calamity.")
            if random.random() < 0.5:
                hero.curse_of_decay += 1
                logs.append(f"💀 {hero.name} gains 1 Curse of Decay.")
        return logs

    def process_control_buffs(self, heroes):
        fear_count = sum(1 for h in heroes if h.has_fear)
        silence_count = sum(1 for h in heroes if h.has_silence)
        seal_count = sum(1 for h in heroes if h.has_seal_of_light)
        logs = []

        if fear_count > 0:
            bonus = fear_count * 50
            self.hd_bonus += bonus
            self.apply_buff("fear_buff", {"attribute": "HD", "bonus": bonus, "rounds": 15})
            logs.append(f"🧠 Boss gains +{bonus} HD from fear effects.")
        if silence_count > 0:
            self.energy += silence_count * 50
            logs.append(f"🔋 Boss gains {silence_count * 50} energy from silence effects.")
        if seal_count > 0:
            bonus = seal_count * 15
            self.all_damage_bonus += bonus
            self.apply_buff("seal_buff", {"all_damage_bonus": bonus, "rounds": 15})
            logs.append(f"✨ Boss gains +{bonus}% all damage from Seal of Light.")
        return logs

    def process_poison_and_other_effects(self):
        msg = self.process_poison()
        return [msg] if msg else []

    def remove_non_skill_debuff(self):
        if self.non_skill_debuffs:
            removed = self.non_skill_debuffs.pop(0)
            return f"🧹 Boss removes non-skill debuff: {removed}."
        return ""

    def end_of_round_effects(self, heroes, round_num):
        logs = [f"🔄 Boss end-of-round effects for Round {round_num}."]
        logs.extend(self.process_poison_and_other_effects())

        if self.shrink_debuff:
            self.shrink_debuff["rounds"] -= 1
            if self.shrink_debuff["rounds"] <= 0:
                self.shrink_debuff = None
                logs.append("🌀 Boss's shrink debuff expires.")

        non_skill_msg = self.remove_non_skill_debuff()
        if non_skill_msg:
            logs.append(non_skill_msg)

        alive_heroes = [h for h in heroes if h.is_alive()]
        if alive_heroes:
            hero_high = max(alive_heroes, key=lambda h: h.atk)
            hero_high.energy = max(hero_high.energy - 100, 0)
            logs.append(f"🔋 Boss drains 100 energy from {hero_high.name}.")
            hero_high.apply_buff("boss_attack_debuff", {"attack_multiplier": 0.60, "rounds": 2})
            logs.append(f"🔻 {hero_high.name} receives -40% ATK debuff for 2 rounds.")
            hero_high.curse_of_decay += 3
            logs.append(f"💀 Boss inflicts 3 Curse of Decay on {hero_high.name}.")

        bonus = int(self.atk * 0.15)
        BuffHandler.apply_buff(self, "end_of_round_atk_buff", {
            "attribute": "atk", "bonus": bonus, "rounds": 9999
        })
        logs.append(f"📈 Boss attack increased by {bonus}. New ATK: {self.atk + bonus}")

        logs.extend(self.process_control_buffs(heroes))
        self.process_buffs()

        return logs
