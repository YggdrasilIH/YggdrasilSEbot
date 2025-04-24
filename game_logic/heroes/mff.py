from .base import Hero
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage

class MFF(Hero):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evolutionary_factor = 0
        self.permanent_ef3_bonus_active = False

    def active_skill(self, boss, team):
        logs = [f"🧪 {self.name} uses Active Skill:"]

        logs.extend(hero_deal_damage(self, boss, self.atk * 16, is_active=True, team=team))
        logs.append(f"☠️ Applies Poison: {int(self.atk * 12)} for 3 rounds.")
        logs.extend(BuffHandler.apply_debuff(boss, "poison", {
            "attribute": "poison", "damage": int(self.atk * 12), "rounds": 3
        }))

        removed = [name for name, data in boss.buffs.items()
                   if isinstance(data, dict) and "attribute" in data and "bonus" in data and data["attribute"] in BuffHandler.ATTRIBUTE_BUFF_KEYS]
        for buff_name in removed[:2]:
            del boss.buffs[buff_name]
        if removed:
            logs.append(f"🧹 Removes buffs from Boss: {', '.join(removed[:2])}.")

        self.evolutionary_factor = min(self.evolutionary_factor + 1, 3)
        logs.append(f"🔬 Gains 1 Evolutionary Factor (now {self.evolutionary_factor}).")

        logs.extend(self.apply_evolutionary_factor_effects(team))
        return logs

    def basic_attack(self, boss, team):
        logs = [f"🔬 {self.name} uses Basic Attack:"]

        logs.extend(hero_deal_damage(self, boss, self.atk * 10, is_active=False, team=team))
        logs.append(f"☠️ Applies Poison: {int(self.atk * 5.6)} for 2 rounds.")
        logs.extend(BuffHandler.apply_debuff(boss, "poison", {
            "attribute": "poison", "damage": int(self.atk * 5.6), "rounds": 2
        }))

        regen_amt = int(self.max_hp * 0.15)
        logs.append(f"🧬 Gains Regen: {regen_amt} HP over 2 rounds.")
        logs.extend(BuffHandler.apply_buff(self, "mff_regen", {
            "attribute": "regen", "heal_amount": regen_amt, "rounds": 2
        }, boss))
        return logs

    def passive_on_ally_attack(self, ally, boss):
        logs = []
        buffs = []

        buffs += BuffHandler.apply_buff(ally, "mff_passive_adr", {
            "attribute": "DR", "bonus": 12, "rounds": 3
        }, boss)
        buffs += BuffHandler.apply_buff(ally, "mff_passive_atk", {
            "attribute": "atk", "bonus": int(ally.atk * 0.12), "rounds": 3
        }, boss)
        buffs += BuffHandler.apply_buff(ally, "mff_passive_precision", {
            "attribute": "precision", "bonus": 10, "rounds": 3
        }, boss)
        shield_val = int(self.atk * 2)
        ally.apply_buff("mff_passive_shield", {"attribute": "shield", "shield": shield_val, "rounds": 3})


        if buffs:
            logs.append(f"🧬 {self.name} passively empowers {ally.name}: +ATK, DR, Precision, Shield.")
        return logs

    def apply_evolutionary_factor_effects(self, team):
        logs = []

        if self.evolutionary_factor == 1:
            for ally in team.heroes:
                logs.extend(BuffHandler.apply_buff(ally, "ef1_dr", {
                    "attribute": "DR", "bonus": 40, "rounds": 3
                }))
                logs.extend(BuffHandler.apply_buff(ally, "ef1_ctrl", {
                    "attribute": "control_immunity", "bonus": 35, "rounds": 3
                }))
            logs.append("🌱 EF1 (Evolutionary Factor): All allies gain +40% DR and +35% Control Immunity.")

        elif self.evolutionary_factor == 2:
            for ally in team.heroes:
                logs.extend(BuffHandler.apply_buff(ally, "ef2_atk", {
                    "attribute": "atk", "bonus": int(ally.atk * 0.22), "rounds": 3
                }))
                shield_val = int(self.atk * 26)
                ally.apply_buff("ef2_shield", {"attribute": "shield", "shield": shield_val, "rounds": 3})
                logs.append(f"🛡️ {ally.name} gains a {shield_val} shield from MFF's EF2.")
            logs.append(f"🌿 EF2 (Evolutionary Factor): All allies gain +22% ATK and a {int(self.atk * 26)} shield.")

        elif self.evolutionary_factor == 3 and not self.permanent_ef3_bonus_active:
            self.permanent_ef3_bonus_active = True
            logs.extend(BuffHandler.apply_buff(self, "ef3_self_atk", {
                "attribute": "atk", "bonus": int(self.atk * 0.12), "rounds": 9999
            }))
            logs.extend(BuffHandler.apply_buff(self, "ef3_self_speed", {
                "attribute": "speed", "bonus": 15, "rounds": 9999
            }))

            for ally in team.heroes:
                if ally != self:
                    logs.extend(BuffHandler.apply_buff(ally, "ef3_ally_atk", {
                        "attribute": "atk", "bonus": int(self.atk * 0.12 * 0.33), "rounds": 9999
                    }))
                    logs.extend(BuffHandler.apply_buff(ally, "ef3_ally_speed", {
                        "attribute": "speed", "bonus": int(15 * 0.33), "rounds": 9999
                    }))
            logs.append("🌳 EF3 (Evolutionary Factor): MFF gains permanent bonuses. Allies gain 33% of EF3 effects.")

        return logs

    def end_of_round(self, boss, team, round_num):
        logs = super().end_of_round(boss, team, round_num)

        if self.permanent_ef3_bonus_active:
            atk_bonus = int(self.atk * 0.12)
            speed_bonus = 15
            poison_multiplier = 0.10

            BuffHandler.apply_buff(self, "ef3_self_atk_tick", {
                "attribute": "atk", "bonus": atk_bonus, "rounds": 1
            })
            BuffHandler.apply_buff(self, "ef3_self_speed_tick", {
                "attribute": "speed", "bonus": speed_bonus, "rounds": 1
            })
            self.ef3_poison_bonus = getattr(self, "ef3_poison_bonus", 0) + poison_multiplier

            ally_buffs = []
            for ally in team.heroes:
                if ally != self:
                    ally_atk = int(self.atk * 0.12 * 0.33)
                    ally_speed = int(15 * 0.33)
                    BuffHandler.apply_buff(ally, "ef3_ally_atk_tick", {
                        "attribute": "atk", "bonus": ally_atk, "rounds": 1
                    })
                    BuffHandler.apply_buff(ally, "ef3_ally_speed_tick", {
                        "attribute": "speed", "bonus": ally_speed, "rounds": 1
                    })
                    ally.ef3_poison_bonus = getattr(ally, "ef3_poison_bonus", 0) + (poison_multiplier * 0.33)
                    ally_buffs.append(f"{ally.name}: +{ally_atk} ATK, +{ally_speed} SPD, +{int(ally.ef3_poison_bonus * 100)}% poison")

            logs.append(f"🌳 {self.name} refreshes EF3 buffs: +{atk_bonus} ATK, +{speed_bonus} SPD, +10% poison (now {int(self.ef3_poison_bonus * 100)}%).")
            if ally_buffs:
                logs.append("🌿 Allies receive EF3 (33%) buffs: " + "; ".join(ally_buffs))

        return logs
