from game_logic.heroes.base import Hero
from game_logic.boss import Boss
from game_logic.team import Team
from game_logic.control_effects import apply_control_effect

class DummyHero(Hero):
    def __init__(self, name):
        super().__init__(
            name=name,
            hp=1_000_000_000,
            atk=100_000_000,
            armor=1000,
            spd=2000,
            crit_rate=0,
            crit_dmg=0,
            ctrl_immunity=0,  # Force control effect application
            hd=0,
            precision=0
        )
        self.immune_control_effect = None  # No immunity to any effect
    
boss = Boss()
h1 = DummyHero("Hero1")
h2 = DummyHero("Hero2")
h3 = DummyHero("Hero3")


# If you want all 3 on back line instead
heroes = [h1, h2, h3]
team = Team(heroes, front_line=[], back_line=heroes)


logs = ["--- CONTROL INFLICT TEST ---"]

for hero in team.heroes:
    hero.calamity = 5
    logs.append(f"{hero.name} hits 5 Calamity.")
    logs += apply_control_effect(hero, ["fear", "silence", "seal_of_light"], boss=boss, team=team)

logs.append("\n--- Boss Buffs After Control ---")
logs.append(boss.get_status_description())

for log in logs:
    print(log)
