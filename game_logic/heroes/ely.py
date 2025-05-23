from .base import Hero
import random
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage
from utils.log_utils import stylize_log

class ELY(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None, lifestar=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact, lifestar=lifestar)

    def active_skill(self, boss, team):
        logs = [stylize_log("damage", f"{self.name} uses active skill.")]
        if self.has_silence:
            logs.append(stylize_log("control", f"{self.name} is silenced and cannot use active skill."))
            return logs

        logs += hero_deal_damage(self, boss, self.atk * 14, is_active=True, team=team)

        shrink = {
            "multiplier_dealt": 0.4,
            "multiplier_received": 1.4,
            "rounds": 2
        }

        if boss.shrink_debuff:
            shrink["multiplier_dealt"] = min(shrink["multiplier_dealt"], boss.shrink_debuff["multiplier_dealt"])
            shrink["multiplier_received"] = max(shrink["multiplier_received"], boss.shrink_debuff["multiplier_received"])
        boss.shrink_debuff = shrink

        logs.append(stylize_log("debuff", f"{self.name} applies Shrink to {boss.name}: -60% damage dealt, +40% damage received."))
        return logs

    def basic_attack(self, boss, team):
        logs = [stylize_log("damage", f"{self.name} begins basic attack.")]
        if self.has_fear:
            logs.append(stylize_log("control", f"{self.name} is feared and cannot perform basic attack."))
            return logs

        logs += hero_deal_damage(self, boss, self.atk * 10, is_active=False, team=team)

        shrink = {
            "multiplier_dealt": 0.4,
            "multiplier_received": 1.4,
            "rounds": 2
        }
        if boss.shrink_debuff:
            shrink["multiplier_dealt"] = min(shrink["multiplier_dealt"], boss.shrink_debuff["multiplier_dealt"])
            shrink["multiplier_received"] = max(shrink["multiplier_received"], boss.shrink_debuff["multiplier_received"])
        boss.shrink_debuff = shrink

        logs.append(stylize_log("debuff", f"{self.name} reapplies Shrink: -60% damage dealt, +40% damage received."))
        return logs

    def passive_trigger(self, source, boss, team):

        logs = []
        logs.append(stylize_log("passive", f"{self.name} triggers passive: damage-based Shrink extension."))
        if boss.shrink_debuff:
            boss.shrink_debuff["rounds"] += 1
            logs.append(stylize_log("debuff", f"{self.name} extends Shrink duration on {boss.name} by 1 round."))
        return logs
