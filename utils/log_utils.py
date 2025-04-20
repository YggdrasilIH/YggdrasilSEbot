# utils/log_utils.py

def stylize_log(message, category):
    prefix_map = {
        "energy": "🔋",         # Energy gain/loss
        "attack": "⚔️",         # Basic/Active attacks
        "counter": "↩️",        # Counterattacks
        "poison": "🧪",         # Poison/Bleed effects
        "buff": "🛡️",           # Shields/Buffs
        "debuff": "🔻",         # Debuffs (like atk/armor/speed reductions)
        "calamity": "☠️",       # Calamity
        "curse": "🧿",          # Curse of Decay
        "transition": "🟣",     # Transition Skills
        "passive": "🌀"         # Misc/Passives
    }
    return f"{prefix_map.get(category, '')} {message}"
