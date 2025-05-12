from .base import Hero
import random
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage
from game_logic.control_effects import clear_control_effect
from utils.log_utils import group_team_buffs
from utils.log_utils import debug


class LBRM(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None, lifestar=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact, lifestar=lifestar)
        self.transition_power = 0
        self.power_of_dream = 0
        self.ctrl_removal_limit = 1
        self.ctrl_removal_used = False
        self.wings_effect = False
        self.magnification_effect = False
        self.protection_effect = False

    def handle_self_control_removal(self, effect, boss, team):
        logs = []

        # Re-check the status just before acting
        currently_afflicted = getattr(self, f"has_{effect}", False)

        print(f"[DEBUG-LBRM-CHECK] handle_self_control_removal: {effect} → Wings={self.wings_effect}, Used={self.ctrl_removal_used}, Seal={self.has_seal_of_light}, EffectPresent={currently_afflicted}")

        if (
            self.wings_effect
            and not self.ctrl_removal_used
            and not self.has_seal_of_light
            and currently_afflicted
        ):
            logs.append(clear_control_effect(self, effect))
            self.ctrl_removal_used = True
            self.energy += 30
            logs.append(f"🪽 {self.name} removes {effect.replace('_', ' ').title()} from herself (Mirror Wings). +30 Energy.")
            print(f"[DEBUG-CLEANSE] {self.name} successfully cleansed {effect} (Mirror Wings). Energy now {self.energy}.")
        else:
            print(f"[DEBUG-CLEANSE] {self.name} failed cleanse attempt → Wings={self.wings_effect}, Used={self.ctrl_removal_used}, Seal={self.has_seal_of_light}, EffectPresent={currently_afflicted}")

        return logs


    def on_control_afflicted(self, target, effect):
        logs = []

        if target == self:
            return logs  # Self-cleanse happens elsewhere

        if self.has_seal_of_light:
            return logs

        # Only cleanse if control is actually applied
        if not getattr(target, f"has_{effect}", False):
            return logs

        # Ensure we have enough energy to cleanse
        if self.energy < 30:
            return logs

        # Cleanse immediately
        self.energy -= 30
        self.power_of_dream += 1

        logs.append(clear_control_effect(target, effect))
        logs.append(f"🪽 {self.name} removes {effect.replace('_', ' ').title()} from {target.name} (manual Wings). Shield granted, +1 Power of Dream.")

        actual = target.add_shield(int(self.atk * 15))
        logs.append(f"🛡️ {target.name} gains {actual // 1_000_000}M shield (capped).")

        print(f"[DEBUG-CLEANSE] {self.name} triggered cleanse on ally: 🪽 {self.name} removes {effect} from {target.name} (Wings). +1 Power of Dream, shield granted.")

        return logs


    def start_of_battle(self, team, boss):
        self.ctrl_removal_limit = 1
        self.ctrl_removal_used = False
        logs = [f"✨ {self.name} activates Mirror Magic (Wings, Magnification, Protection)."]

        buffs_to_apply = [
            ("wings_ctrl_immunity", {"attribute": "control_immunity", "bonus": 8, "rounds": 999}),
            ("wings_speed", {"attribute": "spd", "bonus": 8, "rounds": 999}),
            ("magnification_add", {"attribute": "all_damage_dealt", "bonus": 10, "rounds": 999}),
            ("mirror_dr", {"attribute": "DR", "bonus": 6 * 3, "rounds": 999}),
        ]

        for name, data in buffs_to_apply:
            success, msg = BuffHandler.apply_buff(self, name, data, boss=boss)
            if msg:
                logs.append(msg)

        actual = self.add_shield(int(self.atk * 28))
        logs.append(f"🛡️ {self.name} gains {actual // 1_000_000}M shield (capped).")

        self.wings_effect = self.magnification_effect = self.protection_effect = True
        return logs


    def basic_attack(self, boss, team):
        
        if getattr(self, "power_of_dream", 0) >= 2:
            self.power_of_dream = 0
            self.energy += 50
            return self.active_skill(boss, team)

        def do_attack():
            logs = []
            debug(f"{self.name} starts BASIC attack")

            logs.extend(hero_deal_damage(
                self, boss, self.atk * (10 + self.skill_damage / 100),
                is_active=False, team=team, allow_counter=True
            ))

            extra = min(int(0.15 * boss.hp), int(30 * self.atk))
            logs.append(f"➕ {self.name} deals additional {extra} flat damage from Magnification.")
            boss.hp -= extra
            return logs

        return self.with_basic_flag(do_attack)

    def active_skill(self, boss, team):
        if self.has_seal_of_light:
            return []

        debug(f"{self.name} starts ACTIVE SKILL")

        self.ctrl_removal_limit = min(2, self.ctrl_removal_limit + 1)
        logs = []

        logs.extend(hero_deal_damage(
            self, boss, self.atk * (24 + self.skill_damage / 100),
            is_active=True, team=team, allow_counter=True
        ))

        logs.append("🔻 Boss -15 Control Immunity (3 rounds).")
        boss.apply_buff("ctrl_immunity_down", {"decrease": 15, "rounds": 3})

        buffs_applied = []
        # Dream Magic Wings
        ally_wings = max(team.heroes, key=lambda h: h.spd)
        BuffHandler.apply_buff(ally_wings, "wings_buff", {"attribute": "spd", "bonus": 8, "rounds": 4})
        BuffHandler.apply_buff(ally_wings, "wings_ctrl", {"attribute": "control_immunity", "bonus": 8, "rounds": 4})
        buffs_applied.append((ally_wings.name, "+8 SPD & +8 Control Immunity (Wings)"))
        ally_wings.wings_effect = True
        ally_wings.extra_ctrl_removals = min(getattr(ally_wings, "extra_ctrl_removals", 0) + 1, 2)
        ally_wings.wings_from_transition = False

        # Dream Magic Magnification
        ally_mag = max(team.heroes, key=lambda h: h.atk)
        BuffHandler.apply_buff(ally_mag, "magnification_buff", {"attribute": "all_damage_dealt", "bonus": 10, "rounds": 4})
        buffs_applied.append((ally_mag.name, "+10% All Damage Dealt (Magnification)"))
        ally_mag.magnification_effect = True

        # Dream Magic Protection
        ally_prot = min(team.heroes, key=lambda h: h.hp)
        shield_amt = int(ally_prot.atk * 28)
        ally_prot.apply_buff("protection_shield", {"attribute": "shield", "shield": shield_amt, "rounds": 4})
        buffs_applied.append((ally_prot.name, f"+{shield_amt // 1_000_000}M Shield (Protection)"))
        ally_prot.protection_effect = True

        self.transition_power += 6
        logs.append(f"✨ Gains 6 TP → {self.transition_power}.")

        if buffs_applied:
            logs.append("✨ Active Skill Buffs:")
            logs.extend(group_team_buffs(buffs_applied))

        # 🟡 NEW — trigger transition skill immediately if TP > 6
        if self.transition_power > 6:
            logs.extend(self.release_transition_skill(boss, team))

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
        boss.take_damage(damage_to_deal, source_hero=self, team=team, real_attack=False, bypass_modifiers=True)

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

        BuffHandler.apply_debuff(boss, "dmg_down", {"attribute": "damage_output", "bonus": -10, "rounds": 2})
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

        return logs

    def passive_trigger(self, ally, boss, team):
        logs = []

        print(f"[DEBUG-LBRM-PASSIVE] Attempting cleanse for {ally.name} → Seal={self.has_seal_of_light}, Energy={self.energy}")

        if self.has_seal_of_light:
            return logs

        # Skip if ally has Dream Magic Wings with control removal stacks available
        if any(getattr(ally, f"has_{e}", False) and getattr(ally, "extra_ctrl_removals", 0) > 0 for e in ["fear", "silence", "seal_of_light"]):
            print(f"[DEBUG-LBRM-PASSIVE] Skipping cleanse for {ally.name} — Effect present & Wings stack available")
            return logs


        if any([ally.has_silence, ally.has_fear, ally.has_seal_of_light]) and self.energy >= 30:
            effects = [e for e in ["silence", "fear", "seal_of_light"] if getattr(ally, f"has_{e}", False)]
            if effects:
                chosen = random.choice(effects)
                logs.append(clear_control_effect(ally, chosen))
                logs.append(f"🪽 {self.name} removes {chosen.replace('_', ' ').title()} from {ally.name} (Wings). +1 Power of Dream, shield granted.")
                self.power_of_dream += 1
                shield_value = int(self.atk * 15)
                actual = ally.add_shield(shield_value)
                logs.append(f"🛡️ {ally.name} gains {actual // 1_000_000}M shield (capped).")

        return logs
