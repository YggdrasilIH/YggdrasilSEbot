from .base import Hero
from game_logic.damage_utils import hero_deal_damage
from game_logic.buff_handler import BuffHandler
import random

class DGN(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None, lifestar=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact, lifestar=lifestar)
        self.undying_shadow = False
        self.bright_blessing = False
        self.transition_power = 0
        self.fluorescent_triggered = False

    def format_damage_log(self, amount):
        return f"{amount // 1_000_000}M dmg"

    def start_of_battle(self, team, boss):
        logs = []
        target = boss if not hasattr(boss, "heroes") else max(boss.heroes, key=lambda h: h.atk)
        target.undying_shadow = True
        logs.append(f"{self.name} inflicts Undying Shadow on {target.name} until battle ends.")

        top_ally = max([h for h in team.heroes if h.is_alive()], key=lambda h: h.atk)
        top_ally.bright_blessing = True
        logs.append(f"{self.name} grants Bright Blessing to {top_ally.name} until battle ends.")

        return logs

    def active_skill(self, boss, team):
        logs = [f"{self.name} begins active skill."]
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs

        base = self.atk * 14
        logs.extend(hero_deal_damage(self, boss, base, is_active=True, team=team, allow_counter=True, allow_crit=True))

        count = sum(1 for b in boss.buffs.values() if BuffHandler.is_attribute_reduction(b, strict=True))
        bonus = self.atk * 10 * count
        if bonus:
            logs.extend(hero_deal_damage(self, boss, bonus, is_active=True, team=team, allow_counter=False, allow_crit=True))

        total = base + bonus
        aoe = int(total * 0.7)
        for ally in team.heroes:
            if getattr(ally, "undying_shadow", False):
                ally.hp -= aoe
                logs.append(f"{self.name} deals {self.format_damage_log(aoe)} AOE damage to {ally.name} (Undying Shadow).")

        for h in [self] + [a for a in team.heroes if getattr(a, "bright_blessing", False) and a != self]:
            h.apply_buff("gg_atk", {"attribute": "atk", "bonus": int(h.atk * 0.16), "rounds": 2})
            h.apply_buff("gg_hd", {"attribute": "hd", "bonus": 20, "rounds": 2})
            h.apply_buff("gg_DR", {"attribute": "DR", "bonus": 16, "rounds": 2})
            h.apply_buff("gg_cd", {"attribute": "crit_dmg", "bonus": 20, "rounds": 2})
            heal = int(h.max_hp * 0.18)
            h.hp = min(h.max_hp, h.hp + heal)
            logs.append(f"{self.name} grants Guiding Glow to {h.name} for 2 rounds and heals {heal} HP.")

        self.transition_power += 6
        logs.append(f"{self.name} gains 6 TP from active skill (TP now: {self.transition_power}).")
        return logs

    def basic_attack(self, boss, team):
        logs = [f"{self.name} begins basic attack."]
        if self.has_fear:
            logs.append(f"{self.name} is feared and cannot perform basic attack.")
            return logs

        logs.extend(hero_deal_damage(self, boss, self.atk * 12, is_active=False, team=team, allow_counter=True, allow_crit=True))

        count = sum(1 for b in boss.buffs.values() if BuffHandler.is_attribute_reduction(b, strict=True))
        bonus = self.atk * 10 * count
        if bonus:
            logs.extend(hero_deal_damage(self, boss, bonus, is_active=False, team=team, allow_counter=False, allow_crit=True))

        total = self.atk * 12 + bonus
        shield = int(total * 0.5)
        for h in [self] + [a for a in team.heroes if getattr(a, "bright_blessing", False) and a != self]:
            h.shield += shield
            logs.append(f"{self.name} grants {self.format_damage_log(shield)} shield to {h.name}.")

        buffs = [(n, b) for n, b in self.buffs.items() if BuffHandler.is_attribute_buff(b)]
        replicate = random.sample(buffs, min(2, len(buffs)))
        for ally in team.heroes:
            if getattr(ally, "bright_blessing", False):
                for name, buff in replicate:
                    ally.apply_buff(f"replicated_{name}", buff.copy())
                    logs.append(f"{self.name} replicates {name} to {ally.name}.")

        boss.apply_buff("armor_down", {"attribute": "armor", "bonus": -0.18, "rounds": 2})
        boss.apply_buff("block_down", {"attribute": "block", "bonus": -0.18, "rounds": 2})
        logs.append(f"{self.name} reduces {boss.name}'s Armor and Block by 18% for 2 rounds.")

        for h in [self] + [a for a in team.heroes if getattr(a, "bright_blessing", False) and a != self]:
            if random.random() < 0.5:
                reducible = [(n, b) for n, b in h.buffs.items() if BuffHandler.is_attribute_reduction(b)]
                if reducible:
                    to_remove = random.choice(reducible)
                    del h.buffs[to_remove[0]]
                    logs.append(f"{self.name} removes attribute reduction '{to_remove[0]}' from {h.name}.")

        return logs

    def end_of_round(self, boss, team, round_num=None):
        logs = []
        if self.transition_power < 12:
            return logs

        self.transition_power -= 12
        logs.append(f"{self.name} consumes 12 TP to trigger FULL transition skill.")

        targets = [boss] if not hasattr(boss, "heroes") else boss.heroes
        for enemy in targets:
            enemy.apply_buff("full_atk_down", {"attribute": "atk", "bonus": -0.5, "rounds": 3})
            enemy.apply_buff("full_crit_down", {"attribute": "crit_rate", "bonus": -0.5, "rounds": 3})
            enemy.apply_buff("full_ctrl_immunity_down", {"attribute": "control_immunity", "bonus": -0.5, "rounds": 3})
            logs.append(f"{enemy.name} receives -50% ATK, -50% Crit Rate, -50% Control Immunity for 3 rounds.")

            debuff_count = sum(1 for b in enemy.buffs.values() if isinstance(b, dict))
            bonus = self.atk * 20 * debuff_count
            logs.extend(hero_deal_damage(self, enemy, bonus, is_active=True, team=team, allow_counter=False, allow_crit=False))

        target = min(targets, key=lambda e: e.hp if e.is_alive() else float('inf'))
        if target and target.is_alive():
            count = sum(1 for b in target.buffs.values() if isinstance(b, dict))
            bonus = self.atk * 6 * count
            logs.extend(hero_deal_damage(self, target, bonus, is_active=True, team=team, allow_counter=False, allow_crit=False))

        top_enemy = max(targets, key=lambda e: e.atk if e.is_alive() else -1)
        removable = [n for n, d in top_enemy.buffs.items() if isinstance(d, dict) and BuffHandler.is_attribute_buff(d, strict=True)]
        if removable:
            removed = random.choice(removable)
            del top_enemy.buffs[removed]
            logs.append(f"{self.name} removes buff '{removed}' from {top_enemy.name}.")

        for ally in team.heroes:
            applied, msg = BuffHandler.apply_buff(ally, "transition_crit_dmg_up", {"attribute": "crit_dmg", "bonus": 50, "rounds": 2}, boss)
            if applied:
                logs.append(f"{ally.name} gains +50% Crit Damage for 2 rounds from {self.name}'s transition skill.")
            elif msg:
                logs.append(msg)

        if random.random() < 0.5:
            for ally in team.heroes:
                ally.energy += 20
                logs.append(f"{ally.name} gains +20 energy from {self.name}'s transition skill.")

        return logs

    def on_receive_damage(self, damage, team, source):
        logs = []
        if getattr(source, "is_alive", lambda: False)() and hasattr(damage, "source_type") and damage.source_type in ["basic", "active"]:
            logs.append(f"{self.name} retaliates against {source.name} for using {damage.source_type} skill.")
            logs.extend(hero_deal_damage(self, source, self.atk * 10, is_active=False, team=team, allow_counter=False, allow_crit=False))
            source.apply_buff("crit_down", {"attribute": "crit_rate", "bonus": -28, "rounds": 2})
            source.apply_buff("atk_down", {"attribute": "atk", "bonus": -0.06, "rounds": 4})

            for ally in team.heroes:
                if ally != self and getattr(ally, "bright_blessing", False) and ally.is_alive():
                    logs.append(f"{ally.name} retaliates against {source.name} for being hit.")
                    logs.extend(hero_deal_damage(ally, source, ally.atk * 10, is_active=False, team=team, allow_counter=False, allow_crit=False))
                    source.apply_buff("crit_down", {"attribute": "crit_rate", "bonus": -28, "rounds": 2})

        if not self.fluorescent_triggered and self.hp / self.max_hp < 0.5:
            self.fluorescent_triggered = True
            heal = int(self.max_hp * 0.25)
            shield = int(self.max_hp * 0.25)
            self.hp = min(self.max_hp, self.hp + heal)
            self.shield += shield
            self.apply_buff("holy_dmg_up", {"attribute": "hd", "bonus": 20, "rounds": 6})
            self.apply_buff("damage_reduction_up", {"attribute": "DR", "bonus": 0.30, "rounds": 2})
            self.apply_buff("healing_received_up", {"attribute": "healing_received", "bonus": 0.50, "rounds": 2})
            logs.append(f"{self.name} activates Fluorescent Shield: heals {self.format_damage_log(heal)}, gains {self.format_damage_log(shield)} shield, +20% holy damage.")

        for ally in team.heroes:
            if getattr(ally, "bright_blessing", False) and not getattr(ally, "fluorescent_triggered", False):
                if ally.hp / ally.max_hp < 0.5:
                    ally.fluorescent_triggered = True
                    heal = int(ally.max_hp * 0.25)
                    shield = int(ally.max_hp * 0.25)
                    ally.hp = min(ally.max_hp, ally.hp + heal)
                    ally.shield += shield
                    ally.apply_buff("holy_dmg_up", {"attribute": "hd", "bonus": 20, "rounds": 6})
                    ally.apply_buff("damage_reduction_up", {"attribute": "DR", "bonus": 0.30, "rounds": 2})
                    ally.apply_buff("healing_received_up", {"attribute": "healing_received", "bonus": 0.50, "rounds": 2})
                    logs.append(f"{ally.name} activates Fluorescent Shield: heals {self.format_damage_log(heal)}, gains {self.format_damage_log(shield)} shield, +20% holy damage.")

        return logs
