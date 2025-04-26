from .base import Hero
import random
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage
from utils.log_utils import group_team_buffs

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
        buffs_applied = []

        for ally in team.heroes:
            if ally != self:
                ally.queens_guard = True
                buffs_applied.append((ally.name, "+24% All Damage Dealt"))
                buffs_applied.append((ally.name, "+8% ADR"))
                ally.apply_attribute_buff_with_curse("all_damage_dealt", 24, boss)
                ally.apply_attribute_buff_with_curse("ADR", 8, boss)

        if buffs_applied:
            logs.append("✨ Queen's Guard Buffs:")
            logs.extend(group_team_buffs(buffs_applied))

        return logs


    def active_skill(self, boss, team):
        logs = []
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs

        dmg = self.atk * 18
        logs.extend(hero_deal_damage(self, boss, dmg, is_active=True, team=team, allow_counter=True, allow_crit=True))

        effects = []
        boss.bleed = self.atk * 18
        boss.bleed_duration = 2
        effects.append("Bleed")

        boss.abyssal_corruption = getattr(boss, "abyssal_corruption", 0) + 1
        if random.random() < 0.25:
            boss.abyssal_corruption += 1
            effects.append("Abyssal Corruption +2")
        else:
            effects.append("Abyssal Corruption +1")

        stacks = boss.abyssal_corruption

        # Apply or refresh Crit Damage Taken / Dealt effects
        BuffHandler.apply_debuff(boss, "crit_dmg_in", {
            "attribute": "crit_damage_taken",
            "bonus": 24 * stacks,
            "rounds": 9999
        })
        BuffHandler.apply_debuff(boss, "crit_dmg_out", {
            "attribute": "crit_damage",
            "bonus": -24 * stacks,
            "rounds": 9999
        })
        effects.append(f"-24% Crit DMG Dealt, +24% Crit DMG Taken × {stacks}")

        # Apply -10% crit rate once if not already present
        if "crit_down_ac" not in boss.buffs:
            logs.extend(BuffHandler.apply_debuff(boss, "crit_down_ac", {
                "attribute": "crit_rate",
                "bonus": -0.10,
                "rounds": 2
            }))
            effects.append("-10% Crit Rate")

        self.transition_power += 6
        effects.append(f"Gains 6 TP (now {self.transition_power})")

        logs.append(f"🎯 {self.name} deals 1800% ATK → {' | '.join(effects)}.")

        if self.transition_power >= 12:
            logs.extend(self.release_transition_skill(team, boss))

        return logs

    def basic_attack(self, boss, team):
        logs = []
        if self.has_fear:
            logs.append(f"{self.name} is feared and cannot use basic attack.")
            return logs

        dmg = self.atk * 12
        logs.extend(hero_deal_damage(self, boss, dmg, is_active=False, team=team, allow_counter=True, allow_crit=True))

        buff_logs = []
        logs.extend(BuffHandler.apply_debuff(boss, "crit_down_basic", {
            "attribute": "crit_rate",
            "bonus": -0.25,
            "rounds": 2
        }))
        buff_logs.append("-25% Crit Rate")

        buff_logs.extend(self.apply_attribute_buff_with_curse("crit_rate", 18, boss))
        buff_logs.extend(self.apply_attribute_buff_with_curse("crit_dmg", 18, boss))

        logs.append(f"🔪 {self.name} Basic Attack effects: {' | '.join(buff_logs)}.")
        return logs

    def release_transition_skill(self, team, boss):
            if self.has_seal_of_light:
                return []  # Transition Skill blocked by Seal of Light

            logs = [f"🔄 {self.name} activates Transition Skill (TP -12 → {self.transition_power - 12})."]
            self.transition_power -= 12

            atk_buffs, heals, curse_penalties, energy_gain = [], [], [], []
            buffs_applied = []

            for ally in team.heroes:
                if getattr(ally, "queens_guard", False):
                    atk_buffs += ally.apply_attribute_buff_with_curse("atk", 10, boss)
                    heal_amt = int(ally.max_hp * 0.50)
                    ally.hp = min(ally.max_hp, ally.hp + heal_amt)
                    heals.append(f"{ally.name} +{self.format_damage_log(heal_amt)} (+10% ATK)")

            if atk_buffs:
                logs.append("🛡️ Queen's Guard Buffs: " + " | ".join(atk_buffs))
            if heals:
                logs.append("❤️ Queen's Guard Healing: " + " | ".join(heals))

            for ally in team.heroes:
                buffs_applied.append((ally.name, "+10% All Damage Dealt"))
                buffs_applied.append((ally.name, "+20% ADR"))
                buffs_applied.append((ally.name, "+20% DR"))

                ally.apply_attribute_buff_with_curse("all_damage_dealt", 10, boss)
                ally.apply_attribute_buff_with_curse("ADR", 20, boss)
                ally.apply_attribute_buff_with_curse("DR", 20, boss)

                if ally != self:
                    if ally.curse_of_decay > 0:
                        damage = int(boss.atk * 30)
                        ally.hp -= damage
                        ally.curse_of_decay -= 1
                        curse_penalties.append(f"{ally.name} takes {self.format_damage_log(damage)} (Curse)")
                    else:
                        ally.energy += 20
                        energy_gain.append(ally.name)

            if buffs_applied:
                logs.append("✨ Team Buffs Applied:")
                logs.extend(group_team_buffs(buffs_applied))

            if curse_penalties:
                logs.append("💀 Curse Penalties: " + " | ".join(curse_penalties))
            if energy_gain:
                logs.append(f"⚡ Energy +20: {', '.join(energy_gain)}")

            logs.extend(BuffHandler.apply_debuff(boss, "atk_down", {"attribute": "atk", "bonus": -0.15, "rounds": 2}))
            logs.append(f"🔻 Boss -15% ATK (2 rounds)")

            heal_all = int(self.atk * 12)
            for ally in team.heroes:
                ally.hp = min(ally.max_hp, ally.hp + heal_all)
            logs.append(f"❤️ Team Heal: {self.format_damage_log(heal_all)} each (1200% ATK).")

            return logs

    def end_of_round(self, boss, team, round_num=None):
        if self.has_seal_of_light:
            return super().end_of_round(boss, team, round_num)  # Passive healing blocked by Seal of Light
        logs = super().end_of_round(boss, team, round_num)
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
