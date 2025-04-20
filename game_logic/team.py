from game_logic.foresight import apply_foresight
from game_logic.heroes.mff import MFF  # Central foresight handler
from game_logic.buff_handler import grant_energy  # Central energy handling

class Team:
    def trigger_mff_passive(self, attacker, boss):
        logs = []
        if attacker.has_fear or attacker.has_silence:
            return logs  # MFF passive does not trigger if attacker is disabled

        for hero in self.heroes:
            if isinstance(hero, MFF) and hero != attacker and hero.is_alive():
                logs.extend(hero.passive_on_ally_attack(attacker, boss))
        return logs  # MFF passive does not trigger if attacker is disabled
        
        for hero in self.heroes:
            if isinstance(hero, MFF) and hero != attacker and hero.is_alive():
                logs.extend(hero.passive_on_ally_attack(attacker, boss))
        return logs

    def __init__(self, heroes, front_line, back_line):
        self.heroes = heroes
        self.front_line = front_line
        self.back_line = back_line

          # ✅ Give each hero a reference to their team
        for hero in self.heroes:
            hero.team = self
            if hero.artifact and hasattr(hero.artifact, "bind_team"):
                hero.artifact.bind_team(self)

    def energy_gain_on_being_hit(self, target, logs, crit_occurred):
        if not hasattr(target, "energy"):
            return
        gain = 20 if crit_occurred else 10
        target.energy += gain

        if not hasattr(self, "_batched_energy_logs"):
            self._batched_energy_logs = {}

        self._batched_energy_logs.setdefault(gain, []).append(target.name)

    def perform_turn(self, boss, round_num):
        logs = []
        if not boss.is_alive():
            return logs

        # ✅ Grant 50 energy to all heroes at the start of the round (consolidated)
        from game_logic.buff_handler import BuffHandler
        energy_gain_lines = []
        curse_lines = []
        for hero in self.heroes:
            result = BuffHandler.apply_buff(hero, "start_of_round_energy", {
                "attribute": "energy", "bonus": 50, "rounds": 1
            }, boss)
            for line in result:
                if isinstance(line, str) and "offsets" in line:
                    curse_lines.append(line)
                else:
                    energy_gain_lines.append(line)
        if energy_gain_lines:
            grouped = {}
            for l in energy_gain_lines:
                if isinstance(l, str) and "+50 energy" in l:
                    name = l.split()[0]
                    grouped.setdefault(50, []).append(name)
            for amount, names in grouped.items():
                logs.append(f"⚡ Start-of-Round Energy: {', '.join(names)} (+{amount})")
        if curse_lines:
            logs.extend([str(l) for l in curse_lines if isinstance(l, str)])
        if not boss.is_alive():
            return logs
        logs.append(f"⚔️ Team begins actions for Round {round_num}.")

        for hero in self.heroes:
            if hero.is_alive():
                if hero.energy >= 100 and not hero.has_silence:
                    logs.append(f"💥 {hero.name} has enough energy for active skill.")
                    skill_logs = hero.active_skill(boss, self)
                    logs.extend(skill_logs)
                    logs.extend(self.trigger_mff_passive(hero, boss))
                    logs.extend(apply_foresight(hero, "active"))
                    hero.energy = 0
                    logs.append(grant_energy(hero, 50))

                    crit_occurred = any("CRIT" in str(line) for line in skill_logs)
                    self.energy_gain_on_being_hit(boss, logs, crit_occurred)
                else:
                    logs.append(f"🔪 {hero.name} uses basic attack.")
                    skill_logs = hero.basic_attack(boss, self)
                    logs.extend(skill_logs)
                    logs.extend(self.trigger_mff_passive(hero, boss))
                    logs.extend(apply_foresight(hero, "basic"))
                    logs.append(grant_energy(hero, 50))

                    crit_occurred = any("CRIT" in str(line) for line in skill_logs)
                    self.energy_gain_on_being_hit(boss, logs, crit_occurred)

        logs.append(f"🔥 Boss takes its turn.")
        boss_logs = []
        boss_logs.extend(boss.active_skill(self.heroes, round_num))
        boss_logs.extend(boss.basic_attack(self.heroes, round_num))
        boss_logs.extend(boss.counterattack(self.heroes))
        logs.extend(boss_logs)

        crit_hit_heroes = [h for h in self.heroes if h.is_alive()]
        crit_occurred = any("CRIT" in str(line) and any(h.name in str(line) for h in crit_hit_heroes) for line in boss_logs)
        for hero in self.heroes:
            if hero.is_alive():
                self.energy_gain_on_being_hit(hero, logs, crit_occurred)

        # NEW: Trigger post-boss passives like LBRM and PDE
        for hero in self.heroes:
            if hero.is_alive() and hasattr(hero, "passive_trigger"):
                if hero.__class__.__name__ == "PDE":
                    logs.extend(hero.passive_trigger(self.heroes, boss, self))
                else:
                    for ally in self.heroes:
                        if ally != hero and ally.is_alive():
                            logs.extend(hero.passive_trigger(ally, boss, self))

        return logs

    def end_of_round(self, boss, round_num):
        logs = []
        if not boss.is_alive():
            return logs
        logs.append(f"🖚 End of Round {round_num} effects begin.")
        for hero in self.heroes:
            if hero.is_alive():
                logs.extend(hero.end_of_round(boss, self, round_num))
        logs.extend(boss.end_of_round_effects(self.heroes, round_num))
        logs.append(f"🧠 Boss and team end-of-round effects completed.")
        return logs

    def status_descriptions(self):
        return [hero.get_status_description() for hero in self.heroes]
