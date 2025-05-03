from .base import Hero
from game_logic.damage_utils import hero_deal_damage
import random
from math import floor
from game_logic.buff_handler import BuffHandler
from utils.log_utils import debug


class LFA(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None, lifestar=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact, lifestar=lifestar)
        self.transition_power = 0

    def add_or_update_buff(self, hero, buff_name, buff_data):
        if buff_name in hero.buffs:
            existing = hero.buffs[buff_name]
            if "bonus" in buff_data:
                existing["bonus"] += buff_data.get("bonus", 0)
        else:
            hero.apply_buff(buff_name, buff_data)

    def active_skill(self, boss, team):
        logs = []
        

        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs
        debug(f"{self.name} starts ACTIVE skill")
        crit_failed = False
        hits = []

        # Step 1: Add 2 base hits (can crit)
        for _ in range(2):
            hits.append(("base", self.atk * self.skill_multiplier(12)))

        # Step 2: If boss < 60% HP, add 2 more hits (can crit)
        if boss.hp < boss.max_hp * 0.60:
            for _ in range(2):
                hits.append(("base", self.atk * self.skill_multiplier(12)))

            # Heal based on second set of hits
            second_total = sum(h[1] for h in hits[2:])
            heal_amt = int(second_total * 1.20)
            self.hp = min(self.max_hp, self.hp + heal_amt)
            logs.append(f"❤️ {self.name} heals for {heal_amt // 1_000_000}M HP from extra attacks.")

        # Step 3: Final single hit (cannot crit)
        hits.append(("final", self.atk * self.skill_multiplier(12)))

        # Step 4: Process each hit separately
        for i, (hit_type, dmg) in enumerate(hits):
            allow_crit = hit_type == "base"
            allow_counter = i == 0  # First hit only
            result_logs = hero_deal_damage(
                self, boss, dmg, is_active=True, team=team,
                allow_counter=allow_counter, allow_crit=allow_crit
            )
            logs.extend(result_logs)

            # Track crit_failed if base hit missed
            if allow_crit and all("CRIT" not in r for r in result_logs if isinstance(r, str)):
                crit_failed = True

        # Step 5: Burst (crittable, no counter)
        base_total = sum(h[1] for h in hits)
        burst_damage = int(base_total * 1.20)
        logs.append(f"🔫 {self.name} unleashes {burst_damage // 1_000_000}M bonus burst damage.")
        logs.extend(hero_deal_damage(
            self, boss, burst_damage, is_active=True, team=team,
            allow_counter=False, allow_crit=True
        ))

        # Step 6: Balanced Strike override
        if hasattr(self.trait_enable, "override_crit_check"):
            self.trait_enable.override_crit_check(crit_failed)

        # Step 7: Buffs and debuffs
        steal_amount = int(boss.base_atk * 0.30)
        logs.extend(BuffHandler.apply_debuff(boss, "lfa_atk_down_active", {
            "attribute": "atk", "bonus": -0.30, "rounds": 9999
        }))
        logs.append(f"🔻 {boss.name}'s ATK reduced by 30% permanently from LFA's active skill.")

        logs.extend(BuffHandler.apply_buff(self, "lfa_atk_steal_buff", {
            "attribute": "atk", "bonus": steal_amount, "rounds": 9999
        }, boss))
        logs.append(f"💪 {self.name} gains +{steal_amount:,} ATK permanently by stealing it from the boss.")

        # Step 8: Transition power
        self.transition_power += 6
        logs.append(f"{self.name} gains 6 layers of Transition Power (TP now: {self.transition_power}).")

        if self.transition_power >= 12:
            logs.extend(self.release_transition_skill(boss, team))

        return logs

    def basic_attack(self, boss, team):
        if self.has_fear:
            return [f"{self.name} is feared and cannot perform basic attack."]

        def do_attack():
            logs = []
            debug(f"{self.name} starts BASIC attack")


            # ✅ Main basic hit triggers counter
            dmg = self.atk * self.skill_multiplier(9.6)
            logs.extend(hero_deal_damage(
                self, boss, dmg,
                is_active=False, team=team,
                allow_counter=True, allow_crit=True
            ))

            # ✅ Buff application (no counter)
            logs.extend(self.apply_attribute_buff_with_curse("crit_rate", 24, boss))

            return logs

        return self.with_basic_flag(do_attack)


    def release_transition_skill(self, boss, team):
        logs = []
        if self.has_seal_of_light:
            return []

        if self.transition_power >= 12:
            self.transition_power -= 12
            logs.append(f"🔄 {self.name} activates Transition Skill (TP -12 → {self.transition_power}).")

            total_damage = 0
            for i in range(2):
                dmg = self.atk * (15+self.skill_damage/100)
                total_damage += dmg
                logs.extend(hero_deal_damage(self, boss, dmg, is_active=True, team=team, allow_counter=False, allow_crit=True))

            logs.extend(BuffHandler.apply_debuff(boss, "atk_down", {"attribute": "atk", "bonus": -0.5, "rounds": 3}))
            logs.append(f"🔻 {boss.name} loses 50% ATK for 3 rounds.")

            extra_from_hp = int(0.08 * boss.max_hp)
            cap_damage = int(self.atk * (15))
            extra_damage = min(extra_from_hp, cap_damage)
            total_damage += extra_damage
            logs.append(f"💥 {self.name} deals {extra_damage // 1_000_000}M based on 8% of boss max HP (capped at 1500% ATK).")

            logs.extend(BuffHandler.apply_debuff(boss, "atk_down_secondary", {"attribute": "atk", "bonus": -0.15, "rounds": 2}))
            logs.append(f"🔻 {boss.name} loses 15% ATK for 2 rounds.")

            if boss.hp >= 0.50 * boss.max_hp:
                bonus_dmg = self.atk * (12+self.skill_damage/100)
                total_damage += bonus_dmg
                logs.append(f"🌟 {self.name} deals +1200% bonus damage because Boss HP ≥ 50%.")

            logs.extend(hero_deal_damage(self, boss, total_damage, is_active=True, team=team, allow_counter=False, allow_crit=False))

            BuffHandler.apply_buff(self, "lfa_all_dmg_up", {"attribute": "all_damage_dealt", "bonus": 15, "rounds": 2}, boss)
            logs.append(f"✅ {self.name} gains +15 all_damage_dealt for 2 rounds.")

        return logs

    def end_of_round(self, boss, team, round_num=None):
        return super().end_of_round(boss, team, round_num)
