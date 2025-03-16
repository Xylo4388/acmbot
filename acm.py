import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import aiohttp
from discord import app_commands
import traceback

# Load environment variables
load_dotenv()
TOKEN = os.environ["TOKEN"]
POLSU_API_KEY = os.environ["POLSU_API_KEY"]

# Bot setup
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
bot = commands.Bot(command_prefix="‎ ", intents=intents)


# On bot ready
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} global slash commands")
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.listening, name="/altcheck <username>"
            ),
        )
    except Exception as e:
        print(f"Error syncing commands: {e}")


# Alt-check slash command
@bot.tree.command(name="altcheck", description="Check for alts on a Minecraft account")
@app_commands.describe(username="The Minecraft username to check")
async def altcheck(interaction: discord.Interaction, username: str):
    # Log command usage
    if interaction.guild:
        location = f"Guild: {interaction.guild.name} (ID: {interaction.guild.id})"
    else:
        location = "DMs"
    print(
        f"[COMMAND] User: {interaction.user} (ID: {interaction.user.id}) used /altcheck with username: {username} in {location}")

    try:
        # Acknowledge the interaction immediately
        await interaction.response.defer()

        # Perform asynchronous HTTP requests
        async with aiohttp.ClientSession() as session:
            # Fetch UUID from Mojang API
            mojang_response = await session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
            if mojang_response.status != 200:
                print(f"[ERROR] Mojang API request failed for username: {username}")
                await interaction.followup.send(f"Could not find player: {username}")
                return

            mojang_data = await mojang_response.json()
            uuid = mojang_data.get("id")
            current_username = mojang_data.get("name")
            name_mc_link = f"https://namemc.com/profile/{uuid}"

            # Fetch alts from Polsu API
            polsu_url = f"https://api.polsu.xyz/polsu/bedwars/quickbuy/all?uuid={uuid}"
            headers = {"API-Key": POLSU_API_KEY}
            polsu_response = await session.get(polsu_url, headers=headers)

            if polsu_response.status != 200:
                print(f"[ERROR] Polsu API request failed for UUID: {uuid} (Username: {username})")
                await interaction.followup.send(f"Error fetching data from Polsu for {username}")
                return

            polsu_data = await polsu_response.json()
            alts = []
            if polsu_data.get("success") and "data" in polsu_data and "quickbuy" in polsu_data["data"]:
                quickbuy_array = polsu_data["data"]["quickbuy"]
                for entry in quickbuy_array:
                    alt_username = entry.get("username", "Unknown")
                    alt_uuid = None
                    if alt_username != "Unknown":
                        # Fetch UUID for alt username
                        mojang_alt_response = await session.get(
                            f"https://api.mojang.com/users/profiles/minecraft/{alt_username}")
                        if mojang_alt_response.status == 200:
                            mojang_alt_data = await mojang_alt_response.json()
                            alt_uuid = mojang_alt_data.get("id")

                    # Construct the NameMC link if UUID is available
                    if alt_uuid:
                        alt_namemc_link = f"https://namemc.com/profile/{alt_uuid}"
                        alts.append(f"[{alt_username}]({alt_namemc_link})")
                    else:
                        alts.append(alt_username)

        # Create the embed
        embed = discord.Embed(title=f"Alt Check: {current_username}", color=0x00ff00)
        embed.add_field(name="UUID", value=uuid, inline=False)
        embed.add_field(name="NameMC Profile", value=f"[Link]({name_mc_link})", inline=False)

        if alts:
            embed.add_field(name="Alts Found", value="\n".join(alts), inline=False)
        else:
            embed.add_field(name="Alts Found", value="No alts found", inline=False)

        # Update embed footer with @username tag
        user_tag = f"@{interaction.user.name}"  # Proper @username format
        if interaction.guild:
            embed.set_footer(text=f"Requested by {user_tag} in {interaction.guild.name}")
        else:
            embed.set_footer(text=f"Requested by {user_tag} in DMs")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        # Log the error in the console
        print(f"[ERROR] Exception occurred while running /altcheck with username: {username}")
        traceback.print_exc()

        # Send error message to the user
        await interaction.followup.send(
            "An unexpected error occurred while processing your request. Please try again later.")


# Run the bot
bot.run(TOKEN)