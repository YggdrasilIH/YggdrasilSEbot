from .base import Hero
from game_logic.damage_utils import hero_deal_damage
from game_logic.buff_handler import BuffHandler
import random

class DGN(Hero):
    def on_end_of_round(self, team, boss):
        # Begin Fluorescent Shield processing
        shield_logs = []
        enemies = [boss] if not hasattr(boss, "heroes") else boss.heroes

        if self.transition_power >= 12:
            self.transition_power -= 12
            logs.append(f"{self.name} consumes 12 TP to trigger FULL transition skill.")
            for enemy in enemies:
                enemy.apply_buff("full_atk_down", {"attribute": "atk", "bonus": -0.5, "rounds": 3})
                enemy.apply_buff("full_crit_down", {"attribute": "crit_rate", "bonus": -0.5, "rounds": 3})
                enemy.apply_buff("full_ctrl_immunity_down", {"attribute": "control_immunity", "bonus": -0.5, "rounds": 3})
                logs.append(f"{enemy.name} receives -50% ATK, -50% Crit Rate, -50% Control Immunity for 3 rounds.")

                debuff_count = sum(
                    1 for buff in enemy.buffs.values()
                    if isinstance(buff, dict) and ("attribute" in buff or "bonus" in buff)
                )
                extra_damage = self.atk * 20 * debuff_count
                logs.append(f"{self.name} deals {extra_damage} bonus damage to {enemy.name} based on {debuff_count} debuffs.")
                logs.extend(hero_deal_damage(self, enemy, extra_damage, is_active=True, team=team))

            # Deal 600% ATK damage for each debuff to the enemy with the lowest HP
            target = min(enemies, key=lambda e: e.hp if e.is_alive() else float('inf'))
            if target and target.is_alive():
                debuff_count = sum(
                    1 for buff in target.buffs.values()
                    if isinstance(buff, dict) and ("attribute" in buff or "bonus" in buff)
                )
                bonus_damage = self.atk * 6 * debuff_count
                logs.append(f"{self.name} deals {bonus_damage} additional damage to lowest HP target {target.name} from {debuff_count} debuffs.")
                logs.extend(hero_deal_damage(self, target, bonus_damage, is_active=True, team=team))

            # Remove 1 random buff from enemy with highest ATK
            top_enemy = max(enemies, key=lambda e: e.atk if e.is_alive() else -1)
            if top_enemy and top_enemy.buffs:
                removable = list(top_enemy.buffs.keys())
                removed = random.choice(removable)
                del top_enemy.buffs[removed]
                logs.append(f"{self.name} removes buff '{removed}' from {top_enemy.name}.")

            # 50% chance to give all allies +20 energy
            # Also increase all allies' crit damage by 50% for 2 rounds
            for ally in team.heroes:
                ally.apply_buff("transition_crit_dmg_up", {"attribute": "crit_dmg", "bonus": 50, "rounds": 2})
                logs.append(f"{ally.name} gains +50% Crit Damage for 2 rounds from DGN's transition skill.")
            if random.random() < 0.5:
                for ally in team.heroes:
                    ally.energy += 20
                    logs.append(f"{ally.name} gains +20 energy from DGN's transition skill.")

                return logs + shield_logs
    def on_receive_damage(self, damage, team, source):
        logs = []

        # Passive retaliation for DGN and Bright Blessing ally
        if source and hasattr(source, "is_alive") and source.is_alive():
            if damage.source_type in ["basic", "active"]:
                if self.hp > 0:
                    logs.append(f"{self.name} retaliates against {source.name} for using {damage.source_type} skill.")
                    logs.extend(hero_deal_damage(self, source, self.atk * 10, is_active=False, team=team))
                    source.apply_buff("crit_down", {"attribute": "crit_rate", "bonus": -28, "rounds": 2})
                    source.apply_buff("atk_down", {"attribute": "atk", "bonus": -0.06, "rounds": 4})
                    source.apply_buff("atk_down", {"attribute": "atk", "bonus": -0.06, "rounds": 4})
                    logs.append(f"{source.name}'s Crit Rate reduced by 28% for 2 rounds.")

                for ally in team.heroes:
                    if ally != self and getattr(ally, "bright_blessing", False) and ally.hp > 0:
                        logs.append(f"{ally.name} retaliates against {source.name} for being hit.")
                        logs.extend(hero_deal_damage(ally, source, ally.atk * 10, is_active=False, team=team))
                        source.apply_buff("crit_down", {"attribute": "crit_rate", "bonus": -28, "rounds": 2})
                        logs.append(f"{source.name}'s Crit Rate reduced by 28% by {ally.name}.")
        logs = []
        if not hasattr(self, "fluorescent_triggered"):
            self.fluorescent_triggered = False
        if not self.fluorescent_triggered and self.hp / self.max_hp < 0.5:
            self.fluorescent_triggered = True
            heal = int(self.max_hp * 0.25)
            shield = int(self.max_hp * 0.25)
            self.hp = min(self.max_hp, self.hp + heal)
            self.shield += shield
            self.apply_buff("holy_dmg_up", {"bonus": 20, "rounds": 6})
            self.apply_buff("damage_reduction_up", {"attribute": "DR", "bonus": 0.30, "rounds": 2})
            self.apply_buff("healing_received_up", {"bonus": 0.50, "rounds": 2})
            logs.append(f"{self.name} activates Fluorescent Shield: heals {heal}, gains {shield} shield, +20% holy damage.")

        for ally in team.heroes:
            if getattr(ally, "bright_blessing", False):
                if not hasattr(ally, "fluorescent_triggered"):
                    ally.fluorescent_triggered = False
                if not ally.fluorescent_triggered and ally.hp / ally.max_hp < 0.5:
                    ally.fluorescent_triggered = True
                    heal = int(ally.max_hp * 0.25)
                    shield = int(ally.max_hp * 0.25)
                    ally.hp = min(ally.max_hp, ally.hp + heal)
                    ally.shield += shield
                    ally.apply_buff("holy_dmg_up", {"bonus": 20, "rounds": 6})
                    ally.apply_buff("damage_reduction_up", {"attribute": "DR", "bonus": 0.30, "rounds": 2})
                    ally.apply_buff("healing_received_up", {"bonus": 0.50, "rounds": 2})
                    logs.append(f"{ally.name} activates Fluorescent Shield: heals {heal}, gains {shield} shield, +20% holy damage.")
        return logs
    def start_of_battle(self, team, boss):
        logs = []

        # Apply Undying Shadow to enemy with highest ATK
        enemy_team = [boss] if not hasattr(boss, "heroes") else boss.heroes
        if enemy_team:
            target = max(enemy_team, key=lambda h: h.atk)
            target.undying_shadow = True
            logs.append(f"{self.name} inflicts Undying Shadow on {target.name} until battle ends.")

        # Apply Bright Blessing to ally with highest ATK
        allies = [h for h in team.heroes if h.is_alive()]
        if allies:
            top_ally = max(allies, key=lambda h: h.atk)
            top_ally.bright_blessing = True
            logs.append(f"{self.name} grants Bright Blessing to {top_ally.name} until battle ends.")

        return logs
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact)
        self.undying_shadow = False
        self.bright_blessing = False
        self.transition_power = 0

    def active_skill(self, boss, team):
        logs = [f"{self.name} begins active skill."]
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs

        logs.extend(hero_deal_damage(self, boss, self.atk * 14, is_active=True, team=team))

        reduction_count = sum(
            1 for buff in boss.buffs.values()
            if isinstance(buff, dict) and 'attribute' in buff and BuffHandler.is_attribute_reduction(buff)
        )
        bonus_damage = self.atk * 10 * reduction_count
        if bonus_damage > 0:
            logs.append(f"{self.name} gains bonus damage for {reduction_count} attribute reductions.")
            logs.extend(hero_deal_damage(self, boss, bonus_damage, is_active=True, team=team))

        total_damage = self.atk * 14 + bonus_damage
        aoe_damage = int(total_damage * 0.70)
        for ally in team.heroes:
            if getattr(ally, "undying_shadow", False):
                ally.hp -= aoe_damage
                logs.append(f"{self.name} deals {aoe_damage} AOE damage to {ally.name} (Undying Shadow).")

        targets = [self] + [h for h in team.heroes if getattr(h, "bright_blessing", False)]
        for target in targets:
            target.apply_buff("guiding_glow", {
                "attack": 0.16,
                "hd": 0.20,
                "damage_reduction": 0.16,
                "crit_dmg": 0.20,
                "rounds": 2
            })
            heal_amt = int(target.max_hp * 0.18)
            target.hp = min(target.max_hp, target.hp + heal_amt)
            logs.append(f"{self.name} grants Guiding Glow to {target.name} for 2 rounds and heals {heal_amt} HP.")

        own_reductions = [
            (name, buff) for name, buff in self.buffs.items()
            if BuffHandler.is_attribute_reduction(buff)
        ]
        replicated = random.sample(own_reductions, min(2, len(own_reductions)))
        for enemy in team.heroes:
            if getattr(enemy, "undying_shadow", False):
                for name, buff in replicated:
                    enemy.apply_buff(f"replicated_{name}", {
                        "attribute": buff["attribute"],
                        "bonus": buff["bonus"],
                        "rounds": buff["rounds"]
                    })
                    logs.append(f"{self.name} replicates {name} to {enemy.name} (Undying Shadow).")

        lost_hp = boss.max_hp - boss.hp
        extra_damage = min(int(lost_hp * 0.30), int(self.atk * 15))
        if extra_damage > 0:
            logs.append(f"{self.name} deals {extra_damage} extra damage based on boss's lost HP (capped at 1500% ATK).")
            logs.extend(hero_deal_damage(self, boss, extra_damage, is_active=True, team=team))

        return logs

    def after_attack(self, source, target, skill_type, team):
        logs = []
        if skill_type not in ["basic", "active"]:
            return logs

        if getattr(target, "undying_shadow", False):
            attribute_reductions = [
                (name, buff) for name, buff in target.buffs.items()
                if BuffHandler.is_attribute_reduction(buff)
            ]
            replicated = random.sample(attribute_reductions, min(2, len(attribute_reductions)))
            for name, buff in replicated:
                target.apply_buff(f"replicated_{name}", {
                    "attribute": buff["attribute"],
                    "bonus": buff["bonus"],
                    "rounds": buff["rounds"]
                })
                logs.append(f"{source.name} replicates {name} back onto {target.name}.")
        return logs

    def basic_attack(self, boss, team):
        logs = [f"{self.name} begins basic attack."]
        if self.has_fear:
            logs.append(f"{self.name} is feared and cannot perform basic attack.")
            return logs

        # Initial hit
        logs.extend(hero_deal_damage(self, boss, self.atk * 12, is_active=True, team=team))

        # Bonus damage for each attribute reduction on the boss
        reduction_count = sum(
            1 for buff in boss.buffs.values()
            if isinstance(buff, dict) and 'attribute' in buff and BuffHandler.is_attribute_reduction(buff)
        )
        bonus_damage = self.atk * 10 * reduction_count
        if bonus_damage > 0:
            logs.append(f"{self.name} gains bonus damage for {reduction_count} attribute reductions.")
            logs.extend(hero_deal_damage(self, boss, bonus_damage, is_active=True, team=team))

        # Grant shield equal to 50% of total damage dealt to self and Bright Blessing allies
        total_damage = self.atk * 12 + bonus_damage
        shield_value = int(total_damage * 0.50)
        for hero in [self] + [h for h in team.heroes if getattr(h, "bright_blessing", False)]:
            hero.shield += shield_value
            logs.append(f"{self.name} grants {shield_value} shield to {hero.name}.")

        # Replicate 2 random attribute buffs from self to Bright Blessing allies
        attribute_buffs = [
            (name, buff) for name, buff in self.buffs.items()
            if BuffHandler.is_attribute_buff(buff)
        ]
        replicated = random.sample(attribute_buffs, min(2, len(attribute_buffs)))
        for ally in team.heroes:
            if getattr(ally, "bright_blessing", False):
                for name, buff in replicated:
                    ally.apply_buff(f"replicated_{name}", {
                        "attribute": buff["attribute"],
                        "bonus": buff["bonus"],
                        "rounds": buff["rounds"]
                    })
                    logs.append(f"{self.name} replicates {name} to {ally.name}.")

        # Reduce armor and block of the boss by 18% for 2 rounds
        boss.apply_buff("armor_down", {"attribute": "armor", "bonus": -0.18, "rounds": 2})
        boss.apply_buff("block_down", {"attribute": "block", "bonus": -0.18, "rounds": 2})
        logs.append(f"{self.name} reduces {boss.name}'s Armor and Block by 18% for 2 rounds.")

        # 50% chance to remove one attribute reduction from self and from one Bright Blessing ally
        for hero in [self] + [h for h in team.heroes if getattr(h, "bright_blessing", False)]:
            if random.random() < 0.5:
                reducible = [
                    (name, buff) for name, buff in hero.buffs.items()
                    if BuffHandler.is_attribute_reduction(buff)
                ]
                if reducible:
                    to_remove = random.choice(reducible)
                    del hero.buffs[to_remove[0]]
                    logs.append(f"{self.name} removes attribute reduction '{to_remove[0]}' from {hero.name}.")

        return logs
