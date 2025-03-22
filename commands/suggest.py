import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
from utils import log_command, log_error, log_info

load_dotenv()

# Load suggestion channel from environment variable
SUGGESTION_CHANNEL = os.environ["SUGGESTIONS"]

def setup(bot):
    @bot.tree.command(name="suggest", description="Send a suggestion to the Admins.")
    @app_commands.describe(suggestion="Your suggestion to send")
    async def suggest(interaction: discord.Interaction, suggestion: str):
        try:
            log_command(interaction.user.name, "suggest", "Sending new suggestion")
            
            # Fetch the SUGGESTION_CHANNEL dynamically
            suggestion_channel = bot.get_channel(int(SUGGESTION_CHANNEL))
            if not suggestion_channel:
                log_error("Channel Not Found", interaction.user.name, "suggest", f"Suggestion channel {SUGGESTION_CHANNEL} not found")
                await interaction.response.send_message("❌ Suggestion channel not found. Please contact the administrator.", ephemeral=True)
                return

            # Create an embed for the suggestion
            embed = discord.Embed(
                title="New Suggestion Received",
                description="",
                color=discord.Color.blue()
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
            log_command(interaction.user.name, "suggest", f"Successfully sent suggestion from {interaction.user}")

            # Notify the user that their suggestion has been received
            await interaction.response.send_message("✅ Your suggestion has been sent! Thank you!", ephemeral=True)

        except discord.Forbidden:
            log_error("Permission Error", interaction.user.name, "suggest", "Bot lacks permission to send messages in suggestion channel")
            await interaction.response.send_message(
                "❌ I don't have permission to send messages in the suggestion channel.",
                ephemeral=True,
            )
        except Exception as e:
            log_error("Command Error", interaction.user.name, "suggest", str(e))
            await interaction.response.send_message("❌ An error occurred while sending your suggestion.", ephemeral=True) 