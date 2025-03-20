import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import aiohttp
import json
from discord import app_commands
import traceback
import requests
from discord.ui import View, Button

# Load environment variables
load_dotenv()
TOKEN = os.environ["TOKEN"]
POLSU_API_KEY = os.environ["POLSU_API_KEY"]
HYPIXEL_API_KEY = os.environ["HYPIXEL_API_KEY"]

# ID of the user to whom suggestions should be sent
SUGGESTION_CHANNEL = 1351712640434438154
RENDER_CHANNEL = 1351712676471902208
ADMIN_ID = 569334038326804490

# Bot setup
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
bot = commands.Bot(command_prefix="‎ ", intents=intents)


# Load rendertype data from JSON file
def load_render_type_data():
    try:
        with open("rendertype.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Save rendertype data to JSON file
def save_render_type_data(data):
    with open("rendertype.json", "w") as file:
        json.dump(data, file, indent=4)


def calculate_fkdr(kills, deaths):
    return kills / deaths if deaths != 0 else kills  # Avoid division by zero


# Hypixel API call
def fetch_hypixel_data(username, api_key):
    url = f"https://api.hypixel.net/player?name={username}&key={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data.get("success") and "player" in data and data["player"]:  # Ensure player data exists
            stats = data["player"].get("stats", {})
            bedwars = stats.get("Bedwars", {})

            final_kills = bedwars.get("final_kills_bedwars", 0)
            final_deaths = bedwars.get("final_deaths_bedwars", 0)

            return final_kills, final_deaths
        else:
            return None  # Handle case where player data is unavailable
    else:
        return None  # Handle failed API call


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
                type=discord.ActivityType.playing, name="Alt Checker | /altcheck"
            ),
        )
    except Exception as e:
        print(f"Error syncing commands: {e}")


@bot.tree.command(name="discord", description="Get a link to join our Discord server!")
async def discord_embed(interaction: discord.Interaction):
    # Create an embed
    embed = discord.Embed(
        title="Join our Discord Server!",
        description="Click the button below to join our Discord server!",
        color=discord.Color.blue()
    )

    # Create a button
    button = Button(
        label="🔗 Join Server",
        style=discord.ButtonStyle.link,
        url="https://discord.gg/BXTeeSBPWE"
    )

    # Add the button to a view
    view = View()
    view.add_item(button)

    # Send the embed with the view
    await interaction.response.send_message(embed=embed, view=view)



