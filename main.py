# main.py
from dotenv import load_dotenv
load_dotenv()
import os
import discord
from discord.ext import commands
from game_logic import Hero, Boss, Team  # Our __init__.py exposes these classes.
from game_logic.artifacts import Scissors, DB, Mirror, Antlers
from game_logic.cores import active_core, PDECore  # Import from the new cores module



# Mapping dictionaries for converting acronyms.
purify_mapping = {
    "CP": "Control_Purify",
    "ARP": "Attribute_Reduction_Purify",
    "MP": "Mark_Purify"
}
trait_mapping = {
    "BS": "Balanced_Strike",
    "UW": "Unbending_Will"
}
hero_acronym_mapping = {
    "SQH": "hero_SQH_Hero",
    "LFA": "hero_LFA_Hero",
    "MFF": "hero_MFF_Hero",
    "ELY": "hero_ELY_Hero",
    "PDE": "hero_PDE_Hero",
    "LBRM": "hero_LBRM_Hero",
    "DGN": "hero_DGN_Hero"
}

# Utility function to parse numbers with optional shorthand suffixes.
def parse_number(s):
    s = s.strip()
    if s[-1].lower() == "b":
        return float(s[:-1]) * 1e9
    elif s[-1].lower() == "m":
        return float(s[:-1]) * 1e6
    elif s[-1].lower() == "k":
        return float(s[:-1]) * 1e3
    else:
        return float(s)

# Artifact mapping function.
def get_artifact_instance(artifact_code):
    code = artifact_code.strip().lower()
    if not code or code == "none":
        return None
    elif code == "scissors":
        return Scissors()
    elif code == "db":
        return DB()
    elif code == "mirror":
        return Mirror()
    elif code == "antlers":
        return Antlers()
    else:
        return None

# Global dictionary to store pending team configurations per user.
pending_teams = {}

# Define bot intents.
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Replace with your actual Discord Guild ID.
guild_id = discord.Object(id=1358992627424428176)

