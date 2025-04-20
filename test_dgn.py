from game_logic.heroes.dgn import DGN
from game_logic.team import Team
from game_logic.boss import Boss
from game_logic.buff_handler import BuffHandler


def simulate_dgn():
    dgn = DGN("DGN", 1_000_000_000, 100_000_000, 4000, 100, 0, 150, 0, 0, 100)
    boss = Boss()
    team = Team([dgn], front_line=[dgn], back_line=[])
    dgn.buffs["atk_down_self"] = {"attribute": "atk", "bonus": -0.1, "rounds": 2}
    dgn.buffs["speed_down_self"] = {"attribute": "speed", "bonus": -10, "rounds": 2}
    dgn.transition_power = 12

    logs = []
    logs.extend(dgn.start_of_battle(team, boss))
    logs.extend(dgn.active_skill(boss, team))

    # STRICT after_attack filtering
    debuffs_to_replicate = [
        (name, buff) for name, buff in boss.buffs.items()
        if BuffHandler.is_attribute_reduction(buff, strict=True)
    ]
    for name, buff in debuffs_to_replicate[:2]:
        boss.apply_buff(f"replicated_{name}", buff)
        logs.append(f"DGN replicates {name} back onto {boss.name}.")

    logs.extend(dgn.end_of_round(boss, team, round_num=1))

    # Test basic attack
    logs.append("--- Basic Attack ---")
    logs.extend(dgn.basic_attack(boss, team))

    # Test on_receive_damage
    class Dummy:
        def __init__(self):
            self.name = "FakeAttacker"
            self.hp = 1_000_000_000
            self.atk = 1
            self.shield = 0
            self.buffs = {}
            self.is_alive = lambda: True
            def apply_buff(name, val): self.buffs[name] = val
            self.apply_buff = apply_buff

    dgn.hp = dgn.max_hp // 4  # trigger Fluorescent Shield
    logs.append("--- On Receive Damage ---")
    logs.extend(dgn.on_receive_damage(type("Damage", (), {"source_type": "active"}), team, Dummy()))

    for line in logs:
        print(line)

simulate_dgn()
