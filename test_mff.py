from game_logic.heroes.mff import MFF
from game_logic.heroes.sqh import SQH
from game_logic.heroes.lfa import LFA
from game_logic.boss import Boss
from game_logic.team import Team

from game_logic.buff_handler import BuffHandler

def simulate_mff():
    logs = []

    # Create heroes
    mff = MFF("MFF", hp=100_000_000, atk=2_000_000, armor=4000, spd=100,
              crit_rate=10, crit_dmg=150, ctrl_immunity=100, hd=0, precision=100)

    sqh = SQH("SQH", hp=80_000_000, atk=1_500_000, armor=4000, spd=90,
              crit_rate=10, crit_dmg=150, ctrl_immunity=70, hd=0, precision=100)

    lfa = LFA("LFA", hp=75_000_000, atk=1_200_000, armor=4000, spd=85,
              crit_rate=10, crit_dmg=150, ctrl_immunity=70, hd=0, precision=100)

    team = Team(heroes=[mff, sqh, lfa], front_line=[mff], back_line=[sqh, lfa])
    boss = Boss()

    # Add test buffs to the boss before MFF uses active skill
    BuffHandler.apply_buff(boss, "test_buff_1", {"attribute": "atk", "bonus": 100_000, "rounds": 3})
    BuffHandler.apply_buff(boss, "test_buff_2", {"attribute": "armor", "bonus": 500, "rounds": 3})
    BuffHandler.apply_buff(boss, "test_buff_3", {"attribute": "precision", "bonus": 20, "rounds": 3})
    logs.append("🧪 Applied 3 test buffs to Boss before MFF active skill.")

    # 1. MFF basic attack
    logs.extend(mff.basic_attack(boss, team))

    # 2. Trigger MFF's passive by ally attacks
    logs.extend(team.trigger_mff_passive(sqh, boss))
    logs.extend(team.trigger_mff_passive(lfa, boss))

    # 3. MFF active skill → EF1
    logs.extend(mff.active_skill(boss, team))

    # 4. MFF active skill → EF2
    logs.extend(mff.active_skill(boss, team))

    # 5. MFF active skill → EF3
    logs.extend(mff.active_skill(boss, team))

    # 6. End of round — tick EF3 buffs
    logs.extend(mff.on_end_of_round(team, boss))

    # Optional: print status
    logs.append(mff.get_status_description())
    logs.append(sqh.get_status_description())
    logs.append(lfa.get_status_description())
    logs.append(boss.get_status_description())

    return logs

if __name__ == "__main__":
    for log in simulate_mff():
        print(log)
