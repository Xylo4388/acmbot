import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import json
from dotenv import load_dotenv
from utils import log_command, log_error, log_info
from difflib import SequenceMatcher
from datetime import datetime

load_dotenv()

# API Keys
POLSU_API_KEY = os.environ["POLSU_KEY"]
URCHIN_API_KEY = os.environ["URCHIN_KEY"]

def load_render_type_data():
    try:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(current_dir, "data")
        with open(os.path.join(data_dir, "rendertype.json"), "r") as f:
            return json.load(f)
    except Exception as e:
        log_error("Render Data Load", "System", "load_render_type_data", str(e))
        return {}

def calculate_name_similarity(name1, name2):
    """Calculate similarity between two names using SequenceMatcher"""
    return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()

async def fetch_name_history(uuid):
    """Fetch name history from Mojang API"""
    url = f"https://api.mojang.com/user/profiles/{uuid}/names"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None

async def fetch_similar_names(username):
    """Fetch similar names from Mojang API"""
    url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                uuid = data.get("id")
                # Get name history to check for similar names
                history = await fetch_name_history(uuid)
                if history:
                    similar_names = []
                    for entry in history:
                        name = entry.get("name")
                        if name and calculate_name_similarity(name, username) >= 0.95:
                            similar_names.append({
                                "name": name,
                                "changed_at": entry.get("changedToAt", 0),
                                "similarity": calculate_name_similarity(name, username)
                            })
                    return similar_names
            return None

async def fetch_bwstats(uuid):
    """Fetch Bedwars stats from bwstats.shivam.pro"""
    url = f"https://bwstats.shivam.pro/user/{uuid}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                html = await response.text()
                # Extract stats from HTML
                final_kills = extract_value(html, "<td>Final Kills</td><td>", "</td>").replace(",", "")
                final_deaths = extract_value(html, "<td>Final Deaths</td><td>", "</td>").replace(",", "")
                return int(final_kills), int(final_deaths)
            return None, None

def extract_value(text, start_delimiter, end_delimiter):
    """Extract value between delimiters"""
    start_index = text.find(start_delimiter)
    if start_index == -1:
        return "0"
    start_index += len(start_delimiter)
    end_index = text.find(end_delimiter, start_index)
    return text[start_index:end_index].strip() if end_index != -1 else "0"

async def fetch_urchin_data(username, api_key):
    urchin_url = f"https://urchin.ws/player/{username}?api_key={api_key}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(urchin_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("detail") == "Invalid API key":
                        return "API_DOWN"
                    return data
                return "API_ERROR"
    except Exception as e:
        log_error("Urchin API Error", username, "fetch_urchin_data", str(e))
        return "API_ERROR"

def calculate_fkdr(final_kills, final_deaths):
    if final_deaths == 0 and final_kills > 0:
        return final_kills
    if final_kills is None or final_deaths is None or (final_kills == 0 and final_deaths == 0):
        return "N/A"
    return final_kills / final_deaths

