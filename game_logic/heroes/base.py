# game_logic/heroes/base.py

import random
from math import floor
from game_logic.enables import ControlPurify, AttributeReductionPurify, MarkPurify, BalancedStrike, UnbendingWill
from game_logic.artifacts import Scissors, DB, Mirror, Antlers
from game_logic.cores import active_core
from game_logic.control_effects import apply_control_effect, clear_control_effect
from game_logic.buff_handler import BuffHandler

class Hero:
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.atk = atk
        self.original_atk = atk
        self.armor = armor
        self.original_armor = armor
        self.spd = spd
        self.crit_rate = crit_rate
        self.crit_dmg = crit_dmg
        self.ctrl_immunity = ctrl_immunity
        self.hd = hd
        self.precision = precision
        self.energy = 50
        self.status_effects = set()
        self.has_silence = False
        self.silence_rounds = 0
        self.has_fear = False
        self.fear_rounds = 0
        self.has_seal_of_light = False
        self.seal_rounds = 0
        self.curse_of_decay = 0
        self.calamity = 0
        self.artifact = artifact
        self.all_damage_dealt = 0
        self.buffs = {}
        self.regen_buff = None
        self.poison_effects = []
        self.shield = 0
        self.DR = 35
        self.ADR = 8
        self.atk_reduction = 0
        self.armor_reduction = 0
        self.bleed = 0
        self.bleed_duration = 0
        self.mystical_veil = 0
        self.shadow_lurk = 0
        self.immune_control_effect = random.choice(["fear", "silence", "seal_of_light"])
        self.gk = False
        self.defier = False

    def set_enables(self, purify, trait):
        self.purify_enable = purify
        self.trait_enable = trait

    def is_alive(self):
        return self.hp > 0

    def apply_damage(self, damage, boss, team=None):
        if "boss_attack_debuff" in self.buffs:
            damage = int(damage * self.buffs["boss_attack_debuff"]["attack_multiplier"])
        crit = random.random() < (self.crit_rate / 100)
        if crit:
            damage *= (self.crit_dmg / 100)
        damage *= (1 + self.hd * 0.007) * (1 + min(self.precision, 150) * 0.003)
        damage *= (1 + self.all_damage_dealt / 100)

        if isinstance(self.trait_enable, BalancedStrike):
            heal_amt, dmg_bonus = self.trait_enable.apply_crit_bonus(damage, crit)
            damage += dmg_bonus
            self.hp = min(self.max_hp, self.hp + heal_amt)

        if getattr(self, "gk", False) and self.hp > 0:
            ratio = boss.hp / self.hp
            if ratio > 1:
                bonus_steps = floor((ratio - 1) / 0.10)
                bonus_multiplier = min(bonus_steps * 0.02, 1.0)
                damage = int(damage * (1 + bonus_multiplier))

        if getattr(self, "defier", False):
            if boss.hp >= 0.70 * boss.max_hp:
                damage = int(damage * 1.30)

        counter_logs = boss.take_damage(damage, source_hero=self, team=team)
        self.hp = max(self.hp, 0)
        return int(damage), f"{self.name} deals {int(damage)} ({'CRIT' if crit else 'Normal'}) damage.", counter_logs

    def apply_buff(self, buff_name, buff_data):
        self.buffs[buff_name] = buff_data

    def process_buffs(self):
        expired = []
        for buff in list(self.buffs.keys()):
            self.buffs[buff]["rounds"] -= 1
            if self.buffs[buff]["rounds"] <= 0:
                expired.append(buff)
        for buff_name in expired:
            buff = self.buffs[buff_name]
            if "attribute" in buff and "bonus" in buff:
                attr = buff["attribute"]
                setattr(self, attr, getattr(self, attr) - buff["bonus"])
            if "crit_rate_increase" in buff:
                self.crit_rate -= buff["crit_rate_increase"]
            if "crit_dmg_increase" in buff:
                self.crit_dmg -= buff["crit_dmg_increase"]
            del self.buffs[buff_name]
        if self.regen_buff:
            self.regen_buff["rounds"] -= 1
            if self.regen_buff["rounds"] <= 0:
                self.regen_buff = None

    def process_poison(self):
        total_poison = 0
        for effect in list(self.poison_effects):
            total_poison += effect["damage"]
            effect["rounds"] -= 1
            if effect["rounds"] <= 0:
                self.poison_effects.remove(effect)
        if total_poison > 0:
            self.hp -= total_poison
            self.hp = max(self.hp, 0)
            return f"{self.name} takes {total_poison} poison damage."
        return ""

    def apply_bleed(self, boss):
        if self.bleed_duration > 0 and self.bleed > 0:
            bleed_damage = self.bleed
            boss.take_damage(bleed_damage)
            self.bleed_duration -= 1
            return f"{self.name} deals {bleed_damage} bleed damage to {boss.name}."
        return None

    def process_calamity(self):
        messages = []
        if self.calamity >= 5:
            original_immunity = getattr(self, 'original_ctrl_immunity', 100)
            min_allowed = max(0, original_immunity - 100)
            self.ctrl_immunity = max(self.ctrl_immunity, min_allowed)

            duration = 2
            if active_core is not None:
                duration = active_core.modify_control_duration(duration)

            for effect in ["silence", "fear", "seal_of_light"]:
                if self.immune_control_effect == effect:
                    messages.append(f"{self.name} is immune to {effect.replace('_', ' ').title()}.")
                    clear_control_effect(self, effect)
                else:
                    msg = apply_control_effect(self, effect, duration)
                    messages.append(msg)

            messages.append(f"{self.name}'s control immunity reduced by 100. Calamity triggered.")
            self.calamity = 0
        return messages

    def end_of_round(self, boss, team, round_num):
        messages = []
        self.process_buffs()
        poison_msg = self.process_poison()
        if poison_msg:
            messages.append(poison_msg)
        bleed_msg = self.apply_bleed(boss)
        if bleed_msg:
            messages.append(bleed_msg)
        messages.extend(self.process_calamity())
        messages.extend(BuffHandler.cap_stats(self))
        if self.artifact and hasattr(self.artifact, "apply_end_of_round"):
            messages.extend(self.artifact.apply_end_of_round(self, team, boss, round_num))
        return messages

    def apply_attribute_effect(self, effect, ratio):
        buff_value = effect.get("value", 0) * ratio
        current = getattr(self, effect.get("attribute", "atk"))
        setattr(self, effect.get("attribute", "atk"), current + buff_value)

    def apply_attribute_buff_with_curse(self, attribute, buff_value, boss):
        messages = []
        if self.curse_of_decay > 0:
            damage = int(boss.atk * 30)
            self.hp -= damage
            self.hp = max(self.hp, 0)
            self.curse_of_decay -= 1
            messages.append(f"❌ Curse of Decay offsets {attribute} buff on {self.name}! Takes {damage} damage. (1 layer removed)")
        else:
            current = getattr(self, attribute)
            setattr(self, attribute, current + buff_value)
            messages.append(f"✅ {self.name} gains +{buff_value} {attribute}. (No Curse interference)")
        return messages

    def get_status_description(self):
        status = f"{self.name} Status:\n"
        status += f"  HP: {int(self.hp)}/{int(self.max_hp)}\n"
        status += f"  Energy: {self.energy}\n"
        status += f"  Control Immunity: {self.ctrl_immunity}\n"
        status += f"  Calamity: {self.calamity}\n"
        status += f"  Curse of Decay: {self.curse_of_decay}\n"
        if self.atk_reduction:
            status += f"  ATK Reduction: {self.atk_reduction*100:.0f}%\n"
        if self.armor_reduction:
            status += f"  Armor Reduction: {self.armor_reduction*100:.0f}%\n"
        control_effects = []
        if self.has_silence:
            control_effects.append(f"Silence ({self.silence_rounds} rounds)")
        if self.has_fear:
            control_effects.append(f"Fear ({self.fear_rounds} rounds)")
        if self.has_seal_of_light:
            control_effects.append(f"Seal of Light ({self.seal_rounds} rounds)")
        if control_effects:
            status += "  Control Effects: " + ", ".join(control_effects) + "\n"
        status += f"  Immune to: {self.immune_control_effect}\n"
        return status

    def trigger_foresight_basic(self):
        self.all_damage_dealt += 30
        self.energy += 50
        self.apply_buff("foresight_basic", {"attribute": "all_damage_dealt", "bonus": 30, "rounds": 15})
        return f"{self.name} gains Foresight (Basic): +30% damage for 15 rounds and +50 energy."

    def trigger_foresight_active(self):
        self.crit_rate += 30
        self.crit_dmg += 100
        self.apply_buff("foresight_active", {"crit_rate_increase": 30, "crit_dmg_increase": 100, "rounds": 2})
        return f"{self.name} gains Foresight (Active): +30% crit rate and +100% crit dmg for 2 rounds."

    @classmethod
    def from_stats(cls, hero_id, stats, artifact):
        from .sqh import SQH
        from .lfa import LFA
        from .mff import MFF
        from .ely import ELY
        from .lbrm import LBRM
        from .pde import PDE
        from .dgn import DGN
        hp, atk, spd = stats
        if hero_id == "hero_SQH_Hero":
            return SQH("SQH", hp, atk, armor=4000, spd=spd, crit_rate=10, crit_dmg=150,
                       ctrl_immunity=70, hd=0, precision=100, artifact=artifact)
        elif hero_id == "hero_LFA_Hero":
            return LFA("LFA", hp, atk, armor=1200, spd=spd, crit_rate=20, crit_dmg=150,
                       ctrl_immunity=70, hd=150, precision=150, artifact=artifact)
        elif hero_id == "hero_MFF_Hero":
            return MFF("MFF", hp, atk, armor=4000, spd=spd, crit_rate=8, crit_dmg=150,
                       ctrl_immunity=100, hd=0, precision=100, artifact=artifact)
        elif hero_id == "hero_ELY_Hero":
            return ELY("ELY", hp, atk, armor=5000, spd=spd, crit_rate=9, crit_dmg=150,
                       ctrl_immunity=80, hd=0, precision=100, artifact=artifact)
        elif hero_id == "hero_PDE_Hero":
            return PDE("PDE", hp, atk, armor=4000, spd=spd, crit_rate=11, crit_dmg=150,
                       ctrl_immunity=105, hd=0, precision=100, artifact=artifact)
        elif hero_id == "hero_LBRM_Hero":
            return LBRM("LBRM", hp, atk, armor=4000, spd=spd, crit_rate=10, crit_dmg=145,
                        ctrl_immunity=110, hd=0, precision=100, artifact=artifact)
        elif hero_id == "hero_DGN_Hero":
            return DGN("DGN", hp, atk, armor=4000, spd=spd, crit_rate=10, crit_dmg=150,
                       ctrl_immunity=80, hd=0, precision=100, artifact=artifact)
        else:
            return cls("Default", hp, atk, armor=1000, spd=spd, crit_rate=10, crit_dmg=150,
                       ctrl_immunity=100, hd=0, precision=100, artifact=artifact)
