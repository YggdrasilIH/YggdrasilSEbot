from game_logic.heroes.sqh import SQH
from game_logic.team import Team
from game_logic.boss import Boss

def simulate_sqh():
    sqh = SQH("SQH", 1_000_000_000, 100_000_000, 4000, 100, 50, 150, 0, 0, 100)
    ally = SQH("Ally", 1_000_000_000, 100_000_000, 4000, 100, 50, 150, 0, 0, 100)
    boss = Boss()
    team = Team([sqh, ally], front_line=[sqh], back_line=[ally])
    sqh.transition_power = 6
    
    logs = []
    logs.extend(sqh.start_of_battle(team, boss))
    logs.extend(sqh.active_skill(boss, team))
    logs.extend(sqh.basic_attack(boss, team))
    logs.extend(sqh.on_end_of_round(team, boss))
    logs.extend(sqh.take_damage(500000000, source=boss, team=team))

    for line in logs:
        print(line)

simulate_sqh()
