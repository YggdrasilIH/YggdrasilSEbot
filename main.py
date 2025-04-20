from dotenv import load_dotenv
load_dotenv()
import os
import discord
from discord.ext import commands
from game_logic import Hero, Boss, Team
from game_logic.artifacts import Scissors, DB, Mirror, Antlers
from game_logic.cores import active_core, PDECore

purify_mapping = {"CP": "Control_Purify", "ARP": "Attribute_Reduction_Purify", "MP": "Mark_Purify"}
trait_mapping = {"BS": "Balanced_Strike", "UW": "Unbending_Will"}
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

pending_teams = {}
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree
guild_id = discord.Object(id=1358992627424428176)

@tree.command(name="startgame", description="Start the boss battle game", guild=guild_id)
async def start_game(interaction: discord.Interaction):
    await interaction.response.send_message("🧪 This is a placeholder start game command.", ephemeral=True)

@tree.command(name="debugquick", description="Run a fast debug battle summary", guild=guild_id)
async def debug_quick(interaction: discord.Interaction):
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
        h = Hero.from_stats(hid, [hp, atk, spd], artifact=artifact)
        h.set_enables(purify, trait)
        h.gk = h.defier = True
        h.total_damage_dealt = 0
        heroes.append(h)

    team = Team(heroes, heroes[:2], heroes[2:])
    boss = Boss()
    for hero in team.heroes:
        if hasattr(hero, "start_of_battle"):
            hero.start_of_battle(team, boss)

    for round_num in range(1, 16):
        if all(not h.is_alive() for h in team.heroes) or not boss.is_alive():
            break
        team.perform_turn(boss, round_num)
        team.end_of_round(boss, round_num)

    top_dmg_hero = max(team.heroes, key=lambda h: getattr(h, "total_damage_dealt", 0))
    verdict = "✅ Boss defeated!" if not boss.is_alive() else ("❌ All heroes have fallen!" if all(not h.is_alive() for h in team.heroes) else "⚔️ Battle ended after 15 rounds.")
    lines = [f"{verdict}", f"🏹 Total Damage: {boss.total_damage_taken / 1e9:.2f}B"]
    hero_stats = [(h.name, getattr(h, "total_damage_dealt", 0)) for h in team.heroes]
    top_name = top_dmg_hero.name
    for name, dmg in hero_stats:
        label = f"**{name}**" if name == top_name else name
        lines.append(f"{label}: {dmg / 1e9:.2f}B damage")
    await interaction.response.send_message("".join(lines), ephemeral=True)


@tree.command(name="debugbattle", description="Run full battle with logs", guild=guild_id)
async def debug_battle(interaction: discord.Interaction):
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
        h = Hero.from_stats(hid, [hp, atk, spd], artifact=artifact)
        h.set_enables(purify, trait)
        h.gk = h.defier = True
        h.total_damage_dealt = 0
        heroes.append(h)

    team = Team(heroes, heroes[:2], heroes[2:])
    boss = Boss()
    logs = []
    for hero in team.heroes:
        if hasattr(hero, "start_of_battle"):
            logs.extend(hero.start_of_battle(team, boss))

    for round_num in range(1, 16):
        if all(not h.is_alive() for h in team.heroes) or not boss.is_alive():
            break
        logs.extend(team.perform_turn(boss, round_num))
        logs.extend(team.end_of_round(boss, round_num))

    verdict = "✅ Boss defeated!" if not boss.is_alive() else ("❌ All heroes have fallen!" if all(not h.is_alive() for h in team.heroes) else "⚔️ Battle ended after 15 rounds.")
    logs.append(verdict)
    chunks = ["".join(logs[i:i+20]) for i in range(0, len(logs), 20)]
    await interaction.response.send_message(chunks[0], ephemeral=True)
    for chunk in chunks[1:]:
        await interaction.followup.send(chunk, ephemeral=True)


@tree.command(name="debugfast", description="Run a fast 3-round battle", guild=guild_id)
async def debug_fast(interaction: discord.Interaction):
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
        h = Hero.from_stats(hid, [hp, atk, spd], artifact=artifact)
        h.set_enables(purify, trait)
        h.gk = h.defier = True
        h.total_damage_dealt = 0
        heroes.append(h)

    team = Team(heroes, heroes[:2], heroes[2:])
    boss = Boss()
    for hero in team.heroes:
        if hasattr(hero, "start_of_battle"):
            hero.start_of_battle(team, boss)

    for round_num in range(1, 4):
        if all(not h.is_alive() for h in team.heroes) or not boss.is_alive():
            break
        team.perform_turn(boss, round_num)
        team.end_of_round(boss, round_num)

    await interaction.response.send_message(f"Fast test complete. Boss HP: {int(boss.hp):,}", ephemeral=True)

@bot.event
async def on_ready():
    synced = await tree.sync(guild=guild_id)
    print(f"Synced commands: {[cmd.name for cmd in synced]}")
    print(f"Logged in as {bot.user}")

bot.run(os.environ["DISCORD_TOKEN"])
