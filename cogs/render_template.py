import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from io import StringIO
from utils.command_helper import get_command_name

# Load environment variables từ .env (chỉ dùng khi không có trong system env)
load_dotenv()

# Ưu tiên lấy từ system environment variables
GUILD_ID = int(os.environ.get('GUILD_ID') or os.getenv('GUILD_ID'))


class Template(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        # Tạo command với tên động
        self.get_template_command = app_commands.Command(
            name=get_command_name("get_template"),
            description="Slash command: lấy template viết cogs",
            callback=self.get_template_callback
        )
        self.bot.tree.add_command(self.get_template_command, guild=discord.Object(id=GUILD_ID))
    
    async def cog_unload(self):
        self.bot.tree.remove_command(self.get_template_command.name, guild=discord.Object(id=GUILD_ID))
    
    async def get_template_callback(self, interaction: discord.Interaction):
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "template.py")
        with open(template_path, "r", encoding="utf-8") as f:
            template_code = f.read()
        file = discord.File(fp=StringIO(template_code), filename="template.py")
        await interaction.response.send_message(
            content="Đây là file template.py cho cogs:",
            file=file,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Template(bot))