@bot.tree.command(name="altcheck", description="Check for alts on a Minecraft account")
@app_commands.describe(username="The Minecraft username to check")
async def altcheck(interaction: discord.Interaction, username: str):
    print(f"[COMMAND] {interaction.user} used /altcheck with username: {username}")
    try:
        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            # Fetch the correct UUID and name using the Mojang API
            mojang_response = await session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
            if mojang_response.status != 200:
                await interaction.followup.send(f"Could not find player: {username}")
                return

            mojang_data = await mojang_response.json()
            uuid = mojang_data.get("id")
            correct_username = mojang_data.get("name")  # This is the correct Minecraft username, case-sensitive.
            name_mc_link = f"https://namemc.com/profile/{uuid}"

            # Use the render_type (current_render) in the Lunar Eclipse skin viewer URL
            render_data = load_render_type_data()
            current_render = render_data.get(username, "default")  # Default to "default" if not found
            skin_image_url = f"https://starlightskins.lunareclipse.studio/render/{current_render}/{username}/bust"

            # Request rank from Polsu API
            headers = {"API-Key": POLSU_API_KEY}
            polsu_url_rank = f"https://api.polsu.xyz/polsu/bedwars/formatted?uuid={uuid}"
            polsu_response_rank = await session.get(polsu_url_rank, headers=headers)

            if polsu_response_rank.status != 200:
                await interaction.followup.send(f"Error fetching data from Polsu for {username}")
                return

            polsu_data_rank = await polsu_response_rank.json()
            rank = polsu_data_rank.get("data", {}).get("rank", None)
            formatted_current_username = f"[{rank}] {correct_username}" if rank else correct_username

            # Fetch Hypixel FKDR stats for the main account
            async def fetch_hypixel_stats(player_username):
                hypixel_url = f"https://api.hypixel.net/player?name={player_username}&key={HYPIXEL_API_KEY}"
                try:
                    hypixel_response = await session.get(hypixel_url)
                    if hypixel_response.status != 200:
                        print(f"[DEBUG] Hypixel API error: Received status {hypixel_response.status}")
                        return None, None

                    hypixel_data = await hypixel_response.json()
                    if not hypixel_data.get("success") or not hypixel_data.get("player"):
                        print(f"[DEBUG] Invalid Hypixel API response for {player_username}: {hypixel_data}")
                        return None, None

                    stats = hypixel_data["player"].get("stats", {}).get("Bedwars", {})
                    final_kills = stats.get("final_kills_bedwars", 0)
                    final_deaths = stats.get("final_deaths_bedwars", 0)
                    print(
                        f"[DEBUG] Stats for {player_username}: Final Kills = {final_kills}, Final Deaths = {final_deaths}")
                    return final_kills, final_deaths
                except Exception as e:
                    print(f"[ERROR] Error fetching Hypixel stats for {player_username}: {e}")
                    return None, None

            def calculate_fkdr(final_kills, final_deaths):
                if final_deaths == 0 and final_kills > 0:
                    return final_kills  # Avoid division by zero: return kills if deaths are 0
                if final_kills is None or final_deaths is None or (final_kills == 0 and final_deaths == 0):
                    return "N/A"  # Unknown or no stats available
                return final_kills / final_deaths

            current_kills, current_deaths = await fetch_hypixel_stats(correct_username)
            current_fkdr = calculate_fkdr(current_kills, current_deaths)

            if isinstance(current_fkdr, float):
                current_fkdr = f"{current_fkdr:.2f}"  # Format FKDR to 2 decimal places

            # Fetch alts using the quickbuy API
            polsu_url_alts = f"https://api.polsu.xyz/polsu/bedwars/quickbuy/all?uuid={uuid}"
            polsu_response_alts = await session.get(polsu_url_alts, headers=headers)

            if polsu_response_alts.status != 200:
                await interaction.followup.send(f"Error fetching alts data from Polsu for {username}")
                return

            polsu_data_alts = await polsu_response_alts.json()
            alts = []

            if polsu_data_alts.get("success") and "data" in polsu_data_alts and "quickbuy" in polsu_data_alts["data"]:
                quickbuy_array = polsu_data_alts["data"]["quickbuy"]
                for entry in quickbuy_array:
                    alt_username = entry.get("username", "Unknown")
                    if alt_username == "Unknown":
                        alts.append(f"{alt_username} | N/A FKDR")
                        continue

                    mojang_alt_response = await session.get(
                        f"https://api.mojang.com/users/profiles/minecraft/{alt_username}")
                    if mojang_alt_response.status != 200:
                        alts.append(f"{alt_username} | N/A FKDR")
                        continue
                    mojang_alt_data = await mojang_alt_response.json()
                    alt_uuid = mojang_alt_data.get("id")

                    # Fetch rank and FKDR for the alt
                    polsu_response_rank_alt = await session.get(
                        f"https://api.polsu.xyz/polsu/bedwars/formatted?uuid={alt_uuid}", headers=headers)
                    formatted_alt_username = alt_username
                    if polsu_response_rank_alt.status == 200:
                        polsu_data_rank_alt = await polsu_response_rank_alt.json()
                        rank_alt = polsu_data_rank_alt.get("data", {}).get("rank", None)
                        if rank_alt:
                            formatted_alt_username = f"[{rank_alt}] {alt_username}"

                    alt_kills, alt_deaths = await fetch_hypixel_stats(alt_username)
                    alt_fkdr = calculate_fkdr(alt_kills, alt_deaths)
                    if isinstance(alt_fkdr, float):
                        alt_fkdr = f"{alt_fkdr:.2f}"

                    alts.append(f"[{formatted_alt_username}](https://namemc.com/profile/{alt_uuid}) | {alt_fkdr} FKDR")

            alts.sort()

            # Create the embed with the player's skin image as the thumbnail
            embed = discord.Embed(title=f"Alt Check: {formatted_current_username}", color=0x00ff00)
            embed.set_thumbnail(url=skin_image_url)
            embed.add_field(name="UUID", value=uuid, inline=False)
            embed.add_field(name="NameMC Profile", value=f"[Link]({name_mc_link})", inline=False)
            embed.add_field(name="FKDR", value=f"{current_fkdr}", inline=False)

            if alts:
                embed.add_field(name="Alts Found", value="\n".join(alts), inline=False)
            else:
                embed.add_field(name="Alts Found", value="No alts found", inline=False)

            embed.set_footer(
                text=f"Requested by: {interaction.user} in {interaction.guild}",
                icon_url=interaction.user.display_avatar.url if interaction.user.display_avatar else None
            )
            await interaction.followup.send(
                content="For more info, visit the **[wiki](https://github.com/Xylo4388/acmbot/wiki)**",
                embed=embed
            )

    except Exception as e:
        print(f"[ERROR] Exception occurred while running /altcheck with username: {username}")
        traceback.print_exc()
        await interaction.followup.send("An unexpected error occurred. Please try again later.")

