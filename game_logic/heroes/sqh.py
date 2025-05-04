from .base import Hero
import random
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage
from utils.log_utils import group_team_buffs
from utils.log_utils import debug


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

                _, msg1 = BuffHandler.apply_buff(ally, "queens_guard_add", {
                    "attribute": "all_damage_dealt", "bonus": 24, "rounds": 9999
                }, boss=boss)
                if msg1:
                    logs.append(msg1)

                _, msg2 = BuffHandler.apply_buff(ally, "queens_guard_adr", {
                    "attribute": "ADR", "bonus": 8, "rounds": 9999
                }, boss=boss)
                if msg2:
                    logs.append(msg2)

        if buffs_applied:
            logs.append("✨ Queen's Guard Buffs:")
            logs.extend(group_team_buffs(buffs_applied))

        return logs



    def active_skill(self, boss, team):
        logs = []
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs
        debug(f"{self.name} starts ACTIVE skill")

        dmg = self.atk * (18 + self.skill_damage / 100)
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
        BuffHandler.apply_debuff(boss, "crit_dmg_in", {
            "attribute": "crit_damage_taken", "bonus": 24 * stacks, "rounds": 9999
        })
        BuffHandler.apply_debuff(boss, "crit_dmg_out", {
            "attribute": "crit_damage", "bonus": -24 * stacks, "rounds": 9999
        })
        effects.append(f"-24% Crit DMG Dealt, +24% Crit DMG Taken × {stacks}")

        if "crit_down_ac" not in boss.buffs:
            logs.extend(BuffHandler.apply_debuff(boss, "crit_down_ac", {
                "attribute": "crit_rate", "bonus": -0.10, "rounds": 2
            }))
            effects.append("-10% Crit Rate")

        self.transition_power += 6
        effects.append(f"Gains 6 TP (now {self.transition_power})")

        logs.append(f"🎯 {self.name} deals 1800% ATK → {' | '.join(effects)}.")

        if self.transition_power >= 12:
            logs.extend(self.release_transition_skill(team, boss))

        return logs

    def basic_attack(self, boss, team):
        if self.has_fear:
            return [f"{self.name} is feared and cannot use basic attack."]

        def do_attack():
            logs = []
            debug(f"{self.name} starts BASIC attack")

            # ✅ Main hit — should allow counter
            dmg = self.atk * (12 + self.skill_damage / 100)
            logs.extend(hero_deal_damage(
                self, boss, dmg,
                is_active=False, team=team,
                allow_counter=True, allow_crit=True
            ))

            buff_logs = []

            # ❌ Attribute debuff — no counter
            logs.extend(BuffHandler.apply_debuff(boss, "crit_down_basic", {
                "attribute": "crit_rate", "bonus": -0.25, "rounds": 2
            }))
            buff_logs.append("-25% Crit Rate")

            # ❌ Self buffs — Curse-aware
            _, msg1 = BuffHandler.apply_buff(self, "crit_rate_up_basic", {
                "attribute": "crit_rate", "bonus": 18, "rounds": 6
            }, boss=boss)
            if msg1:
                buff_logs.append(msg1)

            _, msg2 = BuffHandler.apply_buff(self, "crit_dmg_up_basic", {
                "attribute": "crit_dmg", "bonus": 18, "rounds": 6
            }, boss=boss)
            if msg2:
                buff_logs.append(msg2)

            logs.append(f"🔪 {self.name} Basic Attack effects: {' | '.join(buff_logs)}.")
            return logs

        return self.with_basic_flag(do_attack)


    def release_transition_skill(self, team, boss):
        if self.has_seal_of_light:
            return []  # Transition Skill blocked by Seal of Light

        logs = [f"🔄 {self.name} activates Transition Skill (TP -12 → {self.transition_power - 12})."]
        self.transition_power -= 12

        atk_buffs, heals, buffs_applied = [], [], []

        for ally in team.heroes:
            if getattr(ally, "queens_guard", False):
                _, msg = BuffHandler.apply_buff(ally, "atk_up_transition", {
                    "attribute": "atk", "bonus": 10, "rounds": 3
                }, boss=boss)
                if msg:
                    atk_buffs.append(msg)

                heal_amt = int(ally.max_hp * 0.50)
                before = ally.hp
                ally.hp = min(ally.max_hp, ally.hp + heal_amt)
                actual = ally.hp - before
                ally._healing_done += actual
                heals.append(f"{ally.name} +{self.format_damage_log(actual)} (+10% ATK)")

        if atk_buffs:
            logs.append("🛡️ Queen's Guard Buffs: " + " | ".join(atk_buffs))
        if heals:
            logs.append("❤️ Queen's Guard Healing: " + " | ".join(heals))

        for ally in team.heroes:
            for attr, val in [("all_damage_dealt", 10), ("ADR", 20), ("DR", 20)]:
                _, msg = BuffHandler.apply_buff(ally, f"{attr}_transition", {
                    "attribute": attr, "bonus": val, "rounds": 3
                }, boss=boss)
                if msg:
                    logs.append(msg)
                buffs_applied.append((ally.name, f"+{val}% {attr}"))

            if ally != self:
                _, msg = BuffHandler.apply_buff(ally, f"transition_energy_{random.randint(1000,9999)}", {
                    "attribute": "energy", "bonus": 20, "rounds": 0
                }, boss=boss)
                if msg:
                    logs.append(msg)

        if buffs_applied:
            logs.append("✨ Team Buffs Applied:")
            logs.extend(group_team_buffs(buffs_applied))

        logs.extend(BuffHandler.apply_debuff(boss, "atk_down", {
            "attribute": "atk", "bonus": -0.15, "rounds": 2
        }))
        logs.append("🔻 Boss -15% ATK (2 rounds)")

        heal_all = int(self.atk * 12)
        for ally in team.heroes:
            before = ally.hp
            ally.hp = min(ally.max_hp, ally.hp + heal_all)
            actual = ally.hp - before
            ally._healing_done += actual
        logs.append(f"❤️ Team Heal: {self.format_damage_log(heal_all)} each (1200% ATK).")

        return logs


    def take_damage(self, damage, source_hero=None, team=None):
        logs = []

        # Armor mitigation
        armor_reduction = min(self.armor / (100 * 20 + 180), 0.75)
        damage *= (1 - armor_reduction)

        # DR
        dr_reduction = min(self.DR / 100, 0.75)
        damage *= (1 - dr_reduction)

        # ADR
        adr_reduction = min(self.ADR / 100, 0.75)
        damage *= (1 - adr_reduction)

        damage = int(damage)

        # Shield absorption
        if self.shield > 0:
            absorbed = min(self.shield, damage)
            self.shield -= absorbed
            damage -= absorbed
            logs.append(f"🛡️ {self.name} absorbs {absorbed // 1_000_000}M with shield.")

        # Unbending Will check
        if hasattr(self, "trait_enable") and hasattr(self.trait_enable, "prevent_death"):
            if self.trait_enable.prevent_death(self, damage):
                damage = self.hp - 1

        # Final HP reduction
        self.hp -= damage
        self.hp = max(self.hp, 0)
        logs.append(f"⚔️ {self.name} takes {self.format_damage_log(damage)} (HP: {self.hp}/{self.max_hp}).")

        # 👑 Queen's Guard Counterattack
        if source_hero and source_hero.is_alive():
            counters = []
            for ally in team.heroes if team else []:
                if ally != self and ally.is_alive() and getattr(ally, "queens_guard", False):
                    counter_dmg = int(ally.atk * 12)
                    source_hero.hp -= counter_dmg
                    source_hero.hp = max(source_hero.hp, 0)
                    counters.append(f"{ally.name} hits back for {self.format_damage_log(counter_dmg)}")
                    logs.extend(BuffHandler.apply_debuff(source_hero, "atk_down_counter", {
                        "attribute": "atk", "bonus": -0.03, "rounds": 2
                    }))
            if counters:
                logs.append("👑 Queen's Guard counterattacks: " + "; ".join(counters))

        return logs
