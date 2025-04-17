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
        logs = []
        for ally in team.heroes:
            if ally != self:
                ally.queens_guard = True
                logs.extend(ally.apply_attribute_buff_with_curse("all_damage_dealt", 24, boss))
                logs.extend(ally.apply_attribute_buff_with_curse("ADR", 8, boss))
                logs.append(f"{ally.name} receives Queen’s Guard (+24% all damage, +8% ADR).")
        return logs

    def active_skill(self, boss, team):
        logs = []
        logs.append(f"{self.name} begins active skill.")
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
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
        logs.append(f"{self.name} begins basic attack.")
        if self.has_fear:
            logs.append(f"{self.name} is feared and cannot use basic attack.")
            return logs
        logs.extend(hero_deal_damage(self, boss, self.atk * 12, is_active=False, team=team))
        return logs

    def release_transition_skill(self, team, boss):
        logs = []
        self.transition_power -= 12
        logs.append(f"{self.name} consumes 12 TP to release Transition Skill (TP now: {self.transition_power}).")

        for ally in team.heroes:
            if getattr(ally, "queens_guard", False):
                bonus_atk = ally.atk * 0.10
                logs.extend(ally.apply_attribute_buff_with_curse("atk", bonus_atk, boss))
                heal_amt = int(ally.max_hp * 0.60)
                ally.hp = min(ally.max_hp, ally.hp + heal_amt)
                logs.append(f"{ally.name} (Queen's Guard) gets +10% ATK and is healed for {heal_amt} HP.")

        for ally in team.heroes:
            logs.extend(ally.apply_attribute_buff_with_curse("all_damage_dealt", 10, boss))
            logs.extend(ally.apply_attribute_buff_with_curse("ctrl_immunity", 20, boss))
            logs.extend(ally.apply_attribute_buff_with_curse("DR", 20, boss))
            if ally != self:
                if ally.curse_of_decay > 0:
                    damage = int(boss.atk * 30)
                    ally.hp -= damage
                    ally.curse_of_decay -= 1
                    logs.append(f"{ally.name} offsets Energy gain with Curse of Decay, taking {damage} damage.")
                else:
                    ally.energy += 20
                    logs.append(f"{ally.name} gains 20 energy.")
        logs.append("All allies gain +10% all damage, +20% control immunity, +20% DR, and +20 energy (or offset by Curse).")

        boss.apply_buff("atk_down", {"attribute": "atk", "bonus": -int(boss.atk * 0.15), "rounds": 2})
        logs.append("Boss attack reduced by 15% for 2 rounds.")

        heal_all = int(self.atk * 12)
        for ally in team.heroes:
            ally.hp = min(ally.max_hp, ally.hp + heal_all)
        logs.append(f"All allies healed for {heal_all} HP (1200% of {self.name}'s ATK).")

        return logs

    def take_damage(self, damage, source=None):
        self.hp -= damage
        self.hp = max(self.hp, 0)
        logs = []
        if hasattr(self, 'team') and source and source.is_alive():
            for ally in self.team.heroes:
                if ally != self and ally.is_alive() and getattr(ally, "queens_guard", False):
                    counter_dmg = int(ally.atk * 12)
                    source.hp -= counter_dmg
                    logs.append(f"👑 {ally.name} counterattacks {source.name} for {counter_dmg} damage.")
                    logs.extend(BuffHandler.apply_debuff(source, "atk_down", {
                        "attribute": "atk", "bonus": -int(source.atk * 0.03), "rounds": 2
                    }))
        return logs
