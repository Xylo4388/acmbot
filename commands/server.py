import discord
from discord.ext import commands
from discord import app_commands
from utils import log_command, log_error, log_info

def setup(bot):
    @bot.tree.command(name="announce", description="Make an announcement")
    @app_commands.describe(
        channel="The channel to announce in",
        title="The title of the announcement",
        message="The announcement message"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def announce(interaction: discord.Interaction, channel: discord.TextChannel, title: str, message: str):
        try:
            await interaction.response.defer(ephemeral=True)
            log_command(interaction.user.name, "announce", f"Making announcement in {channel.name}")

            # Create embed
            embed = discord.Embed(
                title=f"📢 {title}",
                description=message,
                color=discord.Color.blue()
            )

            # Add footer
            embed.set_footer(text=f"Announced by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

            # Send announcement
            await channel.send(embed=embed)
            log_command(interaction.user.name, "announce", f"Successfully sent announcement to {channel.name}")
            await interaction.followup.send(f"Announcement sent to {channel.mention}", ephemeral=True)

        except Exception as e:
            log_error("Command Error", interaction.user.name, "announce", str(e))
            await interaction.followup.send("An error occurred while making the announcement.", ephemeral=True)

    @bot.tree.command(name="poll", description="Create a poll")
    @app_commands.describe(
        question="The poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)"
    )
    async def poll(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
        try:
            await interaction.response.defer(ephemeral=True)
            log_command(interaction.user.name, "poll", f"Creating poll: {question}")

            # Create embed
            embed = discord.Embed(
                title="📊 Poll",
                description=question,
                color=discord.Color.blue()
            )

            # Add options
            embed.add_field(name="Option 1", value=option1, inline=False)
            embed.add_field(name="Option 2", value=option2, inline=False)
            
            if option3:
                embed.add_field(name="Option 3", value=option3, inline=False)
            if option4:
                embed.add_field(name="Option 4", value=option4, inline=False)

            # Add footer
            embed.set_footer(text=f"Poll by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

            # Send poll
            poll_message = await interaction.channel.send(embed=embed)
            await poll_message.add_reaction("1️⃣")
            await poll_message.add_reaction("2️⃣")
            if option3:
                await poll_message.add_reaction("3️⃣")
            if option4:
                await poll_message.add_reaction("4️⃣")
                
            log_command(interaction.user.name, "poll", f"Successfully created poll in {interaction.channel.name}")
            await interaction.followup.send("Poll created!", ephemeral=True)

        except Exception as e:
            log_error("Command Error", interaction.user.name, "poll", str(e))
            await interaction.followup.send("An error occurred while creating the poll.", ephemeral=True)

    @bot.tree.command(name="clear", description="Clear messages in a channel")
    @app_commands.describe(
        amount="Number of messages to clear (1-100)",
        channel="The channel to clear messages from (defaults to current channel)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(interaction: discord.Interaction, amount: int, channel: discord.TextChannel = None):
        try:
            await interaction.response.defer(ephemeral=True)
            log_command(interaction.user.name, "clear", f"Clearing {amount} messages from {channel.name if channel else interaction.channel.name}")

            # Validate amount
            if amount < 1 or amount > 100:
                log_error("Invalid Amount", interaction.user.name, "clear", f"Invalid amount specified: {amount}")
                await interaction.followup.send("Please specify a number between 1 and 100.", ephemeral=True)
                return

            # Use specified channel or current channel
            target_channel = channel or interaction.channel

            # Delete messages
            deleted = await target_channel.purge(limit=amount)
            log_command(interaction.user.name, "clear", f"Successfully cleared {len(deleted)} messages from {target_channel.name}")
            await interaction.followup.send(f"Cleared {len(deleted)} messages from {target_channel.mention}", ephemeral=True)

        except Exception as e:
            log_error("Command Error", interaction.user.name, "clear", str(e))
            await interaction.followup.send("An error occurred while clearing messages.", ephemeral=True) 