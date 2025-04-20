# game_logic/artifacts.py
import random
from game_logic.buff_handler import BuffHandler

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
        if hasattr(boss, "attribute_effects"):
            effects = boss.attribute_effects[-2:]
            for effect in effects:
                for target in team.get_line(hero):
                    target.apply_attribute_effect(effect, ratio=0.3)
                    replicated_msgs.append(stylize_log("buff", f"{target.name} replicates {effect['name']} from boss (Scissors)."))
        return replicated_msgs

class DB(Artifact):
    def bind_team(self, team):
        self.team = team
    def __init__(self):
        self.enabled = True

    def on_active_skill(self, team, boss):
        gained = []
        blocked = []
        extras = []

        for hero in team.heroes:
            success, msg = BuffHandler.apply_buff(hero, "db_energy", {
                "attribute": "energy", "bonus": 20, "rounds": 1
            }, boss)

            if success:
                gained.append(hero.name)
                if random.random() < 0.5:
                    extra_success, _ = BuffHandler.apply_buff(hero, "db_energy_extra", {
                        "attribute": "energy", "bonus": 10, "rounds": 1
                    }, boss)
                    if extra_success:
                        extras.append(hero.name)
            else:
                blocked.append(hero.name)
                if msg:
                    blocked.append(f"{hero.name} (blocked: {msg})")

        msg_parts = []
        if gained:
            main = f"{', '.join(gained)} gain 20 energy"
            if extras:
                main += f" (+10 extra for {', '.join(extras)})"
            msg_parts.append(main)
        if blocked:
            msg_parts.append(f"energy feed to {', '.join(blocked)} blocked by Curse of Decay")

        return [stylize_log("energy", f"Demon Bell: {'; '.join(msg_parts)}.")]

class Mirror(Artifact):
    def bind_team(self, team):
        self.team = team
    def __init__(self):
        self.last_trigger_round = -3
        self.bonus = 0

    def apply_start_of_battle(self, team, round_num):
        self.last_trigger_round = round_num
        self.bonus = 4.5
        for hero in team.heroes:
            hero.all_damage_dealt += self.bonus

    def apply_end_of_round(self, hero, team, boss, round_num):
        msgs = []
        BuffHandler.apply_buff(hero, "mirror_energy", {
            "attribute": "energy", "bonus": 15, "rounds": 1
        }, boss)
        msgs.append(stylize_log("energy", f"{hero.name} gains 15 energy from Mirror."))

        if round_num - self.last_trigger_round >= 3:
            self.last_trigger_round = round_num
            self.bonus = 4.5
            for h in team.heroes:
                h.all_damage_dealt += self.bonus
                msgs.append(stylize_log("buff", f"{h.name} gains {self.bonus:.1f}% all damage from Mirror."))
        else:
            self.bonus -= 1.5
        return msgs

class Antlers(Artifact):
    def apply_end_of_round(self, hero, team, boss, round_num):
        if not hasattr(hero, "antler_stacks"):
            hero.antler_stacks = 0
        hero.antler_stacks += 1
        bonus = 9 * hero.antler_stacks
        hero.all_damage_dealt += 9
        return [stylize_log("buff", f"{hero.name} gains +9% all damage from Antlers (Total: {bonus}%).")]
