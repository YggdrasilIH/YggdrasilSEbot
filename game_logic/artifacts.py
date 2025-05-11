# game_logic/artifacts.py
import random
from game_logic.buff_handler import BuffHandler
from utils.log_utils import group_team_buffs
from utils.log_utils import stylize_log

class Artifact:
    def apply_start_of_battle(self, team, round_num):
        pass

    def apply_end_of_round(self, hero, team, boss, round_num):
        return []


class Scissors(Artifact):
    def bind_team(self, team):
        self.team = team

    def apply_end_of_round(self, hero, team, boss, round_num):
        replicated_msgs = []
        if hasattr(self, "owner") and self.owner and self.owner.has_seal_of_light:
            return [stylize_log("info", f"{self.owner.name}'s Scissors is sealed by Seal of Light.")]

        for buff_name, buff in boss.buffs.items():
            if not isinstance(buff, dict):
                continue

            attr = buff.get("attribute")
            bonus = buff.get("bonus", 0)
            duration = buff.get("rounds", 1)

            if attr not in {"atk", "hd"} or bonus <= 0:
                continue

            scaled_bonus = bonus * 0.3
            if abs(scaled_bonus) < 1e-6:
                continue

            for target in team.get_line(hero):
                buff_data = {
                    "attribute": attr,
                    "bonus": scaled_bonus,
                    "rounds": duration
                }
                if isinstance(bonus, float) and abs(bonus) < 1.0:
                    buff_data["is_percent"] = True

                BuffHandler.apply_buff(target, f"scissors_repl_{buff_name}_{round_num}", buff_data, boss)
                replicated_msgs.append(
                    stylize_log("buff", f"{target.name} replicates +{scaled_bonus:.3f} {attr.upper()} from {buff_name} (Scissors).")
                )

        return replicated_msgs


class DB(Artifact):
    def apply_start_of_battle(self, team, round_num):
        logs = []
        if hasattr(self, "owner") and self.owner and not self.owner.has_seal_of_light:
            BuffHandler.apply_buff(self.owner, f"db_start_energy_{round_num}", {
                "attribute": "energy", "bonus": 50, "rounds": 0
            }, boss=None)
            logs.append(f"⚡ {self.owner.name} gains +50 starting Energy from DB.")
        return logs

    def on_active_skill(self, team, boss):
        logs = []
        buffs_applied = []

        if hasattr(self, "owner") and self.owner and self.owner.has_seal_of_light:
            logs.append(f"❌ {self.owner.name}'s DB is sealed by Seal of Light.")
            return logs

        if hasattr(team, "heroes"):
            for hero in team.heroes:
                energy_buff = {"attribute": "energy", "bonus": 20, "rounds": 0}
                BuffHandler.apply_buff(hero, f"db_energy_{random.randint(1000,9999)}", energy_buff, boss)
                buffs_applied.append((hero.name, "+20 Energy (DB)"))
                if random.random() < 0.5:
                    BuffHandler.apply_buff(hero, f"db_bonus_energy_{random.randint(1000,9999)}", {
                        "attribute": "energy", "bonus": 10, "rounds": 0
                    }, boss)
                    buffs_applied.append((hero.name, "+10 Bonus Energy (DB)"))

        if buffs_applied:
            logs.extend(group_team_buffs(buffs_applied))
        return logs


class dDB(DB):
    def apply_start_of_battle(self, team, round_num):
        logs = []
        buffs_applied = []
        if hasattr(team, "heroes"):
            for hero in team.heroes:
                if hero.has_seal_of_light:
                    continue
                BuffHandler.apply_buff(hero, f"ddb_start_energy_{random.randint(1000,9999)}", {
                    "attribute": "energy", "bonus": 100, "rounds": 0
                }, boss=None)
                buffs_applied.append((hero.name, "+100 Starting Energy (dDB)"))
        if buffs_applied:
            logs.extend(group_team_buffs(buffs_applied))
        return logs

    def on_active_skill(self, team, boss):
        logs = super().on_active_skill(team, boss)
        buffs_applied = []

        if hasattr(self, "owner") and self.owner and self.owner.has_seal_of_light:
            logs.append(f"❌ {self.owner.name}'s DB is sealed by Seal of Light.")
            return logs

        if hasattr(team, "heroes"):
            for hero in team.heroes:
                if hero.energy >= 100:
                    BuffHandler.apply_buff(hero, f"ddb_speed_boost_{random.randint(1000,9999)}", {
                        "attribute": "speed",
                        "bonus": 3,
                        "rounds": 4
                    }, boss)
                    buffs_applied.append((hero.name, "+3 SPD (dDB Boost)"))

        if buffs_applied:
            logs.extend(group_team_buffs(buffs_applied))
        print(f"[DEBUG-DB] {hero.name} gains energy from DB feed. Energy now: {hero.energy}")

        return logs


