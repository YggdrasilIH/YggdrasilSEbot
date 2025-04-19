from .base import Hero
import random
from game_logic.damage_utils import hero_deal_damage
from game_logic.buff_handler import BuffHandler
from game_logic.control_effects import clear_control_effect

class PDE(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact)
        self.transition_power = 0
        self.energy = 0
        self.triggered_this_round = False

    def active_skill(self, boss, team):
        logs = []
        logs.append(f"{self.name} begins active skill.")
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs
        logs.extend(hero_deal_damage(self, boss, self.atk * 20, is_active=True, team=team))
        logs.append(f"{self.name} reduces {boss.name}'s energy by 50.")
        boss.energy = max(boss.energy - 50, 0)
        for ally in team.back_line:
            ally.apply_buff("mystical_veil", {"layers": 2, "rounds": 9999})
            ally.apply_buff("regen", {"heal_amount": int(self.atk * 5), "rounds": 2})
            logs.append(f"{self.name} grants mystical veil and regen to {ally.name}.")
        return logs

    def basic_attack(self, boss, team):
        logs = []
        logs.append(f"{self.name} begins basic attack.")
        if self.has_fear:
            logs.append(f"{self.name} is feared and fails basic attack.")
            return logs
        logs.extend(hero_deal_damage(self, boss, self.atk * 20, is_active=False, team=team))
        logs.append(f"{self.name} executes basic attack.")
        target = min([h for h in team.heroes if h.is_alive()], key=lambda h: h.hp, default=self)
        target.apply_buff("mystical_veil", {"layers": 1, "rounds": 9999})
        target.apply_buff("regen", {"heal_amount": int(self.atk * 12), "rounds": 2})
        logs.append(f"{self.name} grants mystical veil and regen to {target.name}.")
        return logs

    def passive_trigger(self, allies, boss, team):
        logs = []
        controlled = [h for h in allies if h.is_alive() and (h.has_fear or h.has_silence or h.has_seal_of_light)]
        to_cleanse = controlled[:2]

        for h in to_cleanse:
            effects = []
            if h.has_fear:
                effects.append("fear")
            if h.has_silence:
                effects.append("silence")
            if h.has_seal_of_light:
                effects.append("seal_of_light")

            if effects:
                chosen = random.choice(effects)
                logs.append(clear_control_effect(h, chosen))
                logs.append(f"{self.name} removes {chosen.replace('_', ' ').title()} from {h.name}.")

        for h in controlled:
            if h not in to_cleanse:
                logs.extend(BuffHandler.apply_buff(h, "control_resist", {
                    "attribute": "control_immunity", "bonus": 15, "rounds": 3
                }, boss))
                logs.append(f"{self.name} grants +15% Control Immunity to {h.name}.")

        logs.extend(BuffHandler.apply_debuff(boss, "speed_down", {
            "attribute": "speed", "bonus": -12, "rounds": 2
        }))
        logs.append(f"{self.name} reduces {boss.name}'s speed by 12 for 2 rounds.")
        return logs

    def on_receive_damage(self, damage, team, source):
        logs = []
        if source.lower() in ["basic", "active"] and not self.triggered_this_round:
            self.triggered_this_round = True
            if random.random() < 0.8:
                self.transition_power += 1
                logs.append(f"{self.name} gains 1 layer of Transition Power (now {self.transition_power}).")
            if self.transition_power >= 3:
                logs.extend(self.release_transition_skill(team, self.transition_power))
        return logs

    def release_transition_skill(self, team, tp_before_release):
        logs = []
        consume = 18 if tp_before_release >= 18 else 3
        self.transition_power -= consume
        logs.append(f"{self.name} consumes {consume} TP to release Transition Skill.")
        target = min([h for h in team.heroes if h.is_alive()], key=lambda h: h.hp, default=self)

        self.apply_buff("mystical_veil", {"layers": 1, "rounds": 2})
        target.apply_buff("mystical_veil", {"layers": 1, "rounds": 2})
        logs.append(f"{self.name} and {target.name} receive 1 layer of Mystical Veil for 2 rounds.")

        heal_amt = int(self.atk * 12)
        self.hp = min(self.max_hp, self.hp + heal_amt)
        target.hp = min(target.max_hp, target.hp + heal_amt)
        logs.append(f"{self.name} and {target.name} are healed for {heal_amt} HP each.")

        for hero in team.back_line:
            hero.apply_buff("hd_up", {"bonus": hero.hd * 0.10, "rounds": 2})
            logs.append(f"{hero.name} receives +10% HD for 2 rounds.")

        highest = max(team.heroes, key=lambda h: h.atk)
        highest.apply_buff("dmg_up", {"bonus": 15, "rounds": 2})
        logs.append(f"{highest.name} receives +15% damage for 2 rounds.")

        if tp_before_release >= 6:
            team.boss.apply_buff("atk_down", {"value": 0.20, "rounds": 2})
            logs.append(f"{team.boss.name}'s attack is reduced by 20% for 2 rounds.")
            for hero in team.back_line:
                hero.apply_buff("all_dmg_up", {"bonus": 20, "rounds": 3})
                logs.append(f"{hero.name} receives +20% all damage for 3 rounds.")

        return logs

    def on_end_of_round(self, team, boss):
        self.triggered_this_round = False
        return []
