# debugfast_average.py

from game_logic import Hero, Boss, Team
from game_logic.artifacts import Scissors, DB, Mirror, Antlers, dDB, dMirror
from game_logic.cores import PDECore
from game_logic.pets import Phoenix
from game_logic.lifestar import Specter
from game_logic.enables import ControlPurify, AttributeReductionPurify, MarkPurify, BalancedStrike, UnbendingWill
import sys
import os
from contextlib import contextmanager

# 🧹 Suppress stdout during simulation
@contextmanager
def suppress_stdout():
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stdout = original_stdout

purify_mapping = {
    "CP": ControlPurify(),
    "ARP": AttributeReductionPurify(),
    "MP": MarkPurify()
}
trait_mapping = {
    "BS": BalancedStrike(),
    "UW": UnbendingWill()
}

def create_team_and_boss():
    global active_core
    active_core = PDECore()

    data = [
        ("hero_MFF_Hero", 11e11, 6e7, 3800, "CP", "UW", dDB(), 15, 0, 0, 0, 0, 0, 0, 59, 40, 8000),
        ("hero_SQH_Hero", 12e11, 7e7, 3670, "CP", "UW", dMirror(), 15, 0, 0, 0, 0, 0, 0, 59, 40, 9000),
        ("hero_LFA_Hero", 20e11, 1.75e8, 3540, "MP", "BS", Antlers(), 15, 70, 150, 150, 500, 150, 150, 0, 16, 8999),
        ("hero_DGN_Hero", 14e11, 9e7, 3300, "CP", "UW", Scissors(), 15, 0, 0, 0, 0, 0, 0, 59, 16, 79999),
        ("hero_PDE_Hero", 9e11, 6e7, 2300, "CP", "UW", Scissors(), 15, 0, 0, 0, 0, 0, 0, 59, 40, 8444),
        ("hero_LBRM_Hero", 9.9e11, 5e7, 2000, "CP", "UW", dMirror(), 14, 0, 0, 0, 0, 0, 0, 59, 46, 8000)
    ]

    heroes = []
    for hid, hp, atk, spd, purify, trait, artifact, dt_level, crit_rate, crit_dmg, precision, hd, skill_damage, add, dr, adr, armor in data:
        lifestar = Specter() if hid == "hero_LFA_Hero" else None
        h = Hero.from_stats(hid, [hp, atk, spd], artifact=artifact, lifestar=lifestar)
        h.set_enables(purify_mapping.get(purify), trait_mapping.get(trait))
        h.dt_level = dt_level

        # Offensive stats
        h.crit_rate += crit_rate
        h._base_crit_rate += crit_rate
        h.crit_dmg += crit_dmg
        h._base_crit_dmg += crit_dmg
        h.precision += precision
        h._base_precision += precision
        h._base_skill_damage += skill_damage
        h.hd += hd
        h._base_hd += hd
        h.all_damage_dealt += add
        h._base_all_damage_dealt += add

        # Defensive stats
        h.DR += dr
        h._base_dr += dr
        h.ADR += adr
        h._base_adr += adr
        h.armor += armor
        h.original_armor += armor

        h.gk = h.defier = True
        h.total_damage_dealt = 0
        heroes.append(h)

    team = Team(heroes, heroes[:2], heroes[2:], pet=Phoenix())
    boss = Boss()

    return team, boss, heroes

def run_debugfast_average():
    num_simulations = 1000
    hero_totals = {}
    boss_totals = []

    best_damage = -float('inf')
    worst_damage = float('inf')
    best_sim = None
    worst_sim = None

    with suppress_stdout():  # 🔇 No spam inside simulation
        for sim_num in range(num_simulations):
            team, boss, heroes = create_team_and_boss()

            for hero in heroes:
                if hasattr(hero, "start_of_battle"):
                    hero.start_of_battle(team, boss)

            for round_num in range(1, 16):
                if all(not h.is_alive() for h in team.heroes) or not boss.is_alive():
                    break

                for hero in team.heroes:
                    if hero.lifestar and hasattr(hero.lifestar, "start_of_round"):
                        hero.lifestar.start_of_round(hero, team, boss, round_num)

                _ = team.perform_turn(boss, round_num)
                _ = team.end_of_round(boss, round_num)

            for hero in heroes:
                hero_totals.setdefault(hero.name, 0)
                hero_totals[hero.name] += hero.total_damage_dealt

            team_total = sum(h.total_damage_dealt for h in heroes)
            boss_totals.append(team_total)

            # Track best and worst
            if team_total > best_damage:
                best_damage = team_total
                best_sim = [h.total_damage_dealt for h in heroes]
            if team_total < worst_damage:
                worst_damage = team_total
                worst_sim = [h.total_damage_dealt for h in heroes]

    # 🧠 OUTSIDE suppress_stdout → safe to print
    print("\n🏹 FINAL AVERAGE SUMMARY (across {} battles)\n".format(num_simulations))
    team_total_avg = sum(boss_totals) / num_simulations

    for name, total in hero_totals.items():
        avg_damage = total / num_simulations
        percent = (avg_damage / team_total_avg) * 100 if team_total_avg > 0 else 0
        label = f"{name:>8}"
        if avg_damage >= 1e13:
            dmg_str = f"{avg_damage:.2e}"
        else:
            dmg_str = f"{avg_damage / 1e9:6.2f}B"
        print(f"{label}: {dmg_str} AVG DMG ({percent:5.1f}%)")

    if team_total_avg >= 1e13:
        total_str = f"{team_total_avg:.2e}"
    else:
        total_str = f"{team_total_avg / 1e9:6.2f}B"

    print(f"\n🏆 Average Total Team Damage: {total_str}")

    # 🏆 Output best and worst battle results
    print(f"\n⭐ Best Single Battle: {best_damage:.2e}")
    print(f"📉 Worst Single Battle: {worst_damage:.2e}")


if __name__ == "__main__":
    run_debugfast_average()
