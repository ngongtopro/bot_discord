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
        
        # Tạo command với tên động dựa trên stage (dev/production)
        # Command sẽ tự động thêm prefix "dev" nếu STAGE=dev trong .env
        self.template_command = app_commands.Command(
            name=get_command_name("template"),  # Sẽ là "devtemplate" hoặc "template"
            description="Slash command: template",
            callback=self.template_callback
        )
        
        # Thêm command vào tree với guild restriction
        self.bot.tree.add_command(self.template_command, guild=discord.Object(id=GUILD_ID))
    
    async def cog_unload(self):
        # Xóa command khi unload cog
        self.bot.tree.remove_command(self.template_command.name, guild=discord.Object(id=GUILD_ID))
    
    async def template_callback(self, interaction: discord.Interaction):
        """Callback cho template command"""
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

async def setup(bot):
    await bot.add_cog(Template(bot))
