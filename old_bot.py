import discord
from discord import app_commands
from dotenv import load_dotenv
import os
load_dotenv()


TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
APPLICATION_ID = int(os.getenv("APPLICATION_ID"))

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # Sync slash commands với server
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)

client = MyClient()

# Slash command: /hello
@client.tree.command(name="hello", description="Chào bot 👋")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Xin chào, {interaction.user.mention}!")

# Slash command: /multi a b
@client.tree.command(name="multi", description="Nhân 2 số")
@app_commands.describe(a="Số thứ nhất", b="Số thứ hai")
async def add(interaction: discord.Interaction, a: int, b: int):
    await interaction.response.send_message(f"{a} * {b} = {a*b}")

async def load_extensions():
    for ext in ["cogs.slash"]:
        try:
            await client.load_extension(ext)
            print(f"✅ Loaded {ext}")
        except Exception as e:
            print(f"❌ Failed to load {ext}: {e}")


client.run(TOKEN)
