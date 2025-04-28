# game_logic/artifacts.py
import random
from game_logic.buff_handler import BuffHandler
from utils.log_utils import group_team_buffs

def stylize_log(category, message):
    icons = {
        "energy": "🔶",
        "buff": "🔷",
        "debuff": "🔻",
        "damage": "🟢",
        "heal": "🟣",
        "control": "🔵",
        "info": "📘"
    }
    icon = icons.get(category, "📘")
    return f"{icon} {message}"

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
        if hero.has_seal_of_light:
            return replicated_msgs

        # Replicate Boss HD
        if boss.hd > 0:
            scaled_hd = int(boss.hd * 0.3)
            for target in team.get_line(hero):
                target.apply_buff(f"scissors_hd_{hero.name}_{round_num}", {
                    "attribute": "hd",
                    "bonus": scaled_hd,
                    "rounds": 15  # Boss Fear HD buffs last 15 rounds → we match that
                })
                replicated_msgs.append(stylize_log("buff", f"{target.name} replicates {scaled_hd} HD from Boss (Scissors)."))

        # Replicate Boss ATK (optional)
        if boss.atk > 0:
            scaled_atk = int(boss.atk * 0.3)
            for target in team.get_line(hero):
                target.apply_buff(f"scissors_atk_{hero.name}_{round_num}", {
                    "attribute": "atk",
                    "bonus": scaled_atk,
                    "rounds": 9999  # Boss ATK buff is permanent stacking
                })
                replicated_msgs.append(stylize_log("buff", f"{target.name} replicates {scaled_atk} ATK from Boss (Scissors)."))

        return replicated_msgs


class DB(Artifact):
    def on_active_skill(self, team, boss):
        logs = []
        buffs_applied = []
        if hasattr(team, "heroes"):
            for hero in team.heroes:
                if hero.has_seal_of_light:
                    continue
                if hero.curse_of_decay > 0:
                    hero.curse_of_decay -= 1
                    damage = boss.atk * 30
                    hero.hp -= damage
                    if hero.hp < 0:
                        hero.hp = 0
                    logs.append(f"💀 Curse of Decay offsets energy buff on {hero.name}. Takes {int(damage):,} damage. (1 layer removed)")
                else:
                    hero.energy += 20
                    buffs_applied.append((hero.name, "+20 Energy (DB)"))
                    if random.random() < 0.5:
                        hero.energy += 10
                        buffs_applied.append((hero.name, "+10 Bonus Energy (DB)"))

        if buffs_applied:
            logs.extend(group_team_buffs(buffs_applied))
        return logs

class Mirror(Artifact):
    def __init__(self):
        self.last_trigger_round = -3
        self.bonus = 4.5

    def apply_end_of_round(self, hero, team, boss, round_num):
        msgs = []
        buffs_applied = []

        if hero.has_seal_of_light:
            return [stylize_log("info", f"{hero.name}'s Mirror effect is sealed and does nothing.")]

        if hero.curse_of_decay > 0:
            hero.curse_of_decay -= 1
            damage = boss.atk * 30
            hero.hp -= damage
            if hero.hp < 0:
                hero.hp = 0
            msgs.append(f"💀 Curse of Decay offsets energy buff on {hero.name}. Takes {int(damage):,} damage. (1 layer removed)")
        else:
            hero.energy += 15
            buffs_applied.append((hero.name, "+15 Energy (Mirror)"))

        if round_num - self.last_trigger_round >= 3:
            self.last_trigger_round = round_num
            self.bonus = 4.5
            for h in team.heroes:
                BuffHandler.apply_buff(h, f"mirror_damage_bonus_{round_num}", {
                    "attribute": "all_damage_dealt",
                    "bonus": self.bonus,
                    "rounds": 3
                }, boss)
                buffs_applied.append((h.name, f"+{self.bonus:.1f}% All Damage (Mirror)"))
        else:
            self.bonus -= 1.5

        if buffs_applied:
            msgs.extend(group_team_buffs(buffs_applied))

        return msgs

# game_logic/artifacts.py

# game_logic/artifacts.py

class Antlers(Artifact):
    def apply_end_of_round(self, hero, team, boss, round_num):
        if not hasattr(hero, "antler_stacks"):
            hero.antler_stacks = 0
        hero.antler_stacks += 1

        bonus = 9
        buff_name = f"antlers_round_{hero.antler_stacks}"

        hero.apply_buff(buff_name, {
            "attribute": "all_damage_dealt",
            "bonus": bonus,
            "rounds": 9999,
            "skill_buff": True  # ✅ Now protected from Curse of Decay
        })

        hero.all_damage_dealt += bonus  # Still increment numerical stat directly too

        return [stylize_log("buff", f"{hero.name} gains +9% all damage from Antlers (Total {hero.antler_stacks * 9}%).")]
