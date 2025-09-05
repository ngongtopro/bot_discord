import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv
from io import StringIO
# Load environment variables
load_dotenv()


class Template(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="get_template", description="Slash command: lấy template viết cogs")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))  # Restrict to specific guild
    async def get_template(self, interaction: discord.Interaction):
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
