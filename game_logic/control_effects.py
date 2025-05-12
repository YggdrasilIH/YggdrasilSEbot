from game_logic.cores import active_core
import random

def apply_control_effect(hero, effects, *args, boss=None, team=None):
    if args:
        if not boss and len(args) > 0:
            boss = args[0]
        if not team and len(args) > 1:
            team = args[1]

    logs = []

    if not isinstance(effects, list):
        effects = [effects]

    control_afflicted = []

    for effect_name in effects:
        # Skip if already applied
        if getattr(hero, f"has_{effect_name}", False):
            continue

        duration = active_core.modify_control_duration(2) if active_core else 2

        # Permanent immunity
        if hero.immune_control_effect == effect_name:
            logs.append(f"🚫 {hero.name} is permanently immune to {effect_name}.")
            continue

        # Bypass 100 ctrl immunity if boss is applying
        ctrl_immunity = getattr(hero, "ctrl_immunity", 0)
        immunity_bypass = False
        if boss:
            ctrl_immunity = max(0, ctrl_immunity - 100)
            immunity_bypass = True

        resist_chance = min(max(ctrl_immunity, 0), 100)
        if random.random() < (resist_chance / 100):
            bypass_note = " (after -100 bypass)" if immunity_bypass else ""
            logs.append(f"🛡️ {hero.name} resists {effect_name.replace('_', ' ').title()} ({resist_chance}% Control Immunity){bypass_note}.")
            continue

        # ✅ Apply effect
        setattr(hero, f"has_{effect_name}", True)
        setattr(hero, f"{effect_name}_rounds", duration)
        control_afflicted.append(effect_name)
        logs.append(f"💥 {hero.name} receives {effect_name.replace('_', ' ').title()} for {duration} rounds.")

        # Boss reacts
        if boss:
            boss.on_hero_controlled(hero, effect_name)

        # Self-cleansing (LBRM)
        if hasattr(hero, "on_control_afflicted"):
            print(f"[DEBUG-CLEANSE-CHECK] {hero.name} checking SELF for {effect_name}: {getattr(hero, f'has_{effect_name}', None)}")
            result = hero.on_control_afflicted(hero, effect_name)
            if result:
                logs += result

        # Teammate cleansing
        if team:
            for ally in team.heroes:
                if ally != hero and hasattr(ally, "on_control_afflicted"):
                    print(f"[DEBUG-CLEANSE-CHECK] {ally.name} checking {hero.name} for {effect_name}: {getattr(hero, f'has_{effect_name}', None)}")
                    result = ally.on_control_afflicted(hero, effect_name)
                    if result:
                        logs += result

        # Passive triggers
        if team:
            for responder in team.heroes:
                if hasattr(responder, "passive_trigger"):
                    logs += responder.passive_trigger(hero, boss, team)

    # Summarize final applied effects (after cleanse attempts)
    final_effects = [e for e in control_afflicted if getattr(hero, f"has_{e}", False)]
    if final_effects:
        control_list = " and ".join([e.replace("_", " ").capitalize() for e in final_effects])
        logs.append(f"🔋 {hero.name} is controlled by {control_list} for {duration} rounds.")

    return logs, control_afflicted



def clear_control_effect(hero, effect_name: str):
    setattr(hero, f"has_{effect_name}", False)
    setattr(hero, f"{effect_name}_rounds", 0)
    return f"🧹 {hero.name} has {effect_name.replace('_', ' ').capitalize()} removed."


