import random

class Specter:
    def start_of_round(self, hero, team, boss, round_num):
        logs = []
        if round_num == 1:
            logs.append(f"🔆 Start of Round {round_num} for {hero.name} (Specter)")
            if not hero.has_seal_of_light:
                hero.energy += 50
                logs.append(f"🌟 {hero.name} gains +50 Energy from **Specter** passive (Round 1). Total: {hero.energy}")
                hero.apply_buff("specter_passive_add", {"attribute": "all_damage_dealt", "bonus": 15, "rounds": 1})
                hero.apply_buff("specter_passive_adr", {"attribute": "ADR", "bonus": 20, "rounds": 1})
                logs.append(f"    ➕ {hero.name} gains +15% ADD and +20% ADR for 1 round.")
                eligible_allies = [h for h in team.heroes if h != hero and h.is_alive()]
                if eligible_allies:
                    target = random.choice(eligible_allies)
                    target.apply_buff("specter_passive_add_ally", {"attribute": "all_damage_dealt", "bonus": 15, "rounds": 1})
                    target.apply_buff("specter_passive_adr_ally", {"attribute": "ADR", "bonus": 20, "rounds": 1})
                    logs.append(f"🌟 {target.name} gains +15% ADD and +20% ADR from **Specter** passive (Round 1).")
            else:
                logs.append(f"❌ {hero.name}'s Specter passive (Round 1) blocked by Seal of Light.")
        return logs

    def __init__(self):
        self.star_soul_count = 0
        self.pending_burst = False

    def end_of_round(self, hero, team, boss, round_num):
        logs = []
        logs.append(f"🔚 End of Round {round_num} for {hero.name} (Specter)")
        if hero.has_seal_of_light:
            logs.append(f"❌ {hero.name}'s **Specter** end-of-round effects are blocked by **Seal of Light**.")
            return logs

        # Passive effect every round: Convert 1-2 attribute reductions
        reductions = [
            (name, data) for name, data in hero.buffs.items()
            if isinstance(data, dict) and "attribute" in data and "bonus" in data and data["bonus"] < 0
        ]
        if reductions:
            convert_target = random.choice(reductions)
            attr = convert_target[1]["attribute"]
            bonus_val = abs(convert_target[1]["bonus"])
            remaining_rounds = convert_target[1].get("rounds", 2)
            hero.buffs.pop(convert_target[0])
            hero.apply_buff(f"specter_convert_{attr}", {
                "attribute": attr, "bonus": bonus_val, "rounds": remaining_rounds
            })
            logs.append(f"🔄 {hero.name} converts attribute reduction '{convert_target[0]}' to +{bonus_val} {attr} ({remaining_rounds} rounds).")

            remaining = [r for r in reductions if r != convert_target]
            if remaining and random.random() < 0.3:
                second = random.choice(remaining)
                attr = second[1]["attribute"]
                bonus_val = abs(second[1]["bonus"])
                remaining_rounds = second[1].get("rounds", 2)
                hero.buffs.pop(second[0])
                hero.apply_buff(f"specter_convert_{attr}_extra", {
                    "attribute": attr, "bonus": bonus_val, "rounds": remaining_rounds
                })
                logs.append(f"✨ {hero.name} converts another reduction '{second[0]}' to +{bonus_val} {attr} ({remaining_rounds} rounds) (30% bonus proc).")

        # Burst effects only Rounds 1–5
        if round_num <= 5:
            burst_logs = self.grant_burst_buffs(hero, team, round_num)
            logs.extend(burst_logs)
            logs.append(f"📦 Returned {len(burst_logs)} logs from grant_burst_buffs.")
        return logs


    def on_after_action(self, hero, team):
        print(f"[DEBUG] Specter.on_after_action triggered by {hero.name}")
        if hero.has_seal_of_light:
            return [f"❌ {hero.name}'s **Specter** Star Soul Skill is blocked by **Seal of Light**."]
        logs = []

        if self.pending_burst:
            logs.append(f"🌌 **Star Soul Burst** is triggered by {hero.name}!")
            logs.extend(self.apply_all_effects(hero, team))
            self.pending_burst = False
            self.star_soul_count = 0
            return logs

        logs.append(f"🌠 {hero.name}'s **Specter** triggers a Star Soul Skill.")
        self.star_soul_count += 1

        effect = random.choice(["energy", "add", "adr"])
        logs.extend(self.apply_effect(effect, hero, team))

        if self.star_soul_count >= 3:
            self.pending_burst = True
            logs.append(f"💫 **Star Soul Burst** is now primed! It will activate after {hero.name}'s next action.")

        return logs

    def on_ally_hit(self, target_hero, team, source_type):
        print(f"[DEBUG] Specter.on_ally_hit called for {target_hero.name} from source: {source_type}")
        logs = []
        if source_type not in ["basic", "active"] or not target_hero.is_alive():
            return logs
        if target_hero.has_seal_of_light:
            logs.append(f"❌ {target_hero.name} cannot receive **Specter** passive from being hit due to **Seal of Light**.")
            return logs
        if target_hero.hp > 0.5 * target_hero.max_hp:
            target_hero.energy += 10
            logs.append(f"✨ {target_hero.name} gains +10 Energy from **Specter** (hit while HP > 50%). Total: {target_hero.energy}")
            logs.append(f"✨ {target_hero.name} gains +10 Energy from **Specter** (hit while HP > 50%).")
        else:
            shield_val = int(target_hero.max_hp * 0.08)
            target_hero.shield += shield_val
            logs.append(f"    🛡️ {target_hero.name}'s shield total is now {target_hero.shield}.")
            logs.append(f"🛡️ {target_hero.name} gains a shield of {shield_val} from **Specter** (hit while HP ≤ 50%).")
        return logs

    def apply_effect(self, effect, hero, team):
        print(f"[DEBUG] Specter.apply_effect: {effect} for {hero.name}")
        logs = []
        logs.append(f"✨ Applying Star Soul Skill: {effect.upper()} for {hero.name}")

        if effect == "energy":
            target = max(team.heroes, key=lambda h: h.spd if h.is_alive() else -1)
            target.energy += 100
            logs.append(f"⚡ {target.name} (fastest ally) gains +100 Energy from **Specter**. Total: {target.energy}")
            if not hero.has_seal_of_light:
                hero.energy += 50
                logs.append(f"🌀 {hero.name} gains +50 Energy from Star Soul Skill (self-mirrored). Total: {hero.energy}")
            else:
                logs.append(f"❌ {hero.name}'s mirrored energy gain blocked by Seal of Light.")

        elif effect == "add":
            target = max(team.heroes, key=lambda h: h.atk if h.is_alive() else -1)
            target.apply_buff("specter_add", {"attribute": "all_damage_dealt", "bonus": 20, "rounds": 1})
            logs.append(f"🔑 {target.name} (highest ATK) gains +20% All Damage Dealt for 1 round from **Specter**.")
            if not hero.has_seal_of_light:
                hero.apply_buff("specter_add_self", {"attribute": "all_damage_dealt", "bonus": 10, "rounds": 2})
                logs.append(f"🌀 {hero.name} gains +10% All Damage Dealt for 2 rounds (mirrored).")
            else:
                logs.append(f"❌ {hero.name}'s mirrored ADD buff blocked by Seal of Light.")

        elif effect == "adr":
            target = min(team.heroes, key=lambda h: h.hp if h.is_alive() else float('inf'))
            target.apply_buff("specter_adr", {"attribute": "ADR", "bonus": 25, "rounds": 1})
            logs.append(f"🛡️ {target.name} (lowest HP) gains +25% ADR for 1 round from **Specter**.")
            if not hero.has_seal_of_light:
                hero.apply_buff("specter_adr_self", {"attribute": "ADR", "bonus": 12.5, "rounds": 2})
                logs.append(f"🌀 {hero.name} gains +12.5% ADR for 2 rounds (mirrored).")
            else:
                logs.append(f"❌ {hero.name}'s mirrored ADR buff blocked by Seal of Light.")

        return logs

    def apply_all_effects(self, hero, team):
        print(f"[DEBUG] Specter.apply_all_effects for {hero.name}")
        logs = []
        for effect in ["energy", "add", "adr"]:
            logs.extend(self.apply_effect(effect, hero, team))
        return logs

    def grant_burst_buffs(self, hero, team, round_num):
        logs = []
        logs.append(f"🔆 Specter: Beginning Burst Buff Processing for {hero.name} in Round {round_num}")
        print(f"[DEBUG] Specter.grant_burst_buffs triggered for {hero.name} in Round {round_num}")
        if not hero.has_seal_of_light:
            hero.energy += 50
            hero.apply_buff(f"specter_burst_add_self_{round_num}", {"attribute": "all_damage_dealt", "bonus": 15, "rounds": 1})
            logs.append(f"    ➕ {hero.name} gains +15% ADD for 1 round.")
            hero.apply_buff(f"specter_burst_adr_self_{round_num}", {"attribute": "ADR", "bonus": 20, "rounds": 1})
            logs.append(f"    🛡️ {hero.name} gains +20% ADR for 1 round.")
            logs.append(f"🌟 {hero.name} gains +50 Energy, +15% ADD, +20% ADR from **Specter** burst (Round {round_num}).")
        else:
            logs.append(f"❌ {hero.name}'s Specter burst (Round {round_num}) blocked by Seal of Light.")

        eligible_allies = [h for h in team.heroes if h != hero and h.is_alive()]
        if eligible_allies:
            target = random.choice(eligible_allies)
            target.apply_buff(f"specter_burst_add_ally_{round_num}", {"attribute": "all_damage_dealt", "bonus": 15, "rounds": 1})
            logs.append(f"    ➕ {target.name} gains +15% ADD for 1 round.")
            target.apply_buff(f"specter_burst_adr_ally_{round_num}", {"attribute": "ADR", "bonus": 20, "rounds": 1})
            logs.append(f"    🛡️ {target.name} gains +20% ADR for 1 round.")
            logs.append(f"🌟 {target.name} gains +15% ADD and +20% ADR from **Specter** burst (Round {round_num}).")
        return logs
