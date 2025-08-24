import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestCog(commands.Cog):
    """Test cog để demo upload functionality"""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="test", description="Test command từ cog được upload")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))
    async def test_command(self, interaction: discord.Interaction):
        """Test command đơn giản"""
        embed = discord.Embed(
            title="🧪 Test Command",
            description="Command này được tạo từ file upload!",
            color=discord.Color.blue()
        )
        embed.add_field(name="User", value=interaction.user.mention, inline=True)
        embed.add_field(name="Guild", value=interaction.guild.name, inline=True)
        embed.set_footer(text="Test cog uploaded successfully!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="info", description="Thông tin về test cog")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))
    async def info_command(self, interaction: discord.Interaction):
        """Info command"""
        await interaction.response.send_message(
            "📋 **Test Cog Info**\n"
            "• Cog này được tạo để test upload functionality\n"
            "• Chứa 2 commands: `/test` và `/info`\n"
            "• Sử dụng guild-specific commands\n"
            "✅ Upload cog thành công!"
        )

async def setup(bot):
    """Setup function bắt buộc cho mọi cog"""
    await bot.add_cog(TestCog(bot))
    print("✅ TestCog đã được load thành công!")
