# game_logic/pets.py

class Pet:
    def bind_team(self, team):
        self.team = team
    def apply_start_of_battle(self, team):
        return []
    def apply_end_of_round(self, team, boss, round_num):
        return []

class Phoenix(Pet):
    def __init__(self):
        self.energy = 0
        self.pending_special = False

    def bind_team(self, team):
        self.team = team

    def apply_start_of_battle(self, team):
        for hero in team.heroes:
            hero.hd += 20
            hero.crit_dmg += 20
        return []  # No logs at start

    def apply_end_of_round(self, team, boss, round_num):
        logs = []
        self.energy += 20
        if self.pending_special:
            logs += self.fire_special(team, boss, round_num)
            self.pending_special = False
        elif self.energy >= 100:
            self.pending_special = True
            self.energy = 100
        return logs

    def on_hero_active(self, hero):
        self.energy += 10
        if self.energy >= 100:
            self.pending_special = True
            self.energy = 100

    def fire_special(self, team, boss, round_num):
        logs = []

        # Apply a "burn" effect (similar to poison)
        boss.poison_effects.append({
            "damage": 300_000,
            "rounds": 3,
            "attribute": "burn"  # distinguish if needed
        })

        # Set special burn-damage buff for heroes
        for hero in team.heroes:
            hero.phoenix_burn_bonus_rounds = 3  # custom tracking

        logs.append(f"🔥 Phoenix uses active and heroes gain 80% increased damage against burning targets (3 rounds).")
        self.energy = 0
        return logs
