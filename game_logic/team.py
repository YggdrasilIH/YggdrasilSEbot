from game_logic.foresight import apply_foresight
from game_logic.heroes.mff import MFF  # Central foresight handler
from game_logic.buff_handler import grant_energy  # Central energy handling

class Team:
    def get_line(self, hero):
        """Return all allies in the same line (front_line or back_line) as the given hero."""
        if hero in self.front_line:
            return self.front_line
        elif hero in self.back_line:
            return self.back_line
        return []
    def trigger_mff_passive(self, attacker, boss):
        logs = []
        if attacker.has_fear or attacker.has_silence:
            return logs  # MFF passive does not trigger if attacker is disabled
        for hero in self.heroes:
            if isinstance(hero, MFF) and hero != attacker and hero.is_alive():
                logs.extend(hero.passive_on_ally_attack(attacker, boss))
        return logs

    def __init__(self, heroes, front_line, back_line):
        self.heroes = heroes
        self.front_line = front_line
        self.back_line = back_line

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
                    add_targets = []
                    for ally in self.heroes:
                        if ally.is_alive():
                            buff_key = f"add_on_{hero.name}_active"
                            if buff_key not in ally.buffs:
                                success, _ = BuffHandler.apply_buff(ally, buff_key, {
                                    "attribute": "all_damage_dealt", "bonus": 3, "rounds": 9999
                                }, boss)
                                if success:
                                    add_targets.append(ally.name)
                    if add_targets:
                        logs.append(f"✨ All Damage Dealt +3%: {', '.join(add_targets)} (from {hero.name}'s active skill)")
                    logs.extend(skill_logs)
                    if hero.lifestar and hasattr(hero.lifestar, "on_after_action"):
                        logs.extend(hero.lifestar.on_after_action(hero, self))
                    if hero.artifact and hasattr(hero.artifact, "on_active_skill"):
                        logs.extend(hero.artifact.on_active_skill(self, boss))
                    logs.extend(self.trigger_mff_passive(hero, boss))
                    logs.extend(apply_foresight(hero, "active"))
                    hero.energy = 0

                    crit_occurred = any("CRIT" in str(line) for line in skill_logs)
                    self.energy_gain_on_being_hit(boss, logs, crit_occurred)
                else:
                    logs.append(f"🔪 {hero.name} uses basic attack.")
                    skill_logs = hero.basic_attack(boss, self)
                    logs.extend(skill_logs)
                    if hero.lifestar and hasattr(hero.lifestar, "on_after_action"):
                        logs.extend(hero.lifestar.on_after_action(hero, self))
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
                hero_logs = []
                
                # Call process_buffs to tick down buffs and debuffs
                hero.process_buffs()  # This will decrement the rounds for buffs and debuffs
                
                # Call the hero's custom end_of_round logic
                if hasattr(hero, "end_of_round"):
                    hero_logs += hero.end_of_round(boss, self, round_num)
                
                # Handle Lifestar end-of-round effects if applicable
                if hasattr(hero, "lifestar") and hero.lifestar and hasattr(hero.lifestar, "end_of_round"):
                    hero_logs += hero.lifestar.end_of_round(hero, self, boss, round_num)

                # Handle Scissors replication logs (if any)
                scissors_logs = [entry for entry in hero_logs if "Scissors" in entry]
                non_scissors_logs = [entry for entry in hero_logs if entry not in scissors_logs]

                # Check if Mirror artifact effects need to be logged
                if hero.artifact and any("Mirror" in str(type(hero.artifact)) for _ in [0]):
                    for entry in hero_logs:
                        if "energy" in entry.lower():
                            logs.append(entry)
                        elif "offsets" in entry:
                            logs.append(entry)

                # If Scissors replication logs are found, process them
                if scissors_logs:
                    effect_map = {}
                    for entry in scissors_logs:
                        if "replicates" in entry:
                            parts = entry.split("replicates")
                            hero_name = parts[0].strip().split()[-1]
                            effect = parts[1].strip().split("from")[0].strip()
                            effect_map.setdefault(effect, []).append(hero_name)
                    logs.append("✂️ Scissors Replication:")
                    for effect, heroes in effect_map.items():
                        logs.append(f"  {effect}: {', '.join(heroes)}")

                logs.extend(non_scissors_logs)

                                # Decrement control effects manually (like fear, silence, etc.)
                if hero.has_fear:
                    hero.fear_rounds -= 1
                    if hero.fear_rounds <= 0:
                        hero.has_fear = False
                        hero.fear_rounds = 0
                        hero_logs.append(f"{hero.name}'s Fear has ended.")

                if hero.has_silence:
                    hero.silence_rounds -= 1
                    if hero.silence_rounds <= 0:
                        hero.has_silence = False
                        hero.silence_rounds = 0
                        hero_logs.append(f"{hero.name}'s Silence has ended.")

                if hero.has_seal_of_light:
                    hero.seal_rounds -= 1
                    if hero.seal_rounds <= 0:
                        hero.has_seal_of_light = False
                        hero.seal_rounds = 0
                        hero_logs.append(f"{hero.name}'s Seal of Light has ended.")

        # Process boss end-of-round effects (if any)
        logs.extend(boss.end_of_round_effects(self.heroes, round_num))

        logs.append(f"🧠 Boss and team end-of-round effects completed.")
        return logs

    def status_descriptions(self):
        return [hero.get_status_description() for hero in self.heroes]
