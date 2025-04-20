from game_logic.heroes.lfa import LFA
from game_logic.boss import Boss
from game_logic.team import Team



def simulate_lfa():
    lfa = LFA("LFA", 1_000_000_000, 100_000_000, 4000, 100, 100, 150, 0, 0, 100)
    boss = Boss()
    team = Team([lfa], front_line=[lfa], back_line=[])

    logs = []
    lfa.transition_power = 12  # Force transition trigger
    logs.extend(lfa.active_skill(boss, team))
    logs.extend(lfa.basic_attack(boss, team))
    if hasattr(lfa, "on_end_of_round"):
        logs.extend(lfa.on_end_of_round(team, boss))

    for line in logs:
        print(line)  # Print raw representation to debug 'damage' entries

simulate_lfa()