# Set render type command (only for specific user)
@bot.tree.command(name="setrender", description="Set render type for a Minecraft username")
@app_commands.describe(username="The Minecraft username", render_type="The render type to set")
async def set_render_type(interaction: discord.Interaction, username: str, render_type: str):
    if interaction.user.id != ADMIN_ID:
        await interaction.response.send_message("You are not authorized to use this command.")
        return

    try:
        # Load existing render type data
        render_data = load_render_type_data()

        # Update the render type for the specified username
        render_data[username] = render_type

        # Save the updated data back to the JSON file
        save_render_type_data(render_data)

        await interaction.response.send_message(f"Render type for {username} has been set to {render_type}.")

    except Exception as e:
        print(f"[ERROR] Exception occurred while setting render type for {username}: {e}")
        await interaction.response.send_message("An error occurred while updating the render type.")

# Suggest command
@bot.tree.command(name="suggest", description="Send a suggestion to the Admins.")
@app_commands.describe(suggestion="Your suggestion to send")
async def suggest(interaction: discord.Interaction, suggestion: str):
    try:
        # Fetch the SUGGESTION_CHANNEL dynamically
        suggestion_channel = bot.get_channel(SUGGESTION_CHANNEL)
        if not suggestion_channel:
            await interaction.response.send_message("❌ Suggestion channel not found. Please contact the administrator.", ephemeral=True)
            return

        # Create an embed for the suggestion
        embed = discord.Embed(
            title="New Suggestion Received",
            description="",
            color=discord.Color.blue()  # You can choose any color
        )
        embed.add_field(name="Suggestion", value=suggestion, inline=False)
        embed.add_field(name="From", value=f"{interaction.user} (ID: {interaction.user.id})", inline=False)
        embed.add_field(
            name="Location",
            value=f"{interaction.guild.name}" if interaction.guild else "User DMs",
            inline=False,
        )
        embed.set_footer(text=f"Created by @bedwarr")

        # Send the embed to the suggestion channel
        await suggestion_channel.send(embed=embed)

        print(f"[SUGGESTION] from {interaction.user}")

        # Notify the user that their suggestion has been received
        await interaction.response.send_message("✅ Your suggestion has been sent! Thank you!", ephemeral=True)

    except discord.Forbidden:
        # Error handling in case the bot doesn't have permission to send messages
        await interaction.response.send_message(
            "❌ I don't have permission to send messages in the suggestion channel.",
            ephemeral=True,
        )
    except Exception as e:
        print(f"[ERROR] Error sending suggestion: {e}")
        await interaction.response.send_message("❌ An error occurred while sending your suggestion.", ephemeral=True)

# Request change command
@bot.tree.command(name="requestchange", description="Request a change for your player model rendering")
@app_commands.describe(username="Minecraft username", render_type="The render type you want to change to")
async def request_change(interaction: discord.Interaction, username: str, render_type: str):
    valid_render_types = [
        "default", "marching", "walking", "crouching", "crossed", "criss_cross", "ultimate", "isometric",
        "head", "custom", "cheering", "relaxing", "trudging", "cowering", "pointing", "lunging", "dungeons",
        "facepalm", "sleeping", "dead", "archer", "kicking", "mojavatar", "reading", "high_ground", "clown"
    ]
    if render_type not in valid_render_types:
        await interaction.response.send_message(f"❌ Invalid render type. Please choose a valid type from [Lunar Eclipse Docs](<https://docs.lunareclipse.studio/>).", ephemeral=True)
        return

    # Load render type data
    render_data = load_render_type_data()

    # Get the current render type (defaults to "default" if not found)
    current_render = render_data.get(username, "default")

    # Create an embed for the request change
    embed = discord.Embed(
        title="Player Model Change Request",
        description=f"**Username:** {username}\n**Current Render:** {current_render}\n**Requested Render:** {render_type}",
        color=discord.Color.green()
    )
    embed.add_field(name="Request Sent By", value=f"{interaction.user} (ID: {interaction.user.id})", inline=False)
    embed.add_field(name="Location", value=f"{interaction.guild.name}" if interaction.guild else "User DMs", inline=False)
    embed.set_footer(text=f"Requested by {interaction.user.name}")

    # Send the embed to the render channel and suggestion channel
    render_channel = bot.get_channel(RENDER_CHANNEL)

    await render_channel.send(embed=embed)

    # Notify the user that the suggestion has been sent
    await interaction.response.send_message(
        "✅ Your request for the player model change has been sent! Thank you.", ephemeral=True
    )


# Run the bot
bot.run(TOKEN)
