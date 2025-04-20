from game_logic.heroes.pde import PDE
from game_logic.boss import Boss
from game_logic.team import Team

def simulate_pde():
    pde = PDE("PDE", 1_000_000_000, 100_000_000, 4000, 100, 30, 150, 100, 0, 100)
    ally1 = PDE("Ally1", 1_000_000_000, 90_000_000, 4000, 100, 30, 150, 100, 0, 100)
    ally2 = PDE("Ally2", 1_000_000_000, 90_000_000, 4000, 100, 30, 150, 100, 0, 100)
    pde.transition_power = 4
    boss = Boss()
    team = Team([pde, ally1, ally2], front_line=[pde], back_line=[ally1, ally2])

    logs = []

    # Simulate start
    logs.append("🔷 Turn 1: PDE uses active skill")
    logs.extend(pde.active_skill(boss, team))

    logs.append("🔷 Turn 2: PDE uses basic attack")
    logs.extend(pde.basic_attack(boss, team))

    logs.append("🔷 Turn 3: Trigger passive effect on control")
    ally1.has_fear = True
    ally2.has_silence = True
    logs.extend(pde.passive_trigger([ally1, ally2], boss, team))

    logs.append("🔷 Turn 4: Boss attacks PDE (simulated)")
    pde.transition_power = 3
    pde.triggered_this_round = False
    logs.extend(pde.on_receive_damage(boss, team, "active"))
    logs.extend(pde.end_of_round(boss, team, round_num=4))

    for line in logs:
        print(line)

if __name__ == "__main__":
    simulate_pde()
