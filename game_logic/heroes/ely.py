from .base import Hero
import random
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage, apply_direct_damage

class ELY(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact)
        self.transition_power = 0

    def active_skill(self, boss, team):
        logs = [f"{self.name} uses active skill."]
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs

        logs.extend(hero_deal_damage(self, boss, self.atk * 14, is_active=True, team=team))

        shrink = {
            "multiplier_dealt": 0.90,
            "multiplier_received": 1.10,
            "rounds": 2
        }

        if boss.shrink_debuff:
            shrink["multiplier_dealt"] *= boss.shrink_debuff["multiplier_dealt"]
            shrink["multiplier_received"] *= boss.shrink_debuff["multiplier_received"]
        boss.shrink_debuff = shrink
        logs.append(f"{self.name} applies Shrink to {boss.name}: -10% damage dealt, +10% damage received (stacks).")

        self.transition_power += 6
        logs.append(f"{self.name} gains 6 TP from active skill (TP now: {self.transition_power}).")

        return logs

    def basic_attack(self, boss, team):
        logs = [f"{self.name} begins basic attack."]
        if self.has_fear:
            logs.append(f"{self.name} is feared and cannot perform basic attack.")
            return logs

        logs.extend(hero_deal_damage(self, boss, self.atk * 10, is_active=False, team=team))

        shrink = {
            "multiplier_dealt": 0.95,
            "multiplier_received": 1.05,
            "rounds": 2
        }
        if boss.shrink_debuff:
            shrink["multiplier_dealt"] *= boss.shrink_debuff["multiplier_dealt"]
            shrink["multiplier_received"] *= boss.shrink_debuff["multiplier_received"]
        boss.shrink_debuff = shrink
        logs.append(f"{self.name} reapplies Shrink: -5% dealt, +5% received (stacks).")

        return logs

    def passive_trigger(self, team, boss):
        logs = []
        logs.append(f"{self.name} triggers passive: damage-based Shrink extension.")
        if boss.shrink_debuff:
            boss.shrink_debuff["rounds"] += 1
            logs.append(f"{self.name} extends Shrink duration on {boss.name} by 1 round.")
        return logs

    def on_receive_damage(self, damage, team, source):
        logs = []
        if source.lower() in ["basic", "active"]:
            self.transition_power += 6
            logs.append(f"{self.name} gains 6 TP from receiving {source} hit (TP now: {self.transition_power}).")
        return logs

    def release_transition_skill(self, boss, team):
        logs = []
        if self.transition_power >= 6:
            self.transition_power -= 6
            logs.append(f"{self.name} consumes 6 TP to release Transition Skill (TP now: {self.transition_power}).")

            bonus = int(self.atk * 12)
            logs.append(apply_direct_damage(self, boss, bonus, team=team))

            shrink = {
                "multiplier_dealt": 0.90,
                "multiplier_received": 1.10,
                "rounds": 3
            }
            if boss.shrink_debuff:
                shrink["multiplier_dealt"] *= boss.shrink_debuff["multiplier_dealt"]
                shrink["multiplier_received"] *= boss.shrink_debuff["multiplier_received"]
            boss.shrink_debuff = shrink
            logs.append(f"{self.name} reapplies stacked Shrink (Transition): -10% dealt, +10% received.")

        return logs

    def on_end_of_round(self, team, boss):
        logs = []
        if self.transition_power >= 6:
            logs.extend(self.release_transition_skill(boss, team))
        return logs