# ---------------------------
# Step 1: Hero Lineup Selection (Comma-Separated)
# ---------------------------
@tree.command(name="startgame", description="Start the boss battle game", guild=guild_id)
async def start_game(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Enter your hero lineup as a comma-separated list of acronyms (positions 1 to 6, in order). \n"
        "Example: SQH, LFA, MFF, ELY, PDE, DGN",
        ephemeral=True
    )

    def check_message(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        lineup_msg = await bot.wait_for("message", check=check_message, timeout=120)
    except Exception:
        await interaction.followup.send("Timed out waiting for hero lineup input.", ephemeral=True)
        return

    # Process input: strip spaces and ignore empty strings.
    selected = [x.strip().upper() for x in lineup_msg.content.split(",") if x.strip()]
    if len(selected) != 6:
        await interaction.followup.send("Error: You must enter exactly 6 hero acronyms.", ephemeral=True)
        return

    # Validate each acronym.
    for hero_acr in selected:
        if hero_acr not in hero_acronym_mapping:
            await interaction.followup.send(f"Error: Unknown hero acronym: {hero_acr}", ephemeral=True)
            return

    user_id = interaction.user.id
    pending_teams[user_id] = {
        "expected": [hero_acronym_mapping[acr] for acr in selected],
        "enables": {},
        "heroes": []
    }
    response_text = "Heroes selected in lineup order (Positions 1-6):\n" + ", ".join(selected)
    response_text += "\n(Front Line: positions 1-2; Back Line: positions 3-6)"
    response_text += "\nNow, please enter enable settings for each hero using the following format:\n"
    response_text += "Example: SQH CP UW; LFA ARP UW; MFF CP BS; ELY CP BS; PDE ARP UW; DGN MP UW"
    await interaction.followup.send(response_text, ephemeral=True)

    # ---------------------------
    # Step 2: Enable Settings Input
    # ---------------------------
    try:
        enables_msg = await bot.wait_for("message", check=check_message, timeout=120)
    except Exception:
        await interaction.followup.send("Timed out waiting for enable settings.", ephemeral=True)
        return
    enables_input = enables_msg.content.strip()
    entries = [entry.strip() for entry in enables_input.split(";") if entry.strip()]
    for entry in entries:
        parts = entry.split()
        if len(parts) != 3:
            await interaction.followup.send(f"Error: Invalid format in entry '{entry}'. Expected e.g., SQH CP UW", ephemeral=True)
            return
        hero_acr, purify_code, trait_code = parts
        if hero_acr not in hero_acronym_mapping:
            await interaction.followup.send(f"Error: Unknown hero acronym: {hero_acr}", ephemeral=True)
            return
        if purify_code not in purify_mapping or trait_code not in trait_mapping:
            await interaction.followup.send(f"Error: Invalid codes in entry: '{entry}'", ephemeral=True)
            return
        full_hero_id = hero_acronym_mapping[hero_acr]
        pending_teams[user_id]["enables"][full_hero_id] = (purify_mapping[purify_code], trait_mapping[trait_code])
    await interaction.followup.send("Enable settings recorded.", ephemeral=True)

    # ---------------------------
    # Step 3: Stat Input (HP, ATK, SPD)
    # ---------------------------
    await interaction.followup.send("Enter comma-separated HP values for the heroes (lineup order; suffixes B, M, K allowed):", ephemeral=True)
    try:
        hp_msg = await bot.wait_for("message", check=check_message, timeout=120)
    except Exception:
        await interaction.followup.send("Timed out waiting for HP values.", ephemeral=True)
        return
    try:
        hp_values = [parse_number(val) for val in hp_msg.content.split(",") if val.strip()]
    except Exception as e:
        await interaction.followup.send(f"Error parsing HP values: {e}", ephemeral=True)
        return

    await interaction.followup.send("Enter comma-separated ATK values (lineup order; suffixes allowed):", ephemeral=True)
    try:
        atk_msg = await bot.wait_for("message", check=check_message, timeout=120)
    except Exception:
        await interaction.followup.send("Timed out waiting for ATK values.", ephemeral=True)
        return
    try:
        atk_values = [parse_number(val) for val in atk_msg.content.split(",") if val.strip()]
    except Exception as e:
        await interaction.followup.send(f"Error parsing ATK values: {e}", ephemeral=True)
        return

    await interaction.followup.send("Enter comma-separated SPD values (lineup order):", ephemeral=True)
    try:
        spd_msg = await bot.wait_for("message", check=check_message, timeout=120)
    except Exception:
        await interaction.followup.send("Timed out waiting for SPD values.", ephemeral=True)
        return
    try:
        spd_values = [parse_number(val) for val in spd_msg.content.split(",") if val.strip()]
    except Exception as e:
        await interaction.followup.send(f"Error parsing SPD values: {e}", ephemeral=True)
        return

    if not (len(hp_values) == len(atk_values) == len(spd_values) == len(pending_teams[user_id]["expected"])):
        await interaction.followup.send("Error: The number of stat values does not match the number of heroes selected.", ephemeral=True)
        return

    # ---------------------------
    # Step 4: Artifact Selection
    # ---------------------------
    await interaction.followup.send("Enter artifact codes for each hero as a comma-separated list (lineup order):", ephemeral=True)
    await interaction.followup.send("Valid codes: None, Scissors, DB, Mirror, Antlers", ephemeral=True)
    try:
        artifact_msg = await bot.wait_for("message", check=check_message, timeout=120)
    except Exception:
        await interaction.followup.send("Timed out waiting for artifact selection.", ephemeral=True)
        return
    artifact_codes = [code.strip() for code in artifact_msg.content.split(",") if code.strip()]
    if len(artifact_codes) != len(pending_teams[user_id]["expected"]):
        await interaction.followup.send("Error: The number of artifact codes must match the number of heroes selected.", ephemeral=True)
        return

    # ---------------------------
    # Step 5: Copy Selection (GK/DEF)
    # ---------------------------
    await interaction.followup.send("Enter copy codes for each hero as a comma-separated list (lineup order).\n"
                                      "For each hero, type: GK if equipping Giant Killer, DEF if equipping Defier, "
                                      "both separated by a space if both, or 'none' if no copy.",
                                      ephemeral=True)
    try:
        copy_msg = await bot.wait_for("message", check=check_message, timeout=120)
    except Exception:
        await interaction.followup.send("Timed out waiting for copy selection. Defaulting to no copies.", ephemeral=True)
        copy_codes = ["none"] * len(pending_teams[user_id]["expected"])
    else:
        copy_codes = [code.strip().upper() for code in copy_msg.content.split(",") if code.strip()]
    if len(copy_codes) != len(pending_teams[user_id]["expected"]):
        await interaction.followup.send("Error: The number of copy entries must match the number of heroes selected.", ephemeral=True)
        return

    # ---------------------------
    # Step 6: Core of Origin Selection
    # ---------------------------
    await interaction.followup.send("Select the Core of Origin for the team: enter 'PDE' for PDE's Core or 'none':", ephemeral=True)
    try:
        core_msg = await bot.wait_for("message", check=check_message, timeout=60)
    except Exception:
        await interaction.followup.send("Timed out waiting for core selection. No core will be used.", ephemeral=True)
        selected_core = "none"
    else:
        selected_core = core_msg.content.strip().lower()
    from game_logic.cores import active_core  # Re-import if necessary.
    if selected_core == "pde":
        from game_logic.cores import PDECore
        active_core = PDECore()
    else:
        active_core = None

    # ---------------------------
    # Step 7: Fight Mode Selection
    # ---------------------------
    await interaction.followup.send("Choose fight mode: enter 'detailed' for round-by-round logs or 'summary' for final summary only:", ephemeral=True)
    try:
        mode_msg = await bot.wait_for("message", check=check_message, timeout=60)
    except Exception:
        await interaction.followup.send("Timed out waiting for fight mode selection. Defaulting to detailed mode.", ephemeral=True)
        mode = "detailed"
    else:
        mode = mode_msg.content.strip().lower()
        if mode not in ["detailed", "summary"]:
            await interaction.followup.send("Invalid input. Defaulting to detailed mode.", ephemeral=True)
            mode = "detailed"

    # ---------------------------
    # Step 8: Create Hero Instances and Configure Team
    # ---------------------------
    user_config = pending_teams[user_id]
    hero_ids = user_config["expected"]  # Ordered list of hero IDs.
    user_config["heroes"] = []
    for i, hero_id in enumerate(hero_ids):
        artifact_instance = get_artifact_instance(artifact_codes[i])
        hero_instance = Hero.from_stats(hero_id, [hp_values[i], atk_values[i], spd_values[i]],
                                        artifact=artifact_instance if artifact_instance is not None else None)
        # Apply enable settings if provided.
        if hero_id in user_config["enables"]:
            purify_opt, trait_opt = user_config["enables"][hero_id]
            hero_instance.set_enables(purify_opt, trait_opt)
        # Process copy settings.
        copy_entry = copy_codes[i]
        # Check for GK (Giant Killer)
        if "GK" in copy_entry.upper():
            hero_instance.gk = True
        # Check for DEF (Defier, or "DEFIER")
        if "DEF" in copy_entry.upper():
            hero_instance.defier = True

        user_config["heroes"].append(hero_instance)

    # Assign front line (first 2 heroes) and back line (positions 3-6).
    front_line = user_config["heroes"][:2]
    back_line = user_config["heroes"][2:]
    team = Team(user_config["heroes"], front_line=front_line, back_line=back_line)
    boss = Boss()
    await interaction.followup.send("All heroes configured. Battle starting!", ephemeral=True)

    # ---------------------------
    # Step 9: Run Battle Rounds (Using battle.py)
    # ---------------------------
    from battle import simulate_battle
    battle_logs = await simulate_battle(interaction, team, boss, mode)
    for log in battle_logs:
        await interaction.followup.send(log)

    if not boss.is_alive():
        await interaction.followup.send("Boss defeated!", ephemeral=True)
    elif all(not h.is_alive() for h in team.heroes):
        await interaction.followup.send("All heroes have fallen!", ephemeral=True)
    else:
        await interaction.followup.send("Battle ended after 15 rounds.", ephemeral=True)
    del pending_teams[user_id]

@tree.command(name="debugbattle", description="Run a test battle with a pre-set team", guild=guild_id)
async def debug_battle(interaction: discord.Interaction):
    from game_logic import Hero, Boss, Team
    from game_logic.artifacts import Antlers
    from battle import simulate_battle

    hero_ids = [
        "hero_SQH_Hero", "hero_MFF_Hero", "hero_DGN_Hero",
        "hero_LFA_Hero", "hero_PDE_Hero", "hero_LBRM_Hero"
    ]
    stats = [(1e10, 1e9, 3000)] * 6  # High HP, ATK, SPD

    heroes = []
    for hero_id, (hp, atk, spd) in zip(hero_ids, stats):
        hero = Hero.from_stats(hero_id, [hp, atk, spd], artifact=Antlers())
        hero.set_enables("Control_Purify", "Unbending_Will")
        heroes.append(hero)

    front_line = heroes[:2]
    back_line = heroes[2:]
    team = Team(heroes, front_line, back_line)
    boss = Boss()

    await interaction.response.send_message("🧪 Starting debug battle with preset heroes...", ephemeral=True)
    logs = await simulate_battle(interaction, team, boss, "detailed")

    for log in logs:
        await interaction.followup.send(log)
# ---------------------------
# Bot Startup and Command Sync
# ---------------------------
@bot.event
async def on_ready():
    synced = await tree.sync(guild=guild_id)
    print(f"Synced commands: {[cmd.name for cmd in synced]}")
    print(f"Logged in as {bot.user}")

bot.run(os.getenv("DISCORD_TOKEN"))
