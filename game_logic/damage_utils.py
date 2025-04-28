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

    # Phase 1: Base scaling
    damage = base_damage
    if crit:
        damage *= 2 + ((crit_dmg) / 100)
    damage *= (1 + source.hd * 0.007)
    damage *= (1 + precision * 0.003)
    damage *= (1 + source.all_damage_dealt / 100)

    # Save phase 1 result
    phase1 = damage

    # Phase 2: Multiplicative bonuses
    poison_bonus = 0
    if any(isinstance(b, dict) and b.get("attribute") == "poison" for b in getattr(target, "buffs", {}).values()):
        poison_bonus = getattr(source, "bonus_damage_vs_poisoned", 0)

    burn_bonus = 0
    if hasattr(source, "phoenix_burn_bonus_rounds") and source.phoenix_burn_bonus_rounds > 0:
        if hasattr(target, "poison_effects"):
            if any(effect.get("attribute") == "burn" for effect in target.poison_effects):
                burn_bonus = 0.80

    gk = 0
    if getattr(source, "gk", False) and source.hp > 0:
        ratio = target.hp / source.hp
        if ratio > 1:
            bonus_steps = floor((ratio - 1) / 0.10)
            gk = min(bonus_steps * 0.02, 1.0)

    defier = 0.30 if getattr(source, "defier", False) and target.hp >= 0.70 * target.max_hp else 0

    bs_bonus = 0
    if hasattr(source, "trait_enable") and hasattr(source.trait_enable, "apply_crit_bonus"):
        raw_for_bs = base_damage * (1 + source.hd * 0.007) * (1 + precision * 0.003) * (1 + source.all_damage_dealt / 100)
        if crit:
            raw_for_bs *= 2 + ((crit_dmg - 100) / 100)
        heal_amt, extra_dmg = source.trait_enable.apply_crit_bonus(int(raw_for_bs), crit)
        bs_bonus = extra_dmg / raw_for_bs if raw_for_bs > 0 else 0
        if heal_amt > 0:
            source.hp = min(source.max_hp, source.hp + heal_amt)
            logs.append(f"❤️ {source.name} heals {heal_amt // 1_000_000}M HP from Balanced Strike.")

    # Final Phase 2 multiplier
    phase2_multiplier = (1 + poison_bonus) * (1 + burn_bonus) * (1 + gk) * (1 + defier) * (1 + bs_bonus)
    damage = int(phase1 * phase2_multiplier)
    # 🆕 DT outgoing bonus
    if hasattr(source, "dt_level") and source.dt_level > 0:
        dt_bonus = 1 + (source.dt_level * 0.10)  # 10% bonus per level
        damage = int(damage * dt_bonus)
        logs.append(f"🔮 {source.name} gains +{int((dt_bonus - 1) * 100)}% damage from DT level {source.dt_level}.")


    # Apply Abyssal Corruption bonus silently
    if crit:
        bonus = 0
        for buff in getattr(target, "buffs", {}).values():
            if isinstance(buff, dict) and buff.get("attribute") == "crit_damage_taken":
                bonus += buff.get("bonus", 0)
        if bonus:
            damage = int(damage * (1 + bonus / 100))

    # DR / ADR reduction silently
    dr = min(getattr(target, "dr", 0), 0.75)
    adr = min(getattr(target, "adr", 0), 0.75)
    damage *= (1 - dr)
    damage *= (1 - adr)

    # Shield
    if target.shield > 0:
        if target.shield >= damage:
            target.shield -= damage
            damage = 0
        else:
            damage -= target.shield
            target.shield = 0

    # Unbending Will
    if hasattr(target, "trait_enable") and hasattr(target.trait_enable, "prevent_death"):
        if target.trait_enable.prevent_death(target, damage):
            logs.append(stylize_log("control", f"{target.name} survives fatal damage due to Unbending Will!"))
            damage = target.hp - 1

    damage = max(0, int(damage))
    if hasattr(source, "total_damage_dealt"):
        source.total_damage_dealt += damage

    # Final damage application
    if hasattr(target, "take_damage"):
        logs += target.take_damage(damage, source, team) or []
    else:
        target.hp -= damage

    if damage > 0:
        logs.append(f"🟢 {source.name} deals {damage // 1_000_000}M damage to {target.name} ({'CRIT' if crit else 'Normal'} hit).")

    if bs_bonus > 0 and extra_dmg > 0:
        if hasattr(target, "take_damage"):
            logs += target.take_damage(extra_dmg, source, team) or []
        else:
            target.hp -= extra_dmg
        logs.append(f"🟢 {source.name} deals {extra_dmg // 1_000_000}M bonus damage from Balanced Strike.")
        if hasattr(source, "total_damage_dealt"):
            source.total_damage_dealt += extra_dmg

    # After-attack effects
    if hasattr(source, "after_attack"):
        logs += source.after_attack(source, target, "active" if is_active else "basic", team) or []

    # Lifestar triggers
    for ally in team.heroes:
        if ally != target and ally.is_alive() and hasattr(ally, "lifestar") and hasattr(ally.lifestar, "on_ally_hit"):
            if hasattr(target, "has_seal_of_light"):
                logs += ally.lifestar.on_ally_hit(target, team, "active" if is_active else "basic") or []

    # On-receive-damage hooks
    if hasattr(target, "on_receive_damage"):
        logs += target.on_receive_damage(damage, team, source) or []

    # Counterattack
    if allow_counter and hasattr(target, "counterattack"):
        logs += target.counterattack(team.heroes)

    return logs