def setup(bot):
    @bot.tree.command(name="altcheck", description="Check for alts on a Minecraft account")
    @app_commands.describe(username="The Minecraft username to check")
    async def altcheck(interaction: discord.Interaction, username: str):
        try:
            await interaction.response.defer(ephemeral=False)
            log_command(interaction.user.name, "altcheck", f"Checking alts for: {username}")

            async with aiohttp.ClientSession() as session:
                # Fetch the correct UUID and name using the Mojang API
                mojang_response = await session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
                if mojang_response.status != 200:
                    await interaction.followup.send(f"Could not find player: {username}", ephemeral=False)
                    return

                mojang_data = await mojang_response.json()
                uuid = mojang_data.get("id")
                correct_username = mojang_data.get("name")
                name_mc_link = f"https://namemc.com/profile/{uuid}"

                # Use the render_type (current_render) in the Lunar Eclipse skin viewer URL
                render_data = load_render_type_data()
                current_render = render_data.get(username, "default")
                skin_image_url = f"https://starlightskins.lunareclipse.studio/render/{current_render}/{username}/bust"

                # Fetch similar names
                similar_names = await fetch_similar_names(correct_username)
                similar_names_text = ""
                if similar_names:
                    similar_names_text = "**Similar Names:**\n"
                    for entry in similar_names:
                        name = entry.get("name")
                        changed_at = entry.get("changed_at", 0)
                        similarity = entry.get("similarity", 0)
                        if changed_at:
                            date = datetime.fromtimestamp(changed_at/1000).strftime('%Y-%m-%d')
                            similar_names_text += f"• {name} ({similarity*100:.1f}% similar, Changed: {date})\n"
                        else:
                            similar_names_text += f"• {name} ({similarity*100:.1f}% similar)\n"

                # Fetch urchin data for the main username
                urchin_data_main = await fetch_urchin_data(correct_username, URCHIN_API_KEY)
                if urchin_data_main == "API_DOWN":
                    type_main = "Urchin API is currently down"
                elif urchin_data_main == "API_ERROR":
                    type_main = "Error fetching Urchin data"
                elif urchin_data_main and "tags" in urchin_data_main and len(urchin_data_main["tags"]) > 0:
                    tags = [tag.get("type", "").title() for tag in urchin_data_main["tags"] if tag.get("type")]
                    type_main = ", ".join(tags) if tags else "None"
                else:
                    type_main = "None"

                # Fetch stats using bwstats API
                current_kills, current_deaths = await fetch_bwstats(uuid)
                current_fkdr = calculate_fkdr(current_kills, current_deaths)

                if isinstance(current_fkdr, float):
                    current_fkdr = f"{current_fkdr:.2f}"

                alts = []

                # Fetch alts using the quickbuy API
                polsu_url_alts = f"https://api.polsu.xyz/polsu/bedwars/quickbuy/all?uuid={uuid}"
                polsu_response_alts = await session.get(polsu_url_alts, headers={"API-Key": POLSU_API_KEY})

                if polsu_response_alts.status != 200:
                    await interaction.followup.send(f"Error fetching alts data from Polsu for {username}", ephemeral=False)
                    return

                polsu_data_alts = await polsu_response_alts.json()

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

                        # Fetch stats for the alt
                        alt_kills, alt_deaths = await fetch_bwstats(alt_uuid)
                        alt_fkdr = calculate_fkdr(alt_kills, alt_deaths)
                        if isinstance(alt_fkdr, float):
                            alt_fkdr = f"{alt_fkdr:.2f}"

                        # Fetch urchin data for the alt username
                        urchin_data_alt = await fetch_urchin_data(alt_username, URCHIN_API_KEY)
                        if urchin_data_alt == "API_DOWN":
                            type_alt = "Urchin API is currently down"
                        elif urchin_data_alt == "API_ERROR":
                            type_alt = "Error fetching Urchin data"
                        elif urchin_data_alt and "tags" in urchin_data_alt and len(urchin_data_alt["tags"]) > 0:
                            tags = [tag.get("type", "").title() for tag in urchin_data_alt["tags"] if tag.get("type")]
                            type_alt = ", ".join(tags) if tags else "None"
                        else:
                            type_alt = "None"

                        alts.append(f"[{alt_username}](https://namemc.com/profile/{alt_uuid}) | {alt_fkdr} FKDR | {type_alt}")

                alts.sort()

                # Create the embed with the player's skin image as the thumbnail
                embed = discord.Embed(title=f"Alt Check: {correct_username}", color=0x00ff00)
                embed.set_thumbnail(url=skin_image_url)
                embed.add_field(name="UUID", value=uuid, inline=False)
                embed.add_field(name="NameMC Profile", value=f"[Link]({name_mc_link})", inline=False)
                embed.add_field(name="FKDR", value=f"{current_fkdr}", inline=False)
                embed.add_field(name="Urchin Tags", value=f"{type_main}", inline=False)
                
                if similar_names_text:
                    embed.add_field(name="Similar Names", value=similar_names_text, inline=False)

                if alts:
                    embed.add_field(name="Alts Found", value="\n".join(alts), inline=False)
                else:
                    embed.add_field(name="Alts Found", value="No alts found.", inline=False)

                await interaction.followup.send(embed=embed, ephemeral=False)
                log_command(interaction.user.name, "altcheck", f"Successfully checked alts for: {username}")

        except Exception as e:
            log_error("Command Error", interaction.user.name, "altcheck", str(e))
            await interaction.followup.send("An error occurred while checking alts.", ephemeral=False) 