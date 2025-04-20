# game_logic/damage_utils.py

from game_logic.buff_handler import BuffHandler
from utils.log_utils import stylize_log
import random
from math import floor

def hero_deal_damage(source, target, base_damage, is_active, team, allow_counter=True, allow_crit=True):
    logs = []
    if not target.is_alive():
        return logs

    crit = False if not allow_crit else random.random() < (source.crit_rate / 100)
    crit_dmg = min(source.crit_dmg, 150)
    precision = min(source.precision, 150)

    damage = base_damage
    if crit:
        # Critical hits do 2x base damage + 1% extra per 1% over 100% crit damage
        damage *= 2 + ((crit_dmg - 100) / 100)

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
        logs.append(f"🟢 {source.name} deals +{poison_extra // 1_000_000}M bonus poison damage to {target.name} (EF3 bonus).")

    # Balanced Strike (Enable)
    if hasattr(source, "trait_enable") and hasattr(source.trait_enable, "apply_crit_bonus"):
        heal_amt, extra_dmg = source.trait_enable.apply_crit_bonus(int(damage), crit)
        damage += extra_dmg
        source.hp = min(source.max_hp, source.hp + heal_amt)
        if heal_amt:
            logs.append(f"❤️ {source.name} heals {heal_amt // 1_000_000}M HP from Balanced Strike.")
        if extra_dmg:
            logs.append(f"🟢 {source.name} deals +{extra_dmg // 1_000_000}M bonus damage from Balanced Strike.")

    # Giant Killer (GK)
    if getattr(source, "gk", False) and source.hp > 0:
        ratio = target.hp / source.hp
        if ratio > 1:
            bonus_steps = floor((ratio - 1) / 0.10)
            bonus_multiplier = min(bonus_steps * 0.02, 1.0)
            damage *= (1 + bonus_multiplier)
            logs.append(f"🟢 {source.name} deals +{int(bonus_multiplier * 100)}% damage from Giant Killer.")

    # Defier (DEF)
    if getattr(source, "defier", False) and target.hp >= 0.70 * target.max_hp:
        damage *= 1.30
        logs.append(f"🟢 {source.name} deals +30% damage from Defier.")

    # DR reduction (offsettable)
    dr = min(getattr(target, "dr", 0), 0.75)
    if dr > 0:
        logs.append(stylize_log("debuff", f"{target.name} reduces damage by {int(dr * 100)}% DR."))
    damage *= (1 - dr)

    # ADR reduction (non-offsettable)
    adr = min(getattr(target, "adr", 0), 0.75)
    if adr > 0:
        logs.append(stylize_log("debuff", f"{target.name} reduces damage by {int(adr * 100)}% ADR."))
    damage *= (1 - adr)

    # Apply shield first
    if target.shield > 0:
        if target.shield >= damage:
            target.shield -= damage
            logs.append(f"🛡️ {target.name}'s shield absorbs {int(damage) // 1_000_000}M damage.")
            damage = 0
        else:
            logs.append(f"🛡️ {target.name}'s shield absorbs {int(target.shield) // 1_000_000}M damage.")
            damage -= target.shield
            target.shield = 0

    # Unbending Will check
    if hasattr(target, "trait_enable") and hasattr(target.trait_enable, "prevent_death"):
        if target.trait_enable.prevent_death(target, damage):
            logs.append(stylize_log("control", f"{target.name} survives fatal damage due to Unbending Will!"))
            damage = target.hp - 1

    # Deal final damage
    damage = max(0, int(damage))
    if hasattr(source, "total_damage_dealt"):
        source.total_damage_dealt += damage

    if hasattr(target, "take_damage"):
        extra_logs = target.take_damage(damage, source, team)
        if isinstance(extra_logs, list):
            logs.extend(extra_logs)
    else:
        target.hp -= damage
        
    if isinstance(damage, int) and damage > 0:
        logs.append(f"🟢 {source.name} deals {damage // 1_000_000}M damage to {target.name} ({'CRIT' if crit else 'Normal'} hit).")

    # Trigger after-attack effects
    if hasattr(source, "after_attack"):
        extra_logs = source.after_attack(source, target, "active" if is_active else "basic", team)
        if isinstance(extra_logs, list):
            logs.extend(extra_logs)

    # Trigger lifestar on_ally_hit for teammates
    for ally in team.heroes:
        if (
            ally != target and ally.is_alive() and
            hasattr(ally, "lifestar") and
            hasattr(ally.lifestar, "on_ally_hit") and
            hasattr(target, "has_seal_of_light")  # Ensure target is a hero
        ):
            extra_logs = ally.lifestar.on_ally_hit(target, team, "active" if is_active else "basic")
            if isinstance(extra_logs, list):
                logs.extend(extra_logs)

    # Trigger on-receive-damage reactions
    if hasattr(target, "on_receive_damage"):
        extra_logs = target.on_receive_damage(damage, team, source)
        if isinstance(extra_logs, list):
            logs.extend(extra_logs)

    # Boss counterattack (only if target is boss and is_active/basic)
    if allow_counter and hasattr(target, "counterattack") and is_active:
        logs.extend(target.counterattack(team.heroes))

    return logs
