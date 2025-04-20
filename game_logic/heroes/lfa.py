from .base import Hero
from game_logic.damage_utils import hero_deal_damage
import random
from math import floor
from game_logic.buff_handler import BuffHandler

class LFA(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None, lifestar=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact, lifestar=lifestar)
        self.transition_power = 0

    def active_skill(self, boss, team):
        logs = [f"💥 {self.name} uses Active Skill:"]
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs

        total_damage = 0
        for i in range(2):
            dmg = self.atk * 12
            logs.extend(hero_deal_damage(self, boss, dmg, is_active=True, team=team, allow_counter=(i == 0), allow_crit=True))
            total_damage += dmg

        if boss.hp < boss.max_hp * 0.60:
            second_total = 0
            for i in range(2):
                dmg = self.atk * 12
                logs.append(f"🗡️ {self.name} deals {dmg // 1_000_000}M base damage (extra hit {i+1}/2).")
                logs.extend(hero_deal_damage(self, boss, dmg, is_active=True, team=team, allow_counter=False, allow_crit=True))
                second_total += dmg
                total_damage += dmg
            heal_amt = int(second_total * 1.20)
            self.hp = min(self.max_hp, self.hp + heal_amt)
            logs.append(f"❤️ {self.name} heals for {heal_amt // 1_000_000}M HP from extra attacks.")

        dmg = self.atk * 12
        logs.extend(hero_deal_damage(self, boss, dmg, is_active=True, team=team, allow_counter=False, allow_crit=True))
        total_damage += dmg

        bonus_damage = int(total_damage * 1.20)
        logs.append(f"💣 {self.name} unleashes {bonus_damage // 1_000_000}M bonus burst damage.")
        logs.extend(hero_deal_damage(self, boss, bonus_damage, is_active=True, team=team, allow_counter=False, allow_crit=False))

        self.transition_power += 6
        logs.append(f"{self.name} gains 6 layers of Transition Power (TP now: {self.transition_power}).")

        if self.transition_power >= 12:
            logs.extend(self.release_transition_skill(boss, team))

        return logs

    def basic_attack(self, boss, team):
        logs = [f"🔪 {self.name} uses Basic Attack:"]
        if self.has_fear:
            logs.append(f"{self.name} is feared and cannot perform basic attack.")
            return logs

        dmg = int(self.atk * 9.6)
        logs.extend(hero_deal_damage(self, boss, dmg, is_active=False, team=team, allow_counter=True, allow_crit=True))
        logs.extend(self.apply_attribute_buff_with_curse("crit_rate", 24, boss))

        return logs

    def release_transition_skill(self, boss, team):
        logs = []
        if self.transition_power >= 12:
            self.transition_power -= 12
            logs.append(f"🔄 {self.name} activates Transition Skill (TP -12 → {self.transition_power}).")

            total_damage = 0
            for i in range(2):
                dmg = self.atk * 15
                total_damage += dmg
                logs.extend(hero_deal_damage(self, boss, dmg, is_active=True, team=team, allow_counter=False, allow_crit=True))

            logs.extend(BuffHandler.apply_debuff(boss, "atk_down", {"attribute": "atk", "bonus": -0.5, "rounds": 3}))
            logs.append(f"🔻 {boss.name} loses 50% ATK for 3 rounds.")

            extra_from_hp = int(0.08 * boss.max_hp)
            cap_damage = int(self.atk * 15)
            extra_damage = min(extra_from_hp, cap_damage)
            total_damage += extra_damage
            logs.append(f"💥 {self.name} deals {extra_damage // 1_000_000}M based on 8% of boss max HP (capped at 1500% ATK).")

            logs.extend(BuffHandler.apply_debuff(boss, "atk_down_secondary", {"attribute": "atk", "bonus": -0.15, "rounds": 2}))
            logs.append(f"🔻 {boss.name} loses 15% ATK for 2 rounds.")

            if boss.hp >= 0.50 * boss.max_hp:
                bonus_dmg = self.atk * 12
                total_damage += bonus_dmg
                logs.append(f"💢 {self.name} deals +1200% bonus damage because Boss HP ≥ 50%.")

            logs.extend(hero_deal_damage(self, boss, total_damage, is_active=True, team=team, allow_counter=False, allow_crit=False))

            self.apply_buff("all_dmg_up", {"bonus": 15, "rounds": 2})
            logs.append(f"✅ {self.name} gains +15 all_damage_dealt for 2 rounds.")

        return logs
