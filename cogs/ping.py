import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Testing(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Slash command: kiểm tra ping")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))  # Restrict to specific guild
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: **{latency}ms**",
            color=discord.Color.green()
        )
        embed.add_field(name="Bot Status", value="✅ Online", inline=True)
        embed.add_field(name="Guild", value=interaction.guild.name, inline=True)
        embed.set_footer(text="Slash command từ cog")
        
        await interaction.response.send_message(embed=embed)



async def setup(bot):
    await bot.add_cog(Testing(bot))
