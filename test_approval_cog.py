import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TestApprovalCog(commands.Cog):
    """Test cog để demo hệ thống approval"""
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="test_approval", description="Test command từ approval system")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))
    async def test_approval(self, interaction: discord.Interaction):
        """Test approval command"""
        embed = discord.Embed(
            title="🧪 Test Approval System",
            description="Command này đã được duyệt bởi owner!",
            color=discord.Color.purple()
        )
        embed.add_field(name="User", value=interaction.user.mention, inline=True)
        embed.add_field(name="Guild", value=interaction.guild.name, inline=True)
        embed.add_field(name="System", value="Approval System", inline=True)
        embed.set_footer(text="✅ Approved by owner!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="approval_info", description="Thông tin về approval system")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))
    async def approval_info(self, interaction: discord.Interaction):
        """Info về approval system"""
        info_text = (
            "📋 **Approval System Info**\n\n"
            "• User thường: File upload → waiting_cogs\n"
            "• Owner: File upload → trực tiếp load\n"
            "• Owner có thể check pending với /check_pending\n"
            "• Owner có thể approve với /approve_cog <index>\n"
            "• User sẽ được thông báo khi cog được duyệt\n\n"
            "✅ **Hệ thống hoạt động tốt!**"
        )
        
        await interaction.response.send_message(info_text)

async def setup(bot):
    """Setup function bắt buộc cho mọi cog"""
    await bot.add_cog(TestApprovalCog(bot))
    print("✅ TestApprovalCog đã được load thành công!")
