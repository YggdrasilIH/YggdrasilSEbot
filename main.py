# main.py
from dotenv import load_dotenv
load_dotenv()
import os
import discord
from discord.ext import commands
from game_logic import Hero, Boss, Team
from game_logic.artifacts import Scissors, DB, Mirror, Antlers
from game_logic.cores import active_core, PDECore
from game_logic.lifestar import Specter
from utils.battle import chunk_logs  # Ensure this is imported at top


from game_logic.enables import ControlPurify, AttributeReductionPurify, MarkPurify, BalancedStrike, UnbendingWill

purify_mapping = {
    "CP": ControlPurify(),
    "ARP": AttributeReductionPurify(),
    "MP": MarkPurify()
}
trait_mapping = {
    "BS": BalancedStrike(),
    "UW": UnbendingWill()
}
hero_acronym_mapping = {
    "SQH": "hero_SQH_Hero", "LFA": "hero_LFA_Hero", "MFF": "hero_MFF_Hero",
    "ELY": "hero_ELY_Hero", "PDE": "hero_PDE_Hero", "LBRM": "hero_LBRM_Hero", "DGN": "hero_DGN_Hero"
}

def parse_number(s):
    s = s.strip()
    if s[-1].lower() == "b": return float(s[:-1]) * 1e9
    if s[-1].lower() == "m": return float(s[:-1]) * 1e6
    if s[-1].lower() == "k": return float(s[:-1]) * 1e3
    return float(s)

def get_artifact_instance(code):
    code = code.strip().lower()
    return {
        "scissors": Scissors(), "db": DB(), "mirror": Mirror(), "antlers": Antlers()
    }.get(code, None)

def get_lifestar_instance(code):
    code = code.strip().lower()
    if not code or code == "none":
        return None
    elif code == "specter":
        return Specter()
    else:
        return None

pending_teams = {}
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
guild_id = discord.Object(id=1358992627424428176)

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

def format_logs_as_bullet_points(logs):
    formatted_lines = []
    for line in logs:
        if isinstance(line, str) and line.strip():
            category = detect_category(str(line))
            formatted_lines.append(stylize_log(str(line), category))
            if category in {"control", "transition", "passive", "curse", "calamity", "debuff", "attack"}:
                formatted_lines.append("")
    return "\n".join(formatted_lines)

def chunk_logs(log_block, limit=1900):
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

@tree.command(name="debugbattle", description="Run full battle with logs", guild=guild_id)
async def debug_battle(interaction):
    from discord import Interaction
    global active_core
    active_core = PDECore()

    data = [
        ("hero_MFF_Hero", 11e9, 60e6, 3800, "MP", "UW", DB()),
        ("hero_SQH_Hero", 12e9, 70e6, 3400, "MP", "UW", DB()),
        ("hero_LFA_Hero", 20e9, 160e6, 3500, "MP", "BS", Antlers()),
        ("hero_DGN_Hero", 14e9, 90e6, 3300, "MP", "UW", Scissors()),
        ("hero_PDE_Hero", 9e9, 60e6, 2300, "MP", "UW", Mirror()),
        ("hero_LBRM_Hero", 9.9e9, 50e6, 2000, "MP", "UW", Mirror())
    ]

    heroes = []
    for hid, hp, atk, spd, purify, trait, artifact in data:
        lifestar = Specter() if hid == "hero_LFA_Hero" else None
        h = Hero.from_stats(hid, [hp, atk, spd], artifact=artifact, lifestar=lifestar)
        h.set_enables(purify, trait)
        h.gk = h.defier = True
        h.total_damage_dealt = 0
        heroes.append(h)

    team = Team(heroes, heroes[:2], heroes[2:])
    boss = Boss()

    await interaction.response.send_message("🧪 Starting debug battle with detailed logs...", ephemeral=True)
    from battle import simulate_battle
    await simulate_battle(interaction, team, boss, mode="detailed")


