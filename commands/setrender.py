import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from dotenv import load_dotenv
from utils import log_command, log_error, log_info

load_dotenv()

# Load admin IDs from environment variable
ADMIN_IDS = [int(id) for id in os.environ["ADMIN_IDS"].split(",")]

def load_render_type_data():
    try:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(current_dir, "data")
        with open(os.path.join(data_dir, "rendertype.json"), "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_render_type_data(data):
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(current_dir, "data")
    with open(os.path.join(data_dir, "rendertype.json"), "w") as file:
        json.dump(data, file, indent=4)

def setup(bot):
    @bot.tree.command(name="setrender", description="Set render type for a Minecraft username")
    @app_commands.describe(username="The Minecraft username", render_type="The render type to set")
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
    async def set_render_type(interaction: discord.Interaction, username: str, render_type: str):
        try:
            log_command(interaction.user.name, "setrender", f"Attempting to set render type for {username} to {render_type}")
            
            # Check if the user's ID is in the list of admin IDs
            if interaction.user.id not in ADMIN_IDS:
                log_error("Unauthorized Access", interaction.user.name, "setrender", "User is not an admin")
                await interaction.response.send_message("You are not authorized to use this command.", ephemeral=False)
                return

            # Load existing render type data
            render_data = load_render_type_data()
            current_render = render_data.get(username, "default")
            log_info("Current Render", interaction.user.name, "setrender", f"Current render for {username}: {current_render}")

            # Update the render type for the specified username
            render_data[username] = render_type

            # Save the updated data back to the JSON file
            save_render_type_data(render_data)
            log_command(interaction.user.name, "setrender", f"Successfully updated render type for {username} from {current_render} to {render_type}")

            await interaction.response.send_message(f"Render type for {username} has been set to {render_type}.", ephemeral=False)

        except Exception as e:
            log_error("Command Error", interaction.user.name, "setrender", str(e))
            await interaction.response.send_message("An error occurred while updating the render type.", ephemeral=False) 