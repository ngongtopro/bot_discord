import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.command_helper import get_command_name

# Load environment variables
load_dotenv()

# Ưu tiên lấy từ system environment variables
GUILD_ID = int(os.environ.get('GUILD_ID') or os.getenv('GUILD_ID'))


class Template(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
        # ============================================
        # CÁCH 1: Command không có parameters
        # ============================================
        self.template_command = app_commands.Command(
            name=get_command_name("template"),
            description="Slash command: template",
            callback=self.template_callback
        )
        self.bot.tree.add_command(self.template_command, guild=discord.Object(id=GUILD_ID))
        
        # ============================================
        # CÁCH 2: Command có parameters - Sử dụng decorator
        # ============================================
        @app_commands.command(name=get_command_name("greet"), description="Chào người dùng")
        @app_commands.describe(name="Tên người cần chào", message="Tin nhắn tùy chọn")
        async def greet_cmd(interaction: discord.Interaction, name: str, message: str = "Hello"):
            await self.greet_callback(interaction, name, message)
        
        self.greet_command = greet_cmd
        self.bot.tree.add_command(greet_cmd, guild=discord.Object(id=GUILD_ID))
    
    async def cog_unload(self):
        # Xóa commands khi unload cog
        guild_obj = discord.Object(id=GUILD_ID)
        self.bot.tree.remove_command(self.template_command.name, guild=guild_obj)
        self.bot.tree.remove_command(self.greet_command.name, guild=guild_obj)
    
    async def template_callback(self, interaction: discord.Interaction):
        """Callback cho template command (không có parameters)"""
        latency = round(self.bot.latency * 1000)
        stage_indicator = "🔧 DEV" if self.bot.is_dev else "🚀 PRODUCTION"
        
        embed = discord.Embed(
            title="🏓 Template!",
            description=f"Latency: **{latency}ms**",
            color=discord.Color.blue() if self.bot.is_dev else discord.Color.green()
        )
        embed.add_field(name="Bot Status", value="✅ Online", inline=True)
        embed.add_field(name="Guild", value=interaction.guild.name, inline=True)
        embed.add_field(name="Stage", value=stage_indicator, inline=True)
        embed.set_footer(text=f"Slash command từ cog - {self.bot.stage}")
        
        await interaction.response.send_message(embed=embed)
    
    async def greet_callback(self, interaction: discord.Interaction, name: str, message: str):
        """Callback cho greet command (có parameters)"""
        stage_indicator = "🔧 DEV" if self.bot.is_dev else "🚀 PRODUCTION"
        
        embed = discord.Embed(
            title=f"{message}, {name}! 👋",
            description=f"Chào mừng bạn đến với bot!",
            color=discord.Color.blue() if self.bot.is_dev else discord.Color.green()
        )
        embed.add_field(name="Stage", value=stage_indicator, inline=True)
        embed.set_footer(text=f"Command với parameters - {self.bot.stage}")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Template(bot))
