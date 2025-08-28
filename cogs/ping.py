import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
import pymongo
from all_def.testing import generation
from all_def.mongodb import get_user, add_user_data, get_user_collection, get_user_data
import time
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

    @app_commands.command(name="testing", description="Slash command: kiểm tra testing")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))  # Restrict to specific guild
    async def testing(self, interaction: discord.Interaction):
        result = generation()
        await interaction.response.send_message(result)

    @app_commands.command(name="set_testing_data", description="Slash command: set testing data")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))  # Restrict to specific guild
    async def set_testing_data(self, interaction: discord.Interaction, value: int):
        await interaction.response.defer()
        timenow = time.time()
        # add the testing_point +=1 when user use this command
        user_id = interaction.user.id
        add_user_data(user_id, "testing_data", 1)
        used = get_user_data(user_id, "testing_data")

        embed = discord.Embed(
            title="✅ Thành công",
            description=f"Đã cập nhật testing_data thành: {value}",
            color=discord.Color.green()
        )
        embed.add_field(name="Số lần sử dụng lệnh này", value=used[1], inline=True)
        time_used = time.time() - timenow
        embed.add_field(name="Thời gian thực hiện", value=f"{time_used * 1000:.2f} ms", inline=True)
        # reply the defer
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Testing(bot))
