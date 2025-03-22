import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from dotenv import load_dotenv
from utils import log_command, log_error, log_info

load_dotenv()

# Load render channel from environment variable
RENDER_CHANNEL = os.environ["RENDERS"]

def load_render_type_data():
    try:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(current_dir, "data")
        with open(os.path.join(data_dir, "rendertype.json"), "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def setup(bot):
    @bot.tree.command(
        name="requestchange", 
        description="Request a change for your player model rendering"
    )
    @app_commands.describe(
        username="Minecraft username", 
        render_type="The render type you want to change to"
    )
    @app_commands.choices(render_type=[
        app_commands.Choice(name="Default", value="default"),
        app_commands.Choice(name="Marching", value="marching"),
        app_commands.Choice(name="Walking", value="walking"),
        app_commands.Choice(name="Crouching", value="crouching"),
        app_commands.Choice(name="Crossed", value="crossed"),
        app_commands.Choice(name="Criss Cross", value="criss_cross"),
        app_commands.Choice(name="Ultimate", value="ultimate"),
        app_commands.Choice(name="Isometric", value="isometric"),
        app_commands.Choice(name="Head", value="head"),
        app_commands.Choice(name="Custom", value="custom"),
        app_commands.Choice(name="Cheering", value="cheering"),
        app_commands.Choice(name="Relaxing", value="relaxing"),
        app_commands.Choice(name="Trudging", value="trudging"),
        app_commands.Choice(name="Cowering", value="cowering"),
        app_commands.Choice(name="Pointing", value="pointing"),
        app_commands.Choice(name="Lunging", value="lunging"),
        app_commands.Choice(name="Dungeons", value="dungeons"),
        app_commands.Choice(name="Facepalm", value="facepalm"),
        app_commands.Choice(name="Sleeping", value="sleeping"),
        app_commands.Choice(name="Dead", value="dead"),
        app_commands.Choice(name="Archer", value="archer"),
        app_commands.Choice(name="Kicking", value="kicking"),
        app_commands.Choice(name="Mojavatar", value="mojavatar"),
        app_commands.Choice(name="High Ground", value="high_ground"),
        app_commands.Choice(name="Clown", value="clown")
    ])
    async def request_change(interaction: discord.Interaction, username: str, render_type: str):
        try:
            log_command(interaction.user.name, "requestchange", f"Requesting render change for {username} to {render_type}")
            
            valid_render_types = [
                "default", "marching", "walking", "crouching", "crossed", "criss_cross", "ultimate", "isometric",
                "head", "custom", "cheering", "relaxing", "trudging", "cowering", "pointing", "lunging", "dungeons",
                "facepalm", "sleeping", "dead", "archer", "kicking", "mojavatar", "reading", "high_ground", "clown"
            ]
            if render_type not in valid_render_types:
                log_error("Invalid Render Type", interaction.user.name, "requestchange", f"Invalid render type: {render_type}")
                await interaction.response.send_message(f"❌ Invalid render type. Please choose a valid type from [Lunar Eclipse Docs](<https://docs.lunareclipse.studio/>).", ephemeral=True)
                return

            # Load render type data
            render_data = load_render_type_data()

            # Get the current render type (defaults to "default" if not found)
            current_render = render_data.get(username, "default")
            log_info("Current Render", interaction.user.name, "requestchange", f"Current render for {username}: {current_render}")

            # Create an embed for the request change
            embed = discord.Embed(
                title="Player Model Change Request",
                description=f"**Username:** {username}\n**Current Render:** {current_render}\n**Requested Render:** {render_type}",
                color=discord.Color.green()
            )
            embed.add_field(name="Request Sent By", value=f"{interaction.user} (ID: {interaction.user.id})", inline=False)
            embed.add_field(name="Location", value=f"{interaction.guild.name}" if interaction.guild else "User DMs", inline=False)
            embed.set_footer(text=f"Requested by {interaction.user.name}")

            # Send the embed to the render channel
            render_channel = bot.get_channel(int(RENDER_CHANNEL))
            
            if render_channel is None:
                log_error("Channel Not Found", interaction.user.name, "requestchange", f"Render channel {RENDER_CHANNEL} not found")
                await interaction.response.send_message(
                    "❌ Error: The render channel could not be found. Please contact an administrator.",
                    ephemeral=True
                )
                return

            try:
                await render_channel.send(embed=embed)
                log_command(interaction.user.name, "requestchange", f"Successfully sent render change request for {username}")
                # Notify the user that the suggestion has been sent
                await interaction.response.send_message(
                    "✅ Your request for the player model change has been sent! Thank you.",
                    ephemeral=True
                )
            except discord.Forbidden:
                log_error("Permission Error", interaction.user.name, "requestchange", "Bot lacks permission to send messages in render channel")
                await interaction.response.send_message(
                    "❌ Error: The bot doesn't have permission to send messages in the render channel. Please contact an administrator.",
                    ephemeral=True
                )
            except Exception as e:
                log_error("Send Error", interaction.user.name, "requestchange", str(e))
                await interaction.response.send_message(
                    "❌ An error occurred while sending your request. Please try again later.",
                    ephemeral=True
                )
        except Exception as e:
            log_error("Command Error", interaction.user.name, "requestchange", str(e))
            await interaction.response.send_message(
                "❌ An unexpected error occurred. Please try again later.",
                ephemeral=True
            ) 