import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from utils.command_helper import get_command_name

# Load environment variables từ .env (chỉ dùng khi không có trong system env)
load_dotenv()

# Ưu tiên lấy từ system environment variables
GUILD_ID = int(os.environ.get('GUILD_ID') or os.getenv('GUILD_ID'))


class Testing(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        # Tạo command với tên động
        self.ping_command = app_commands.Command(
            name=get_command_name("ping"),
            description="Slash command: kiểm tra ping",
            callback=self.ping_callback
        )
        # Thêm command vào tree với guild restriction
        self.bot.tree.add_command(self.ping_command, guild=discord.Object(id=GUILD_ID))
    
    async def cog_unload(self):
        # Xóa command khi unload cog
        self.bot.tree.remove_command(self.ping_command.name, guild=discord.Object(id=GUILD_ID))
    
    async def ping_callback(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        stage_indicator = "🔧 DEV" if self.bot.is_dev else "🚀 PRODUCTION"
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: **{latency}ms**",
            color=discord.Color.blue() if self.bot.is_dev else discord.Color.green()
        )
        embed.add_field(name="Bot Status", value="✅ Online", inline=True)
        embed.add_field(name="Guild", value=interaction.guild.name, inline=True)
        embed.add_field(name="Stage", value=stage_indicator, inline=True)
        embed.set_footer(text=f"Slash command từ cog - {self.bot.stage}")
        
        await interaction.response.send_message(embed=embed)



async def setup(bot):
    await bot.add_cog(Testing(bot))
