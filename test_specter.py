# test_specter.py
from game_logic.heroes.sqh import SQH
from game_logic.heroes.lfa import LFA
from game_logic.lifestar import Specter
from game_logic import Boss, Team
from game_logic.damage_utils import hero_deal_damage


def simulate_specter_trigger():
    logs = []
    print("=== Specter Full Functionality Test ===")

    # Create two heroes
    attacker = SQH("SQH", 1_000_000_000, 100_000_000, 4000, 3000, 100, 150, 100, 0, 100)
    receiver = LFA("LFA", 1_000_000_000, 100_000_000, 4000, 3000, 100, 150, 100, 0, 100)

    # Attach Specter to LFA
    receiver.lifestar = Specter()

    # Setup team and boss
    team = Team([attacker, receiver], front_line=[attacker], back_line=[receiver])
    boss = Boss()

    # Test on_ally_hit
    logs.append("--- Testing on_ally_hit ---")
    logs += hero_deal_damage(attacker, receiver, attacker.atk * 1.2, is_active=True, team=team)

    # Test on_after_action
    logs.append("--- Testing on_after_action ---")
    logs += receiver.lifestar.on_after_action(receiver, team)
    logs += receiver.lifestar.on_after_action(receiver, team)
    logs += receiver.lifestar.on_after_action(receiver, team)
    logs += receiver.lifestar.on_after_action(receiver, team)  # This one should trigger burst

    # Test apply_effect and apply_all_effects (indirectly covered by on_after_action)

    # Test apply_start_of_round (Round 1)
    logs.append("--- Testing apply_start_of_round (Round 1) ---")
    if hasattr(receiver.lifestar, "start_of_round"):
        logs += receiver.lifestar.start_of_round(receiver, team, boss, round_num=1)

    # Apply an attribute reduction before end of round
    logs.append("--- Applying -20% ATK debuff to LFA before end of round ---")
    receiver.apply_buff("test_atk_down", {"attribute": "atk", "bonus": -20, "rounds": 2})

    # LFA takes an action in between
    logs.append("--- LFA takes an action between start and end of Round 1 ---")
    logs += receiver.basic_attack(boss, team)

    # Test apply_end_of_round for each of rounds 1 to 6
    for r in range(1, 7):
        logs.append(f"--- Testing apply_end_of_round (Round {r}) ---")
        if hasattr(receiver.lifestar, "end_of_round"):
            logs += receiver.lifestar.end_of_round(receiver, team, boss, round_num=r)

    # Print all logs
    for log in logs:
        print(log)

if __name__ == "__main__":
    simulate_specter_trigger()
