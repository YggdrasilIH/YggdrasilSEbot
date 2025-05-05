from game_logic.buff_handler import BuffHandler
from utils.log_utils import stylize_log
import random
from math import floor
from game_logic.boss import Boss
from collections import namedtuple

Hit = namedtuple("Hit", ["damage", "can_crit"])

def hero_deal_damage(source, target, base_damage, is_active, team, hits=1, allow_counter=True, allow_crit=True, hit_list=None, crit_chance_bonus=0):

    logs = []
    if not target.is_alive():
        return logs

    manually_flagged = hasattr(source, "_using_real_attack") and source._using_real_attack
    temp_flagged = False

    is_basic = getattr(source, "_current_action_type", None) == "basic"
    is_basic_or_active = is_active or is_basic

    if isinstance(target, Boss) and allow_counter and is_basic_or_active and not manually_flagged:
        source._using_real_attack = True
        temp_flagged = True

    crit_dmg = min(source.crit_dmg, 150)
    precision = min(source.precision, 150)

    all_hits = []
    any_non_crit = False
    any_crit = False

    if hit_list is not None:
        for hit in hit_list:
            dmg = hit["damage"]
            can_crit = hit.get("can_crit", True)
            crit = False
            if can_crit and allow_crit:
                crit_chance = min(source.crit_rate + crit_chance_bonus, 100)
                crit = random.random() < (crit_chance / 100)
                dmg *= (1.5 + (crit_dmg / 100) * 2) if crit else 1.0
            else:
                dmg *= 1.0
            all_hits.append((dmg, crit))
            if not crit:
                any_non_crit = True
            if crit:
                any_crit = True
    else:
        for _ in range(hits):
            crit = False
            if allow_crit:
                crit = random.random() < (source.crit_rate / 100)
                dmg = base_damage * (1.5 + (crit_dmg / 100) * 2) if crit else base_damage * 1.0
            else:
                dmg = base_damage * 1.0
            all_hits.append((dmg, crit))
            if not crit:
                any_non_crit = True
            if crit:
                any_crit = True


    total_damage = sum(d for d, _ in all_hits)

    # Phase 1 modifiers
    total_damage *= (1 + source.hd * 0.007)
    total_damage *= (1 + precision * 0.003)
    total_damage *= (1 + source.all_damage_dealt / 100)

    # Phase 2 multipliers
    poison_bonus = 0
    if any(isinstance(b, dict) and b.get("attribute") == "poison" for b in getattr(target, "buffs", {}).values()):
        poison_bonus = getattr(source, "bonus_damage_vs_poisoned", 0)

    burn_bonus = 0
    if hasattr(source, "phoenix_burn_bonus_rounds") and source.phoenix_burn_bonus_rounds > 0:
        if hasattr(target, "poison_effects") and any(
            effect.get("attribute") == "burn" and effect.get("rounds", 0) > 0
            for effect in target.poison_effects
        ):
            burn_bonus = 0.80

    gk = 0
    if getattr(source, "gk", False) and source.hp > 0:
        ratio = target.hp / source.hp
        if ratio > 1:
            bonus_steps = floor((ratio - 1) / 0.10)
            gk = min(bonus_steps * 0.02, 1.0)

    defier = 0.30 if getattr(source, "defier", False) and target.hp >= 0.70 * target.max_hp else 0
    hp_bonus = 0.12 if target.hp > source.hp else 0
    hp_percent = target.hp / target.max_hp if target.max_hp > 0 else 1
    maim_bonus = round((1 - hp_percent) * 0.30, 4)

    phase2_multiplier = (1 + poison_bonus) * (1 + burn_bonus) * (1 + gk) * (1 + defier) * (1 + hp_bonus) * (1 + maim_bonus)
    total_damage *= phase2_multiplier


    if hasattr(source, "dt_level") and source.dt_level > 0:
        dt_bonus = 1 + (source.dt_level * 0.10)
        total_damage *= dt_bonus
        logs.append(f"🔮 {source.name} gains +{int((dt_bonus - 1) * 100)}% damage from DT level {source.dt_level}.")

    # Apply crit_damage_taken bonus if any hit crit
    if any_crit:
        bonus = sum(buff.get("bonus", 0) for buff in getattr(target, "buffs", {}).values()
                    if isinstance(buff, dict) and buff.get("attribute") == "crit_damage_taken")
        if bonus:
            total_damage *= (1 + bonus / 100)

    # Shrink multiplier (if target has Shrink applied)
    if isinstance(target, Boss) and hasattr(target, "shrink_debuff") and target.shrink_debuff:
        shrink = target.shrink_debuff
        total_damage *= shrink.get("multiplier_received", 1.0)

    # Balanced Strike final damage boost (after all multipliers)
    if any_non_crit:
        bonus_damage = total_damage * 0.30
        total_damage += bonus_damage
        logs.append(f"🔹 {source.name} gains +{int(bonus_damage) // 1_000_000}M from Balanced Strike (post-multiplier).")

    # Healing and extra bonus from trait_enable
    if hasattr(source, "trait_enable") and hasattr(source.trait_enable, "apply_crit_bonus"):
        heal_amt, extra_dmg = source.trait_enable.apply_crit_bonus(int(total_damage), not any_non_crit)
        if heal_amt > 0:
            source.hp = min(source.max_hp, source.hp + heal_amt)
            logs.append(f"❤️ {source.name} heals {heal_amt // 1_000_000}M HP from Balanced Strike.")
        if extra_dmg > 0:
            total_damage += extra_dmg
            logs.append(f"🔹 {source.name} gains +{extra_dmg // 1_000_000}M bonus damage from Balanced Strike.")

    # DR and ADR
    dr = min(getattr(target, "dr", 0), 0.75)
    adr = min(getattr(target, "adr", 0), 0.75)
    total_damage *= (1 - dr)
    total_damage *= (1 - adr)

    if target.shield > 0:
        absorbed = min(target.shield, total_damage)
        target.shield -= absorbed
        total_damage -= absorbed
        logs.append(f"🛡️ {target.name} absorbs {int(absorbed) // 1_000_000}M damage with Shield.")

    if hasattr(target, "trait_enable") and hasattr(target.trait_enable, "prevent_death"):
        if target.trait_enable.prevent_death(target, int(total_damage)):
            logs.append(stylize_log("control", f"{target.name} survives fatal damage due to Unbending Will!"))
            total_damage = target.hp - 1

    final_damage = max(0, int(total_damage))
    if hasattr(source, "total_damage_dealt"):
        source.total_damage_dealt += final_damage

    if hasattr(target, "take_damage"):
        logs += target.take_damage(final_damage, source, team) or []
    else:
        target.hp -= final_damage

    logs.append(f"🔹 {source.name} deals {final_damage // 1_000_000}M damage to {target.name}.")

    if hasattr(source, "after_attack"):
        logs += source.after_attack(source, target, "active" if is_active else "basic", team) or []

    for ally in team.heroes:
        if ally != target and ally.is_alive() and hasattr(ally, "lifestar") and hasattr(ally.lifestar, "on_ally_hit"):
            if hasattr(target, "has_seal_of_light"):
                logs += ally.lifestar.on_ally_hit(target, team, "active" if is_active else "basic") or []

    if hasattr(target, "on_receive_damage"):
        logs += target.on_receive_damage(final_damage, team, source) or []

    if temp_flagged:
        source._using_real_attack = False

    return logs

def apply_flat_reduction(hero, damage):
    if hero.name == "LFA":
        return int(damage * 0.90)
    else:
        return int(damage * 0.70)

def apply_burn(target, damage, rounds, source=None, label="Burn"):
    logs = []
    burn_entry = {
        "attribute": "burn",
        "damage": damage,
        "rounds": rounds
    }

    if hasattr(target, "poison_effects"):
        target.poison_effects.append(burn_entry)
        logs.append(f"🔥 {target.name} is burned for {damage // 1_000_000}M over {rounds} rounds. ({label})")
    else:
        logs.append(f"⚠️ Burn failed: {target.name} has no poison_effects list.")
    return logs
