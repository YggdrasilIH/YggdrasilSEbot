
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
    await interaction.response.send_message("Enter 6 hero acronyms (e.g., SQH, LFA, MFF...):", ephemeral=True)
    def check(m): return m.author == interaction.user and m.channel == interaction.channel

    try: lineup_msg = await bot.wait_for("message", check=check, timeout=120)
    except: await interaction.followup.send("⏱️ Timed out.", ephemeral=True); return

    selected = [x.strip().upper() for x in lineup_msg.content.split(",") if x.strip()]
    if len(selected) != 6:
        await interaction.followup.send("❌ Must provide exactly 6 acronyms.", ephemeral=True); return

    mapped_ids = []
    for acr in selected:
        if acr not in hero_acronym_mapping:
            await interaction.followup.send(f"❌ Unknown hero acronym: {acr}", ephemeral=True)
            return
        mapped_ids.append(hero_acronym_mapping[acr])

    user_id = interaction.user.id
    pending_teams[user_id] = {"expected": mapped_ids, "enables": {}, "heroes": []}

    await interaction.followup.send("Enter enable settings (e.g., SQH CP UW; LFA ARP UW; ...):", ephemeral=True)
    try: enables_msg = await bot.wait_for("message", check=check, timeout=120)
    except: await interaction.followup.send("⏱️ Timed out.", ephemeral=True); return

    for entry in enables_msg.content.strip().split(";"):
        parts = entry.strip().split()
        if len(parts) != 3: continue
        hero, purify, trait = parts
        full_id = hero_acronym_mapping.get(hero.upper())
        if full_id and purify in purify_mapping and trait in trait_mapping:
            pending_teams[user_id]["enables"][full_id] = (purify_mapping[purify], trait_mapping[trait])

    await interaction.followup.send("Enter HP values (comma-separated):", ephemeral=True)
    hp = [parse_number(v) for v in (await bot.wait_for("message", check=check, timeout=120)).content.split(",")]

    await interaction.followup.send("Enter ATK values (comma-separated):", ephemeral=True)
    atk = [parse_number(v) for v in (await bot.wait_for("message", check=check, timeout=120)).content.split(",")]

    await interaction.followup.send("Enter SPD values (comma-separated):", ephemeral=True)
    spd = [parse_number(v) for v in (await bot.wait_for("message", check=check, timeout=120)).content.split(",")]

    await interaction.followup.send("Enter artifacts (comma-separated, or 'none'):", ephemeral=True)
    artifacts = [get_artifact_instance(v) for v in (await bot.wait_for("message", check=check, timeout=120)).content.split(",")]

    await interaction.followup.send("Enter copy codes for each hero (GK, DEF, GK DEF, or none):", ephemeral=True)
    try: copy_msg = await bot.wait_for("message", check=check, timeout=120)
    except: copy_msg = None
    copy_codes = [x.upper() for x in copy_msg.content.split(",")] if copy_msg else ["none"] * 6

    await interaction.followup.send("Select Core of Origin: PDE or none:", ephemeral=True)
    try: core_msg = await bot.wait_for("message", check=check, timeout=60)
    except: core_msg = None
    global active_core
    active_core = PDECore() if (core_msg and core_msg.content.lower() == "pde") else None

    await interaction.followup.send("Choose fight mode: detailed or summary:", ephemeral=True)
    try: mode_msg = await bot.wait_for("message", check=check, timeout=60)
    except: mode = "detailed"
    else:
        mode = mode_msg.content.lower()
        if mode not in ["detailed", "summary"]: mode = "detailed"

    ids = pending_teams[user_id]["expected"]
    user_config = pending_teams[user_id]
    for i, hero_id in enumerate(ids):
        hero = Hero.from_stats(hero_id, [hp[i], atk[i], spd[i]], artifact=artifacts[i])
        if hero_id in user_config["enables"]:
            hero.set_enables(*user_config["enables"][hero_id])
        if "GK" in copy_codes[i]: hero.gk = True
        if "DEF" in copy_codes[i]: hero.defier = True
        user_config["heroes"].append(hero)

    front, back = user_config["heroes"][:2], user_config["heroes"][2:]
    team, boss = Team(user_config["heroes"], front, back), Boss()

    from battle import simulate_battle
    logs = []
    for hero in team.heroes:
        if hasattr(hero, "start_of_battle"):
            logs.extend(hero.start_of_battle(team, boss))
    logs += await simulate_battle(interaction, team, boss, mode)

    for log in logs:
        await interaction.followup.send(log)
    del pending_teams[user_id]

@tree.command(name="debugbattle", description="Run a debug battle", guild=guild_id)
async def debug_battle(interaction: discord.Interaction):
    from game_logic.artifacts import DB, Mirror, Scissors, Antlers
    from battle import simulate_battle
    global active_core
    active_core = PDECore()

    data = [
        ("hero_SQH_Hero", 1e10, 1e9, 3000, "MP", "UW", DB()),
        ("hero_MFF_Hero", 1e10, 1e9, 3000, "MP", "UW", DB()),
        ("hero_DGN_Hero", 1e10, 1e9, 3000, "MP", "UW", Scissors()),
        ("hero_LFA_Hero", 1e10, 1e9, 3000, "MP", "UW", Antlers()),
        ("hero_PDE_Hero", 1e10, 1e9, 3000, "MP", "UW", Mirror()),
        ("hero_LBRM_Hero", 1e10, 1e9, 3000, "MP", "UW", Mirror())
    ]

    heroes = []
    for hid, hp, atk, spd, purify, trait, artifact in data:
        h = Hero.from_stats(hid, [hp, atk, spd], artifact=artifact)
        h.set_enables(purify, trait)
        h.gk = h.defier = True
        heroes.append(h)

    team = Team(heroes, heroes[:2], heroes[2:])
    boss = Boss()
    await interaction.response.send_message("🧪 Starting debug battle...", ephemeral=True)

    logs = []
    for hero in team.heroes:
        if hasattr(hero, "start_of_battle"):
            logs.extend(hero.start_of_battle(team, boss))
    logs += await simulate_battle(interaction, team, boss, "detailed")

    for log in logs:
        await interaction.followup.send(log)

@bot.event
async def on_ready():
    synced = await tree.sync(guild=guild_id)
    print(f"Synced commands: {[cmd.name for cmd in synced]}")
    print(f"Logged in as {bot.user}")

bot.run(os.environ["DISCORD_TOKEN"])
