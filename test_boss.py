from game_logic.heroes.lbrm import LBRM
from game_logic.heroes import Hero
from game_logic.boss import Boss
from game_logic.team import Team
from game_logic.damage_utils import hero_deal_damage

class DummyHero(Hero):
    def __init__(self, name="Dummy1"):
        super().__init__(name, 1_000_000_000, 100_000_000, 2000, 2000, 30, 50, 0, 0, 0)

# Setup entities
boss = Boss()
lbrm = LBRM("LBRM", 2_000_000_000, 200_000_000, 2000, 2200, 50, 100, 8, 0, 0)
dummy = DummyHero()

team = Team([lbrm, dummy])

# --- ROUND 1: LBRM grants Wings ---
logs = []
logs += lbrm.active_skill(boss, team)

# --- ROUND 2: Seal Dummy1 and LBRM ---
dummy.has_seal_of_light = True
dummy.seal_rounds = 2
dummy.extra_ctrl_removals = 1  # from wings
dummy.wings_effect = True

lbrm.has_seal_of_light = True  # LBRM is sealed

# --- ROUND 3: Dummy attacks and should cleanse self ---
logs.append("=== Dummy attacks while sealed and with Wings stack ===")
logs += hero_deal_damage(dummy, boss, dummy.atk * 10, is_active=False, team=team, allow_counter=False)

# Inject simplified after_attack logic
if dummy.extra_ctrl_removals > 0 and dummy.has_seal_of_light:
    dummy.has_seal_of_light = False
    dummy.seal_rounds = 0
    dummy.extra_ctrl_removals -= 1
    logs.append(f"🧼 {dummy.name} removes Seal of Light using Wings stack (remaining: {dummy.extra_ctrl_removals}).")

# --- Print log ---
for log in logs:
    print(log)
