from .base import Hero
import random
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage

class SQH(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None, lifestar=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact, lifestar=lifestar)
        self.transition_power = 0
        self.queens_guard = False
        self.abyssal_corruption = 0
        self.bleed = 0
        self.bleed_duration = 0

    def format_damage_log(self, amount):
        return f"{amount // 1_000_000}M dmg"

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
        dmg = self.atk * 18
        logs.extend(hero_deal_damage(self, boss, dmg, is_active=True, team=team, allow_counter=True, allow_crit=True))

        boss.bleed = self.atk * 18
        boss.bleed_duration = 2
        logs.append(f"🩸 Applies Bleed (1800% ATK for 2 rounds) to {boss.name}.")

        boss.abyssal_corruption = getattr(boss, "abyssal_corruption", 0) + 1
        ac_msg = "🧿 Applies 1 layer of Abyssal Corruption."
        if random.random() < 0.25:
            boss.abyssal_corruption += 1
            ac_msg += " +1 extra layer (25% chance)!"
        logs.append(ac_msg)

        if getattr(boss, "abyssal_corruption", 0) > 0:
            logs.extend(BuffHandler.apply_debuff(boss, "crit_down_ac", {
                "attribute": "crit_rate",
                "bonus": -0.10,
                "rounds": 2
            }))
            logs.append(f"📉 {boss.name} receives -10% Crit Rate for 2 rounds (Abyssal Corruption).")

        self.transition_power += 6
        logs.append(f"✨ Gains 6 TP (now {self.transition_power}).")

        if self.transition_power >= 12:
            logs.extend(self.release_transition_skill(team, boss))

        return logs

    def basic_attack(self, boss, team):
        logs = []
        if self.has_fear:
            logs.append(f"{self.name} is feared and cannot use basic attack.")
            return logs

        logs.append(f"🔪 {self.name} uses Basic Attack:")
        dmg = self.atk * 12
        logs.extend(hero_deal_damage(self, boss, dmg, is_active=False, team=team, allow_counter=True, allow_crit=True))

        logs.extend(BuffHandler.apply_debuff(boss, "crit_down_basic", {
            "attribute": "crit_rate",
            "bonus": -0.25,
            "rounds": 2
        }))
        logs.append(f"📉 {boss.name} receives -25% Crit Rate for 2 rounds.")
        logs.extend(self.apply_attribute_buff_with_curse("crit_rate", 18, boss))
        logs.extend(self.apply_attribute_buff_with_curse("crit_dmg", 18, boss))
        return logs

    def release_transition_skill(self, team, boss):
        logs = [f"🔄 {self.name} activates Transition Skill (TP -12 → {self.transition_power - 12})."]
        self.transition_power -= 12

        atk_buffs, heals, curse_penalties = [], [], []
        for ally in team.heroes:
            if getattr(ally, "queens_guard", False):
                atk_buffs += ally.apply_attribute_buff_with_curse("atk", 10, boss)
                heal_amt = int(ally.max_hp * 0.50)
                ally.hp = min(ally.max_hp, ally.hp + heal_amt)
                heals.append(f"{ally.name} heals {self.format_damage_log(heal_amt)} (+10% ATK).")

        logs.extend(atk_buffs)
        if heals:
            logs.append("❤️ Queen's Guard Healing: " + " | ".join(heals))

        team_buffs = []
        for ally in team.heroes:
            team_buffs += ally.apply_attribute_buff_with_curse("all_damage_dealt", 10, boss)
            team_buffs += ally.apply_attribute_buff_with_curse("ADR", 20, boss)
            team_buffs += ally.apply_attribute_buff_with_curse("DR", 20, boss)
            if ally != self:
                if ally.curse_of_decay > 0:
                    damage = int(boss.atk * 30)
                    ally.hp -= damage
                    ally.curse_of_decay -= 1
                    curse_penalties.append(f"{ally.name} offsets energy gain (takes {self.format_damage_log(damage)}).")
                else:
                    ally.energy += 20
        logs.extend(team_buffs)

        if curse_penalties:
            logs.append("💀 Curse Penalty: " + " | ".join(curse_penalties))
        else:
            logs.append("⚡ All allies gain +20 energy.")

        logs.extend(BuffHandler.apply_debuff(boss, "atk_down", {"attribute": "atk", "bonus": -0.15, "rounds": 2}))
        logs.append(f"🔻 Boss loses 15% ATK for 2 rounds.")

        heal_all = int(self.atk * 12)
        for ally in team.heroes:
            ally.hp = min(ally.max_hp, ally.hp + heal_all)
        logs.append(f"❤️ Team-wide heal: {self.format_damage_log(heal_all)} per ally (1200% {self.name}'s ATK).")

        return logs

    def end_of_round(self, boss, team, round_num=None):
        logs = []
        heal_self = int(self.max_hp * 0.20)
        self.hp = min(self.max_hp, self.hp + heal_self)
        logs.append(f"💖 {self.name} heals self for {self.format_damage_log(heal_self)}.")

        alive_count = sum(1 for h in team.heroes if h.is_alive())
        ally_heals = []
        for ally in team.heroes:
            if ally != self and ally.is_alive():
                heal_amt = int(ally.max_hp * 0.016 * alive_count)
                ally.hp = min(ally.max_hp, ally.hp + heal_amt)
                ally_heals.append(f"{ally.name} +{self.format_damage_log(heal_amt)}")
        if ally_heals:
            logs.append("💖 Passive healing: " + "; ".join(ally_heals))
        return logs

    def take_damage(self, damage, source=None, team=None):
        self.hp -= damage
        self.hp = max(self.hp, 0)
        logs = [f"⚔️ {self.name} takes {self.format_damage_log(damage)} (HP: {self.hp}/{self.max_hp})."]
        if source and source.is_alive():
            counters = []
            for ally in team.heroes if team else []:
                if ally != self and ally.is_alive() and getattr(ally, "queens_guard", False):
                    counter_dmg = int(ally.atk * 12)
                    source.hp -= counter_dmg
                    source.hp = max(source.hp, 0)
                    counters.append(f"{ally.name} hits back for {self.format_damage_log(counter_dmg)}")
                    logs.extend(BuffHandler.apply_debuff(source, "atk_down_counter", {
                        "attribute": "atk", "bonus": -0.03, "rounds": 2
                    }))
            if counters:
                logs.append("👑 Queen's Guard counterattacks: " + "; ".join(counters))
        return logs
