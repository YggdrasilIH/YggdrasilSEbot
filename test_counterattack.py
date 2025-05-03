# test_counterattack.py

from game_logic import Team, Boss
from game_logic.heroes.base import Hero as BaseHero
from game_logic.artifacts import DB
from game_logic.cores import PDECore, active_core
from game_logic.enables import ControlPurify, BalancedStrike
from game_logic.damage_utils import hero_deal_damage

# Create 6 heroes
heroes = [
    BaseHero.from_stats("hero_SQH_Hero", (12e9, 70e6, 3400), artifact=DB()),
    BaseHero.from_stats("hero_LFA_Hero", (20e9, 160e6, 3540), artifact=DB()),
    BaseHero.from_stats("hero_DGN_Hero", (14e9, 110e6, 3200), artifact=DB()),
    BaseHero.from_stats("hero_PDE_Hero", (9e9, 130e6, 3050), artifact=DB()),
    BaseHero.from_stats("hero_LBRM_Hero", (9.9e9, 90e6, 3100), artifact=DB()),
    BaseHero.from_stats("hero_MFF_Hero", (11e9, 60e6, 3300), artifact=DB()),
]

# Set enables
for h in heroes:
    h.set_enables(ControlPurify(), BalancedStrike())

# Split into front and back line
front_line = heroes[:2]
back_line = heroes[2:]

# Construct team (pass all three arguments)
team = Team(heroes, front_line, back_line)
boss = Boss()

# Enable PDECore globally
active_core = PDECore()

# Run 3 total rounds
logs = []

for round_num in range(1, 4):
    logs.append(f"\n🔁 ROUND {round_num} 🔁")

    # Each hero performs a basic attack
    for hero in heroes:
        if hero.is_alive():
            hero._using_real_attack = True
            logs += hero_deal_damage(hero, boss, int(hero.atk * 12), is_active=False, team=team)

    # Boss performs counterattacks
    logs += boss.flush_counterattacks(heroes)

# Summary
print("\n--- COUNTERATTACK TEST SUMMARY ---")
print(f"Boss HP: {boss.hp:.1e}")
print(f"Boss Energy: {boss.energy}")
print(f"Boss HD: {boss.hd}")
print(f"Boss ADD: {boss.all_damage_dealt}%")
print("\nHero Statuses:")
for hero in heroes:
    print(f"{hero.name}: HP {hero.hp/1e6:.0f}M | Calamity {hero.calamity} | Curse {hero.curse_of_decay}")

# Optionally print logs
print("\n--- LOGS ---")
print("\n".join(logs))
