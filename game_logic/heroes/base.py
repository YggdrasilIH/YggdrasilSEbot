# game_logic/heroes/base.py

import random
from math import floor
from game_logic.enables import ControlPurify, AttributeReductionPurify, MarkPurify, BalancedStrike, UnbendingWill
from game_logic.artifacts import Scissors, DB, Mirror, Antlers
from game_logic.cores import active_core
from game_logic.control_effects import apply_control_effect, clear_control_effect
from game_logic.buff_handler import BuffHandler

class Hero:
    
    def decrement_control_effects(self):
        for effect, rounds_attr in [("fear", "fear_rounds"), ("silence", "silence_rounds"), ("seal_of_light", "seal_rounds")]:
            rounds = getattr(self, rounds_attr, 0)
            if rounds > 0:
                rounds -= 1
                setattr(self, rounds_attr, rounds)
                if rounds <= 0:
                    setattr(self, f"has_{effect}", False)
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                purify_enable=None, trait_enable=None, artifact=None, lifestar=None):
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.atk = atk
        self.original_atk = atk
        self.armor = armor
        self.original_armor = armor
        self.spd = spd
        self.skill_damage = 0
        self.dodge = 0
        self.crit_rate = crit_rate
        self.crit_dmg = crit_dmg
        self.ctrl_immunity = ctrl_immunity  # ✅ Correct here
        self.hd = hd
        self.precision = precision
        self.dt_level = 0
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
        self.lifestar = lifestar
        self.all_damage_dealt = 0
        self.buffs = {}
        self.regen_buff = None
        self.poison_effects = []
        self.shield = 0
        self._healing_done = 0
        self._healing_rounds = []
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
        self.total_damage_dealt = 0
        self.purify_enable = purify_enable
        self.trait_enable = trait_enable
        self.bonus_damage_vs_poisoned = 0
        self._base_hd = self.hd
        self._base_precision = self.precision
        self._base_ctrl_immunity = self.ctrl_immunity
        self._base_dr = self.DR
        self._base_adr = self.ADR
        self._base_dodge = 0
        self._base_all_damage_dealt = self.all_damage_dealt
        self._base_spd = self.spd
        self._base_skill_damage = getattr(self, "skill_damage", 0)
        self._base_block = getattr(self, "block", 0)
        self._base_crit_rate = self.crit_rate
        self._base_crit_dmg = self.crit_dmg
        self._base_armor_break = getattr(self, "armor_break", 0)


        if self.artifact:
            self.artifact.owner = self
        if self.lifestar:
            self.lifestar.owner = self


    def set_enables(self, purify, trait):
        self.purify_enable = purify
        self.trait_enable = trait

    def recalculate_stats(self):
        """Recalculate current stats (ATK, HD, ADD, etc.) based on base stats + buffs."""
        # Reset to original BASE stats
        self.atk = self.original_atk
        self.armor = self.original_armor
        self.all_damage_dealt = 0
        self.hd = self._base_hd
        self.precision = self._base_precision
        self.ctrl_immunity = self._base_ctrl_immunity
        self.DR = self._base_dr
        self.ADR = self._base_adr
        self.spd = self._base_spd
        self.skill_damage = self._base_skill_damage
        self.block = self._base_block
        self.crit_rate = self._base_crit_rate
        self.crit_dmg = self._base_crit_dmg
        self.armor_break = self._base_armor_break
        self.dodge = self._base_dodge  # Reset first

        # Apply active buffs
        for buff in self.buffs.values():
            if isinstance(buff, dict):
                attr = buff.get("attribute")
                attr = buff.get("attribute", "").lower()
                val = buff.get("bonus", 0)

                if attr == "all_damage_dealt":
                    self.all_damage_dealt += val
                elif attr == "atk":
                    self.atk += val
                elif attr == "armor":
                    self.armor += val
                elif attr == "speed":
                    self.spd += val
                elif attr == "skill_damage":
                    self.skill_damage += val
                elif attr == "precision":
                    self.precision += val
                elif attr == "block":
                    self.block += val
                elif attr == "crit_rate":
                    self.crit_rate += val
                elif attr == "crit_dmg":
                    self.crit_dmg += val
                elif attr == "armor_break":
                    self.armor_break += val
                elif attr == "control_immunity":
                    self.ctrl_immunity += val
                elif attr == "dr":
                    self.DR += val
                elif attr == "hd":
                    self.hd += val
                elif attr == "adr":
                    self.ADR += val
                elif attr == "energy":
                    self.energy += val
                elif attr == "dodge":
                    self.dodge += val


        # Hardcaps
        if self.precision > 150:
            self.precision = 150
        if self.crit_dmg > 150:
            self.crit_dmg = 150


    def is_alive(self):
        return self.hp > 0

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
                alias = {
        "control_immunity": "ctrl_immunity",
        "crit_damage": "crit_dmg",
        "crit_rate": "crit_rate",
        "damage_reduction": "DR",
        "all_damage_reduction": "ADR",
        "atk": "atk",
        "armor": "armor",
        "precision": "precision",
        "hd": "hd",
        "spd": "spd",
        "healing_received": "healing_received",
        "all_damage_dealt": "all_damage_dealt"
    }
                real_attr = alias.get(attr, attr)
                if hasattr(self, real_attr):
                    setattr(self, real_attr, getattr(self, real_attr) - buff["bonus"])
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
            return f"☠️ {self.name}: {total_poison / 1e6:.0f}M Poison"
        return ""

    def apply_bleed(self, boss):
        if self.bleed_duration > 0 and self.bleed > 0:
            bleed_damage = self.bleed
            logs = boss.take_damage(bleed_damage, source_hero=self)
            self.bleed_duration -= 1
            label = f"🩸 {self.name} → {boss.name}: {bleed_damage / 1e6:.0f}M Bleed"
            if isinstance(logs, list):
                return logs + [label]
            return [label]
        return []

    def skill_multiplier(self, base_percent):
        energy_bonus = max(0, self.energy - 100)
        return base_percent + (self.skill_damage / 100) + (energy_bonus / 100)

    def process_regen_buffs(self):
        logs = []
        for name, buff in self.buffs.items():
            if "heal_amount" in buff and buff.get("rounds", 0) > 0:
                heal = buff["heal_amount"]
                before = self.hp
                self.hp = min(self.max_hp, self.hp + heal)
                actual = self.hp - before
                self._healing_done += actual
                logs.append(f"🩹 {self.name} heals {actual // 1_000_000}M via {name}.")
        return logs


    def end_of_round(self, boss, team, round_num):
        self.decrement_control_effects()

        self.recalculate_stats()
        messages = []
        messages.append(f"🔄 End-of-Round for {self.name}")

        self.process_buffs()
        if hasattr(self, "phoenix_burn_bonus_rounds") and self.phoenix_burn_bonus_rounds > 0:
            self.phoenix_burn_bonus_rounds -= 1


        poison_msg = self.process_poison()
        if poison_msg:
            messages.append(poison_msg)

        bleed_msg = self.apply_bleed(boss)
        if bleed_msg:
            messages.append(bleed_msg)

        messages.extend(BuffHandler.cap_stats(self))

        # ✅ Purify Enable (Control, Attribute Reduction, Mark)
        if self.purify_enable and hasattr(self.purify_enable, "apply_end_of_round"):
            purify_result = self.purify_enable.apply_end_of_round(self, boss)
            if purify_result:
                messages.append(purify_result)

        if self.artifact and hasattr(self.artifact, "apply_end_of_round"):
            artifact_logs = self.artifact.apply_end_of_round(self, team, boss, round_num)
            if artifact_logs:
                messages.extend(artifact_logs)
        messages.extend(self.process_regen_buffs())


        messages.append(f"📉 {self.get_status_description()}")
        return messages

    def apply_attribute_effect(self, effect, ratio):
        buff_value = effect.get("value", 0) * ratio
        current = getattr(self, effect.get("attribute", "atk"))
        setattr(self, effect.get("attribute", "atk"), current + buff_value)



    def add_shield(self, amount):
        before = self.shield
        self.shield = min(self.shield + amount, self.max_hp)
        return self.shield - before  # actual amount added

    def get_status_description(self):
        from collections import defaultdict

        status = f"{self.name} Status:  HP {self.hp / 1e6:.0f}M/{self.max_hp / 1e6:.0f}M | Energy {self.energy} | Ctrl Imm {self.ctrl_immunity}"
        status += f" | Calamity {self.calamity} | Curse {self.curse_of_decay}"

        attr_buffs = []
        attr_debuffs = []

        for buff in self.buffs.values():
            if isinstance(buff, dict) and "attribute" in buff and "bonus" in buff:
                val = buff["bonus"]
                label = buff["attribute"]
                if val > 0:
                    attr_buffs.append((label, val))
                elif val < 0:
                    attr_debuffs.append((label, val))

        # Add legacy reductions
        if self.atk_reduction:
            attr_debuffs.append(("atk", -self.atk_reduction * 100))
        if self.armor_reduction:
            attr_debuffs.append(("armor", -self.armor_reduction * 100))

        if attr_buffs:
            grouped = defaultdict(float)
            for attr, val in attr_buffs:
                grouped[attr] += val
            formatted = [f"+{int(v) if v.is_integer() else round(v, 1)}{k}" for k, v in grouped.items()]
            status += " | Buffs: " + ", ".join(formatted)

        if attr_debuffs:
            grouped = defaultdict(float)
            for attr, val in attr_debuffs:
                grouped[attr] += val
            formatted = [f"{int(v) if v.is_integer() else round(v, 1)}{k}" for k, v in grouped.items()]
            status += " | Debuffs: " + ", ".join(formatted)

        control_effects = []
        if self.has_silence:
            control_effects.append(f"Silence({self.silence_rounds})")
        if self.has_fear:
            control_effects.append(f"Fear({self.fear_rounds})")
        if self.has_seal_of_light:
            control_effects.append(f"Seal({self.seal_rounds})")

        if control_effects:
            icon_map = {
                "Silence": "🔇",
                "Fear": "😱",
                "Seal": "🔒"
            }
            styled = [f"{icon_map.get(effect.split('(')[0], '')}{effect}" for effect in control_effects]
            status += " | Ctrl: " + ", ".join(styled)

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
    def from_stats(cls, hero_id, stats, artifact=None, lifestar=None):
        from .sqh import SQH
        from .lfa import LFA
        from .mff import MFF
        from .ely import ELY
        from .lbrm import LBRM
        from .pde import PDE
        from .dgn import DGN
        hp, atk, spd = stats
        if hero_id == "hero_SQH_Hero":
            hero = SQH("SQH", hp, atk, armor=7000, spd=spd, crit_rate=10, crit_dmg=150,
                       ctrl_immunity=70, hd=0, precision=100, artifact=artifact, lifestar=lifestar)
        elif hero_id == "hero_LFA_Hero":
            hero = LFA("LFA", hp, atk, armor=4200, spd=spd, crit_rate=20, crit_dmg=150,
                       ctrl_immunity=70, hd=150, precision=150, artifact=artifact, lifestar=lifestar)
        elif hero_id == "hero_MFF_Hero":
            hero = MFF("MFF", hp, atk, armor=4000, spd=spd, crit_rate=8, crit_dmg=150,
                       ctrl_immunity=100, hd=0, precision=100, artifact=artifact, lifestar=lifestar)
        elif hero_id == "hero_ELY_Hero":
            hero = ELY("ELY", hp, atk, armor=5000, spd=spd, crit_rate=9, crit_dmg=150,
                       ctrl_immunity=80, hd=0, precision=100, artifact=artifact, lifestar=lifestar)
        elif hero_id == "hero_PDE_Hero":
            hero = PDE("PDE", hp, atk, armor=9000, spd=spd, crit_rate=11, crit_dmg=150,
                       ctrl_immunity=125, hd=0, precision=100, artifact=artifact, lifestar=lifestar)
        elif hero_id == "hero_LBRM_Hero":
            hero = LBRM("LBRM", hp, atk, armor=7000, spd=spd, crit_rate=10, crit_dmg=145,
                        ctrl_immunity=130, hd=0, precision=100, artifact=artifact, lifestar=lifestar)
        elif hero_id == "hero_DGN_Hero":
            hero = DGN("DGN", hp, atk, armor=12000, spd=spd, crit_rate=10, crit_dmg=150,
                       ctrl_immunity=80, hd=0, precision=100, artifact=artifact, lifestar=lifestar)
        else:
            hero = cls("Default", hp, atk, armor=1000, spd=spd, crit_rate=10, crit_dmg=150,
                       ctrl_immunity=100, hd=0, precision=100, artifact=artifact, lifestar=lifestar)
        hero.energy = 50
        return hero

    def take_damage(self, damage, source_hero=None, team=None):
        logs = []

        # Armor mitigation
        armor_reduction = min(self.armor / (100 * 20 + 180), 0.75)
        damage *= (1 - armor_reduction)

        # DR mitigation
        dr_reduction = min(self.DR / 100, 0.75)
        damage *= (1 - dr_reduction)

        # ADR mitigation
        adr_reduction = min(self.ADR / 100, 0.75)
        damage *= (1 - adr_reduction)

        # Round down to int after all reductions
        damage = int(damage)

        # Shield absorption
        if self.shield > 0:
            absorbed = min(self.shield, damage)
            self.shield -= absorbed
            damage -= absorbed
            logs.append(f"🛡️ {self.name} absorbs {absorbed // 1_000_000}M with shield.")

        # Unbending Will check
        if hasattr(self, "trait_enable") and hasattr(self.trait_enable, "prevent_death"):
            if self.trait_enable.prevent_death(self, damage):
                damage = self.hp - 1

        # Final HP application
        self.hp -= damage
        self.hp = max(self.hp, 0)

        logs.append(f"🔻 {self.name} takes {damage // 1_000_000}M damage.")
        return logs

    def with_basic_flag(self, damage_func):
        """Temporarily marks an action as a basic attack for counterattack logic."""
        self._current_action_type = "basic"
        try:
            return damage_func()
        finally:
            del self._current_action_type
