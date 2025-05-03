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
        # Skip if hero already has this control effect
        if getattr(hero, f"has_{effect_name}", False):
            continue

        duration = active_core.modify_control_duration(2) if active_core else 2

        # Static immunity to one effect
        if hero.immune_control_effect == effect_name:
            logs.append(f"🚫 {hero.name} is permanently immune to {effect_name}.")
            continue
        ctrl_immunity = getattr(hero, "ctrl_immunity", 0)
        if boss:
            ctrl_immunity = max(0, ctrl_immunity - 100)  # Boss ignores 100

        resist_chance = min(max(ctrl_immunity, 0), 100)
        if random.random() < (resist_chance / 100):
            logs.append(f"🛡️ {hero.name} resists {effect_name.replace('_', ' ').title()} ({resist_chance}% Control Immunity).")
            continue


        # ✅ Skip if already under this control effect
        # Already afflicted — skip reapplying, but still trigger boss passive
        if getattr(hero, f"has_{effect_name}", False):
            if boss:
                boss.on_hero_controlled(hero, effect_name)
            continue


        # ✅ Apply control effect
        setattr(hero, f"has_{effect_name}", True)
        setattr(hero, f"{effect_name}_rounds", duration)
        control_afflicted.append(effect_name)
        logs.append(f"💥 {hero.name} receives {effect_name.replace('_', ' ').title()} for {duration} rounds.")

        if boss:
            boss.on_hero_controlled(hero, effect_name)

    if control_afflicted:
        control_list = " and ".join([effect.replace("_", " ").capitalize() for effect in control_afflicted])
        logs.append(f"🔋 {hero.name} is controlled by {control_list} for {duration} rounds.")

    return logs, control_afflicted





def clear_control_effect(hero, effect_name: str):
    setattr(hero, f"has_{effect_name}", False)
    setattr(hero, f"{effect_name}_rounds", 0)
    return f"🧹 {hero.name} has {effect_name.replace('_', ' ').capitalize()} removed."


