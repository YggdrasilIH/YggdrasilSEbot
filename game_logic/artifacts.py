# game_logic/artifacts.py
import random

def stylize_log(category, message):
    icons = {
        "energy": "🔶",
        "buff": "🔷",
        "debuff": "🔻",
        "damage": "🟢",
        "heal": "🟣",
        "control": "🟥",
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
    def __init__(self):
        self.enabled = True

    def on_active_skill(self, team):
        messages = []
        for hero in team.heroes:
            hero.energy += 20
            msg = stylize_log("energy", f"{hero.name} gains 20 energy from Demon Bell.")
            if random.random() < 0.5:
                hero.energy += 10
                msg += " +10 extra!"
            messages.append(msg)
        return messages

class Mirror(Artifact):
    def __init__(self):
        self.last_trigger_round = -3
        self.bonus = 0

    def apply_start_of_battle(self, team, round_num):
        self.last_trigger_round = round_num
        self.bonus = 4.5
        for hero in team.heroes:
            hero.all_damage_dealt += self.bonus

    def apply_end_of_round(self, hero, team, boss, round_num):
        msgs = [stylize_log("energy", f"{hero.name} gains 15 energy from Mirror.")]
        hero.energy += 15
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
        if not hasattr(hero, "antler_buff"):
            hero.antler_buff = 0
        hero.all_damage_dealt += 9
        hero.antler_buff = 15
        return [stylize_log("buff", f"{hero.name} gains 9% all damage from Antlers.")]
