from game_logic.buff_handler import BuffHandler
from utils.log_utils import stylize_log
import random
from math import floor
from game_logic.boss import Boss

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

def hero_deal_damage(source, target, base_damage, is_active, team, allow_counter=True, allow_crit=True):
    logs = []
    if not target.is_alive():
        return logs

    manually_flagged = hasattr(source, "_using_real_attack") and source._using_real_attack
    temp_flagged = False

    is_basic = getattr(source, "_current_action_type", None) == "basic"
    is_basic_or_active = is_active or is_basic

    # 🧠 Inject real_attack flag if this is an active or basic vs Boss
    if isinstance(target, Boss) and allow_counter and is_basic_or_active and not manually_flagged:
        print(f"[DEBUG] Auto-setting _using_real_attack for {source.name} (target is Boss).")
        source._using_real_attack = True
        temp_flagged = True

    crit = False if not allow_crit else random.random() < (source.crit_rate / 100)
    crit_dmg = min(source.crit_dmg, 150)
    precision = min(source.precision, 150)

    damage = base_damage
    if crit:
        damage *= 1.5 + (crit_dmg / 100) * 2
    damage *= (1 + source.hd * 0.007)
    damage *= (1 + precision * 0.003)
    damage *= (1 + source.all_damage_dealt / 100)
    phase1 = damage

    # Phase 2 multipliers
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
    hp_bonus = 0
    if target.hp > source.hp:
        hp_bonus = 0.12
        logs.append(f"🟥 {source.name} gains +12% bonus vs higher-HP target.")

    maim_bonus = 0
    if target.max_hp > 0:
        hp_percent = target.hp / target.max_hp
        maim_bonus = round((1 - hp_percent) * 0.30, 4)
        if maim_bonus > 0:
            logs.append(f"🪓 {source.name} gains +{int(maim_bonus * 100)}% Maim bonus (target at {int(hp_percent * 100)}% HP).")

    phase2_multiplier = (1 + poison_bonus) * (1 + burn_bonus) * (1 + gk) * (1 + defier) * (1 + hp_bonus) * (1 + maim_bonus)
    damage = int(phase1 * phase2_multiplier)

    if hasattr(source, "dt_level") and source.dt_level > 0:
        dt_bonus = 1 + (source.dt_level * 0.10)
        damage = int(damage * dt_bonus)
        logs.append(f"🔮 {source.name} gains +{int((dt_bonus - 1) * 100)}% damage from DT level {source.dt_level}.")

    if hasattr(source, "trait_enable") and hasattr(source.trait_enable, "apply_crit_bonus"):
        heal_amt, extra_dmg = source.trait_enable.apply_crit_bonus(damage, crit)
        if heal_amt > 0:
            source.hp = min(source.max_hp, source.hp + heal_amt)
            logs.append(f"❤️ {source.name} heals {heal_amt // 1_000_000}M HP from Balanced Strike.")
        if extra_dmg > 0:
            damage += extra_dmg
            logs.append(f"🟢 {source.name} gains +{extra_dmg // 1_000_000}M bonus damage from Balanced Strike.")

    if crit:
        bonus = 0
        for buff in getattr(target, "buffs", {}).values():
            if isinstance(buff, dict) and buff.get("attribute") == "crit_damage_taken":
                bonus += buff.get("bonus", 0)
        if bonus:
            damage = int(damage * (1 + bonus / 100))

    dr = min(getattr(target, "dr", 0), 0.75)
    adr = min(getattr(target, "adr", 0), 0.75)
    damage *= (1 - dr)
    damage *= (1 - adr)

    if target.shield > 0:
        absorbed = min(target.shield, damage)
        target.shield -= absorbed
        damage -= absorbed
        logs.append(f"🛡️ {target.name} absorbs {absorbed // 1_000_000}M damage with Shield.")

    if hasattr(target, "trait_enable") and hasattr(target.trait_enable, "prevent_death"):
        if target.trait_enable.prevent_death(target, damage):
            logs.append(stylize_log("control", f"{target.name} survives fatal damage due to Unbending Will!"))
            damage = target.hp - 1

    damage = max(0, int(damage))
    if hasattr(source, "total_damage_dealt"):
        source.total_damage_dealt += damage

    if hasattr(target, "take_damage"):
        print(f"[DEBUG] {source.name} → Dealing {damage} to {target.name} (calling take_damage)")
        logs += target.take_damage(damage, source, team) or []
    else:
        target.hp -= damage

    print(f"[DEBUG] {source.name} → Final damage to {target.name}: {damage} (real_attack={getattr(source, '_using_real_attack', False)})")

    if damage > 0:
        logs.append(f"🟢 {source.name} deals {damage // 1_000_000}M damage to {target.name} ({'CRIT' if crit else 'Normal'} hit).")

    if hasattr(source, "after_attack"):
        logs += source.after_attack(source, target, "active" if is_active else "basic", team) or []

    for ally in team.heroes:
        if ally != target and ally.is_alive() and hasattr(ally, "lifestar") and hasattr(ally.lifestar, "on_ally_hit"):
            if hasattr(target, "has_seal_of_light"):
                logs += ally.lifestar.on_ally_hit(target, team, "active" if is_active else "basic") or []

    if hasattr(target, "on_receive_damage"):
        logs += target.on_receive_damage(damage, team, source) or []

    # ❌ Do NOT flush counterattack here
    # Boss will handle it at end of hero turns

    if temp_flagged:
        source._using_real_attack = False
        print(f"[DEBUG] {source.name} → Reset _using_real_attack after temporary injection.")

    return logs


