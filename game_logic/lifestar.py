import random
from game_logic.buff_handler import BuffHandler
from utils.log_utils import group_team_buffs
from game_logic.damage_utils import apply_burn

class Nova:
    def __init__(self):
        self.star_soul_count = 0
        self.pending_burst = False
        self.burn_retaliation_count = 0

    def start_of_round(self, hero, team, boss, round_num):
        logs = [f"✨ Start of Round {round_num} for {hero.name} (Nova)"]
        return logs

    def end_of_round(self, hero, team, boss, round_num):
        logs = [f"🖚 End of Round {round_num} for {hero.name} (Nova)"]
        buffs_applied = []

        for enemy in [boss] + getattr(boss, "heroes", []):
            if not enemy.is_alive():
                continue
            BuffHandler.apply_debuff(enemy, "blazing_nova", {
                "attribute": "blazing_nova",
                "bonus": 0,
                "rounds": 1
            })
            BuffHandler.apply_debuff(enemy, "blazing_nova_block_down", {
                "attribute": "block",
                "bonus": -60,
                "rounds": 1
            })
            BuffHandler.apply_debuff(enemy, "blazing_nova_dodge_down", {
                "attribute": "dodge",
                "bonus": -30,
                "rounds": 1
            })
            buffs_applied.append((enemy.name, "-60% Block, -30% Dodge (Blazing Nova)"))

        if buffs_applied:
            logs.append("✨ Nova Passive: Blazing Nova applied to enemies:")
            logs.extend(group_team_buffs(buffs_applied))

        return logs

    def on_after_action(self, hero, team, boss):
        if hero.has_seal_of_light:
            return ["❌ Nova Star Soul Skill blocked by Seal of Light."]

        logs = []
        self.star_soul_count += 1
        logs.append(f"🌠 {hero.name} triggers **Nova** Star Soul Skill.")

        logs.extend(self.apply_star_soul_skill(hero, team, boss))

        if self.star_soul_count >= 3:
            self.pending_burst = True
            logs.append("💫 **Star Soul Burst** is now primed and will activate after next action.")

        if self.pending_burst:
            logs.extend(self.apply_star_soul_burst(hero, team, boss))
            self.pending_burst = False
            self.star_soul_count = 0

        return logs

    def apply_star_soul_skill(self, hero, team, boss):
        logs = []
        enemies = [boss] + getattr(boss, "heroes", [])
        enemies = [e for e in enemies if e.is_alive()]
        if not enemies:
            return logs

        highest_hp_target = max(enemies, key=lambda e: e.hp)
        blazing_targets = [e for e in enemies if any(b.get("attribute") == "blazing_nova" for b in e.buffs.values())]
        random_blazing = random.choice(blazing_targets) if blazing_targets else None

        for target in [highest_hp_target, random_blazing]:
            if target:
                logs.extend(apply_burn(target, int(hero.max_hp * 0.33), 2, source=hero, label="Nova Burn"))

        return logs

    def apply_star_soul_burst(self, hero, team, boss):
        logs = [f"🌟 {hero.name} unleashes **Nova Star Soul Burst**!"]

        enemies = [boss] + getattr(boss, "heroes", [])
        enemies = [e for e in enemies if e.is_alive()]

        for enemy in enemies:
            logs.extend(apply_burn(enemy, int(hero.max_hp * 0.33), 3, source=hero, label="Nova Burst DOT"))
            if any(b.get("attribute") == "blazing_nova" for b in enemy.buffs.values()):
                logs.extend(apply_burn(enemy, int(hero.max_hp * 0.33), 3, source=hero, label="Bonus Nova DOT"))

        hero.energy += 100
        logs.append(f"⚡ {hero.name} gains +100 Energy from Nova Burst.")

        alive_allies = [h for h in team.heroes if h.is_alive() and h != hero]
        chosen = random.sample(alive_allies, min(4, len(alive_allies)))
        for ally in chosen:
            for _ in range(3):
                BuffHandler.apply_buff(ally, f"nova_heal_{random.randint(1000,9999)}", {
                    "attribute": "regen",
                    "heal_amount": int(hero.max_hp * 0.33),
                    "rounds": 1
                })
                logs.append(f"🢕 {ally.name} receives 33% Max HP healing from Nova Burst.")

        return logs

    def on_receive_attack(self, hero, attacker, boss):
        logs = []
        if not attacker.is_alive():
            return logs
        if any(b.get("attribute") == "blazing_nova" for b in attacker.buffs.values()):
            logs.append(f"🔥 {attacker.name} has Blazing Nova and triggers retaliation.")
            logs.extend(apply_burn(attacker, int(hero.max_hp * 0.33), 2, source=hero, label="Nova Retaliation DOT"))
            self.burn_retaliation_count += 1

            if self.burn_retaliation_count >= 3:
                logs.append(f"🔥 {hero.name}'s retaliation counter reaches 3 → AOE burn triggered.")
                enemies = [boss] + getattr(boss, "heroes", [])
                for enemy in enemies:
                    if enemy.is_alive():
                        logs.extend(apply_burn(enemy, int(hero.max_hp * 0.33), 2, source=hero, label="Nova Passive AOE"))
                self.burn_retaliation_count = 0
        return logs



