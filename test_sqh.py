from game_logic.heroes.sqh import SQH
from game_logic.boss import Boss
from game_logic.team import Team
from game_logic.artifacts import DB
from game_logic.enables import MarkPurify, BalancedStrike
from game_logic.pets import Phoenix
from game_logic.buff_handler import BuffHandler
from game_logic.damage_utils import hero_deal_damage


def run_sqh_skill_test():
    # Create SQH (frontline) and dummy ally (backline)
    sqh = SQH("SQH", hp=10_000_000_000, atk=200_000_000, armor=4000, spd=100,
              crit_rate=30, crit_dmg=150, ctrl_immunity=100, hd=50, precision=100,
              purify_enable=MarkPurify(), trait_enable=BalancedStrike(), artifact=DB())

    dummy_ally = SQH("Ally", hp=8_000_000_000, atk=180_000_000, armor=3000, spd=90,
                     crit_rate=30, crit_dmg=150, ctrl_immunity=100, hd=30, precision=80)

    # Assemble team with 1 frontline and 1 backline hero
    team = Team(
            heroes=[sqh, dummy_ally],
            front_line=[sqh],
            back_line=[dummy_ally], pet=Phoenix()
        )

    boss = Boss()

    print("\n--- START OF BATTLE ---")
    logs = sqh.start_of_battle(team, boss)
    for log in logs:
        print(log)

    print("\n--- ROUND 1: ACTIVE SKILL ---")
    logs = sqh.active_skill(boss, team)
    for log in logs:
        print(log)

    print(f"➡️ Boss Abyssal Corruption: {getattr(boss, 'abyssal_corruption', 0)}")
    print(f"➡️ Boss Buffs: {[(k, v) for k, v in boss.buffs.items() if 'crit' in k.lower()]}")

    print("\n--- ROUND 2: BASIC ATTACK ---")
    logs = sqh.basic_attack(boss, team)
    for log in logs:
        print(log)

    print(f"➡️ SQH Buffs: {[(k, v) for k, v in sqh.buffs.items()]}")

    print("\n--- ROUND 3: ACTIVE SKILL ---")
    logs = sqh.active_skill(boss, team)
    for log in logs:
        print(log)

    print(f"➡️ Boss Abyssal Corruption: {getattr(boss, 'abyssal_corruption', 0)}")
    print(f"➡️ Boss Buffs: {[(k, v) for k, v in boss.buffs.items() if 'crit' in k.lower()]}")

    print("\n--- ROUND 4: ACTIVE SKILL (Triggers Transition) ---")
    logs = sqh.active_skill(boss, team)
    for log in logs:
        print(log)

    print(f"➡️ Boss Abyssal Corruption: {getattr(boss, 'abyssal_corruption', 0)}")
    print(f"➡️ Boss Buffs: {[(k, v) for k, v in boss.buffs.items() if 'crit' in k.lower()]}")

    # Custom comparison test: CRIT with 0 vs 5 Abyssal
    print("\n--- CUSTOM COMPARISON: 0 Abyssal vs 5 Abyssal (Crit Forced) ---")
    base_sqh = SQH("SQH_Test", 10_000_000_000, 200_000_000, 3000, 100, 100, 100, 0, 0, 0)
    base_sqh.crit_rate = 100
    base_sqh.crit_dmg = 100
    base_sqh.precision = 0
    base_sqh.all_damage_dealt = 0
    base_sqh._using_real_attack = True
    base_sqh._current_action_type = "active"
    dummy_team = Team([base_sqh], [base_sqh], [])

    # 0 Abyssal
    boss_clean = Boss()
    boss_clean.hp = boss_clean.max_hp = 100_000_000_000
    logs = hero_deal_damage(base_sqh, boss_clean, base_sqh.atk * 18, is_active=True, team=dummy_team, allow_counter=False)
    print("\n➡️ Damage with 0 Abyssal:")
    for log in logs:
        print(log)

    # 5 Abyssal
    boss_corrupted = Boss()
    boss_corrupted.hp = boss_corrupted.max_hp = 100_000_000_000
    boss_corrupted.abyssal_corruption = 5
    BuffHandler.apply_debuff(boss_corrupted, "crit_dmg_in", {
        "attribute": "crit_damage_taken", "bonus": 120, "rounds": 9999
    })
    logs = hero_deal_damage(base_sqh, boss_corrupted, base_sqh.atk * 18, is_active=True, team=dummy_team, allow_counter=False)
    print("\n➡️ Damage with 5 Abyssal:")
    for log in logs:
        print(log)

if __name__ == "__main__":
    run_sqh_skill_test()
