from game_logic.foresight import apply_foresight
from game_logic.heroes.mff import MFF  # Central foresight handler
from game_logic.buff_handler import grant_energy  # Central energy handling

class Team:
    def trigger_mff_passive(self, attacker, boss):
        logs = []
        for hero in self.heroes:
            if isinstance(hero, MFF) and hero != attacker and hero.is_alive():
                logs.extend(hero.passive_on_ally_attack(attacker, boss))
        return logs

    def __init__(self, heroes, front_line, back_line):
        self.heroes = heroes
        self.front_line = front_line
        self.back_line = back_line

    def perform_turn(self, boss, round_num):
        logs = []
        logs.append(f"⚔️ Team begins actions for Round {round_num}.")

        for hero in self.heroes:
            if hero.is_alive():
                if hero.energy >= 100 and not hero.has_silence:
                    logs.append(f"💥 {hero.name} has enough energy for active skill.")
                    logs.extend(hero.active_skill(boss, self))
                    logs.extend(self.trigger_mff_passive(hero, boss))
                    logs.extend(apply_foresight(hero, "active"))
                    hero.energy = 0
                    logs.append(grant_energy(hero, 50))
                else:
                    logs.append(f"🔪 {hero.name} uses basic attack.")
                    logs.extend(hero.basic_attack(boss, self))
                    logs.extend(self.trigger_mff_passive(hero, boss))
                    logs.extend(apply_foresight(hero, "basic"))
                    logs.append(grant_energy(hero, 50))

        logs.append(f"🔥 Boss takes its turn.")
        logs.extend(boss.active_skill(self.heroes, round_num))
        logs.extend(boss.basic_attack(self.heroes, round_num))
        logs.extend(boss.counterattack(self.heroes))
        return logs

    def end_of_round(self, boss, round_num):
        logs = []
        logs.append(f"🔚 End of Round {round_num} effects begin.")
        for hero in self.heroes:
            if hero.is_alive():
                logs.extend(hero.end_of_round(boss, self, round_num))
        logs.extend(boss.end_of_round_effects(self.heroes, round_num))
        logs.append(f"🧠 Boss and team end-of-round effects completed.")
        return logs

    def status_descriptions(self):
        return [hero.get_status_description() for hero in self.heroes]
