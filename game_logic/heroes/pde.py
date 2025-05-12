from .base import Hero
import random
from game_logic.damage_utils import hero_deal_damage
from game_logic.buff_handler import BuffHandler
from game_logic.control_effects import clear_control_effect
from utils.log_utils import group_team_buffs
from utils.log_utils import debug


class PDE(Hero):
    def __init__(self, name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                 purify_enable=None, trait_enable=None, artifact=None, lifestar=None):
        super().__init__(name, hp, atk, armor, spd, crit_rate, crit_dmg, ctrl_immunity, hd, precision,
                         purify_enable, trait_enable, artifact, lifestar=lifestar)
        self.transition_power = 0
        self.energy = 0
        self.triggered_this_round = False

    def add_or_update_buff(self, hero, buff_name, buff_data):
        if buff_name in hero.buffs:
            existing = hero.buffs[buff_name]
            if "layers" in buff_data:
                existing["layers"] = min(existing.get("layers", 0) + buff_data.get("layers", 0), 3)

            if "bonus" in buff_data:
                existing["bonus"] += buff_data.get("bonus", 0)
            if "heal_amount" in buff_data:
                existing["heal_amount"] += buff_data.get("heal_amount", 0)
        else:
            hero.apply_buff(buff_name, buff_data)

    def active_skill(self, boss, team):
        logs = []
        if self.has_silence:
            logs.append(f"{self.name} is silenced and cannot use active skill.")
            return logs
        debug(f"{self.name} starts ACTIVE skill")

        # ✅ Damage should trigger counterattack
        logs.extend(hero_deal_damage(
            self, boss, self.atk * (20 + self.skill_damage / 100),
            is_active=True, team=team, allow_counter=True
        ))

        # ❌ Energy drain (no counter)
        logs.append(f"{self.name} reduces {boss.name}'s energy by 50.")
        boss.energy = max(boss.energy - 50, 0)

        # ❌ Buff application (no counter)
        grant_logs = []
        for ally in team.back_line:
            self.add_or_update_buff(ally, "mystical_veil", {"layers": 2, "rounds": 9999})
            self.add_or_update_buff(ally, "regen", {"heal_amount": int(self.atk * 5), "rounds": 2})
            grant_logs.append(f"{ally.name}: Mystical Veil + Regen")
        if grant_logs:
            logs.append(f"✨ PDE grants: {', '.join(grant_logs)}")

        return logs


    def basic_attack(self, boss, team):
        if self.has_fear:
            return [f"{self.name} is feared and fails basic attack."]

        def do_attack():
            logs = []
            debug(f"{self.name} starts BASIC attack")

            # ✅ Main hit triggers counterattack
            logs.extend(hero_deal_damage(
                self, boss, self.atk * (20 + self.skill_damage / 100),
                is_active=False, team=team, allow_counter=True
            ))

            # ❌ Buffs should not trigger counterattack
            target = min([h for h in team.heroes if h.is_alive()], key=lambda h: h.hp, default=self)
            self.add_or_update_buff(target, "mystical_veil", {"layers": 1, "rounds": 9999})
            self.add_or_update_buff(target, "regen", {"heal_amount": int(self.atk * 12), "rounds": 2})
            logs.append(f"✨ PDE grants to {target.name}: Mystical Veil + Regen")

            return logs

        return self.with_basic_flag(do_attack)


    def passive_trigger(self, allies, boss, team):
        if self.has_seal_of_light:
            return []  # Passive blocked by Seal of Light
        logs = []
        cleanse_logs = []
        buff_logs = []

        controlled = [h for h in team.heroes if h.is_alive() and (h.has_fear or h.has_silence or h.has_seal_of_light)]

        to_cleanse = controlled[:2]

        for h in to_cleanse:
            effects = []
            if h.has_fear:
                effects.append("fear")
            if h.has_silence:
                effects.append("silence")
            if h.has_seal_of_light:
                effects.append("seal_of_light")

            if effects:
                chosen = random.choice(effects)
                logs.append(clear_control_effect(h, chosen))
                cleanse_logs.append(f"{h.name}: Cleansed {chosen.replace('_', ' ').title()}")

        for h in controlled:
            if h not in to_cleanse:
                BuffHandler.apply_buff(h, "control_resist", {
                    "attribute": "control_immunity", "bonus": 15, "rounds": 3
                }, boss)
                buff_logs.append(f"{h.name}: +15% Control Immunity")

        BuffHandler.apply_debuff(boss, "speed_down", {
            "attribute": "spd", "bonus": -12, "rounds": 2
        })
        logs.append(f"{self.name} reduces {boss.name}'s speed by 12 for 2 rounds.")

        if cleanse_logs:
            logs.append("🧹 PDE cleanses: " + ", ".join(cleanse_logs))
        if buff_logs:
            logs.append("✨ PDE buffs: " + ", ".join(buff_logs))

        return logs

    def on_receive_damage(self, attacker, team, attack_type):
        if self.has_seal_of_light:
            return []  # Passive blocked by Seal of Light
        
        
        logs = []
        if self._last_damage_received == 0:
            return logs
        if attack_type.lower() in ["basic", "active"]:
            if self.transition_power >= 3:
                logs.append(f"{self.name} is struck by a {attack_type.lower()} skill and triggers transition skill.")
                logs.extend(self.release_transition_skill(team, self.transition_power, attacker))
            else:
                if not self.triggered_this_round and random.random() < 0.8:
                    self.transition_power += 1
                    logs.append(f"{self.name} gains 1 layer of Transition Power (now {self.transition_power}).")
            self.triggered_this_round = True
        return logs

    def release_transition_skill(self, team, tp_before_release, boss):
            logs = []
            if tp_before_release >= 18:
                self.transition_power -= 18
                logs.append(f"{self.name} consumes all 18 TP to release full Transition Skill.")
            else:
                logs.append(f"{self.name} releases Transition Skill (no TP consumed).")

            target = min([h for h in team.heroes if h.is_alive()], key=lambda h: h.hp, default=self)
            self.add_or_update_buff(self, "mystical_veil", {"layers": 1, "rounds": 2})
            self.add_or_update_buff(target, "mystical_veil", {"layers": 1, "rounds": 2})
            logs.append(f"✨ PDE grants Mystical Veil: {self.name} & {target.name}")

            heal_amt = int(self.atk * 12)
            before_self = self.hp
            before_target = target.hp
            self.hp = min(self.max_hp, self.hp + heal_amt)
            target.hp = min(target.max_hp, target.hp + heal_amt)
            actual_self = self.hp - before_self
            actual_target = target.hp - before_target
            self._healing_done += actual_self
            target._healing_done += actual_target
            debug(f"{self.name} transition heals {self.name} for {actual_self} HP ({actual_self / 1e6:.1f}M)")
            debug(f"{self.name} transition heals {target.name} for {actual_target} HP ({actual_target / 1e6:.1f}M)")
            logs.append(f"🩹 PDE heals: {self.name} & {target.name} for {heal_amt // 1_000_000}M each.")

            buffs_applied = []
            for hero in team.back_line:
                BuffHandler.apply_buff(hero, "pde_hd_up", {"attribute": "hd", "bonus": 10, "rounds": 2}, boss)
                buffs_applied.append((hero.name, "+10% HD"))

            highest = max(team.heroes, key=lambda h: h.atk)
            BuffHandler.apply_buff(highest, "pde_dmg_up", {"attribute": "all_damage_dealt", "bonus": 15, "rounds": 2}, boss)
            buffs_applied.append((highest.name, "+15% All Damage Dealt"))

            if tp_before_release >= 6:
                boss.apply_buff("atk_down", {"value": 0.20, "rounds": 2})
                logs.append(f"🔻 {boss.name}'s attack reduced by 20% for 2 rounds.")
                for hero in team.back_line:
                    BuffHandler.apply_buff(hero, "pde_all_dmg_up", {"attribute": "all_damage_dealt", "bonus": 20, "rounds": 3}, boss)
                    buffs_applied.append((hero.name, "+20% All Damage Dealt"))

            if buffs_applied:
                logs.append("✨ PDE Buffs Applied:")
                logs.extend(group_team_buffs(buffs_applied))

            return logs

    def end_of_round(self, boss, team, round_num=None):
        logs = super().end_of_round(boss, team, round_num)
        self.triggered_this_round = False
        return logs