class Mirror(Artifact):
    def __init__(self):
        self.last_trigger_round = -3
        self.bonus = 4.5
        self.ctrl_bonus = 3

    def apply_start_of_battle(self, team, round_num):
        logs = []
        if hasattr(self, "owner") and self.owner and not self.owner.has_seal_of_light:
            BuffHandler.apply_buff(self.owner, f"mirror_start_energy_{round_num}", {
                "attribute": "energy", "bonus": 75, "rounds": 0
            }, boss=None)
            logs.append(f"⚡ {self.owner.name} gains +75 starting Energy from Mirror.")
        return logs

    def apply_end_of_round(self, hero, team, boss, round_num):
        msgs = []
        buffs_applied = []

        if hasattr(self, "owner") and self.owner and self.owner.has_seal_of_light:
            msgs.append(f"❌ {self.owner.name}'s DB is sealed by Seal of Light.")
            return msgs

        BuffHandler.apply_buff(hero, f"mirror_energy_{round_num}", {
            "attribute": "energy",
            "bonus": 15,
            "rounds": 0
        }, boss)
        buffs_applied.append((hero.name, "+15 Energy (Mirror)"))

        if round_num - self.last_trigger_round >= 3:
            self.last_trigger_round = round_num
            self.bonus = 4.5
            self.ctrl_bonus = 3

            for h in team.heroes:
                BuffHandler.apply_buff(h, f"mirror_damage_bonus_{round_num}", {
                    "attribute": "all_damage_dealt",
                    "bonus": self.bonus,
                    "rounds": 3
                }, boss)
                buffs_applied.append((h.name, f"+{self.bonus:.1f}% All Damage (Mirror)"))

                BuffHandler.apply_buff(h, f"mirror_ctrl_bonus_{round_num}", {
                    "attribute": "ctrl_immunity",
                    "bonus": self.ctrl_bonus,
                    "rounds": 3
                }, boss)
                buffs_applied.append((h.name, f"+{self.ctrl_bonus}% Ctrl Immunity (Mirror)"))
        else:
            self.bonus -= 1.5
            if self.ctrl_bonus > 0:
                self.ctrl_bonus -= 1

        if buffs_applied:
            msgs.extend(group_team_buffs(buffs_applied))
        print(f"[DEBUG-MIRROR] {hero.name} gains +15 energy from Mirror (curse check: {hero.curse_of_decay})")

        return msgs


class dMirror(Mirror):
    def __init__(self):
        super().__init__()
        self.last_trigger_round = -3
        self.bonus = 4.5
        self.dr_bonus = 3
        self.ctrl_bonus = 3

    def apply_start_of_battle(self, team, round_num):
        logs = []
        if hasattr(self, "owner") and self.owner and not self.owner.has_seal_of_light:
            BuffHandler.apply_buff(self.owner, f"dmirror_start_energy_{round_num}", {
                "attribute": "energy", "bonus": 100, "rounds": 0
            }, boss=None)
            logs.append(f"⚡ {self.owner.name} gains +100 starting Energy from dMirror.")
        return logs

    def apply_end_of_round(self, hero, team, boss, round_num):
        msgs = []
        buffs_applied = []

        if hasattr(self, "owner") and self.owner and self.owner.has_seal_of_light:
            msgs.append(f"❌ {self.owner.name}'s DB is sealed by Seal of Light.")
            return msgs

        BuffHandler.apply_buff(hero, f"dmirror_energy_{round_num}", {
            "attribute": "energy",
            "bonus": 15,
            "rounds": 0
        }, boss)
        buffs_applied.append((hero.name, "+15 Energy (dMirror)"))

        heal_amt = int(hero.max_hp * 0.06)
        hero.hp = min(hero.max_hp, hero.hp + heal_amt)
        buffs_applied.append((hero.name, f"+{heal_amt // 1_000_000}M Heal (dMirror)"))

        if round_num - self.last_trigger_round >= 3:
            self.last_trigger_round = round_num
            self.bonus = 4.5
            self.dr_bonus = 3
            self.ctrl_bonus = 3

            for h in team.heroes:
                BuffHandler.apply_buff(h, f"dmirror_damage_bonus_{round_num}", {
                    "attribute": "all_damage_dealt",
                    "bonus": self.bonus,
                    "rounds": 3
                }, boss)
                buffs_applied.append((h.name, f"+{self.bonus:.1f}% All Damage (dMirror)"))

                BuffHandler.apply_buff(h, f"dmirror_dr_bonus_{round_num}", {
                    "attribute": "DR",
                    "bonus": self.dr_bonus,
                    "rounds": 3
                }, boss)
                buffs_applied.append((h.name, f"+{self.dr_bonus}% DR (dMirror)"))

                BuffHandler.apply_buff(h, f"dmirror_ctrl_bonus_{round_num}", {
                    "attribute": "ctrl_immunity",
                    "bonus": self.ctrl_bonus,
                    "rounds": 3
                }, boss)
                buffs_applied.append((h.name, f"+{self.ctrl_bonus}% Ctrl Immunity (dMirror)"))
        else:
            self.bonus -= 1.5
            if self.dr_bonus > 0:
                self.dr_bonus -= 1
            if self.ctrl_bonus > 0:
                self.ctrl_bonus -= 1

        if buffs_applied:
            msgs.extend(group_team_buffs(buffs_applied))

        return msgs


class Antlers(Artifact):
    def apply_end_of_round(self, hero, team, boss, round_num):
        if hasattr(self, "owner") and self.owner and self.owner.has_seal_of_light:
            return [stylize_log("info", f"{self.owner.name}'s Mirror is sealed by Seal of Light.")]

        if not hasattr(hero, "antler_stacks"):
            hero.antler_stacks = 0
        hero.antler_stacks += 1

        bonus = 9
        buff_name = f"antlers_round_{hero.antler_stacks}"

        BuffHandler.apply_buff(hero, buff_name, {
            "attribute": "all_damage_dealt",
            "bonus": bonus,
            "rounds": 9999,
            "skill_buff": True
        }, boss)

        return [stylize_log("buff", f"{hero.name} gains +9% all damage from Antlers (Total {hero.antler_stacks * 9}%).")]
