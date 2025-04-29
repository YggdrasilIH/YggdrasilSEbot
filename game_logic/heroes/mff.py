from .base import Hero
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage
from utils.log_utils import group_team_buffs

class MFF(Hero):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evolutionary_factor = 0
        self.permanent_ef3_bonus_active = False

    def add_or_update_buff(self, hero, buff_name, buff_data):
        if buff_name in hero.buffs:
            existing = hero.buffs[buff_name]
            if "bonus" in buff_data:
                existing["bonus"] += buff_data.get("bonus", 0)
            if "heal_amount" in buff_data:
                existing["heal_amount"] += buff_data.get("heal_amount", 0)
            if "shield" in buff_data:
                existing["shield"] += buff_data.get("shield", 0)
        else:
            hero.apply_buff(buff_name, buff_data)

    def active_skill(self, boss, team):
        logs = []
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs

        logs.extend(hero_deal_damage(self, boss, self.atk * (16+self.skill_damage), is_active=True, team=team))

        poison_damage = int(self.atk * (12+self.skill_damage/100))
        logs.append(f"☠️ Applies Poison: {poison_damage} for 3 rounds.")
        logs.extend(BuffHandler.apply_debuff(boss, "poison", {
            "attribute": "poison", "damage": poison_damage, "rounds": 3
        }))

        # Find all ATK and HD buffs
        atk_buffs = [name for name, data in boss.buffs.items()
                    if isinstance(data, dict) and data.get("attribute") == "atk"]
        hd_buffs = [name for name, data in boss.buffs.items()
                    if isinstance(data, dict) and data.get("attribute") == "HD"]

        # Remove ALL ATK buffs
        for buff_name in atk_buffs:
            buff = boss.buffs.pop(buff_name, None)
            if buff:
                boss.atk -= buff.get("bonus", 0)

        # Remove ALL HD buffs
        for buff_name in hd_buffs:
            buff = boss.buffs.pop(buff_name, None)
            if buff:
                boss.hd -= buff.get("bonus", 0)

        removed_buffs = atk_buffs + hd_buffs
        if removed_buffs:
            logs.append(f"🧹 {self.name} removes boss buffs: {', '.join(removed_buffs)}.")
            
        boss.recalculate_stats()

        # Gain EF stack
        self.evolutionary_factor = min(self.evolutionary_factor + 1, 3)
        logs.append(f"🔬 Gains 1 Evolutionary Factor (now {self.evolutionary_factor}).")

        logs.extend(self.apply_evolutionary_factor_effects(team))
        return logs



    def basic_attack(self, boss, team):
        logs = []
        if self.has_fear:
            logs.append(f"{self.name} is feared and cannot use basic attack.")
            return logs

        logs.extend(hero_deal_damage(self, boss, self.atk * (10+self.skill_damage/100), is_active=False, team=team))
        poison_damage = int(self.atk * 5.6)
        logs.append(f"☠️ Applies Poison: {poison_damage} for 2 rounds.")
        logs.extend(BuffHandler.apply_debuff(boss, "poison", {
            "attribute": "poison", "damage": poison_damage, "rounds": 2
        }))

        regen_amt = int(self.max_hp * 0.15)
        self.add_or_update_buff(self, "mff_regen", {"attribute": "regen", "heal_amount": regen_amt, "rounds": 2})
        logs.append(f"🧬 Gains Regen: {regen_amt} HP over 2 rounds.")
        return logs

    def passive_on_ally_attack(self, ally, boss):
        if self.has_seal_of_light:
            return []  # Passive blocked by Seal of Light
        logs = []
        buffs = []

        buffs += BuffHandler.apply_buff(ally, "mff_passive_adr", {
            "attribute": "ADR", "bonus": 12, "rounds": 3
        }, boss)
        buffs += BuffHandler.apply_buff(ally, "mff_passive_atk", {
            "attribute": "atk", "bonus": int(ally.atk * 0.12), "rounds": 3
        }, boss)
        buffs += BuffHandler.apply_buff(ally, "mff_passive_precision", {
            "attribute": "precision", "bonus": 10, "rounds": 3
        }, boss)

        shield_val = int(self.atk * 2)
        self.add_or_update_buff(ally, "mff_passive_shield", {"attribute": "shield", "shield": shield_val, "rounds": 3})

        if buffs:
            logs.append(f"🧬 {self.name} empowers {ally.name}: +ATK, ADR, Precision, Shield.")
        return logs

    def apply_evolutionary_factor_effects(self, team):
            logs = []
            buffs_applied = []

            if self.evolutionary_factor == 1:
                for ally in team.heroes:
                    BuffHandler.apply_buff(ally, "ef1_adr", {
                        "attribute": "ADR", "bonus": 40, "rounds": 3
                    })
                    buffs_applied.append((ally.name, "+40% ADR"))
                    BuffHandler.apply_buff(ally, "ef1_ctrl", {
                        "attribute": "ctrl_immunity", "bonus": 35, "rounds": 3
                    })
                    buffs_applied.append((ally.name, "+35% Control Immunity"))
                if buffs_applied:
                    logs.append("🌱 EF1 Buffs Applied:")
                    logs.extend(group_team_buffs(buffs_applied))

            elif self.evolutionary_factor == 2:
                for ally in team.heroes:
                    BuffHandler.apply_buff(ally, "ef2_atk", {
                        "attribute": "atk", "bonus": int(ally.atk * 0.22), "rounds": 3
                    })
                    buffs_applied.append((ally.name, "+22% ATK"))
                    shield_val = int(self.atk * 26)
                    self.add_or_update_buff(ally, "ef2_shield", {"attribute": "shield", "shield": shield_val, "rounds": 3})
                    buffs_applied.append((ally.name, f"+{shield_val} Shield"))
                if buffs_applied:
                    logs.append("🌿 EF2 Buffs Applied:")
                    logs.extend(group_team_buffs(buffs_applied))

            elif self.evolutionary_factor == 3 and not self.permanent_ef3_bonus_active:
                self.permanent_ef3_bonus_active = True
                logs.append("🌳 EF3 unlocked: stacking bonuses begin.")

                # MFF starts at +10% bonus to poisoned targets
                self.bonus_damage_vs_poisoned = 10.0
                for ally in team.heroes:
                    if ally != self and ally.is_alive():
                        # Allies start at +3.3% bonus to poisoned targets
                        ally.bonus_damage_vs_poisoned = 3.3


            return logs

    def end_of_round(self, boss, team, round_num):
        if self.has_seal_of_light:
            return super().end_of_round(boss, team, round_num)  # Passive stacking blocked by Seal of Light
        logs = super().end_of_round(boss, team, round_num)

        if self.permanent_ef3_bonus_active:
            # MFF self stacking
            self.add_or_update_buff(self, "ef3_self_atk", {"attribute": "atk", "bonus": int(self.atk * 0.12), "rounds": 9999})
            self.add_or_update_buff(self, "ef3_self_speed", {"attribute": "speed", "bonus": 15, "rounds": 9999})
            self.bonus_damage_vs_poisoned += 10.0  # MFF gains +10% poison bonus each round

            # Allies stacking
            for ally in team.heroes:
                if ally != self and ally.is_alive():
                    ally_atk = int(self.atk * 0.12 * 0.33)
                    ally_speed = int(15 * 0.33)
                    self.add_or_update_buff(ally, "ef3_ally_atk", {"attribute": "atk", "bonus": ally_atk, "rounds": 9999})
                    self.add_or_update_buff(ally, "ef3_ally_speed", {"attribute": "speed", "bonus": ally_speed, "rounds": 9999})
                    ally.bonus_damage_vs_poisoned += 3.3  # Allies gain +3.3% poison bonus each round

            logs.append(f"🌳 {self.name} stacks EF3 buffs: +12% ATK, +15 SPD, +10% Poison Bonus (self), +3.3% (allies).")

        return logs
