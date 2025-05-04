
from game_logic import Hero, Boss, Team
from game_logic.artifacts import DB, Mirror
from game_logic.cores import PDECore
from game_logic.lifestar import Specter, Nova
from game_logic.pets import Phoenix
from game_logic.enables import ControlPurify, AttributeReductionPurify, MarkPurify, BalancedStrike, UnbendingWill
from utils.battle import chunk_logs
from utils.log_utils import debug
import random
import sys, os
from contextlib import contextmanager

@contextmanager
def suppress_stdout():
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stdout = original_stdout


# Config
NUM_BATTLES = 10

# Setup maps
purify_mapping = {"CP": ControlPurify(), "ARP": AttributeReductionPurify(), "MP": MarkPurify()}
trait_mapping = {"BS": BalancedStrike(), "UW": UnbendingWill()}

control_effects = ["fear", "silence", "seal_of_light"]
control_counter = {name: 0 for name in ["SQH", "LFA", "DGN", "PDE", "LBRM", "MFF"]}
disable_counter = {name: 0 for name in control_counter}
rounds_tracked = 3

def make_hero(name, stats, purify, trait, artifact, lifestar):
    h = Hero.from_stats(name, stats, artifact=artifact, lifestar=lifestar)
    h.set_enables(purify_mapping[purify], trait_mapping[trait])
    return h

def run_simulation():
    global control_counter, disable_counter
    for _ in range(NUM_BATTLES):
        heroes = [
            make_hero("hero_SQH_Hero", [12e9, 70e6, 3670], "CP", "UW", Mirror(), Nova()),
            make_hero("hero_LFA_Hero", [20e9, 160e6, 3540], "MP", "BS", Mirror(), Specter()),
            make_hero("hero_DGN_Hero", [14e9, 90e6, 3300], "CP", "UW", Mirror(), None),
            make_hero("hero_PDE_Hero", [9e9, 60e6, 2300], "CP", "UW", DB(), None),
            make_hero("hero_LBRM_Hero", [9e9, 50e6, 2000], "CP", "UW", Mirror(), None),
            make_hero("hero_MFF_Hero", [11e9, 60e6, 3800], "MP", "UW", DB(), None)
        ]

        for h in heroes:
            h.dt_level = 15
            h.energy = 50
            h._base_crit_rate = h.crit_rate = 150
            h._base_crit_dmg = h.crit_dmg = 150
            h._base_precision = h.precision = 150

            h.random_control_immunity = random.choice(control_effects)

        team = Team(heroes, heroes[:2], heroes[2:], pet=Phoenix())
        boss = Boss()
        from game_logic.cores import PDECore
        global active_core
        active_core = PDECore()

        for h in team.heroes:
            if hasattr(h, "start_of_battle"):
                h.start_of_battle(team, boss)

        for round_num in range(1, rounds_tracked + 1):
            team.perform_turn(boss, round_num)
            team.end_of_round(boss, round_num)
            for h in team.heroes:
                name = h.name
                if not h.is_alive():
                    continue
                if any([h.has_fear, h.has_silence, h.has_seal_of_light]):
                    disable_counter[name] += 1
                    if h.has_fear:
                        control_counter[name] += 1
                    if h.has_silence:
                        control_counter[name] += 1
                    if h.has_seal_of_light:
                        control_counter[name] += 1

# Run and report
run_simulation()

print(f"📊 Results over {NUM_BATTLES} battles (Rounds 1–{rounds_tracked}):")
print(f"{'Hero':>8} | {'Disables':>9} | {'Ctrl Effects':>13} | {'% Disabled':>11}")
print("-" * 48)
for hero in disable_counter:
    disables = disable_counter[hero]
    total_rounds = NUM_BATTLES * rounds_tracked
    percent = disables / total_rounds * 100
    print(f"{hero:>8} | {disables:9} | {control_counter[hero]:13} | {percent:10.1f}%")