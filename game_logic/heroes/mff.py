from .base import Hero
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage
from utils.log_utils import group_team_buffs
from utils.log_utils import debug

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
        debug(f"{self.name} starts ACTIVE skill")


        # ✅ Counterattack allowed here
        logs.extend(hero_deal_damage(
            self, boss, self.atk * (16 + self.skill_damage),
            is_active=True, team=team, allow_counter=True
        ))

        # Poison application (no counter)
        poison_damage = int(self.atk * (12 + self.skill_damage / 100))
        logs.append(f"☠️ Applies Poison: {poison_damage} for 3 rounds.")
        logs.extend(BuffHandler.apply_debuff(boss, "poison", {
            "attribute": "poison", "damage": poison_damage, "rounds": 3
        }))

        # Remove ALL ATK and HD buffs from boss
        atk_buffs = [name for name, data in boss.buffs.items()
                    if isinstance(data, dict) and data.get("attribute") == "atk"]
        hd_buffs = [name for name, data in boss.buffs.items()
                    if isinstance(data, dict) and data.get("attribute") == "HD"]

        for buff_name in atk_buffs:
            buff = boss.buffs.pop(buff_name, None)
            if buff:
                boss.atk -= buff.get("bonus", 0)

        for buff_name in hd_buffs:
            buff = boss.buffs.pop(buff_name, None)
            if buff:
                boss.hd -= buff.get("bonus", 0)

        removed_buffs = atk_buffs + hd_buffs
        if removed_buffs:
            logs.append(f"🧹 {self.name} removes boss buffs: {', '.join(removed_buffs)}.")

        boss.recalculate_stats()

        # EF logic
        self.evolutionary_factor = min(self.evolutionary_factor + 1, 3)
        logs.append(f"🔬 Gains 1 Evolutionary Factor (now {self.evolutionary_factor}).")

        logs.extend(self.apply_evolutionary_factor_effects(team))
        return logs



    def basic_attack(self, boss, team):
        if self.has_fear:
            return [f"{self.name} is feared and cannot use basic attack."]

        def do_attack():
            logs = []
            debug(f"{self.name} starts BASIC attack")


            # ✅ Main hit — counterattack should occur
            logs.extend(hero_deal_damage(
                self, boss, self.atk * (10 + self.skill_damage / 100),
                is_active=False, team=team, allow_counter=True
            ))

            # ❌ Poison application — no counter
            poison_damage = int(self.atk * 5.6)
            logs.append(f"☠️ Applies Poison: {poison_damage} for 2 rounds.")
            logs.extend(BuffHandler.apply_debuff(boss, "poison", {
                "attribute": "poison", "damage": poison_damage, "rounds": 2
            }))

            # ❌ Regen application — no counter
            regen_amt = int(self.max_hp * 0.15)
            self.add_or_update_buff(self, "mff_regen", {
                "attribute": "regen", "heal_amount": regen_amt, "rounds": 2
            })
            logs.append(f"🧬 Gains Regen: {regen_amt} HP over 2 rounds.")

            return logs

        return self.with_basic_flag(do_attack)


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
            return super().end_of_round(boss, team, round_num)

        logs = super().end_of_round(boss, team, round_num)

        if self.permanent_ef3_bonus_active:
            # Remove prior self EF3 buffs and accumulate their values
            atk_total = 0
            spd_total = 0
            for name in list(self.buffs):
                if name.startswith("ef3_self_atk_"):
                    atk_total += self.buffs[name]["bonus"]
                    del self.buffs[name]
                elif name.startswith("ef3_self_speed_"):
                    spd_total += self.buffs[name]["bonus"]
                    del self.buffs[name]

            # Stack new round’s EF3 buffs
            atk_total += int(self.atk * 0.12)
            spd_total += 15
            self.apply_buff(f"ef3_self_atk_{round_num}", {
                "attribute": "atk", "bonus": atk_total, "rounds": 9999, "skill_buff": True
            })
            self.apply_buff(f"ef3_self_speed_{round_num}", {
                "attribute": "speed", "bonus": spd_total, "rounds": 9999, "skill_buff": True
            })
            self.bonus_damage_vs_poisoned += 10.0

            for ally in team.heroes:
                if ally == self or not ally.is_alive():
                    continue

                # Remove and accumulate old EF3 buffs
                ally_atk = 0
                ally_spd = 0
                poison_bonus = 0
                for name in list(ally.buffs):
                    if name.startswith("ef3_ally_atk_"):
                        ally_atk += ally.buffs[name]["bonus"]
                        del ally.buffs[name]
                    elif name.startswith("ef3_ally_speed_"):
                        ally_spd += ally.buffs[name]["bonus"]
                        del ally.buffs[name]
                    elif name.startswith("ef3_poison_bonus_"):
                        poison_bonus += ally.buffs[name]["bonus"]
                        del ally.buffs[name]

                # Add new stack
                ally_atk += int(ally.atk * 0.12)
                ally_spd += 5
                poison_bonus += 3.3

                ally.apply_buff(f"ef3_ally_atk_{round_num}", {
                    "attribute": "atk", "bonus": ally_atk, "rounds": 9999, "skill_buff": True
                })
                ally.apply_buff(f"ef3_ally_speed_{round_num}", {
                    "attribute": "speed", "bonus": ally_spd, "rounds": 9999, "skill_buff": True
                })
                ally.apply_buff(f"ef3_poison_bonus_{round_num}", {
                    "attribute": "poison_bonus", "bonus": poison_bonus, "rounds": 9999, "skill_buff": True
                })

                if not hasattr(ally, "bonus_damage_vs_poisoned"):
                    ally.bonus_damage_vs_poisoned = 0.0
                ally.bonus_damage_vs_poisoned += 3.3

            logs.append(f"🌳 {self.name} stacks EF3: {atk_total} ATK, {spd_total} SPD (self), +3.3% Poison Bonus to allies.")

        return logs