@tree.command(name="debugquick", description="Run a fast debug battle summary", guild=guild_id)
async def debug_quick(interaction: discord.Interaction):
    global active_core
    active_core = PDECore()

    data = [
        ("hero_MFF_Hero", 11e9, 60e6, 3800, "MP", "UW", DB()),
        ("hero_SQH_Hero", 12e9, 70e6, 3400, "MP", "UW", DB()),
        ("hero_LFA_Hero", 20e9, 16e7, 3540, "CP", "BS", Antlers()),
        ("hero_DGN_Hero", 14e9, 90e6, 3300, "MP", "UW", Scissors()),
        ("hero_PDE_Hero", 9e9, 60e6, 2300, "MP", "UW", Mirror()),
        ("hero_LBRM_Hero", 9.9e9, 50e6, 2000, "MP", "UW", Mirror())
    ]

    heroes = []
    for hid, hp, atk, spd, purify, trait, artifact in data:
        lifestar = Specter() if hid == "hero_LFA_Hero" else None
        h = Hero.from_stats(hid, [hp, atk, spd], artifact=artifact, lifestar=lifestar)
        h.set_enables(purify, trait)
        h.gk = h.defier = True
        h.total_damage_dealt = 0
        h._damage_rounds = []
        heroes.append(h)

    team = Team(heroes, heroes[:2], heroes[2:])
    boss = Boss()

    for hero in team.heroes:
        if hero.artifact and hasattr(hero.artifact, "apply_start_of_battle"):
            result = hero.artifact.apply_start_of_battle(team, round_num=1)
            if result:
                print(f"[DEBUG] {hero.name} artifact start-of-battle effect triggered.")
        if hasattr(hero, "start_of_battle"):
            hero.start_of_battle(team, boss)

    round_summaries = []
    for round_num in range(1, 16):
        for hero in team.heroes:
            if hero.lifestar and hasattr(hero.lifestar, "start_of_round"):
                hero.lifestar.start_of_round(hero, team, boss, round_num)
        for hero in team.heroes:
            if hero.lifestar and hasattr(hero.lifestar, "start_of_round"):
                hero.lifestar.start_of_round(hero, team, boss, round_num)

                if all(not h.is_alive() for h in team.heroes) or not boss.is_alive():
                    break

        hero_start_dmg = {h.name: getattr(h, "total_damage_dealt", 0) for h in team.heroes}
        team.perform_turn(boss, round_num)
        team.end_of_round(boss, round_num)
        hero_end_dmg = {h.name: getattr(h, "total_damage_dealt", 0) for h in team.heroes}

        per_hero_logs = []
        for h in team.heroes:
            diff = hero_end_dmg[h.name] - hero_start_dmg[h.name]
            h._damage_rounds.append(diff)
            per_hero_logs.append(f"{h.name}: {diff / 1e9:.2f}B")

        round_total = sum(hero_end_dmg[h] - hero_start_dmg[h] for h in hero_end_dmg)
        round_summaries.append(f"🔁 Round {round_num} ({round_total / 1e9:.2f}B): " + " | ".join(per_hero_logs))

    top_dmg_hero = max(team.heroes, key=lambda h: getattr(h, "total_damage_dealt", 0))
    verdict = "✅ Boss defeated!" if not boss.is_alive() else ("❌ All heroes have fallen!" if all(not h.is_alive() for h in team.heroes) else "⚔️ Battle ended after 15 rounds.")
    lines = [f"{verdict}", f"🏹 Total Damage: {boss.total_damage_taken / 1e9:.2f}B"]
    lines += round_summaries

    for h in team.heroes:
        label = f"**{h.name}**" if h == top_dmg_hero else h.name
        total = sum(h._damage_rounds)
        lines.append(f"{label}: {total / 1e9:.2f}B total")

    await interaction.response.send_message("\n".join(lines), ephemeral=True)

