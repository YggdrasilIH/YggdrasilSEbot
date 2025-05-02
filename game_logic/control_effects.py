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
        duration = active_core.modify_control_duration(2) if active_core else 2

        # Static immunity to one effect
        if hero.immune_control_effect == effect_name:
            continue

        # ✅ Clamp control immunity between 0 and 100
        raw_ctrl = getattr(hero, "ctrl_immunity", 0)
        effective_ctrl = min(max(raw_ctrl, 0), 100)
        if random.random() < (effective_ctrl / 100):
            logs.append(f"🛡️ {hero.name} resists {effect_name.replace('_', ' ').title()} ({effective_ctrl}% Control Immunity).")
            continue

        # ✅ Apply control effect
        setattr(hero, f"has_{effect_name}", True)
        setattr(hero, f"{effect_name}_rounds", duration)
        control_afflicted.append(effect_name)

    if control_afflicted:
        control_list = " and ".join([effect.replace("_", " ").capitalize() for effect in control_afflicted])
        logs.append(f"🔋 {hero.name} is controlled by {control_list} for {duration} rounds.")

        if boss:
            for effect in control_afflicted:
                boss.on_hero_controlled(hero, effect)

    return logs, control_afflicted




def clear_control_effect(hero, effect_name: str):
    setattr(hero, f"has_{effect_name}", False)
    setattr(hero, f"{effect_name}_rounds", 0)
    return f"🧹 {hero.name} has {effect_name.replace('_', ' ').capitalize()} removed."


