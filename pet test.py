from game_logic.heroes.base import Hero 
from game_logic.boss import Boss
from game_logic.pets import Phoenix
from game_logic.team import Team
from game_logic.damage_utils import hero_deal_damage, apply_burn
from utils.log_utils import stylize_log


class DummyHero(Hero):
    def __init__(self, name):
        super().__init__(
            name=name, hp=1e9, atk=1e7, armor=0, spd=100,
            crit_rate=100, crit_dmg=150, ctrl_immunity=0, hd=0, precision=0
        )

    def active_skill(self, boss, team):
        logs = []
        hit = {"damage": self.atk * 10, "can_crit": True}
        logs += hero_deal_damage(self, boss, base_damage=0, is_active=True, team=team, hit_list=[hit])
        team.pet.on_hero_active(self)
        return logs


# Setup
hero1 = DummyHero("NovaTester1")
hero2 = DummyHero("NovaTester2")
hero3 = DummyHero("NovaTester3")
hero4 = DummyHero("NovaTester4")
hero5 = DummyHero("NovaTester5")

team = Team(
    heroes=[hero1, hero2, hero3, hero4, hero5],
    front_line=[hero1, hero2],
    back_line=[hero3, hero4, hero5],
    pet=Phoenix()
)
team.pet.bind_team(team)

boss = Boss()
boss.hp = boss.max_hp = 5_000_000_000
boss.poison_effects = []  # Required for Phoenix burn

logs = []
round_num = 1

# Simulate 5 turns of active skills and end of round triggers
for i in range(5):
    logs.append(f"🔁 ROUND {round_num}")
    for hero in team.heroes:
        logs += hero.active_skill(boss, team)
    logs += team.pet.apply_end_of_round(team, boss, round_num)
    round_num += 1

# Output
print("=== Phoenix Natural Activation Test ===")
for log in logs:
    print(log)
