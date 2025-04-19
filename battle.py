import textwrap
from utils.log_utils import stylize_log

DISCORD_MESSAGE_LIMIT = 1900

def detect_category(line):
    lowered = line.lower()
    if "energy" in lowered: return "energy"
    if "heals" in lowered or "healed" in lowered: return "buff"
    if "damage" in lowered: return "attack"
    if "buff" in lowered or "gains" in lowered: return "buff"
    if "debuff" in lowered or "reduction" in lowered: return "debuff"
    if "counter" in lowered: return "counter"
    if "shield" in lowered: return "buff"
    if "poison" in lowered or "bleed" in lowered: return "poison"
    if "fear" in lowered or "silence" in lowered or "seal" in lowered: return "debuff"
    if "calamity" in lowered: return "calamity"
    if "curse of decay" in lowered: return "curse"
    if "transition" in lowered: return "transition"
    if "passive" in lowered: return "passive"
    return ""

def format_logs_as_bullet_points(logs):
    return "\n".join(
        stylize_log(str(line), detect_category(str(line)))
        for line in logs
        if isinstance(line, str) and line.strip()
    )

def chunk_logs(log_block, limit=DISCORD_MESSAGE_LIMIT):
    chunks = []
    current_chunk = ""
    for line in log_block.split("\n"):
        if len(current_chunk) + len(line) + 1 > limit:
            chunks.append(current_chunk.strip())
            current_chunk = ""
        current_chunk += line + "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

async def simulate_battle(interaction, team, boss, mode):
    all_logs = []

    # Trigger start-of-battle effects
    battle_start_logs = []
    for hero in team.heroes:
        if hero.artifact and hasattr(hero.artifact, "apply_start_of_battle"):
            result = hero.artifact.apply_start_of_battle(team, round_num=1)
            if result:
                battle_start_logs.extend(result)

    for hero in team.heroes:
        if hasattr(hero, "start_of_battle") and callable(hero.start_of_battle):
            battle_start_logs.extend(hero.start_of_battle(team, boss))

    if mode == "detailed":
        bullet_block = format_logs_as_bullet_points(battle_start_logs)
        for chunk in chunk_logs(bullet_block):
            await interaction.followup.send(chunk)

    all_logs.extend(battle_start_logs)

    for round_num in range(1, 16):
        round_logs = [f"🔁 **Round {round_num}**"]

        for status in team.status_descriptions():
            round_logs.append(f"📊 Status:\n{status}")

        round_logs += team.perform_turn(boss, round_num)

        if all(not h.is_alive() for h in team.heroes):
            round_logs.append("❌ All heroes have fallen. Defeat!")
            all_logs.extend(round_logs)
            return all_logs
        if not boss.is_alive():
            round_logs.append("🏆 Boss defeated! Victory!")
            all_logs.extend(round_logs)
            return all_logs

        round_logs += team.end_of_round(boss, round_num)
        for status in team.status_descriptions():
            round_logs.append(f"📉 Post-round Status:\n{status}")
        round_logs.append(f"💥 Boss HP: {int(boss.hp)} | 🏹 Total Damage: {int(boss.total_damage_taken)}")

        all_logs.extend(round_logs)

        if mode == "detailed":
            bullet_block = format_logs_as_bullet_points(round_logs)
            for chunk in chunk_logs(bullet_block):
                await interaction.followup.send(chunk)

    # Final summary message
    if all(not h.is_alive() for h in team.heroes):
        all_logs.append("❌ All heroes have fallen. Defeat!")
    elif not boss.is_alive():
        all_logs.append("🏆 Boss defeated! Victory!")
    else:
        all_logs.append("⏳ Battle ended after 15 rounds. Boss survived.")

    if mode == "detailed":
        bullet_block = format_logs_as_bullet_points(all_logs)
        for chunk in chunk_logs(bullet_block):
            await interaction.followup.send(chunk)

    return all_logs
