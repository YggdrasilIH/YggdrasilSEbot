from game_logic.heroes.mff import MFF
from game_logic.heroes.lfa import LFA
from game_logic.heroes.sqh import SQH
from game_logic.heroes.dgn import DGN
from game_logic.heroes.pde import PDE
from game_logic.boss import Boss
from game_logic.pets import Phoenix
from game_logic.team import Team


# ✅ Helper to apply poison
def apply_poison(target, bonus=-0.20, rounds=3, name="test_poison"):
    target.buffs[name] = {
        "attribute": "poison",
        "bonus": bonus,
        "rounds": rounds
    }


# Create one MFF and four other real heroes
hero1 = MFF("MFF", 1e9, 1e7, 0, 100, 100, 150, 0, 0, 0)
hero2 = LFA("LFA", 1e9, 1e7, 0, 100, 100, 150, 0, 0, 0)
hero3 = SQH("SQH", 1e9, 1e7, 0, 100, 100, 150, 0, 0, 0)
hero4 = DGN("DGN", 1e9, 1e7, 0, 100, 100, 150, 0, 0, 0)
hero5 = PDE("PDE", 1e9, 1e7, 0, 100, 100, 150, 0, 0, 0)

team = Team(
    heroes=[hero1, hero2, hero3, hero4, hero5],
    front_line=[hero1, hero2],
    back_line=[hero3, hero4, hero5],
    pet=Phoenix()
)
team.pet.bind_team(team)

boss = Boss()
boss.hp = boss.max_hp = 5_000_000_000
boss.poison_effects = []

logs = []
round_num = 6

# Simulate 3 rounds of active skills and end-of-round triggers
for _ in range(3):
    logs.append(f"🔁 ROUND {round_num}")
    apply_poison(boss)
    boss.apply_buff("test_poison", {"attribute": "poison", "damage": 100, "rounds": 3})

    for hero in team.heroes:
        logs += hero.active_skill(boss, team)

    logs += team.pet.apply_end_of_round(team, boss, round_num)
    logs += team.end_of_round(boss, round_num)
    round_num += 1

# Output
print("=== Poison Bonus Damage Test ===")
for log in logs:
    print(log)

print("\n=== Final Damage Dealt ===")
for hero in team.heroes:
    print(f"{hero.name}: {hero.total_damage_dealt / 1e6:.2f}M")
