from game_logic.heroes.sqh import SQH
from game_logic.team import Team
from game_logic.boss import Boss
from game_logic.buff_handler import BuffHandler

def simulate_sqh():
    sqh = SQH("SQH", 1_000_000_000, 100_000_000, 4000, 100, 50, 150, 0, 0, 100)
    ally = SQH("Ally", 1_000_000_000, 100_000_000, 4000, 100, 50, 150, 0, 0, 100)
    boss = Boss()
    team = Team([sqh, ally], front_line=[sqh], back_line=[ally])
    sqh.transition_power = 6
    sqh.crit_dmg = 150
    sqh.crit_rate = 100

    logs = []
    logs.extend(sqh.start_of_battle(team, boss))
    logs.extend(sqh.active_skill(boss, team))
    logs.extend(sqh.basic_attack(boss, team))
    logs.extend(sqh.end_of_round(boss, team))

    damage_amount = 500_000_000
    # Directly apply damage:
    sqh.hp -= damage_amount
    sqh.hp = max(sqh.hp, 0)
    logs.append(f"⚔️ {sqh.name} takes {damage_amount // 1_000_000}M damage (HP: {sqh.hp}/{sqh.max_hp}).")

    # Queen's Guard Counterattack logic (optional):
    if boss.is_alive():
        counters = []
        for ally in team.heroes:
            if ally != sqh and ally.is_alive() and getattr(ally, "queens_guard", False):
                counter_dmg = int(ally.atk * 12)
                boss.hp -= counter_dmg
                boss.hp = max(boss.hp, 0)
                counters.append(f"{ally.name} hits back for {counter_dmg // 1_000_000}M dmg")
                logs.extend(BuffHandler.apply_debuff(boss, "atk_down_counter", {
                    "attribute": "atk", "bonus": -0.03, "rounds": 2
                }))
        if counters:
            logs.append("👑 Queen's Guard counterattacks: " + "; ".join(counters))

    for line in logs:
        print(line)

simulate_sqh()
