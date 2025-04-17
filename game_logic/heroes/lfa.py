from .base import Hero
from game_logic.damage_utils import hero_deal_damage
import random
from math import floor


class LFA(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact)
        self.transition_power = 0

    def active_skill(self, boss, team):
        logs = [f"{self.name} begins active skill."]
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs

        total_damage = 0
        for i in range(2):
            logs.append(f"{self.name} deals {self.atk * 12} damage on first attack {i+1}.")
            logs.extend(hero_deal_damage(self, boss, self.atk * 12, is_active=True, team=team))
            total_damage += self.atk * 12

        if boss.hp < boss.max_hp * 0.60:
            second_total = 0
            for i in range(2):
                logs.append(f"{self.name} deals {self.atk * 12} damage on extra attack {i+1}.")
                logs.extend(hero_deal_damage(self, boss, self.atk * 12, is_active=True, team=team))
                second_total += self.atk * 12
                total_damage += self.atk * 12
            heal_amt = int(second_total * 1.20)
            self.hp = min(self.max_hp, self.hp + heal_amt)
            logs.append(f"{self.name} heals for {heal_amt} HP from extra attacks.")

        logs.append(f"{self.name} deals {self.atk * 12} damage on additional attack.")
        logs.extend(hero_deal_damage(self, boss, self.atk * 12, is_active=True, team=team))
        total_damage += self.atk * 12

        bonus_damage = int(total_damage * 1.20)
        for enemy in team.heroes:
            enemy.take_damage(bonus_damage)
            logs.append(f"{self.name} deals {bonus_damage} bonus AOE damage to {enemy.name}.")

        self.transition_power += 6
        logs.append(f"{self.name} gains 6 layers of Transition Power (TP now: {self.transition_power}).")

        if self.transition_power >= 12:
            logs.extend(self.release_transition_skill(boss, team))

        return logs

    def basic_attack(self, boss, team):
        logs = [f"{self.name} begins basic attack."]
        if self.has_fear:
            logs.append(f"{self.name} is feared and cannot perform basic attack.")
            return logs

        logs.extend(hero_deal_damage(self, boss, int(self.atk * 9.6), is_active=False, team=team))
        logs.extend(self.apply_attribute_buff_with_curse("crit_rate", 24, boss))

        return logs

    def release_transition_skill(self, boss, team):
        logs = []
        if self.transition_power >= 12:
            self.transition_power -= 12
            logs.append(f"{self.name} consumes 12 layers of TP (TP now: {self.transition_power}) to release Transition Skill.")

            for i in range(2):
                logs.append(f"Transition Skill Hit {i+1}:")
                logs.extend(hero_deal_damage(self, boss, self.atk * 15, is_active=True, team=team))

            boss.apply_buff("atk_down", {"value": 0.50, "rounds": 3})
            logs.append(f"{self.name}'s Transition Skill reduces {boss.name}'s attack by 50% for 3 rounds.")

            extra_from_hp = int(0.08 * boss.max_hp)
            cap_damage = int(self.atk * 15)
            extra_damage = min(extra_from_hp, cap_damage)
            boss.take_damage(extra_damage)
            logs.append(f"{self.name} deals an extra {extra_damage} damage from 8% of boss max HP (capped at 1500% ATK).")

            boss.apply_buff("atk_down_secondary", {"value": 0.15, "rounds": 2})
            logs.append(f"{self.name}'s Transition Skill further reduces {boss.name}'s attack by 15% for 2 rounds.")

            if boss.hp >= 0.50 * boss.max_hp:
                logs.append(f"{self.name} deals additional 1200% damage because boss HP ≥50%:")
                logs.extend(hero_deal_damage(self, boss, self.atk * 12, is_active=True, team=team))

            self.apply_buff("all_dmg_up", {"bonus": 15, "rounds": 2})
            logs.append(f"{self.name}'s all damage dealt is increased by 15% for 2 rounds.")
        return logs


