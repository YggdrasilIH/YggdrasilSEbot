from game_logic.foresight import apply_foresight 
from game_logic.heroes.mff import MFF
from game_logic.buff_handler import grant_energy, BuffHandler
from utils.log_utils import group_team_buffs
from game_logic.lifestar import Nova

CONTROL_EFFECTS = {"fear", "silence", "seal of light"}

def group_control_effects(logs, team):
    grouped = []

    # Keep only non-control logs, skip duplicates
    for line in logs:
        if isinstance(line, str) and any(effect in line.lower() for effect in CONTROL_EFFECTS):
            continue  # Skip raw control lines
        grouped.append(line)

    # Append final consolidated control status
    for hero in team.heroes:
        if not hero.is_alive():
            continue
        effects = []
        if hero.has_fear:
            effects.append("Fear")
        if hero.has_silence:
            effects.append("Silence")
        if hero.has_seal_of_light:
            effects.append("Seal of Light")
        if effects:
            grouped.append(f"🔻 {hero.name} is controlled by {', '.join(effects)} (2 rounds).")

    return grouped


class Team:
    def __init__(self, heroes, front_line, back_line, pet=None):
        self.heroes = heroes
        self.front_line = front_line
        self.back_line = back_line
        self.pet = pet
        for hero in self.heroes:
            hero.team = self
            if hero.artifact and hasattr(hero.artifact, "bind_team"):
                hero.artifact.bind_team(self)

    def get_line(self, hero):
        if hero in self.front_line:
            return self.front_line
        elif hero in self.back_line:
            return self.back_line
        return []

    def trigger_mff_passive(self, attacker, boss):
        logs = []
        if attacker.has_fear or attacker.has_silence:
            return logs
        for hero in self.heroes:
            if isinstance(hero, MFF) and hero != attacker and hero.is_alive():
                logs.extend(hero.passive_on_ally_attack(attacker, boss))
        return logs

    def energy_gain_on_being_hit(self, target, logs, crit_occurred):
        if not hasattr(target, "energy"):
            return
        gain = 20 if crit_occurred else 10
        target.energy += gain
        if not hasattr(self, "_batched_energy_logs"):
            self._batched_energy_logs = {}
        self._batched_energy_logs.setdefault(gain, []).append(target.name)

    def perform_turn(self, boss, round_num):
        for hero in self.heroes:
            print(f"[DEBUG-ENERGY] {hero.name} pre-turn: {hero.energy}")
        logs = []
        if not boss.is_alive():
            return logs

        # 🔄 Sort by speed before acting
        self.heroes.sort(key=lambda h: h.spd, reverse=True)

        for hero in self.heroes:
            success, msg = BuffHandler.apply_buff(hero, f"start_energy_gain_{round_num}", {
                "attribute": "energy", "bonus": 50, "rounds": 0
            }, boss)
            if msg:
                logs.append(msg)
        logs.append("⚡ All heroes gain +50 energy at start of round.")

        for hero in self.heroes:
            if hero.artifact and hasattr(hero.artifact, "start_of_round"):
                hero.artifact.start_of_round(hero, self, boss, round_num)

        for hero in self.heroes:
            if round_num == 1:
                BuffHandler.apply_buff(hero, "start_ADR", {"attribute": "ADR", "bonus": 50, "rounds": 9999})
                BuffHandler.apply_buff(hero, "start_HD", {"attribute": "HD", "bonus": 10, "rounds": 9999})
            if hero.lifestar and hasattr(hero.lifestar, "start_of_round"):
                logs += hero.lifestar.start_of_round(hero, self, boss, round_num)

        if not boss.is_alive():
            return logs

        logs.append(f"⚔️ Team begins actions for Round {round_num}.")

        for hero in self.heroes:
            if not hero.is_alive():
                continue

            hero.recalculate_stats()
            print(f"[DEBUG-BATTLE] {hero.name} Pre-Attack Stats → ATK: {hero.atk:,} | ADD: {hero.all_damage_dealt:.1f}% | HD: {hero.hd}")
            for name, buff in hero.buffs.items():
                print(f"[DEBUG-BATTLE] {hero.name} buff {name}: {buff}")

            hero._using_real_attack = True
            if hero.energy >= 100 and not hero.has_silence:
                skill_logs = hero.active_skill(boss, self)
                logs.extend(skill_logs)
                hero.energy = 0

                # Buff sharing
                buffs_applied = []
                for ally in self.heroes:
                    if ally.is_alive():
                        key = f"add_on_{hero.name}_active"
                        success, _ = BuffHandler.apply_buff(ally, key, {"attribute": "all_damage_dealt", "bonus": 3, "rounds": 9999}, boss)
                        if success:
                            buffs_applied.append((ally.name, "+3% All Damage Dealt"))
                if buffs_applied:
                    logs.extend(group_team_buffs(buffs_applied))

                if hero.lifestar and hasattr(hero.lifestar, "on_after_action"):
                    logs.extend(hero.lifestar.on_after_action(hero, self, boss) if isinstance(hero.lifestar, Nova) else hero.lifestar.on_after_action(hero, self))
                if hero.artifact and hasattr(hero.artifact, "on_active_skill"):
                    logs.extend(hero.artifact.on_active_skill(self, boss))
                logs.extend(self.trigger_mff_passive(hero, boss))
                logs.extend(apply_foresight(hero, "active"))
                if self.pet and hasattr(self.pet, "on_hero_active"):
                    self.pet.on_hero_active(hero)

                crit_occurred = any("CRIT" in str(line) for line in skill_logs)
                self.energy_gain_on_being_hit(hero, logs, crit_occurred)
            else:
                skill_logs = hero.basic_attack(boss, self)
                logs.extend(skill_logs)
                if hero.lifestar and hasattr(hero.lifestar, "on_after_action"):
                    logs.extend(hero.lifestar.on_after_action(hero, self, boss) if isinstance(hero.lifestar, Nova) else hero.lifestar.on_after_action(hero, self))
                logs.extend(self.trigger_mff_passive(hero, boss))
                logs.extend(apply_foresight(hero, "basic"))
                logs.append(grant_energy(hero, 50))

                crit_occurred = any("CRIT" in str(line) for line in skill_logs)
                self.energy_gain_on_being_hit(hero, logs, crit_occurred)

            hero._using_real_attack = False
            logs.extend(boss.flush_counterattacks(self.heroes))

        # 🔄 Boss action phase
        boss_logs = boss.boss_action(self.heroes, round_num)
        logs.extend(boss_logs)


        # 🌀 Lifestar reactive
        for line in boss_logs:
            for hero in self.heroes:
                if hero.is_alive() and hero.lifestar and hasattr(hero.lifestar, "on_receive_attack"):
                    retaliation_logs = hero.lifestar.on_receive_attack(hero, boss, boss)
                    if retaliation_logs:
                        logs.extend(retaliation_logs)

        # 🟢 Crit reaction after boss skill
        crit_hit_heroes = [h for h in self.heroes if h.is_alive()]
        crit_occurred = any("CRIT" in str(line) and any(h.name in str(line) for h in crit_hit_heroes) for line in boss_logs)
        for hero in self.heroes:
            if hero.is_alive():
                self.energy_gain_on_being_hit(hero, logs, crit_occurred)

        # 🔄 Passive triggers (LBRM, PDE)
        for hero in self.heroes:
            if not hero.is_alive() or not hasattr(hero, "passive_trigger"):
                continue
            if hero.__class__.__name__ == "PDE":
                pde_logs = hero.passive_trigger(self.heroes, boss, self)
                for log in pde_logs:
                    if "removes" in log and "from" in log:
                        print(f"[DEBUG-CLEANSE] PDE triggered cleanse: {log}")
                logs.extend(pde_logs)
            else:
                for ally in self.heroes:
                    if ally != hero and ally.is_alive():
                        p_logs = hero.passive_trigger(ally, boss, self)
                        for log in p_logs:
                            if "removes" in log and "from" in log:
                                if hero.__class__.__name__ == "LBRM":
                                    print(f"[DEBUG-CLEANSE] LBRM triggered cleanse on ally: {log}")
                                else:
                                    print(f"[DEBUG-CLEANSE] {hero.name} triggered cleanse: {log}")
                        logs.extend(p_logs)

        logs = group_control_effects(logs, team=self)
        return logs



    def end_of_round(self, boss, round_num):
        logs = []
        if not boss.is_alive():
            return logs

        logs.append(f"🖚 End of Round {round_num} effects begin.")
        buffs_applied = []

        for hero in self.heroes:
            if hero.is_alive():
                # ✅ FIRST: decrement control effects before any buffs/passives
                if hero.has_fear:
                    hero.fear_rounds -= 1
                    if hero.fear_rounds <= 0:
                        hero.has_fear = False
                        hero.fear_rounds = 0
                if hero.has_silence:
                    hero.silence_rounds -= 1
                    if hero.silence_rounds <= 0:
                        hero.has_silence = False
                        hero.silence_rounds = 0
                if hero.has_seal_of_light:
                    hero.seal_rounds -= 1
                    if hero.seal_rounds <= 0:
                        hero.has_seal_of_light = False
                        hero.seal_rounds = 0

                # ⬇️ Then apply normal end-of-round logic
                if "start_ADR" in hero.buffs:
                    hero.buffs["start_ADR"]["bonus"] -= 10
                    if hero.buffs["start_ADR"]["bonus"] <= 0:
                        del hero.buffs["start_ADR"]
                if "start_HD" in hero.buffs:
                    hero.buffs["start_HD"]["bonus"] += 10
                if hero.hp > 0.5 * hero.max_hp:
                    BuffHandler.apply_buff(hero, f"universal_add_{round_num}", {"attribute": "all_damage_dealt", "bonus": 25, "rounds": 2})
                    buffs_applied.append((hero.name, "+25% All Damage Dealt (2 rounds)"))
                else:
                    hero.shield += int(hero.max_hp * 0.25)
                    buffs_applied.append((hero.name, f"+{int(hero.max_hp * 0.25) / 1_000_000:.0f}M Shield"))

                if hasattr(hero, "end_of_round"):
                    logs += hero.end_of_round(boss, self, round_num)

                if hasattr(hero, "lifestar") and hero.lifestar and hasattr(hero.lifestar, "end_of_round"):
                    logs += hero.lifestar.end_of_round(hero, self, boss, round_num)

        if buffs_applied:
            logs.append("🛡️ End-of-Round Buffs:")
            logs.extend(group_team_buffs(buffs_applied))

        logs.extend(boss.end_of_round_effects(self.heroes, round_num))
        for hero in self.heroes:
            if hero.is_alive() and hero.calamity > 0:
                hero.calamity -= 1

        if self.pet:
            logs += self.pet.apply_end_of_round(self, boss, round_num)

        return logs


    def status_descriptions(self):
        return [hero.get_status_description() for hero in self.heroes]
