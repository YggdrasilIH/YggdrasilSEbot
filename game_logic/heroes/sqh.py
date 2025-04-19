from .base import Hero
import random
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage

class SQH(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact)
        self.transition_power = 0
        self.queens_guard = False
        self.abyssal_corruption = 0
        self.bleed = 0
        self.bleed_duration = 0

    def start_of_battle(self, team, boss):
        logs = [f"🏰 {self.name} grants Queen's Guard to all allies (except self)."]
        for ally in team.heroes:
            if ally != self:
                ally.queens_guard = True
                logs.extend(ally.apply_attribute_buff_with_curse("all_damage_dealt", 24, boss))
                logs.extend(ally.apply_attribute_buff_with_curse("ADR", 8, boss))
        return logs

    def active_skill(self, boss, team):
        logs = []
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs

        logs.append(f"🎯 {self.name} uses Active Skill:")
        logs.extend(hero_deal_damage(self, boss, self.atk * 18, is_active=True, team=team))

        self.bleed = self.atk * 18
        self.bleed_duration = 2
        logs.append(f"🩸 Applies Bleed (1800% ATK for 2 rounds).")

        boss.abyssal_corruption = getattr(boss, "abyssal_corruption", 0) + 1
        ac_msg = "🧿 Applies 1 layer of Abyssal Corruption."
        if random.random() < 0.25:
            boss.abyssal_corruption += 1
            ac_msg += " +1 extra layer (25% chance)!"
        logs.append(ac_msg)

        self.transition_power += 6
        logs.append(f"✨ Gains 6 TP (now {self.transition_power}).")

        if self.transition_power >= 12:
            logs.extend(self.release_transition_skill(team, boss))

        return logs

        logs.extend(hero_deal_damage(self, boss, self.atk * 18, is_active=True, team=team))

        self.bleed = self.atk * 18
        self.bleed_duration = 2
        logs.append(f"{self.name} applies Bleed to {boss.name} for 2 rounds (1800% ATK per round).")

        boss.abyssal_corruption = getattr(boss, "abyssal_corruption", 0) + 1
        logs.append(f"{self.name} applies 1 layer of Abyssal Corruption to {boss.name}.")
        if random.random() < 0.25:
            boss.abyssal_corruption += 1
            logs.append(f"{self.name} applies an additional layer of Abyssal Corruption to {boss.name} (25% chance).")

        self.transition_power += 6
        logs.append(f"{self.name} gains 6 layers of Transition Power (TP now: {self.transition_power}).")

        if self.transition_power >= 12:
            logs.extend(self.release_transition_skill(team, boss))

        return logs

    def basic_attack(self, boss, team):
        logs = []
        
        if self.has_fear:
            logs.append(f"{self.name} is feared and cannot use basic attack.")
            return logs
        logs.extend(hero_deal_damage(self, boss, self.atk * 12, is_active=False, team=team))
        return logs

    def release_transition_skill(self, team, boss):
        logs = [f"🔄 {self.name} activates Transition Skill (TP -12 → {self.transition_power - 12})."]
        self.transition_power -= 12

        atk_buffs, heals, curse_penalties = [], [], []
        for ally in team.heroes:
            if getattr(ally, "queens_guard", False):
                bonus_atk = ally.atk * 0.10
                atk_buffs += ally.apply_attribute_buff_with_curse("atk", bonus_atk, boss)
                heal_amt = int(ally.max_hp * 0.60)
                ally.hp = min(ally.max_hp, ally.hp + heal_amt)
                heals.append(f"{ally.name} heals {heal_amt} HP (+10% ATK).")

        logs.extend(atk_buffs)
        if heals:
            logs.append("❤️ Queen's Guard Healing: " + " | ".join(heals))

        team_buffs = []
        for ally in team.heroes:
            buffs = []
            buffs += ally.apply_attribute_buff_with_curse("all_damage_dealt", 10, boss)
            buffs += ally.apply_attribute_buff_with_curse("ctrl_immunity", 20, boss)
            buffs += ally.apply_attribute_buff_with_curse("DR", 20, boss)
            team_buffs.extend(buffs)

            if ally != self:
                if ally.curse_of_decay > 0:
                    damage = int(boss.atk * 30)
                    ally.hp -= damage
                    ally.curse_of_decay -= 1
                    curse_penalties.append(f"{ally.name} offsets energy gain (takes {damage}).")
                else:
                    ally.energy += 20
        logs.extend(team_buffs)

        if curse_penalties:
            logs.append("💀 Curse Penalty: " + " | ".join(curse_penalties))
        else:
            logs.append("⚡ All allies gain +20 energy.")

        boss.apply_buff("atk_down", {"attribute": "atk", "bonus": -int(boss.atk * 0.15), "rounds": 2})
        logs.append("🔻 Boss loses 15% ATK for 2 rounds.")

        heal_all = int(self.atk * 12)
        for ally in team.heroes:
            ally.hp = min(ally.max_hp, ally.hp + heal_all)
        logs.append(f"❤️ Team-wide heal: {heal_all} HP per ally (1200% {self.name}'s ATK).")

        return logs

    def on_end_of_round(self, team, boss):
        logs = []
        heal_self = int(self.max_hp * 0.20)
        self.hp = min(self.max_hp, self.hp + heal_self)
        logs.append(f"💖 {self.name} heals self for {heal_self} HP.")

        alive_count = sum(1 for h in team.heroes if h.is_alive())
        ally_heals = []
        for ally in team.heroes:
            if ally != self and ally.is_alive():
                heal_amt = int(ally.max_hp * 0.016 * alive_count)
                ally.hp = min(ally.max_hp, ally.hp + heal_amt)
                ally_heals.append(f"{ally.name} +{heal_amt} HP")
        if ally_heals:
            logs.append("💖 Passive healing: " + "; ".join(ally_heals))
        return logs

    def take_damage(self, damage, source=None, team=None):
        self.hp -= damage
        self.hp = max(self.hp, 0)
        logs = []
        if source and source.is_alive():
            counters = []
            for ally in team.heroes if team else []:
                if ally != self and ally.is_alive() and getattr(ally, "queens_guard", False):
                    counter_dmg = int(ally.atk * 12)
                    source.hp -= counter_dmg
                    counters.append(f"{ally.name} hits back for {counter_dmg} damage")
                    logs.extend(BuffHandler.apply_debuff(source, "atk_down", {
                        "attribute": "atk", "bonus": -int(source.atk * 0.03), "rounds": 2
                    }))
            if counters:
                logs.append("👑 Queen's Guard counterattacks: " + "; ".join(counters))
        return logs
