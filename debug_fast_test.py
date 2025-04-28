# debugfast_test.py

from game_logic import Hero, Boss, Team
from game_logic.artifacts import Scissors, DB, Mirror, Antlers
from game_logic.cores import PDECore
from game_logic.lifestar import Specter
from game_logic.enables import ControlPurify, AttributeReductionPurify, MarkPurify, BalancedStrike, UnbendingWill
from utils.battle import chunk_logs
import re

purify_mapping = {
    "CP": ControlPurify(),
    "ARP": AttributeReductionPurify(),
    "MP": MarkPurify()
}
trait_mapping = {
    "BS": BalancedStrike(),
    "UW": UnbendingWill()
}

def parse_damage_logs(battle_logs, hero_tracking):
    for log in battle_logs:
        if not isinstance(log, str):
            continue  # Skip non-string logs

        # Boss active skill
        if log.startswith("💥 Boss active hits→"):
            matches = re.findall(r"(\w+) \((\d+)M\)", log)
            for name, dmg in matches:
                if name in hero_tracking:
                    hero_tracking[name]["active"] += int(dmg)

        # Boss basic attack
        if log.startswith("💥 Boss basic hits→"):
            matches = re.findall(r"(\w+) \((\d+)M\)", log)
            for name, dmg in matches:
                if name in hero_tracking:
                    hero_tracking[name]["basic"] += int(dmg)

        # Boss counterattack
        if log.startswith("⏱️ Boss counterattacks→"):
            matches = re.findall(r"(\w+) \((\d+)M\)", log)
            for name, dmg in matches:
                if name in hero_tracking:
                    hero_tracking[name]["counter"] += int(dmg)

        # Curse offset group damage
        if log.startswith("💀 Curse offset damage this round:"):
            matches = re.findall(r"(\w+) (\d+)M", log)
            for name, dmg in matches:
                if name in hero_tracking:
                    hero_tracking[name]["curse"] += int(dmg)

        # ❗ Curse offsets - per hero single line
        if log.startswith("💀 Curse of Decay offsets") and "takes" in log:
            match = re.search(r"(\w+) takes (\d+)M", log)
            if match:
                name, dmg = match.groups()
                if name in hero_tracking:
                    hero_tracking[name]["curse"] += int(dmg)

        # Poison damage
        if log.startswith("☠️"):
            matches = re.findall(r"(\w+): (\d+)M Poison", log)
            for name, dmg in matches:
                if name in hero_tracking:
                    hero_tracking[name]["poison"] += int(dmg)


