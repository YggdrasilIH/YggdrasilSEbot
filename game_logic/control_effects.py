from game_logic.cores import active_core

def apply_control_effect(hero, effect_name: str, rounds: int, boss=None, team=None):
    logs = []

    if active_core:
        rounds = active_core.modify_control_duration(rounds)

    if hero.immune_control_effect != effect_name:
        setattr(hero, f"has_{effect_name}", True)
        setattr(hero, f"{effect_name}_rounds", rounds)
        message = f"⚠️ {hero.name} is afflicted with {effect_name.replace('_', ' ').capitalize()} for {rounds} rounds."
        logs.append(message)

        if boss and team:
            logs.extend(boss.process_control_buffs(team.heroes))

        # Teamwide reaction (e.g. LBRM energy-based cleanse)
        if hasattr(hero, "team"):
            for ally in hero.team.heroes:
                if ally != hero and hasattr(ally, "on_control_afflicted"):
                    logs.extend(ally.on_control_afflicted(hero, effect_name))

        # Self-cleansing via Wings
        if getattr(hero, "extra_ctrl_removals", 0) > 0 and not getattr(hero, "has_seal_of_light", False):
            logs.append(clear_control_effect(hero, effect_name))
            hero.extra_ctrl_removals -= 1
            if not getattr(hero, "wings_from_transition", False):
                hero.energy += 30
            logs.append(f"✨ {hero.name} removes {effect_name.replace('_', ' ').title()} using Wings.")

        return "\n".join(logs)
    else:
        return f"🛡️ {hero.name} is immune to {effect_name.replace('_', ' ').capitalize()}."
    
    
def clear_control_effect(hero, effect_name: str):
    setattr(hero, f"has_{effect_name}", False)
    setattr(hero, f"{effect_name}_rounds", 0)
    return f"🧹 {hero.name} has {effect_name.replace('_', ' ').capitalize()} removed."

def add_calamity(hero, amount, logs, boss=None):
    hero.calamity += amount
    logs.append(f"💀 {hero.name} gains {amount} Calamity. (Total: {hero.calamity})")

    if hero.calamity >= 5:
        original_immunity = getattr(hero, 'original_ctrl_immunity', 100)
        hero.ctrl_immunity = max(hero.ctrl_immunity, max(0, original_immunity - 100))
        duration = 2
        if active_core:
            duration = active_core.modify_control_duration(duration)

        for effect in ["silence", "fear", "seal_of_light"]:
            if hero.immune_control_effect == effect:
                logs.append(f"🛡️ {hero.name} is immune to {effect.replace('_', ' ').title()}.")
                # Do not apply or clear — effect was never applied
            else:
                logs.append(apply_control_effect(hero, effect, duration, boss=boss, team=hero.team if hasattr(hero, 'team') else None))

        logs.append(f"💀 {hero.name}'s control immunity reduced by 100.")
        hero.calamity = 0
