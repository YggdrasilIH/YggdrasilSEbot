from game_logic.boss import Boss
from game_logic.heroes.base import Hero

# Minimal fake Hero class if needed (if importing base Hero too heavy)
class DummyHero:
    def __init__(self, name):
        self.name = name
        self.hp = 1_000_000_000
        self.max_hp = 1_000_000_000
        self.atk = 100_000
        self.armor = 1000
        self.energy = 50
        self.buffs = {}
        self.immune_control_effect = "none"
        self.calamity = 0
        self.shield = 0
        self.ctrl_immunity = 0
        self.curse_of_decay = 0
        self.has_fear = False
        self.has_silence = False
        self.has_seal_of_light = False
        self.team = None
        self.is_alive = lambda: self.hp > 0

    def apply_buff(self, name, data):
        print(f"{self.name} received buff: {name} -> {data}")

heroes = [DummyHero(f"Hero{i+1}") for i in range(6)]
boss = Boss()

# Test 1: Boss Active Skill
print("\n=== Testing Boss Active Skill ===")
logs = boss.active_skill(heroes, 1)
for log in logs:
    print(log)

# Test 2: Boss Basic Attack
print("\n=== Testing Boss Basic Attack ===")
logs = boss.basic_attack(heroes, 1)
for log in logs:
    print(log)

# Test 3: Boss Counterattack
print("\n=== Testing Boss Counterattack ===")
boss._pending_counterattack_needed = True
logs = boss.flush_counterattacks(heroes)
for log in logs:
    print(log)

# Test 4: Boss End of Round
print("\n=== Testing Boss End of Round ===")
logs = boss.end_of_round_effects(heroes, 1)
for log in logs:
    print(log)
