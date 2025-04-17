from .base import Hero
import random
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage

class LBRM(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact)
        self.transition_power = 0

    def start_of_battle(self, team, boss):
        logs = []
        self.wings_effect = True
        self.magnification_effect = True
        self.protection_effect = True
        logs.append(f"{self.name} gains Wings, Magnification, and Protection at battle start.")

        logs.extend(self.apply_attribute_buff_with_curse("control_immunity", 8, boss))
        logs.extend(self.apply_attribute_buff_with_curse("speed", 8, boss))
        logs.extend(self.apply_attribute_buff_with_curse("all_damage_dealt", 10, boss))

        self.shield += int(self.atk * 28)
        logs.append(f"{self.name} gains initial shield of {int(self.atk * 28)} (2800% ATK).")

        dr_bonus = 6 * 3
        logs.extend(self.apply_attribute_buff_with_curse("DR", dr_bonus, boss))

        return logs

    def active_skill(self, boss, team):
        logs = []
        logs.append(f"{self.name} begins active skill.")
        logs.extend(hero_deal_damage(self, boss, self.atk * 24, is_active=True, team=team))

        boss.apply_buff("ctrl_immunity_down", {"decrease": 15, "rounds": 3})
        logs.append(f"{self.name} reduces {boss.name}'s control immunity by 15 for 3 rounds.")

        ally_wings = max(team.heroes, key=lambda h: h.spd)
        logs.extend(BuffHandler.apply_buff(ally_wings, "wings_buff", {
            "attribute": "speed", "bonus": 8, "rounds": 4
        }))
        logs.extend(BuffHandler.apply_buff(ally_wings, "wings_ctrl", {
            "attribute": "control_immunity", "bonus": 8, "rounds": 4
        }))
        ally_wings.wings_effect = True
        logs.append(f"{ally_wings.name} is granted Wings for 4 rounds.")

        ally_mag = max(team.heroes, key=lambda h: h.atk)
        logs.extend(BuffHandler.apply_buff(ally_mag, "magnification_buff", {
            "attribute": "all_damage_dealt", "bonus": 10, "rounds": 4
        }))
        ally_mag.magnification_effect = True
        logs.append(f"{ally_mag.name} is granted Magnification for 4 rounds.")

        ally_prot = min(team.heroes, key=lambda h: h.hp)
        shield_amt = int(ally_prot.atk * 28)
        logs.extend(BuffHandler.apply_buff(ally_prot, "protection_shield", {
            "attribute": "shield", "shield": shield_amt, "rounds": 4
        }))
        ally_prot.protection_effect = True
        logs.append(f"{ally_prot.name} is granted Protection (shield) for 4 rounds.")

        self.transition_power += 6
        logs.append(f"{self.name} gains 6 TP from active skill (TP now: {self.transition_power}).")
        return logs

    def basic_attack(self, boss, team):
        logs = []
        logs.append(f"{self.name} begins basic attack.")
        if hasattr(self, "power_of_dream") and self.power_of_dream >= 2:
            logs.append(f"{self.name} consumes all Power of Dream to use active skill instead.")
            self.power_of_dream = 0
            return self.active_skill(boss, team)

        extra = min(int(0.15 * boss.hp), int(30 * self.atk))
        logs.extend(hero_deal_damage(self, boss, self.atk * 10, is_active=False, team=team))
        logs.append(f"{self.name} deals additional {extra} flat damage from Magnification.")
        boss.hp -= extra
        return logs

    def passive_trigger(self, ally):
        logs = []
        if self.energy >= 30:
            self.energy -= 30
            removed = None
            if ally.has_silence:
                ally.has_silence = False
                ally.silence_rounds = 0
                removed = "Silence"
            elif ally.has_fear:
                ally.has_fear = False
                ally.fear_rounds = 0
                removed = "Fear"
            elif ally.has_seal_of_light:
                ally.has_seal_of_light = False
                ally.seal_rounds = 0
                removed = "Seal"
            if removed:
                self.power_of_dream += 1
                logs.extend(BuffHandler.apply_buff(ally, "lbrm_shield", {
                    "attribute": "shield", "shield": int(self.atk * 15), "rounds": 1
                }))
                logs.append(f"{self.name} removes {removed} from {ally.name}, gains 1 Power of Dream; bonus shield granted.")
        return logs

    def release_transition_skill(self, boss, team):
        logs = []
        if self.transition_power < 6:
            logs.append(f"{self.name} does not have enough TP to release Transition Skill.")
            return logs

        self.transition_power -= 6
        logs.append(f"{self.name} consumes 6 TP for Transition Skill (TP now: {self.transition_power}).")

        calc_damage = int(boss.max_hp * 0.30)
        cap_damage = int(self.atk * 30)
        damage_to_deal = min(calc_damage, cap_damage)
        boss.take_damage(damage_to_deal)
        logs.append(f"{self.name} deals {damage_to_deal} damage to {boss.name} from Transition Skill.")

        option = random.choice([1, 2, 3])
        if option == 1:
            for ally in team.heroes:
                if getattr(ally, "wings_effect", False):
                    bonus = ally.atk * 0.20
                    logs.extend(BuffHandler.apply_buff(ally, "wings_transition_atk_up", {
                        "attribute": "atk", "bonus": int(bonus), "rounds": 2
                    }))
                    ally.extra_ctrl_removals = min(getattr(ally, "extra_ctrl_removals", 0) + 1, 2)
                    logs.append(f"{ally.name} with Wings gains +20% ATK and +1 control removal (now {ally.extra_ctrl_removals}).")
                    break
        elif option == 2:
            for ally in team.heroes:
                if getattr(ally, "magnification_effect", False):
                    logs.extend(BuffHandler.apply_buff(ally, "magnification_adr_up", {
                        "attribute": "ADR", "bonus": 10, "rounds": 2
                    }))
                    heal_amt = int(0.33 * ally.max_hp)
                    ally.hp = min(ally.max_hp, ally.hp + heal_amt)
                    logs.append(f"{ally.name} with Magnification gains +10% ADR and heals {heal_amt} HP.")
                    break
        elif option == 3:
            for ally in team.heroes:
                if getattr(ally, "protection_effect", False):
                    logs.extend(BuffHandler.apply_buff(ally, "bee_sugar_coat", {
                        "attribute": "control_immunity", "bonus": 50, "rounds": 9999
                    }))
                    logs.append(f"{ally.name} with Protection gains Bee Sugar-Coat (50% control immunity until shield lost).")
                    break

        for ally in team.back_line:
            logs.extend(BuffHandler.apply_buff(ally, "holy_dmg_up", {
                "attribute": "holy_damage", "bonus": 10, "rounds": 2
            }))
        logs.append("Back line allies' holy damage increased by 10% for 2 rounds.")

        best_ally = max(team.heroes, key=lambda h: h.atk)
        logs.extend(BuffHandler.apply_buff(best_ally, "dmg_up", {
            "attribute": "all_damage_dealt", "bonus": 15, "rounds": 2
        }))
        logs.append(f"{best_ally.name} gains +15% all damage for 2 rounds.")

        logs.extend(BuffHandler.apply_debuff(boss, "dmg_down", {
            "attribute": "all_damage_dealt", "bonus": -10, "rounds": 2
        }))
        logs.append(f"{boss.name}'s damage dealt reduced by 10% for 2 rounds.")

        for ally in team.back_line:
            logs.extend(BuffHandler.apply_buff(ally, "backline_dmg_up", {
                "attribute": "all_damage_dealt", "bonus": 10, "rounds": 3
            }))
        logs.append("Back line allies' all damage dealt increased by 10% for 3 rounds.")

        return logs

    def on_end_of_round(self, team, boss):
        logs = []
        if self.transition_power >= 6:
            logs.extend(self.release_transition_skill(boss, team))
        return logs
