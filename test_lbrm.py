from game_logic.heroes.lbrm import LBRM
from game_logic.heroes.lfa import LFA
from game_logic.heroes.mff import MFF
from game_logic.boss import Boss
from game_logic.team import Team

def simulate_lbrm():
    logs = []

    # Create LBRM and allies
    lbrm = LBRM("LBRM", hp=100_000_000, atk=2_000_000, armor=4000, spd=100, crit_rate=30, crit_dmg=150,
                ctrl_immunity=100, hd=0, precision=100)

    lfa = LFA("LFA", hp=75_000_000, atk=1_200_000, armor=3000, spd=90, crit_rate=20, crit_dmg=150,
              ctrl_immunity=70, hd=0, precision=100)

    mff = MFF("MFF", hp=80_000_000, atk=1_500_000, armor=3500, spd=85, crit_rate=25, crit_dmg=150,
              ctrl_immunity=70, hd=0, precision=100)

    team = Team(heroes=[lbrm, lfa, mff], front_line=[lbrm], back_line=[lfa, mff])
    boss = Boss()

    # Start of battle
    logs.extend(lbrm.start_of_battle(team, boss))

    # Turn 1: LBRM uses basic (not enough Power of Dream yet)
    logs.extend(lbrm.basic_attack(boss, team))

    # Turn 2: LBRM uses active skill (should grant Wings, Mag, Protection)
    logs.extend(lbrm.active_skill(boss, team))

    # Simulate boss applying control effects to test Wings reactive cleanse
    lfa.has_silence = True
    mff.has_fear = True
    logs.append("💀 Simulated control effects: Silence on LFA, Fear on MFF.")

    # Test passive_trigger after allies are controlled
    logs.extend(lbrm.passive_trigger(lfa, boss, team))
    logs.extend(lbrm.passive_trigger(mff, boss, team))

    # Simulate Wings-based teamwide reactive cleanse
    logs.extend(lbrm.after_attack(lfa, boss, "basic", team))

    # Simulate end of round — if TP is 6+, release transition
    logs.extend(lbrm.on_end_of_round(team, boss))

    # Print status summaries
    logs.append(lbrm.get_status_description())
    logs.append(lfa.get_status_description())
    logs.append(mff.get_status_description())
    logs.append(boss.get_status_description())

    return logs

if __name__ == "__main__":
    for log in simulate_lbrm():
        print(log)
