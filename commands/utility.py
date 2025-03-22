import discord
from discord.ext import commands
from discord import app_commands
import platform
import psutil
import os
from datetime import datetime
from utils import log_command, log_error, log_info
import aiohttp
import json
from difflib import SequenceMatcher

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

def calculate_ratio(value1, value2):
    """Calculate ratio with proper handling of zero values"""
    if value2 == 0:
        return value1 if value1 > 0 else 0
    return value1 / value2

def format_ratio(value):
    """Format ratio to 2 decimal places"""
    return f"{value:.2f}"

def setup(bot):
    @bot.tree.command(name="ping", description="Check the bot's latency")
    async def ping(interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            log_command(interaction.user.name, "ping", "Checking bot latency")
            
            # Calculate latency
            latency = round(bot.latency * 1000)
            
            # Create embed
            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Bot Latency: {latency}ms",
                color=0x00ff00
            )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            log_command(interaction.user.name, "ping", f"Latency: {latency}ms")
            
        except Exception as e:
            log_error("Command Error", interaction.user.name, "ping", str(e))
            await interaction.followup.send("An error occurred while checking latency.", ephemeral=True)

    @bot.tree.command(name="help", description="Show all available commands or get help for a specific command")
    @app_commands.describe(command="The specific command to get help for")
    @app_commands.choices(command=[
        app_commands.Choice(name="altcheck", value="altcheck"),
        app_commands.Choice(name="bedwars", value="bedwars"),
        app_commands.Choice(name="announce", value="announce"),
        app_commands.Choice(name="poll", value="poll"),
        app_commands.Choice(name="clear", value="clear"),
        app_commands.Choice(name="setrender", value="setrender"),
        app_commands.Choice(name="suggest", value="suggest"),
        app_commands.Choice(name="requestchange", value="requestchange"),
        app_commands.Choice(name="discord", value="discord"),
        app_commands.Choice(name="ping", value="ping"),
        app_commands.Choice(name="info", value="info")
    ])
    async def help(interaction: discord.Interaction, command: str = None):
        try:
            await interaction.response.defer(ephemeral=True)
            log_command(interaction.user.name, "help", f"Showing help for command: {command if command else 'all'}")
            
            if command:
                # Get the command object
                cmd = bot.tree.get_command(command.lower())
                if not cmd:
                    await interaction.followup.send(f"Command `/{command}` not found.", ephemeral=True)
                    return
                
                # Create embed for specific command
                embed = discord.Embed(
                    title=f"📚 Help: /{cmd.name}",
                    description=cmd.description,
                    color=0x00ff00
                )
                
                # Add parameter descriptions if any
                if hasattr(cmd, 'parameters'):
                    params = []
                    for param in cmd.parameters:
                        param_desc = getattr(param, 'description', 'No description available')
                        params.append(f"`{param.name}` - {param_desc}")
                    if params:
                        embed.add_field(
                            name="Parameters",
                            value="\n".join(params),
                            inline=False
                        )
                
                # Fetch real-time examples for altcheck and bedwars
                if cmd.name in ["altcheck", "bedwars"]:
                    username = "i4w"
                    uuid = "dcc16a1e5fea48f2890ba36bd7a4ae84"
                    
                    if cmd.name == "altcheck":
                        # Fetch altcheck data
                        async with aiohttp.ClientSession() as session:
                            # Fetch Mojang data
                            mojang_response = await session.get(f"https://api.mojang.com/users/profiles/minecraft/{username}")
                            if mojang_response.status == 200:
                                mojang_data = await mojang_response.json()
                                correct_username = mojang_data.get("name")
                                
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
                                
                                # Fetch urchin data
                                urchin_data = await fetch_urchin_data(correct_username, os.environ["URCHIN_KEY"])
                                if urchin_data == "API_DOWN":
                                    type_main = "Urchin API is currently down"
                                elif urchin_data == "API_ERROR":
                                    type_main = "Error fetching Urchin data"
                                elif urchin_data and "tags" in urchin_data and len(urchin_data["tags"]) > 0:
                                    tags = [tag.get("type", "").title() for tag in urchin_data["tags"] if tag.get("type")]
                                    type_main = ", ".join(tags) if tags else "None"
                                else:
                                    type_main = "None"
                                
                                # Fetch stats
                                current_kills, current_deaths = await fetch_bwstats(uuid)
                                current_fkdr = calculate_fkdr(current_kills, current_deaths)
                                if isinstance(current_fkdr, float):
                                    current_fkdr = f"{current_fkdr:.2f}"
                                
                                # Fetch alts
                                polsu_url_alts = f"https://api.polsu.xyz/polsu/bedwars/quickbuy/all?uuid={uuid}"
                                polsu_response_alts = await session.get(polsu_url_alts, headers={"API-Key": os.environ["POLSU_KEY"]})
                                alts = []
                                if polsu_response_alts.status == 200:
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
                                            
                                            # Fetch urchin data for the alt
                                            urchin_data_alt = await fetch_urchin_data(alt_username, os.environ["URCHIN_KEY"])
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
                                
                                # Create example output
                                example_output = f"`/altcheck username:i4w`\nExample Output:\n```\nAlt Check: {correct_username}\nUUID\n{uuid}\nNameMC Profile\nLink\nFKDR\n{current_fkdr}\nUrchin Tags\n{type_main}\nAlts Found\n" + "\n".join(alts) + "\n```"
                                
                                embed.add_field(
                                    name="Usage Example",
                                    value=example_output,
                                    inline=False
                                )
                    
                    elif cmd.name == "bedwars":
                        # Fetch bedwars data
                        stats = await fetch_bwstats(uuid)
                        if stats:
                            # Calculate ratios
                            wlr = calculate_ratio(stats["wins"], stats["losses"])
                            fkdr = calculate_fkdr(stats["final_kills"], stats["final_deaths"])
                            bblr = calculate_ratio(stats["beds_broken"], stats["beds_lost"])
                            kdr = calculate_ratio(stats["kills"], stats["deaths"])
                            
                            # Create example output
                            example_output = f"`/bedwars username:i4w`\nExample Output:\n```\nBedwars Stats: i4w\nDetailed statistics for Bedwars\n\n🏆 Win/Loss\nWins: `{stats['wins']:,}`\nLosses: `{stats['losses']:,}`\nW/L Ratio: `{format_ratio(wlr)}`\n\n⚔️ Final K/D\nFinal Kills: `{stats['final_kills']:,}`\nFinal Deaths: `{stats['final_deaths']:,}`\nFKDR: `{format_ratio(fkdr)}`\n\n🛏️ Bed Stats\nBeds Broken: `{stats['beds_broken']:,}`\nBeds Lost: `{stats['beds_lost']:,}`\nBBLR: `{format_ratio(bblr)}`\n\n⚔️ K/D\nKills: `{stats['kills']:,}`\nDeaths: `{stats['deaths']:,}`\nK/D Ratio: `{format_ratio(kdr)}`\n```"
                            
                            embed.add_field(
                                name="Usage Example",
                                value=example_output,
                                inline=False
                            )
                
                # Add other command examples
                else:
                    examples = {
                        "announce": "`/announce channel:#announcements title:Welcome New Update! message:We've added new features to the bot!`\nExample Output:\n```\n📢 Welcome New Update!\n\nWe've added new features to the bot!\n\nAnnounced by Admin123\n```",
                        "poll": "`/poll question:Favorite Game Mode? option1:Solo option2:Doubles option3:Trios option4:Teams`\nExample Output:\n```\n📊 Poll\nFavorite Game Mode?\n\nOption 1: Solo\nOption 2: Doubles\nOption 3: Trios\nOption 4: Teams\n\nPoll by User123\n\n[Reactions: 1️⃣ 2️⃣ 3️⃣ 4️⃣]\n```",
                        "clear": "`/clear amount:10 channel:#general`\nExample Output:\n```\nCleared 10 messages from #general\n```",
                        "setrender": "`/setrender username:i4w render_type:default`\nExample Output:\n```\nRender type for i4w has been set to default.\n```",
                        "suggest": "`/suggest suggestion:Add a leaderboard feature`\nExample Output:\n```\n✅ Your suggestion has been sent! Thank you!\n\n[In suggestions channel]\nNew Suggestion Received\nSuggestion: Add a leaderboard feature\nFrom: User123 (ID: 123456789)\nLocation: Server Name\n```",
                        "requestchange": "`/requestchange username:i4w render_type:default`\nExample Output:\n```\n✅ Your request for the player model change has been sent! Thank you.\n\n[In renders channel]\nPlayer Model Change Request\nUsername: i4w\nCurrent Render: current\nRequested Render: default\nRequest Sent By: User123 (ID: 123456789)\nLocation: Server Name\n```",
                        "discord": "`/discord`\nExample Output:\n```\nJoin our Discord Server!\nClick the button below to join our Discord server!\n[🔗 Join Server]\n```",
                        "ping": "`/ping`\nExample Output:\n```\n🏓 Pong!\nBot Latency: 50ms\n```",
                        "info": "`/info`\nExample Output:\n```\nℹ️ Bot Information\nBot Name: Alt Checker Beta\nServers: 1\nUptime: 0d 0h 0m 0s\nLatency: 50ms\nCommands: 11\nVersion: 1.0.0\n\nMade with ❤️ by ACM Team\n```"
                    }
                    
                    if cmd.name in examples:
                        embed.add_field(
                            name="Usage Example",
                            value=examples[cmd.name],
                            inline=False
                        )
                
                embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
                
            else:
                # Create embed with command categories
                embed = discord.Embed(
                    title="📚 Available Commands",
                    description="Here are all the available commands:",
                    color=0x00ff00
                )
                
                # Alt Checker Commands
                embed.add_field(
                    name="🔍 Alt Checker",
                    value="`/altcheck` - Check for alts on a Minecraft account\n"
                          "`/bedwars` - View Bedwars statistics",
                    inline=False
                )
                
                # Settings Commands
                embed.add_field(
                    name="⚙️ Settings",
                    value="`/setrender` - Set your preferred skin render type\n"
                          "`/requestchange` - Request changes to your player model rendering",
                    inline=False
                )
                
                # Community Commands
                embed.add_field(
                    name="👥 Community",
                    value="`/suggest` - Suggest improvements for the bot\n"
                          "`/discord` - Get the Discord server invite",
                    inline=False
                )
                
                # Server Commands
                embed.add_field(
                    name="🖥️ Server",
                    value="`/announce` - Make an announcement (Admin only)\n"
                          "`/poll` - Create a poll\n"
                          "`/clear` - Clear messages (Requires manage messages)",
                    inline=False
                )
                
                # Utility Commands
                embed.add_field(
                    name="🛠️ Utility",
                    value="`/ping` - Check the bot's latency\n"
                          "`/help` - Show this help message\n"
                          "`/info` - View bot information",
                    inline=False
                )
                
                embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            log_command(interaction.user.name, "help", f"Successfully displayed help for {'command' if command else 'all commands'}")
            
        except Exception as e:
            log_error("Command Error", interaction.user.name, "help", str(e))
            await interaction.followup.send("An error occurred while showing the help message.", ephemeral=True)

    @bot.tree.command(name="info", description="View information about the bot")
    async def info(interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            log_command(interaction.user.name, "info", "Showing bot information")
            
            # Calculate uptime
            uptime = datetime.now() - bot.start_time
            days = uptime.days
            hours = uptime.seconds // 3600
            minutes = (uptime.seconds % 3600) // 60
            seconds = uptime.seconds % 60
            
            # Create embed
            embed = discord.Embed(
                title="ℹ️ Bot Information",
                color=0x00ff00
            )
            
            embed.add_field(
                name="Bot Name",
                value=bot.user.name,
                inline=True
            )
            
            embed.add_field(
                name="Servers",
                value=str(len(bot.guilds)),
                inline=True
            )
            
            embed.add_field(
                name="Uptime",
                value=f"{days}d {hours}h {minutes}m {seconds}s",
                inline=True
            )
            
            embed.add_field(
                name="Latency",
                value=f"{round(bot.latency * 1000)}ms",
                inline=True
            )
            
            embed.add_field(
                name="Commands",
                value=str(len(bot.tree.get_commands())),
                inline=True
            )
            
            embed.add_field(
                name="Version",
                value="1.0.0",
                inline=True
            )
            
            embed.set_footer(text="Made with ❤️ by ACM Team")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            log_command(interaction.user.name, "info", "Successfully displayed bot information")
            
        except Exception as e:
            log_error("Command Error", interaction.user.name, "info", str(e))
            await interaction.followup.send("An error occurred while showing bot information.", ephemeral=True) 