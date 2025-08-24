import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SlashCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="example", description="Slash command: example command")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))  # Restrict to specific guild
    async def example(self, interaction: discord.Interaction):
        # Write your command logic here
        return None

async def setup(bot):
    await bot.add_cog(SlashCog(bot))
