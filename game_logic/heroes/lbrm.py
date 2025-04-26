from .base import Hero
import random
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage
from game_logic.control_effects import clear_control_effect
from utils.log_utils import group_team_buffs

class LBRM(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None, lifestar=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact, lifestar=lifestar)
        self.transition_power = 0
        self.power_of_dream = 0
        self.ctrl_removal_limit = 1
        self.ctrl_removal_used = False

    def on_control_afflicted(self, target, effect):
        logs = []
        if self.has_seal_of_light or self.energy < 30 or not getattr(target, f"has_{effect}", False):
            return logs
        self.energy -= 30
        self.power_of_dream += 1
        logs.append(clear_control_effect(target, effect))
        target.shield += int(self.atk * 15)
        logs.append(f"🪽 {self.name} removes {effect.replace('_', ' ').title()} from {target.name} (manual Wings). Shield granted, +1 Power of Dream.")
        return logs

    def start_of_battle(self, team, boss):
        self.ctrl_removal_limit = 1
        self.ctrl_removal_used = False
        logs = [f"✨ {self.name} activates Mirror Magic (Wings, Magnification, Protection)."]
        logs.extend(self.apply_attribute_buff_with_curse("ctrl_immunity", 8, boss))
        logs.extend(self.apply_attribute_buff_with_curse("spd", 8, boss))
        logs.extend(self.apply_attribute_buff_with_curse("all_damage_dealt", 10, boss))
        self.shield += int(self.atk * 28)
        logs.append(f"🛡️ {self.name}: +{int(self.atk * 28 / 1e6):.0f}M Shield (Mirror Magic).")
        dr_bonus = 6 * 3
        logs.extend(self.apply_attribute_buff_with_curse("DR", dr_bonus, boss))
        self.wings_effect = self.magnification_effect = self.protection_effect = True
        return logs

    def basic_attack(self, boss, team):
        logs = []
        if getattr(self, "power_of_dream", 0) >= 2:
            self.power_of_dream = 0
            self.energy += 50
            return self.active_skill(boss, team)
        extra = min(int(0.15 * boss.hp), int(30 * self.atk))
        logs.extend(hero_deal_damage(self, boss, self.atk * 10, is_active=False, team=team))
        logs.append(f"➕ {self.name} deals additional {extra} flat damage from Magnification.")
        boss.hp -= extra
        return logs

    def active_skill(self, boss, team):
        if self.has_seal_of_light:
            return []
        self.ctrl_removal_limit = min(2, self.ctrl_removal_limit + 1)
        logs = []
        logs.extend(hero_deal_damage(self, boss, self.atk * 24, is_active=True, team=team))
        logs.append("🔻 Boss -15 Control Immunity (3 rounds).")
        boss.apply_buff("ctrl_immunity_down", {"decrease": 15, "rounds": 3})

        buffs_applied = []

        ally_wings = max(team.heroes, key=lambda h: h.spd)
        BuffHandler.apply_buff(ally_wings, "wings_buff", {"attribute": "spd", "bonus": 8, "rounds": 4})
        BuffHandler.apply_buff(ally_wings, "wings_ctrl", {"attribute": "ctrl_immunity", "bonus": 8, "rounds": 4})
        buffs_applied.append((ally_wings.name, "+8 SPD & +8 Control Immunity (Wings)"))
        ally_wings.wings_effect = True
        ally_wings.extra_ctrl_removals = min(getattr(ally_wings, "extra_ctrl_removals", 0) + 1, 2)
        ally_wings.wings_from_transition = False

        ally_mag = max(team.heroes, key=lambda h: h.atk)
        BuffHandler.apply_buff(ally_mag, "magnification_buff", {"attribute": "all_damage_dealt", "bonus": 10, "rounds": 4})
        buffs_applied.append((ally_mag.name, "+10% All Damage Dealt (Magnification)"))
        ally_mag.magnification_effect = True

        ally_prot = min(team.heroes, key=lambda h: h.hp)
        shield_amt = int(ally_prot.atk * 28)
        ally_prot.apply_buff("protection_shield", {"attribute": "shield", "shield": shield_amt, "rounds": 4})
        buffs_applied.append((ally_prot.name, f"+{shield_amt//1_000_000}M Shield (Protection)"))
        ally_prot.protection_effect = True

        self.transition_power += 6
        logs.append(f"✨ Gains 6 TP → {self.transition_power}.")
        if buffs_applied:
            logs.append("✨ Active Skill Buffs:")
            logs.extend(group_team_buffs(buffs_applied))

        return logs

    def release_transition_skill(self, boss, team):
        if self.has_seal_of_light:
            return []
        logs = []
        if self.transition_power < 6:
            logs.append(f"⚠️ {self.name} lacks TP for Transition Skill.")
            return logs
        self.transition_power -= 6
        logs.append(f"🔁 {self.name} uses Transition Skill (TP → {self.transition_power}).")

        calc_damage = int(boss.max_hp * 0.30)
        cap_damage = int(self.atk * 30)
        damage_to_deal = min(calc_damage, cap_damage)
        boss.take_damage(damage_to_deal)
        logs.append(f"💥 Deals {damage_to_deal / 1e6:.0f}M damage to Boss.")

        option = random.choice([1, 2, 3])
        buffs_applied = []

        if option == 1:
            for ally in team.heroes:
                if getattr(ally, "wings_effect", False):
                    bonus = ally.atk * 0.20
                    BuffHandler.apply_buff(ally, "wings_transition_atk_up", {"attribute": "atk", "bonus": int(bonus), "rounds": 2})
                    ally.extra_ctrl_removals = min(getattr(ally, "extra_ctrl_removals", 0) + 1, 2)
                    ally.wings_from_transition = True
                    buffs_applied.append((ally.name, "+20% ATK, +1 Control Removal (Wings Transition)"))
                    break
        elif option == 2:
            for ally in team.heroes:
                if getattr(ally, "magnification_effect", False):
                    BuffHandler.apply_buff(ally, "magnification_adr_up", {"attribute": "ADR", "bonus": 10, "rounds": 2})
                    heal_amt = int(0.33 * ally.max_hp)
                    ally.hp = min(ally.max_hp, ally.hp + heal_amt)
                    buffs_applied.append((ally.name, f"+10% ADR, +{heal_amt//1_000_000}M HP (Magnification Transition)"))
                    break
        elif option == 3:
            for ally in team.heroes:
                if getattr(ally, "protection_effect", False):
                    BuffHandler.apply_buff(ally, "bee_sugar_coat", {"attribute": "ctrl_immunity", "bonus": 50, "rounds": 9999})
                    buffs_applied.append((ally.name, "Bee Sugar-Coat (50% Control Immunity)") )
                    break

        for ally in team.back_line:
            BuffHandler.apply_buff(ally, "holy_dmg_up", {"attribute": "holy_damage", "bonus": 10, "rounds": 2})
            buffs_applied.append((ally.name, "+10% Holy Damage (Backline)"))

        best_ally = max(team.heroes, key=lambda h: h.atk)
        BuffHandler.apply_buff(best_ally, "dmg_up", {"attribute": "all_damage_dealt", "bonus": 15, "rounds": 2})
        buffs_applied.append((best_ally.name, "+15% All Damage Dealt (Best Ally)"))

        BuffHandler.apply_debuff(boss, "dmg_down", {"attribute": "all_damage_dealt", "bonus": -10, "rounds": 2})
        logs.append("🔻 Boss: -10% All Damage (2 rounds).")

        for ally in team.back_line:
            BuffHandler.apply_buff(ally, "backline_dmg_up", {"attribute": "all_damage_dealt", "bonus": 10, "rounds": 3})
            buffs_applied.append((ally.name, "+10% All Damage (Backline Extra)"))

        if buffs_applied:
            logs.append("✨ Transition Skill Buffs:")
            logs.extend(group_team_buffs(buffs_applied))

        return logs

    def end_of_round(self, boss, team, round_num):
        if self.has_seal_of_light:
            return super().end_of_round(boss, team, round_num)
        self.ctrl_removal_used = False
        logs = super().end_of_round(boss, team, round_num)
        if self.transition_power >= 6:
            logs.extend(self.release_transition_skill(boss, team))
        return logs

    def passive_trigger(self, ally, boss, team):
        if self.has_seal_of_light or self.ctrl_removal_used or self.ctrl_removal_limit <= 0:
            return []
        logs = []
        if any([ally.has_silence, ally.has_fear, ally.has_seal_of_light]) and self.energy >= 30:
            self.energy -= 30
            effects = [e for e in ["silence", "fear", "seal_of_light"] if getattr(ally, f"has_{e}", False)]
            if effects:
                chosen = random.choice(effects)
                logs.append(clear_control_effect(ally, chosen))
                logs.append(f"🪽 {self.name} removes {chosen.replace('_', ' ').title()} from {ally.name} (Wings). +1 Power of Dream, shield granted.")
                self.ctrl_removal_used = True
                self.ctrl_removal_limit -= 1
                self.power_of_dream += 1
                ally.apply_buff("lbrm_shield", {"attribute": "shield", "shield": int(self.atk * 15), "rounds": 1})
        return logs

    def after_attack(self, source, target, skill_type, team):
        logs = []
        if skill_type not in ["basic", "active"]:
            return logs
        for ally in team.heroes:
            if ally == source:
                continue
            if getattr(ally, "extra_ctrl_removals", 0) > 0:
                for teammate in team.heroes:
                    if teammate == ally or not teammate.is_alive():
                        continue
                    effects = [e for e in ["silence", "fear", "seal_of_light"] if getattr(teammate, f"has_{e}", False)]
                    if effects:
                        chosen = random.choice(effects)
                        logs.append(clear_control_effect(teammate, chosen))
                        logs.append(f"🪽 {ally.name} removes {chosen.replace('_', ' ').title()} from {teammate.name} (Wings).")
                        if not getattr(ally, "wings_from_transition", False):
                            teammate.energy += 30
                            logs.append(f"⚡ {teammate.name}: +30 Energy from Wings.")
                        ally.extra_ctrl_removals -= 1
                        break
        return logs
