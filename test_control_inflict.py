from game_logic import Hero, Boss, Team
from game_logic.artifacts import Scissors, DB, Mirror, Antlers, dDB, dMirror
from game_logic.cores import PDECore
from game_logic.pets import Phoenix
from game_logic.lifestar import Specter, Nova
from game_logic.enables import ControlPurify, AttributeReductionPurify, MarkPurify, BalancedStrike, UnbendingWill
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

purify_mapping = {"CP": ControlPurify(), "ARP": AttributeReductionPurify(), "MP": MarkPurify()}
trait_mapping = {"BS": BalancedStrike(), "UW": UnbendingWill()}

def run_control_effect_summary():
    from game_logic.cores import active_core
    active_core = PDECore()

    data = [
        ("hero_MFF_Hero", 1.1e12, 6e7, 3800, "CP", "UW", dDB(), 15, 0, 0, 0, 0, 0, 0, 59, 40, 8000),
        ("hero_SQH_Hero", 1.2e12, 7e7, 3670, "CP", "UW", dMirror(), 15, 0, 0, 0, 0, 0, 0, 59, 40, 9000),
        ("hero_LFA_Hero", 2e12, 1.75e8, 3540, "MP", "BS", Antlers(), 15, 70, 150, 150, 600, 150, 150, 0, 16, 8999),
        ("hero_PDE_Hero", 0.9e12, 6e7, 2300, "CP", "UW", Scissors(), 15, 0, 0, 0, 0, 0, 0, 59, 40, 8444),
        ("hero_LBRM_Hero", 0.9e12, 5e7, 2000, "CP", "UW", Scissors(), 14, 0, 0, 0, 0, 0, 0, 59, 46, 8000),
        ("hero_DGN_Hero", 1.4e12, 9e7, 3300, "CP", "UW", Scissors(), 15, 0, 0, 0, 0, 0, 0, 59, 16, 7999)
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
        h.recalculate_stats()
        heroes.append(h)

    team = Team(heroes, heroes[:2], heroes[2:], pet=Phoenix())
    boss = Boss()

    print("\n🔍 CONTROL EFFECT SUMMARY (15 rounds)")
    for hero in team.heroes:
        if hasattr(hero, "start_of_battle"):
            hero.start_of_battle(team, boss)

    for round_num in range(1, 16):
        print(f"\n🔁 Round {round_num}:")
        for hero in team.heroes:
            alive = hero.is_alive()
            if not alive:
                print(f"☠️ {hero.name} is dead.")
                continue
            action_taken = ""
            if hasattr(hero, "has_silence") and hero.has_silence:
                action_taken = "🔇 Silenced — cannot act."
            elif hasattr(hero, "has_fear") and hero.has_fear:
                action_taken = "😱 Feared — cannot act."
            elif hasattr(hero, "has_seal_of_light") and hero.has_seal_of_light:
                action_taken = "🔒 Sealed — passive blocked."
            elif hero.energy >= 100:
                action_taken = "✅ Used Active Skill"
            else:
                action_taken = "✅ Used Basic Attack"
            print(f"{hero.name}: {action_taken}")

        print(f"\n🔁 Round {round_num} Calamity Status:")
        for h in team.heroes:
            print(f"🧿 {h.name}: {h.calamity} stacks")

       # with suppress_stdout():
        team.perform_turn(boss, round_num)
        team.end_of_round(boss, round_num)
 


if __name__ == "__main__":
    run_control_effect_summary()
