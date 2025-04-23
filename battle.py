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
        for hero in team.heroes:
            if hero.is_alive():
                if hero.hp >= hero.max_hp * 0.5:
                    hero.apply_buff("add_bonus_round", {"attribute": "all_damage_dealt", "bonus": 25, "rounds": 2})
                    all_logs.append(f"✨ {hero.name} gains +25% All Damage Dealt for 2 rounds.")
                else:
                    shield_value = int(hero.max_hp * 0.25)
                    hero.shield += shield_value
                    all_logs.append(f"🛡️ {hero.name} gains a shield equal to 25% of max HP ({shield_value}).")
        for hero in team.heroes:
            if not hasattr(hero, "half_hp_triggered"):
                hero.half_hp_triggered = False
            if hero.is_alive() and not hero.half_hp_triggered and hero.hp < hero.max_hp * 0.5:
                hero.hp = min(hero.max_hp, hero.hp + hero.max_hp)
                hero.half_hp_triggered = True
                all_logs.append(f"🩸 {hero.name}'s passive restores them to full HP when an ally falls below 50%!")

        for hero in team.heroes:
            if round_num == 1:
                if not hasattr(hero, "adr_stack"): hero.adr_stack = 50
                if not hasattr(hero, "hd_stack"): hero.hd_stack = 10
                hero.ADR += hero.adr_stack
                hero.hd += hero.hd_stack
                all_logs.append(f"✨ {hero.name} gains +50% ADR and +10 HD at battle start.")
            else:
                if hasattr(hero, "adr_stack") and hero.adr_stack > 0:
                    reduction = min(10, hero.adr_stack)
                    hero.ADR -= reduction
                    hero.adr_stack -= reduction
                    all_logs.append(f"⬇️ {hero.name}'s ADR buff decays by 10%. (Current: {hero.adr_stack}%)")
                if hasattr(hero, "hd_stack"):
                    hero.hd += 10
                    hero.hd_stack += 10
                    all_logs.append(f"⬆️ {hero.name}'s HD buff increases by 10. (Current: {hero.hd_stack})")
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
        for hero in team.heroes:
            if hero.is_alive() and hero.calamity > 0:
                hero.calamity -= 1
                round_logs.append(f"💀 {hero.name} loses 1 Calamity at end of round. (Remaining: {hero.calamity})")
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
