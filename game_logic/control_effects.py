# game_logic/control_effects.py

def apply_control_effect(hero, effect_name: str, rounds: int):
    if hero.immune_control_effect != effect_name:
        setattr(hero, f"has_{effect_name}", True)
        setattr(hero, f"{effect_name}_rounds", rounds)
        return f"⚠️ {hero.name} is afflicted with {effect_name.replace('_', ' ').capitalize()} for {rounds} rounds."
    else:
        return f"🛡️ {hero.name} is immune to {effect_name.replace('_', ' ').capitalize()}."

def clear_control_effect(hero, effect_name: str):
    setattr(hero, f"has_{effect_name}", False)
    setattr(hero, f"{effect_name}_rounds", 0)
    return f"🧹 {hero.name} has {effect_name.replace('_', ' ').capitalize()} removed."