@tree.command(name="debugfast", description="Run a fast debug battle summary", guild=guild_id)
async def debugfast(interaction: discord.Interaction):
    global active_core
    active_core = PDECore()

    data = [
        ("hero_MFF_Hero", 11e9, 60e7, 3800, "MP", "UW", DB()),
        ("hero_SQH_Hero", 12e9, 70e7, 3400, "MP", "UW", DB()),
        ("hero_LFA_Hero", 20e9, 16e8, 3540, "CP", "BS", Antlers()),
        ("hero_DGN_Hero", 14e9, 90e7, 3300, "MP", "UW", Scissors()),
        ("hero_PDE_Hero", 9e9, 60e7, 2300, "MP", "UW", Mirror()),
        ("hero_LBRM_Hero", 9.9e9, 50e7, 2000, "MP", "UW", Mirror())
    ]

    heroes = []
    for hid, hp, atk, spd, purify, trait, artifact in data:
        lifestar = Specter() if hid == "hero_LFA_Hero" else None
        h = Hero.from_stats(hid, [hp, atk, spd], artifact=artifact, lifestar=lifestar)
        h.set_enables(purify_mapping.get(purify), trait_mapping.get(trait))
        h.gk = h.defier = True
        h.total_damage_dealt = 0
        h._damage_rounds = []
        h._energy_rounds = []
        h._curse_offsets_by_source_attr = {}
        heroes.append(h)

    team = Team(heroes, heroes[:2], heroes[2:])
    boss = Boss()

    for hero in team.heroes:
        if hasattr(hero, "start_of_battle"):
            hero.start_of_battle(team, boss)

    round_summaries = []
    for round_num in range(1, 16):
        for hero in team.heroes:
            if hero.lifestar and hasattr(hero.lifestar, "start_of_round"):
                hero.lifestar.start_of_round(hero, team, boss, round_num)
        if all(not h.is_alive() for h in team.heroes) or not boss.is_alive():
            break

        hero_start_dmg = {h.name: h.total_damage_dealt for h in team.heroes}
        hero_start_energy = {h.name: h.energy for h in team.heroes}

        battle_logs = []
        battle_logs += team.perform_turn(boss, round_num)
        battle_logs += team.end_of_round(boss, round_num)

        # Add calamity decay like simulate_battle
        for h in team.heroes:
            if h.is_alive() and h.calamity > 0:
                h.calamity -= 1
                round_summaries.append(f"🧼 {h.name} loses 1 Calamity at end of round. (Now {h.calamity})")

        for h in team.heroes:
            h.battle_logs = battle_logs

        hero_end_dmg = {h.name: h.total_damage_dealt for h in team.heroes}
        hero_end_energy = {h.name: h.energy for h in team.heroes}

        for h in team.heroes:
            logs = getattr(h, "battle_logs", [])
            for line in logs:
                if isinstance(line, str) and "offsets" in line and h.name in line and "(source:" in line:
                    try:
                        source = line.split("(source:")[1].split(")")[0].strip()
                        attr = line.split("offsets ")[1].split(" buff")[0].strip()
                        h._curse_offsets_by_source_attr.setdefault(source, {})
                        h._curse_offsets_by_source_attr[source][attr] = h._curse_offsets_by_source_attr[source].get(attr, 0) + 1
                    except Exception:
                        continue

        if round_num == 1:
            header_line = "         | " + " | ".join(f"{h.name:>6}" for h in team.heroes)
            divider = "-" * len(header_line)
            round_summaries.append("\n" + divider)
            round_summaries.append(header_line)
            round_summaries.append(divider)

        round_summaries.append(f"\n\U0001f501 Round {round_num}")
        round_summaries.append("DMG (B)  | " + " | ".join(f"{(hero_end_dmg[h.name] - hero_start_dmg[h.name]) / 1e9:6.2f}" for h in team.heroes))
        round_summaries.append("\u26a1 \u0394      | " + " | ".join(f"{(hero_end_energy[h.name] - hero_start_energy[h.name]):+6}" for h in team.heroes))
        round_summaries.append("\U0001f9ff Calam | " + " | ".join(f"{h.calamity:6}" for h in team.heroes))
        round_summaries.append("\U0001f480 Curse | " + " | ".join(f"{h.curse_of_decay:6}" for h in team.heroes))

    top_dmg_hero = max(team.heroes, key=lambda h: h.total_damage_dealt)
    verdict = "\u2705 Boss defeated!" if not boss.is_alive() else (
        "\u274c All heroes have fallen!" if all(not h.is_alive() for h in team.heroes)
        else "\u2694\ufe0f Battle ended after 15 rounds."
    )

    lines = [
        verdict,
        f"\U0001f3f9 Total Damage: {boss.total_damage_taken / 1e9:.2f}B",
        "\n\U0001f4ca Final Summary:"
    ]

    team_total = sum(h.total_damage_dealt for h in team.heroes)
    for h in team.heroes:
        dmg = h.total_damage_dealt
        energy = h.energy
        percent = (dmg / team_total * 100) if team_total > 0 else 0
        label = f"**{h.name}**" if h == top_dmg_hero else h.name

        lines.append(f"{label:>6}: {dmg / 1e9:6.2f}B DMG | {energy:>3} ⚡ | {percent:>5.1f}%")

    message = "\n".join(lines + round_summaries)
    chunks = chunk_logs(message, limit=1900)

    await interaction.response.send_message(chunks[0], ephemeral=True)
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk, ephemeral=True)


@tree.command(name="startgame", description="Start the boss battle game", guild=guild_id)
async def start_game(interaction: discord.Interaction):
    await interaction.response.send_message("🧪 This is a placeholder start game command.", ephemeral=True)


@bot.event
async def on_ready():
    synced = await tree.sync(guild=guild_id)
    print(f"Synced commands: {[cmd.name for cmd in synced]}")
    print(f"Logged in as {bot.user}")

bot.run(os.environ["DISCORD_TOKEN"])
