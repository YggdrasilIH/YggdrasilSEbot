from game_logic.cores import active_core

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
    boss_bonuses = []

    for effect_name in effects:
        if active_core:
            duration = active_core.modify_control_duration(2)
        else:
            duration = 2

        if hero.immune_control_effect == effect_name:
            continue  # Skip logging Seal of Light immunity

        setattr(hero, f"has_{effect_name}", True)
        setattr(hero, f"{effect_name}_rounds", duration)
        control_afflicted.append(effect_name)

        if boss and team:
            if effect_name == "fear":
                boss.hd += 50
                boss_bonuses.append("+50 HD")
            elif effect_name == "silence":
                boss.energy += 50
                boss_bonuses.append("+50 Energy")

    if control_afflicted:
        control_list = " and ".join([effect.replace("_", " ").capitalize() for effect in control_afflicted])
        logs.append(f"🔋 {hero.name} is controlled by {control_list} for {duration} rounds.")

    if boss_bonuses:
        bonus_list = " and ".join(boss_bonuses)
        logs.append(f"✨ Boss gains {bonus_list}.")

    return logs


def clear_control_effect(hero, effect_name: str):
    setattr(hero, f"has_{effect_name}", False)
    setattr(hero, f"{effect_name}_rounds", 0)
    return f"🧹 {hero.name} has {effect_name.replace('_', ' ').capitalize()} removed."


def add_calamity(hero, amount, logs, boss=None):
    previous = hero.calamity
    hero.calamity += amount
    if previous < 5 and hero.calamity >= 5:
        original_immunity = getattr(hero, 'original_ctrl_immunity', 100)
        hero.ctrl_immunity = max(hero.ctrl_immunity, max(0, original_immunity - 100))

        effects_to_apply = []
        for effect in ["silence", "fear", "seal_of_light"]:
            if hero.immune_control_effect == effect:
                logs.append(f"🛡️ {hero.name} is immune to {effect.replace('_', ' ').title()}.")
            else:
                effects_to_apply.append(effect)

        if effects_to_apply:
            logs.extend(apply_control_effect(hero, effects_to_apply, boss=boss, team=hero.team if hasattr(hero, 'team') else None))

        hero.calamity = 0
