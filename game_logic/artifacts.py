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
        if hero.has_seal_of_light:
            return [stylize_log("info", f"{hero.name}'s Mirror effect is sealed and does nothing.")]
        return []

class Scissors(Artifact):
    def bind_team(self, team):
        self.team = team
    def apply_end_of_round(self, hero, team, boss, round_num):
        replicated_msgs = []
        if hasattr(boss, "attribute_effects"):
            effects = boss.attribute_effects[-2:]
            for effect in effects:
                if hero.has_seal_of_light:
                    continue  # Artifact suppressed by Seal of Light on wearer
            for target in team.get_line(hero):
                scaled_bonus = int(effect.get("value", 0) * 0.3)
                target.apply_buff(f"scissors_{effect['name']}_{round_num}", {
                    "attribute": effect.get("attribute"),
                    "bonus": scaled_bonus,
                    "rounds": effect.get("rounds", 1)
                })
                replicated_msgs.append(stylize_log("buff", f"{target.name} replicates {effect['name']} from boss (Scissors)."))
        return replicated_msgs

class DB(Artifact):
    def on_active_skill(self, team, boss):
        logs = []
        for hero in team.heroes:
            # Attempt to apply energy, blockable by Curse
            if hero.curse_of_decay > 0:
                hero.curse_of_decay -= 1
                damage = boss.atk * 30
                hero.hp -= damage
                if hero.hp < 0:
                    hero.hp = 0
                logs.append(f"💀 Curse of Decay offsets energy buff on {hero.name}. Takes {int(damage):,} damage. (1 layer removed)")
            else:
                hero.energy += 20
                logs.append(f"⚡ {hero.name} gains +20 energy from DB (direct).")

                # 50% chance to gain +10 more
                import random
                if random.random() < 0.5:
                    hero.energy += 10
                    logs.append(f"⚡ {hero.name} gains an extra +10 energy from DB (direct).")

        return logs

class Mirror(Artifact):
    def __init__(self):
        self.last_trigger_round = -3
        self.bonus = 4.5

    def apply_end_of_round(self, hero, team, boss, round_num):
        msgs = []

        # Curse interaction (blockable energy gain)
        if hero.curse_of_decay > 0:
            hero.curse_of_decay -= 1
            damage = boss.atk * 30
            hero.hp -= damage
            if hero.hp < 0:
                hero.hp = 0
            msgs.append(f"💀 Curse of Decay offsets energy buff on {hero.name}. Takes {int(damage):,} damage. (1 layer removed)")
        else:
            hero.energy += 15
            msgs.append(stylize_log("energy", f"{hero.name} gains +15 energy from Mirror."))

        # Apply all_damage_dealt bonus every 3 rounds
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
