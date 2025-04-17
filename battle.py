# battle.py

import textwrap
from utils.log_utils import stylize_log

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

DISCORD_MESSAGE_LIMIT = 1900  # Slightly below 2000 to account for formatting

def format_logs_as_bullet_points(logs):
    return "\n".join(
        stylize_log(str(line), detect_category(str(line)))
        for line in logs
        if isinstance(line, str) and line.strip()
    )

def chunk_logs(log_block, limit=DISCORD_MESSAGE_LIMIT):
    """Split long log blocks into chunks under the Discord limit."""
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
    if mode == "detailed":
        for round_num in range(1, 16):
            if all(not h.is_alive() for h in team.heroes) or not boss.is_alive():
                break

            logs = [f"🔁 **Round {round_num}**"]

            for status in team.status_descriptions():
                logs.append(f"📊 Status:\n{status}")

            logs += team.perform_turn(boss, round_num)
            logs += team.end_of_round(boss, round_num)

            for status in team.status_descriptions():
                logs.append(f"📉 Post-round Status:\n{status}")

            logs.append(f"💥 Boss HP: {int(boss.hp)} | 🏹 Total Damage: {int(boss.total_damage_taken)}")

            bullet_block = format_logs_as_bullet_points(logs)
            for chunk in chunk_logs(bullet_block):
                await interaction.followup.send(chunk)

    else:
        for round_num in range(1, 16):
            if all(not h.is_alive() for h in team.heroes) or not boss.is_alive():
                break
            team.perform_turn(boss, round_num)
            team.end_of_round(boss, round_num)
        await interaction.followup.send(
            f"📜 Final Summary: Total Damage Dealt: {int(boss.total_damage_taken)}. Boss HP: {int(boss.hp)}."
        )
