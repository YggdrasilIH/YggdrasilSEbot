# game_logic/damage_utils.py

from game_logic.buff_handler import BuffHandler
from utils.log_utils import stylize_log
import random
from math import floor

def hero_deal_damage(source, target, base_damage, is_active, team):
    logs = []
    if not target.is_alive():
        return logs

    crit = random.random() < (source.crit_rate / 100)
    crit_dmg = min(source.crit_dmg, 150)
    precision = min(source.precision, 150)

    damage = base_damage
    if crit:
        damage *= (crit_dmg / 100)

    damage *= (1 + source.hd * 0.007)
    damage *= (1 + precision * 0.003)
    damage *= (1 + source.all_damage_dealt / 100)

    # EF3 poison bonus
    if hasattr(source, "ef3_poison_bonus") and any(
        isinstance(buff, dict) and buff.get("attribute") == "poison"
        for buff in getattr(target, "buffs", {}).values()
    ):
        poison_bonus = getattr(source, "ef3_poison_bonus", 0)
        poison_extra = int(damage * poison_bonus)
        damage += poison_extra
        logs.append(stylize_log("damage", f"{source.name} deals +{poison_extra} bonus poison damage to {target.name} (EF3 bonus)."))

    # Balanced Strike (Enable)
    if hasattr(source, "trait_enable") and hasattr(source.trait_enable, "apply_crit_bonus"):
        heal_amt, extra_dmg = source.trait_enable.apply_crit_bonus(int(damage), crit)
        damage += extra_dmg
        source.hp = min(source.max_hp, source.hp + heal_amt)
        if heal_amt:
            logs.append(stylize_log("heal", f"{source.name} heals {heal_amt} HP from Balanced Strike."))
        if extra_dmg:
            logs.append(stylize_log("damage", f"{source.name} deals +{extra_dmg} bonus damage from Balanced Strike."))

    # Giant Killer (GK)
    if getattr(source, "gk", False) and source.hp > 0:
        ratio = target.hp / source.hp
        if ratio > 1:
            bonus_steps = floor((ratio - 1) / 0.10)
            bonus_multiplier = min(bonus_steps * 0.02, 1.0)
            damage *= (1 + bonus_multiplier)
            logs.append(stylize_log("damage", f"{source.name} deals +{int(bonus_multiplier * 100)}% damage from Giant Killer."))

    # Defier (DEF)
    if getattr(source, "defier", False) and target.hp >= 0.70 * target.max_hp:
        damage *= 1.30
        logs.append(stylize_log("damage", f"{source.name} deals +30% damage from Defier."))

    # Cap damage reduction (DR) and all damage reduction (ADR)
    total_reduction = getattr(target, "dr", 0) + getattr(target, "adr", 0)
    total_reduction = min(total_reduction, 0.75)
    damage *= (1 - total_reduction)

    # Apply shield first
    if target.shield > 0:
        if target.shield >= damage:
            target.shield -= damage
            logs.append(stylize_log("shield", f"{target.name}'s shield absorbs {int(damage)} damage."))
            damage = 0
        else:
            logs.append(stylize_log("shield", f"{target.name}'s shield absorbs {int(target.shield)} damage."))
            damage -= target.shield
            target.shield = 0

    # Unbending Will check
    if hasattr(target, "trait_enable") and hasattr(target.trait_enable, "prevent_death"):
        if target.trait_enable.prevent_death(target, damage):
            logs.append(stylize_log("control", f"{target.name} survives fatal damage due to Unbending Will!"))
            damage = target.hp - 1

    # Deal final damage
    damage = max(0, int(damage))
    if hasattr(target, "take_damage"):
        target.take_damage(damage, source, team)
    else:
        target.hp -= damage
    logs.append(stylize_log("damage", f"{source.name} deals {damage} damage to {target.name} ({'CRIT' if crit else 'Normal'} hit)."))

    # Boss counterattack (only if target is boss and is_active/basic)
    if hasattr(target, "counterattack") and is_active:
        logs.extend(target.counterattack(team.heroes))

    return logs

def calculate_final_damage(source, base_damage, is_crit):
    crit_dmg = min(source.crit_dmg, 150)
    precision = min(source.precision, 150)

    if is_crit:
        base_damage *= (crit_dmg / 100)

    base_damage *= (1 + source.hd * 0.007)
    base_damage *= (1 + precision * 0.003)
    base_damage *= (1 + source.all_damage_dealt / 100)

    return int(base_damage)

def apply_direct_damage(source, target, amount, team=None, ignore_shield=False, ignore_reduction=False):
    logs = []
    damage = amount

    if not ignore_reduction:
        total_reduction = getattr(target, "dr", 0) + getattr(target, "adr", 0)
        total_reduction = min(total_reduction, 0.75)
        damage *= (1 - total_reduction)

    if not ignore_shield and target.shield > 0:
        if target.shield >= damage:
            target.shield -= damage
            logs.append(stylize_log("shield", f"{target.name}'s shield absorbs {int(damage)} damage."))
            damage = 0
        else:
            logs.append(stylize_log("shield", f"{target.name}'s shield absorbs {int(target.shield)} damage."))
            damage -= target.shield
            target.shield = 0

    damage = max(0, int(damage))
    target.hp -= damage
    logs.append(stylize_log("damage", f"{source.name} directly deals {damage} damage to {target.name}."))
    return logs
