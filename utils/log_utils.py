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

def group_team_buffs(buffs_applied):
    from collections import defaultdict
    grouped = defaultdict(list)
    logs = []

    for hero_name, buff_description in buffs_applied:
        grouped[buff_description].append(hero_name)

    for buff_desc, heroes in grouped.items():
        hero_list = ', '.join(heroes)
        logs.append(f"{buff_desc} → {hero_list}")

    return logs

def debug(message: str):
    print(f"[DEBUG] {message}")

