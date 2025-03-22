import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from utils import log_command, log_error, log_info

def setup(bot):
    @bot.tree.command(name="discord", description="Get a link to join our Discord server!")
    async def discord_embed(interaction: discord.Interaction):
        try:
            log_command(interaction.user.name, "discord", "Sending Discord invite")
            
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
            await interaction.response.send_message(embed=embed, view=view, ephemeral=False)
            log_command(interaction.user.name, "discord", "Successfully sent Discord invite")
            
        except Exception as e:
            log_error("Command Error", interaction.user.name, "discord", str(e))
            await interaction.response.send_message("An error occurred while sending the Discord invite.", ephemeral=True) 