class Specter:
    def __init__(self):
        self.star_soul_count = 0
        self.pending_burst = False

    def start_of_round(self, hero, team, boss, round_num):
        logs = []
        buffs_applied = []
        if round_num == 1:
            logs.append(f"🔆 Start of Round {round_num} for {hero.name} (Specter)")
            if not hero.has_seal_of_light:
                hero.energy += 50
                logs.append(f"🌟 {hero.name} gains +50 Energy from **Specter** passive (Round 1). Total: {hero.energy}")
                BuffHandler.apply_buff(hero, "specter_passive_add", {"attribute": "all_damage_dealt", "bonus": 15, "rounds": 1})
                BuffHandler.apply_buff(hero, "specter_passive_adr", {"attribute": "ADR", "bonus": 20, "rounds": 1})
                buffs_applied.append((hero.name, "+15% ADD and +20% ADR"))
                eligible_allies = [h for h in team.heroes if h != hero and h.is_alive()]
                if eligible_allies:
                    target = random.choice(eligible_allies)
                    BuffHandler.apply_buff(target, "specter_passive_add_ally", {"attribute": "all_damage_dealt", "bonus": 15, "rounds": 1})
                    BuffHandler.apply_buff(target, "specter_passive_adr_ally", {"attribute": "ADR", "bonus": 20, "rounds": 1})
                    buffs_applied.append((target.name, "+15% ADD and +20% ADR"))
            else:
                logs.append(f"❌ {hero.name}'s Specter passive (Round 1) blocked by Seal of Light.")
        if buffs_applied:
            logs.append("✨ Specter Start Buffs:")
            logs.extend(group_team_buffs(buffs_applied))
        return logs

    def end_of_round(self, hero, team, boss, round_num):
        logs = []
        buffs_applied = []
        logs.append(f"🔚 End of Round {round_num} for {hero.name} (Specter)")
        if hero.has_seal_of_light:
            logs.append(f"❌ {hero.name}'s **Specter** end-of-round effects are blocked by **Seal of Light**.")
            return logs

        # Group all reductions by attribute (e.g., all -atk, all -armor)
        from collections import defaultdict

        attr_reduction_groups = defaultdict(list)
        for name, data in hero.buffs.items():
            if isinstance(data, dict) and "attribute" in data and "bonus" in data and data["bonus"] < 0:
                attr_reduction_groups[data["attribute"]].append((name, data))

        # Convert one full stack
        logs = []
        converted_attrs = []
        if attr_reduction_groups:
            chosen_attr = random.choice(list(attr_reduction_groups.keys()))
            for name, debuff in attr_reduction_groups[chosen_attr]:
                hero.buffs.pop(name)
            total_bonus = sum(abs(d["bonus"]) for _, d in attr_reduction_groups[chosen_attr])
            duration = max(d.get("rounds", 2) for _, d in attr_reduction_groups[chosen_attr])
            BuffHandler.apply_buff(hero, f"specter_convert_{chosen_attr}", {
                "attribute": chosen_attr,
                "bonus": total_bonus,
                "rounds": duration
            })
            logs.append(f"🔄 {hero.name} converts all reductions of {chosen_attr} (+{total_bonus}) for {duration} rounds.")
            converted_attrs.append(chosen_attr)

        # 30% chance to convert another different attribute stack
        remaining_attrs = [attr for attr in attr_reduction_groups if attr not in converted_attrs]
        if remaining_attrs and random.random() < 0.3:
            second_attr = random.choice(remaining_attrs)
            for name, debuff in attr_reduction_groups[second_attr]:
                hero.buffs.pop(name)
            total_bonus = sum(abs(d["bonus"]) for _, d in attr_reduction_groups[second_attr])
            duration = max(d.get("rounds", 2) for _, d in attr_reduction_groups[second_attr])
            BuffHandler.apply_buff(hero, f"specter_convert_{second_attr}_extra", {
                "attribute": second_attr,
                "bonus": total_bonus,
                "rounds": duration
            })
            logs.append(f"✨ {hero.name} converts another reduction stack of {second_attr} (+{total_bonus}) for {duration} rounds (30% bonus proc).")

        if round_num <= 5:
            burst_logs = self.grant_burst_buffs(hero, team, round_num)
            logs.extend(burst_logs)

        if buffs_applied:
            logs.append("✨ Specter End-of-Round Conversions:")
            logs.extend(group_team_buffs(buffs_applied))

        return logs

    def on_after_action(self, hero, team):
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
        logs = []
        if source_type not in ["basic", "active"] or not target_hero.is_alive():
            return logs
        if target_hero.has_seal_of_light:
            logs.append(f"❌ {target_hero.name} cannot receive **Specter** passive from being hit due to **Seal of Light**.")
            return logs
        if target_hero.hp > 0.5 * target_hero.max_hp:
            target_hero.energy += 10
            logs.append(f"✨ {target_hero.name} gains +10 Energy from **Specter** (hit while HP > 50%). Total: {target_hero.energy}")
        else:
            shield_val = int(target_hero.max_hp * 0.08)
            target_hero.shield += shield_val
            logs.append(f"🛡️ {target_hero.name} gains a shield of {shield_val} from **Specter** (hit while HP ≤ 50%).")
        return logs

    def apply_effect(self, effect, hero, team):
        logs = []
        buffs_applied = []
        logs.append(f"✨ Applying Star Soul Skill: {effect.upper()} for {hero.name}")

        if effect == "energy":
            target = max(team.heroes, key=lambda h: h.spd if h.is_alive() else -1)
            target.energy += 100
            logs.append(f"⚡ {target.name} (fastest ally) gains +100 Energy from **Specter**. Total: {target.energy}")
            if not hero.has_seal_of_light:
                hero.energy += 50
                logs.append(f"🌀 {hero.name} gains +50 Energy from Star Soul Skill (self-mirrored). Total: {hero.energy}")

        elif effect == "add":
            target = max(team.heroes, key=lambda h: h.atk if h.is_alive() else -1)
            BuffHandler.apply_buff(target, "specter_add", {"attribute": "all_damage_dealt", "bonus": 20, "rounds": 1})
            buffs_applied.append((target.name, "+20% All Damage Dealt"))
            if not hero.has_seal_of_light:
                BuffHandler.apply_buff(hero, "specter_add_self", {"attribute": "all_damage_dealt", "bonus": 10, "rounds": 2})
                buffs_applied.append((hero.name, "+10% All Damage Dealt"))

        elif effect == "adr":
            target = min(team.heroes, key=lambda h: h.hp if h.is_alive() else float('inf'))
            BuffHandler.apply_buff(target, "specter_adr", {"attribute": "ADR", "bonus": 25, "rounds": 1})
            buffs_applied.append((target.name, "+25% ADR"))
            if not hero.has_seal_of_light:
                BuffHandler.apply_buff(hero, "specter_adr_self", {"attribute": "ADR", "bonus": 12.5, "rounds": 2})
                buffs_applied.append((hero.name, "+12.5% ADR"))

        if buffs_applied:
            logs.append("✨ Specter Buffs from Star Soul Skill:")
            logs.extend(group_team_buffs(buffs_applied))

        return logs

    def apply_all_effects(self, hero, team):
        logs = []
        for effect in ["energy", "add", "adr"]:
            logs.extend(self.apply_effect(effect, hero, team))
        return logs

    def grant_burst_buffs(self, hero, team, round_num):
        logs = []
        buffs_applied = []
        logs.append(f"🔆 Specter: Beginning Burst Buff Processing for {hero.name} in Round {round_num}")
        if not hero.has_seal_of_light:
            hero.energy += 50
            BuffHandler.apply_buff(hero, f"specter_burst_add_self_{round_num}", {"attribute": "all_damage_dealt", "bonus": 15, "rounds": 1})
            buffs_applied.append((hero.name, "+15% ADD"))
            BuffHandler.apply_buff(hero, f"specter_burst_adr_self_{round_num}", {"attribute": "ADR", "bonus": 20, "rounds": 1})
            buffs_applied.append((hero.name, "+20% ADR"))

        eligible_allies = [h for h in team.heroes if h != hero and h.is_alive()]
        if eligible_allies:
            target = random.choice(eligible_allies)
            BuffHandler.apply_buff(target, f"specter_burst_add_ally_{round_num}", {"attribute": "all_damage_dealt", "bonus": 15, "rounds": 1})
            buffs_applied.append((target.name, "+15% ADD"))
            BuffHandler.apply_buff(target, f"specter_burst_adr_ally_{round_num}", {"attribute": "ADR", "bonus": 20, "rounds": 1})
            buffs_applied.append((target.name, "+20% ADR"))

        if buffs_applied:
            logs.append("✨ Specter Burst Buffs:")
            logs.extend(group_team_buffs(buffs_applied))

        return logs
