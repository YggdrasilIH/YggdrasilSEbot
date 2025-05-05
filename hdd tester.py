from game_logic.heroes.base import Hero
from game_logic.boss import Boss
from game_logic.team import Team
from game_logic.damage_utils import hero_deal_damage, apply_burn
from game_logic.enables import BalancedStrike, UnbendingWill
from game_logic.buff_handler import BuffHandler
import random

class DummyTarget(Boss):
    def __init__(self):
        super().__init__()
        self.hp = 1_000_000_000
        self.max_hp = self.hp
        self.shield = 100_000_000
        self.dr = 0.20
        self.adr = 0.25
        self.buffs = {
            "crit_vulnerability": {"attribute": "crit_damage_taken", "bonus": 30, "rounds": 2},
            "poisoned": {"attribute": "poison", "bonus": 1, "rounds": 2}
        }
        self.poison_effects = [{"attribute": "burn", "damage": 100_000_000, "rounds": 2}]
        self.shrink_debuff = {"multiplier_received": 1.2, "multiplier_dealt": 0.8, "rounds": 2}

    def take_damage(self, dmg, source_hero=None, team=None, real_attack=False):
        print(f"[Boss] Taking {dmg} raw damage (HP before: {self.hp})")
        self.hp -= dmg
        return [f"Boss took {dmg // 1_000_000}M damage."]

    def on_receive_damage(self, damage, team, source):
        print("[Boss] Triggering on_receive_damage hook.")
        return [f"{self.name} reacts to damage."]


class DummyHero(Hero):
    def __init__(self):
        super().__init__(
            name="Tester",
            hp=1_000_000_000,
            atk=100_000_000,
            armor=3000,
            spd=1500,
            crit_rate=100,
            crit_dmg=150,
            ctrl_immunity=0,
            hd=50,
            precision=120,
              # or any % you want
            purify_enable=None,
            trait_enable=BalancedStrike(),
            artifact=None,
            lifestar=None
        )
        self.all_damage_dealt = 20
        self.dt_level = 3
        self.defier = True
        self.gk = True
        self.bonus_damage_vs_poisoned = 0.5
        self.hp = 400_000_000
        self.max_hp = 1_000_000_000
        self._using_real_attack = True
        self.total_damage_dealt = 0

    def after_attack(self, source, target, skill_type, team):
        print(f"[{self.name}] after_attack triggered.")
        return [f"{self.name} triggers after_attack."]


def run_debug_test():
    hero = DummyHero()
    target = DummyTarget()
    team = Team([hero], [hero], [])
    print("\n=== Running Hero Deal Damage Debug Test ===")
    logs = hero_deal_damage(source=hero, target=target, base_damage=hero.atk * 10, is_active=True, team=team)
    for log in logs:
        print("📝", log)


if __name__ == "__main__":
    random.seed(42)  # Force consistent crits etc.
    run_debug_test()
