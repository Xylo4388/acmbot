import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import sys
import random
from datetime import datetime

# Add the commands directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
commands_dir = os.path.join(current_dir, "commands")
sys.path.append(commands_dir)

# Load environment variables from config directory
load_dotenv(os.path.join(current_dir, "config", ".env"))

# Bot setup with required intents
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
bot = commands.Bot(command_prefix="‎ ", intents=intents)
bot.start_time = datetime.now()

# List of commands to rotate through
COMMANDS = [
    "Alt Checker | /altcheck",
    "Bedwars Stats | /bedwars",
    "Utility | /ping",
    "Utility | /help",
    "Utility | /info",
    "Settings | /setrender",
    "Community | /suggest",
    "Community | /requestchange",
    "Community | /discord",
    "Server | /announce",
    "Server | /poll",
    "Server | /clear"
]

@tasks.loop(seconds=15)
async def rotate_activity():
    # Get a random command from the list
    activity = random.choice(COMMANDS)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name=activity
        )
    )

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bot is in {len(bot.guilds)} servers:")
    for guild in bot.guilds:
        print(f"- {guild.name} (ID: {guild.id})")
    await bot.tree.sync()
    # Start the activity rotation
    rotate_activity.start()

# Load commands
from altcheck import setup as setup_altcheck
from setrender import setup as setup_setrender
from suggest import setup as setup_suggest
from requestchange import setup as setup_requestchange
from discord_invite import setup as setup_discord
from bedwars import setup as setup_bedwars
from utility import setup as setup_utility
from server import setup as setup_server

# Setup commands
setup_altcheck(bot)
setup_setrender(bot)
setup_suggest(bot)
setup_requestchange(bot)
setup_discord(bot)
setup_bedwars(bot)
setup_utility(bot)
setup_server(bot)

# Run bot
bot.run(os.environ["TOKEN"])