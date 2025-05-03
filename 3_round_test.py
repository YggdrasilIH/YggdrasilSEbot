from game_logic import Hero, Boss, Team
from game_logic.artifacts import Scissors, DB, Mirror, Antlers, dDB, dMirror
from game_logic.cores import PDECore
from game_logic.pets import Phoenix
from game_logic.lifestar import Specter, Nova
from game_logic.enables import ControlPurify, AttributeReductionPurify, MarkPurify, BalancedStrike, UnbendingWill

# Logging control
LOG_SETTINGS = {
    "battle_flow": False,
    "buffs": False,
    "boss_skills": False,
    "control_effects": True,
    "control_cleansing": True,
    "hero_skills": False,
    "pets": False,
    "core": False,
    "artifacts": False,
    "enables": True,
    "lifestars": False,
    "foresight": False,
    "damage": False,
    "dr_adr_armor": False,
    "dt_levels": False,
    "dodge_heal_shield": False,
    "energy": False,
    "start_of_battle": False,
}

def conditional_log(msg, category="battle_flow"):
    if LOG_SETTINGS.get(category, False):
        print(msg)

purify_mapping = {"CP": ControlPurify(), "ARP": AttributeReductionPurify(), "MP": MarkPurify()}
trait_mapping = {"BS": BalancedStrike(), "UW": UnbendingWill()}

def run_three_round_test():
    global active_core
    active_core = PDECore()

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

    if LOG_SETTINGS["start_of_battle"]:
        conditional_log("\n🚩 Start-of-Battle Effects Triggering...", "start_of_battle")
    for hero in team.heroes:
        if hasattr(hero, "start_of_battle"):
            hero.start_of_battle(team, boss)

    conditional_log("\n🔍 BEGINNING 3-ROUND TEST", "battle_flow")
    for round_num in range(1, 4):
        if all(not h.is_alive() for h in team.heroes) or not boss.is_alive():
            break

        for hero in team.heroes:
            if hero.lifestar and hasattr(hero.lifestar, "start_of_round") and LOG_SETTINGS["lifestars"]:
                conditional_log(f"🌟 {hero.name}'s lifestar triggers at round {round_num}", "lifestars")
                hero.lifestar.start_of_round(hero, team, boss, round_num)

        conditional_log(f"\n🔁 Round {round_num}", "battle_flow")
        team.perform_turn(boss, round_num)
        team.end_of_round(boss, round_num)

    if LOG_SETTINGS["buffs"]:
        conditional_log("\n📋 FINAL BUFF STATES", "buffs")
        for h in team.heroes:
            conditional_log(f"\n{h.name} Buffs (HP: {h.hp/1e6:.0f}M):", "buffs")
            for buff_name, buff in h.buffs.items():
                conditional_log(f"  {buff_name}: {buff}", "buffs")
            conditional_log(f"  Shield: {h.shield/1e6:.1f}M", "buffs")

        conditional_log("\n📊 Boss Buffs:", "buffs")
        for buff_name, buff in boss.buffs.items():
            conditional_log(f"  {buff_name}: {buff}", "buffs")
        conditional_log(f"  Boss HP: {boss.hp/1e6:.1f}M", "buffs")

if __name__ == "__main__":
    run_three_round_test()
