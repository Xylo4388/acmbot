import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
import json
from dotenv import load_dotenv
from utils import log_command, log_error, log_info

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", ".env"))

def load_render_type_data():
    """Load render type data from rendertype.json"""
    try:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(current_dir, "data")
        with open(os.path.join(data_dir, "rendertype.json"), "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def extract_value(text, start_delimiter, end_delimiter):
    """Extract value between delimiters"""
    start_index = text.find(start_delimiter)
    if start_index == -1:
        return "0"
    start_index += len(start_delimiter)
    end_index = text.find(end_delimiter, start_index)
    return text[start_index:end_index].strip() if end_index != -1 else "0"

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
                wins = extract_value(html, "<td>Wins</td><td>", "</td>").replace(",", "")
                losses = extract_value(html, "<td>Losses</td><td>", "</td>").replace(",", "")
                beds_broken = extract_value(html, "<td>Beds Broken</td><td>", "</td>").replace(",", "")
                beds_lost = extract_value(html, "<td>Beds Lost</td><td>", "</td>").replace(",", "")
                kills = extract_value(html, "<td>Kills</td><td>", "</td>").replace(",", "")
                deaths = extract_value(html, "<td>Deaths</td><td>", "</td>").replace(",", "")
                stars = extract_value(html, "Level: ", " ").replace(",", "").replace(" ", "").replace("âœª", "").replace("âœ©", "")
                return {
                    "final_kills": int(final_kills),
                    "final_deaths": int(final_deaths),
                    "wins": int(wins),
                    "losses": int(losses),
                    "beds_broken": int(beds_broken),
                    "beds_lost": int(beds_lost),
                    "kills": int(kills),
                    "deaths": int(deaths),
                    "stars": int(stars)
                }
            return None

def calculate_ratio(value1, value2):
    """Calculate ratio with proper handling of zero values"""
    if value2 == 0:
        return value1 if value1 > 0 else 0
    return value1 / value2

def format_ratio(value):
    """Format ratio to 2 decimal places"""
    return f"{value:.2f}"

def format_stars(stars):
    """Format stars with appropriate symbol"""
    if stars < 1000:
        return f"{stars}✫"
    else:
        return f"{stars}✪"

def remove_color_codes(text):
    """Remove Minecraft color codes from text"""
    if not text:
        return text
    # Remove § and any character after it
    return ''.join(char for i, char in enumerate(text) if char != '§' and (i == 0 or text[i-1] != '§'))

async def fetch_formatted_data(username):
    """Fetch formatted data from Polsu API"""
    url = f"https://api.polsu.xyz/polsu/bedwars/formatted?uuid={username}"
    headers = {"API-Key": os.environ["POLSU_KEY"]}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("success"):
                    formatted_data = data.get("data", {})
                    # Remove color codes from formatted name if it exists
                    if "formatted" in formatted_data:
                        formatted_data["formatted"] = remove_color_codes(formatted_data["formatted"])
                    return formatted_data
    return None

def setup(bot):
    @bot.tree.command(name="bedwars", description="View Bedwars statistics for a player")
    @app_commands.describe(username="The Minecraft username to check")
    async def bedwars(interaction: discord.Interaction, username: str):
        try:
            await interaction.response.defer(ephemeral=False)
            log_command(interaction.user.name, "bedwars", f"Checking stats for {username}")
            
            # Fetch Mojang data to get UUID
            async with aiohttp.ClientSession() as session:
                mojang_response = await session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
                if mojang_response.status != 200:
                    log_error("Player Not Found", interaction.user.name, "bedwars", f"Player {username} not found in Mojang API")
                    await interaction.followup.send(f"Player '{username}' not found.", ephemeral=False)
                    return
                
                mojang_data = await mojang_response.json()
                uuid = mojang_data.get("id")
                correct_username = mojang_data.get("name")
                log_info("Mojang Data", interaction.user.name, "bedwars", f"Found UUID {uuid} for username {correct_username}")
                
                # Fetch Bedwars stats
                stats = await fetch_bwstats(uuid)
                if not stats:
                    log_error("No Stats Found", interaction.user.name, "bedwars", f"No Bedwars stats found for {correct_username}")
                    await interaction.followup.send(f"No Bedwars stats found for {correct_username}.", ephemeral=False)
                    return
                
                # Fetch formatted name
                formatted_data = await fetch_formatted_data(uuid)
                formatted_name = formatted_data.get("formatted", correct_username) if formatted_data else correct_username
                log_info("Formatted Name", interaction.user.name, "bedwars", f"Formatted name for {correct_username}: {formatted_name}")
                
                # Calculate ratios
                wlr = calculate_ratio(stats["wins"], stats["losses"])
                fkdr = calculate_ratio(stats["final_kills"], stats["final_deaths"])
                bblr = calculate_ratio(stats["beds_broken"], stats["beds_lost"])
                kdr = calculate_ratio(stats["kills"], stats["deaths"])
                
                # Create embed
                embed = discord.Embed(
                    title=f"Bedwars Stats: {formatted_name}",
                    description="Detailed statistics for Bedwars",
                    color=0x00ff00
                )
                
                # Load render type data and get the correct render type
                render_data = load_render_type_data()
                render_type = render_data.get(correct_username, "default")
                log_info("Render Type", interaction.user.name, "bedwars", f"Using render type {render_type} for {correct_username}")
                
                # Add skin render thumbnail with the correct render type
                embed.set_thumbnail(url=f"https://starlightskins.lunareclipse.studio/render/{render_type}/{correct_username}/full")
                
                embed.add_field(
                    name="🏆 Win/Loss",
                    value=f"Wins: `{stats['wins']:,}`\nLosses: `{stats['losses']:,}`\nW/L Ratio: `{format_ratio(wlr)}`",
                    inline=False
                )
                
                embed.add_field(
                    name="⚔️ Final K/D",
                    value=f"Final Kills: `{stats['final_kills']:,}`\nFinal Deaths: `{stats['final_deaths']:,}`\nFKDR: `{format_ratio(fkdr)}`",
                    inline=False
                )
                
                embed.add_field(
                    name="🛏️ Bed Stats",
                    value=f"Beds Broken: `{stats['beds_broken']:,}`\nBeds Lost: `{stats['beds_lost']:,}`\nBBLR: `{format_ratio(bblr)}`",
                    inline=False
                )
                
                embed.add_field(
                    name="⚔️ K/D",
                    value=f"Kills: `{stats['kills']:,}`\nDeaths: `{stats['deaths']:,}`\nK/D Ratio: `{format_ratio(kdr)}`",
                    inline=False
                )
                
                embed.add_field(
                    name="⭐ Stars",
                    value=f"`{format_stars(stats['stars'])}`",
                    inline=False
                )
                
                await interaction.followup.send(embed=embed, ephemeral=False)
                log_command(interaction.user.name, "bedwars", f"Successfully displayed stats for {correct_username}")
                
        except Exception as e:
            log_error("Command Error", interaction.user.name, "bedwars", str(e))
            await interaction.followup.send("An error occurred while fetching Bedwars stats.", ephemeral=False) 