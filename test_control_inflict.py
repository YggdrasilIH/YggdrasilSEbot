from game_logic.heroes.lbrm import LBRM
from game_logic.heroes.pde import PDE
from game_logic.boss import Boss
from game_logic.team import Team
from game_logic.heroes.base import Hero
from utils.battle import chunk_logs

class DummyHero(Hero):
    def active_skill(self, boss, team):
        return [f"{self.name} does nothing (active)."]

    def basic_attack(self, boss, team):
        return [f"{self.name} does nothing (basic)."]

# Instantiate heroes
lbrm = LBRM("LBRM", 10_000_000_000, 600_000_000, 3000, 1500, 50, 50, 0, 10, 0)
pde = PDE("PDE", 10_000_000_000, 600_000_000, 3000, 1400, 50, 50, 0, 10, 0)
dummy_allies = [
    DummyHero(f"Dummy{i}", 10_000_000_000, 100_000_000, 3000, 1000 + i * 10, 50, 50, 0, 10, 0)
    for i in range(1, 5)
]
team = Team([lbrm, pde] + dummy_allies, front_line=[lbrm, pde], back_line=dummy_allies)
boss = Boss()

# Boost boss energy so he uses active skill immediately (which gives 2 Calamity)
boss.energy = 100

# Force initial Calamity stack via direct method to simulate counterattacks and debuffs
for h in [dummy_allies[0], dummy_allies[1], lbrm, pde]:
    boss.add_calamity_with_tracking(h, 3, logs=[], boss=boss)  # Now they'll hit 5 after counterattack

# Set energy so all heroes use their actives
for hero in team.heroes:
    hero.energy = 500

# Simulate Round 1
print("🔁 Starting Round 1 Simulation")
active_logs = team.perform_turn(boss, round_num=1)
end_logs = team.end_of_round(boss, round_num=1)

# Print
print("\n".join(chunk_logs("\n".join(active_logs))))
print("\n".join(chunk_logs("\n".join(end_logs))))