def run_debugfast_terminal():
    global active_core
    active_core = PDECore()

    data = [
        ("hero_MFF_Hero", 11e9, 6e7, 3800, "CP", "UW", DB()),
        ("hero_SQH_Hero", 12e9, 7e7, 3700, "CP", "UW", DB()),
        ("hero_LFA_Hero", 20e9, 1.6e8, 3540, "MP", "BS", Antlers()),
        ("hero_DGN_Hero", 14e9, 9e7, 3300, "CP", "UW", Scissors()),
        ("hero_PDE_Hero", 9e9, 6e7, 2300, "CP", "UW", Mirror()),
        ("hero_LBRM_Hero", 9.9e9, 5e7, 2000, "CP", "UW", Mirror())
    ]

    heroes = []
    for hid, hp, atk, spd, purify, trait, artifact in data:
        lifestar = Specter() if hid == "hero_LFA_Hero" else None
        h = Hero.from_stats(hid, [hp, atk, spd], artifact=artifact, lifestar=lifestar)
        h.set_enables(purify_mapping.get(purify), trait_mapping.get(trait))
        h.gk = h.defier = True
        h.total_damage_dealt = 0
        h._damage_rounds = []
        heroes.append(h)

    team = Team(heroes, heroes[:2], heroes[2:])
    boss = Boss()

    for hero in team.heroes:
        if hasattr(hero, "start_of_battle"):
            hero.start_of_battle(team, boss)

    hero_tracking = {h.name: {"active": 0, "basic": 0, "counter": 0, "curse": 0, "poison": 0} for h in heroes}
    boss_buff_tracking = []

    for round_num in range(1, 16):
        if all(not h.is_alive() for h in team.heroes) or not boss.is_alive():
            break

        for hero in team.heroes:
            if hero.lifestar and hasattr(hero.lifestar, "start_of_round"):
                hero.lifestar.start_of_round(hero, team, boss, round_num)

        for h in team.heroes:
            if h.name == "LFA":
                print(f"[DEBUG] {h.name} stats → ATK: {h.atk:,} | ADD: {h.all_damage_dealt:.1f}% | HD: {h.hd}")
                for name, buff in hero.buffs.items():
                    print(f"[DEBUG] LFA buff {name}: {buff}")
        hero_start_dmg = {h.name: h.total_damage_dealt for h in team.heroes}

        battle_logs = []
        battle_logs += team.perform_turn(boss, round_num)
        battle_logs += team.end_of_round(boss, round_num)
        

        # Parse the logs
        parse_damage_logs(battle_logs, hero_tracking)

        # Track boss buffs
        current_boss_buffs = {
            "Round": round_num,
            "ATK": boss.atk,
            "HD": boss.hd,
            "ADD": boss.all_damage_bonus,
            "DR": getattr(boss, "dr", 0),
            "ADR": getattr(boss, "ADR", 0)
        }
        boss_buff_tracking.append(current_boss_buffs)

        hero_end_dmg = {h.name: h.total_damage_dealt for h in team.heroes}

        if round_num == 1:
            header_line = "         | " + " | ".join(f"{h.name:>8}" for h in team.heroes)
            divider = "-" * len(header_line)
            print("\n" + divider)
            print(header_line)
            print(divider)

        print(f"\n🔁 Round {round_num}")
        print("DMG (B)  | " + " | ".join(f"{(hero_end_dmg[h.name] - hero_start_dmg[h.name]) / 1e9:8.2f}" for h in team.heroes))
        print("Energy   | " + " | ".join(f"{h.energy:8}" for h in team.heroes))
        print("Calamity | " + " | ".join(f"{h.calamity:8}" for h in team.heroes))
        print("Curse    | " + " | ".join(f"{h.curse_of_decay:8}" for h in team.heroes))

        for h in team.heroes:
            status = "💀 DEAD" if not h.is_alive() else f"{h.hp/1e6:.0f}M HP"
            print(f"{h.name}: {status}")

        print("-" * 80)

    # FINAL SUMMARY
    print("\n🏹 FINAL SUMMARY\n")
    team_total = sum(h.total_damage_dealt for h in team.heroes)
    for h in team.heroes:
        total = h.total_damage_dealt
        percent = (total / team_total * 100) if team_total else 0
        label = f"{h.name:>8}"
        if total >= 1e13:
            dmg_str = f"{total:.2e}"  # scientific notation
        else:
            dmg_str = f"{total / 1e9:6.2f}B"
        print(f"{label}: {dmg_str} DMG ({percent:5.1f}%)")


    print("\n📊 Damage Breakdown by Source (Total M damage):")
    for h in heroes:
        t = hero_tracking[h.name]
        total = sum(t.values())
        print(f"{h.name:>8}: Active {t['active']:6} | Basic {t['basic']:6} | Counter {t['counter']:6} | Curse {t['curse']:6} | Poison {t['poison']:6} | Total {total:6}")

    print("\n📈 Boss Buff Tracking Per Round:")
    print("Round |   ATK   |   HD   |  ADD  |  DR  | ADR")
    for buffs in boss_buff_tracking:
        print(f"{buffs['Round']:5} | {buffs['ATK']:7} | {buffs['HD']:6} | {buffs['ADD']:5} | {buffs['DR']*100:4.0f}% | {buffs['ADR']*100:4.0f}%")

    if not boss.is_alive():
        print("\n🏆 Boss defeated!")
    elif all(not h.is_alive() for h in team.heroes):
        print("\n❌ All heroes have fallen!")
    else:
        print("\n⏳ Battle ended after 15 rounds (Boss survived).")

if __name__ == "__main__":
    run_debugfast_terminal()
