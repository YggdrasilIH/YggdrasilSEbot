import re
import sys
import os
from contextlib import contextmanager
from game_logic import Hero, Boss, Team
from game_logic.artifacts import Scissors, DB, Mirror, Antlers, dDB, dMirror
from game_logic.cores import PDECore
from game_logic.pets import Phoenix
from game_logic.lifestar import Specter, Nova
from game_logic.enables import ControlPurify, AttributeReductionPurify, MarkPurify, BalancedStrike, UnbendingWill
from utils.battle import chunk_logs

@contextmanager
def suppress_stdout():
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stdout = original_stdout

# Final filter pattern
filter_re = re.compile("⚡|🔪|🗡️|⏱️\\ Boss\\ counterattacks|😱|🔇|💡|🧼|DMG\\ \\(B\\)|Boss\\ Buffs\\ Per\\ Round:|💥\\ Boss\\ active\\ hits|🗯️\\ Boss\\ basic\\ hits|💚|🛡️|💀")

def run_debugfast_filtered():
    global active_core
    active_core = PDECore()

    purify_mapping = {"CP": ControlPurify(), "ARP": AttributeReductionPurify(), "MP": MarkPurify()}
    trait_mapping = {"BS": BalancedStrike(), "UW": UnbendingWill()}

    data = [
        ("hero_MFF_Hero", 1.1e10, 6e7, 3800, "CP", "UW", dDB(), 15, 0, 0, 0, 0, 0, 0, 59, 40, 8000),
        ("hero_SQH_Hero", 1.2e10, 7e7, 3670, "CP", "UW", dMirror(), 15, 0, 0, 0, 0, 0, 0, 59, 40, 9000),
        ("hero_LFA_Hero", 2e10, 1.75e8, 3540, "MP", "BS", Antlers(), 15, 70, 150, 150, 600, 150, 150, 0, 16, 8999),
        ("hero_PDE_Hero", 0.9e10, 6e7, 2300, "CP", "UW", Scissors(), 15, 0, 0, 0, 0, 0, 0, 59, 40, 8444),
        ("hero_LBRM_Hero", 0.9e10, 5e7, 2000, "CP", "UW", Scissors(), 14, 0, 0, 0, 0, 0, 0, 59, 46, 8000),
        ("hero_DGN_Hero", 1.4e10, 9e7, 3300, "CP", "UW", Scissors(), 15, 0, 0, 0, 0, 0, 0, 59, 16, 7999)
    ]

    heroes = []
    for hid, hp, atk, spd, purify, trait, artifact, dt_level, crit_rate, crit_dmg, precision, hd, skill_damage, add, dr, adr, armor in data:
        lifestar = Specter() if hid == "hero_LFA_Hero" else Nova() if hid == "hero_SQH_Hero" else None
        h = Hero.from_stats(hid, [hp, atk, spd], artifact=artifact, lifestar=lifestar)
        h.set_enables(purify_mapping.get(purify), trait_mapping.get(trait))
        h.dt_level = dt_level
        h.crit_rate += crit_rate; h._base_crit_rate += crit_rate
        h.crit_dmg += crit_dmg; h._base_crit_dmg += crit_dmg
        h.precision += precision; h._base_precision += precision
        h._base_skill_damage += skill_damage
        h.hd += hd; h._base_hd += hd
        h.all_damage_dealt += add; h._base_all_damage_dealt += add
        h.DR += dr; h._base_dr += dr
        h.ADR += adr; h._base_adr += adr
        h.armor += armor; h.original_armor += armor
        h.gk = h.defier = True
        h.total_damage_dealt = 0
        h._damage_rounds = []
        heroes.append(h)

    team = Team(heroes, heroes[:2], heroes[2:], pet=Phoenix())
    boss = Boss()

    for hero in team.heroes:
        if hasattr(hero, "start_of_battle"):
            hero.start_of_battle(team, boss)

    boss_buff_tracking = []

    for round_num in range(1, 16):
        if all(not h.is_alive() for h in team.heroes) or not boss.is_alive():
            break

        for hero in team.heroes:
            if hero.lifestar and hasattr(hero.lifestar, "start_of_round"):
                hero.lifestar.start_of_round(hero, team, boss, round_num)

        hero_start_dmg = {h.name: h.total_damage_dealt for h in team.heroes}
        with suppress_stdout():
            logs = team.perform_turn(boss, round_num)
            logs += team.end_of_round(boss, round_num)

        hero_end_dmg = {h.name: h.total_damage_dealt for h in team.heroes}

        print(f"\n🔁 Round {round_num}")
        print("DMG (B)  | " + " | ".join(f"{(hero_end_dmg[h.name] - hero_start_dmg[h.name]) / 1e9:8.2f}" for h in team.heroes))

        for log in logs:
            if isinstance(log, str) and filter_re.search(log):
                print(log)


        boss_buff_tracking.append({
            "Round": round_num,
            "ATK": boss.atk,
            "HD": boss.hd,
            "ADD": boss.all_damage_dealt,
            "DR": boss.dr,
            "ADR": boss.ADR
        })

    print("\n📈 Boss Buffs Per Round:")
    print("Round |   ATK   |   HD   |  ADD  |  DR  | ADR")
    for b in boss_buff_tracking:
        print(f"{b['Round']:5} | {b['ATK']:7} | {b['HD']:6} | {b['ADD']:5} | {b['DR']*100:4.0f}% | {b['ADR']*100:4.0f}%")

if __name__ == "__main__":
    run_debugfast_filtered()
