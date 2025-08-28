import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv
import logging
from pymongo import MongoClient
import time


# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)

class DiscordBot(commands.Bot):
    def __init__(self):
        # Bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        
        # Initialize bot
        super().__init__(
            command_prefix='!',
            intents=intents,
            application_id=int(os.getenv('APPLICATION_ID'))
        )
        
        self.guild_id = int(os.getenv('GUILD_ID'))
        
        # MongoDB connection
        mongo_uri = os.getenv('MONGODB_URI')
        if mongo_uri:
            self.mongo_client = MongoClient(mongo_uri)
            self.mongodb = self.mongo_client.get_database('DiscordBot')
            logging.info('Connected to MongoDB!')
        else:
            self.mongo_client = None
            self.mongodb = None
            logging.warning('No MongoDB URI found in environment!')
        
        self._commands_added = False

    def userdata(self):
        return self.userdata_database
    def get_userdata(self,user_id, variable):
        try:
            cursor = self.userdata().cursor()
            cursor.execute("SELECT value FROM userdata WHERE user_id = ? AND variable = ?", (user_id, variable))
            result = cursor.fetchone()
            # return [user name, variable, value,status]
            return [self.user.name, variable, result[0], "success"] if result else [self.user.name, variable, None, "error"]
        except Exception as e:
            logging.error(f"Lỗi khi get userdata cho {self.user.name} với {variable}: {e}")
            return [self.user.name, variable, None, "error"]

    def set_userdata(self,user_id, variable, value):
        try:
            cursor = self.userdata().cursor()
            cursor.execute("INSERT INTO userdata (user_id, variable, value) VALUES (?, ?, ?) ON CONFLICT(user_id, variable) DO UPDATE SET value = ?", (user_id, variable, value, value))
            self.userdata().commit()
            #  return [self.user.name, variable, value, "success"]
            return [self.user.name, variable, value, "success"]
        except Exception as e:
            logging.error(f"Lỗi khi set userdata cho {self.user.name} với {variable}: {e}")
            return [self.user.name, variable, value, "error"]

    async def setup_hook(self):
        """Called when the bot is starting up"""
        print(f'{self.user} đã đăng nhập!')
        
        # Load cogs
        await self.load_cogs()
        

    
    async def load_cogs(self):
        """Load all cogs from cogs folder"""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Đã load cog: {filename}')
                except Exception as e:
                    print(f'❌ Lỗi load cog {filename}: {e}')
    
    async def on_ready(self):
        """Called when bot is ready"""
        print(f'Bot {self.user} đã sẵn sàng!')
        print(f'Bot ID: {self.user.id}')
        print(f'Guild ID: {self.guild_id}')
        
        # Change bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="slash commands!"
            )
        )
        
        # Sync slash commands to guild for faster testing (chỉ sync một lần)
        if not self._commands_added:
            try:
                # Clear global commands trước (để tránh conflict)
                self.tree.clear_commands(guild=None)
                await self.tree.sync()  # Sync empty global commands
                print("Đã xóa global commands")
                
                # Debug: kiểm tra số lượng commands trong tree
                guild_obj = discord.Object(id=self.guild_id)
                all_commands = self.tree.get_commands(guild=guild_obj)
                global_commands = self.tree.get_commands()
                
                print(f"Debug: {len(all_commands)} commands trong guild tree")
                print(f"Debug: {len(global_commands)} commands trong global tree")
                
                # List commands trong tree
                for cmd in all_commands:
                    print(f"Guild command trong tree: {cmd.name}")
                for cmd in global_commands:
                    print(f"Global command trong tree: {cmd.name}")
                
                # Sync guild commands
                synced_guild = await self.tree.sync(guild=guild_obj)
                
                print(f"Đã sync {len(synced_guild)} guild commands tới guild {self.guild_id}")
                
                # List all guild commands
                for cmd in synced_guild:
                    print(f"  - /{cmd.name}: {cmd.description}")
                    
                self._commands_added = True
            except Exception as e:
                print(f"Lỗi khi sync guild commands: {e}")
    
    # Built-in slash command callbacks

    
    async def _botinfo_callback(self, interaction: discord.Interaction):
        """Bot information slash command"""
        embed = discord.Embed(
            title="🤖 Thông tin Bot",
            color=discord.Color.blue()
        )
        embed.add_field(name="Bot Name", value=self.user.name, inline=True)
        embed.add_field(name="Bot ID", value=self.user.id, inline=True)
        embed.add_field(name="Guild Count", value=len(self.guilds), inline=True)
        embed.add_field(name="User Count", value=len(self.users), inline=True)
        embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
        embed.set_thumbnail(url=self.user.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)
    

    



async def main():
    """Main function to run the bot"""
    # Check environment variables
    token = os.getenv('TOKEN')
    if not token:
        print("❌ Không tìm thấy TOKEN trong file .env!")
        return
    
    application_id = os.getenv('APPLICATION_ID')
    if not application_id:
        print("❌ Không tìm thấy APPLICATION_ID trong file .env!")
        return
        
    guild_id = os.getenv('GUILD_ID')
    if not guild_id:
        print("❌ Không tìm thấy GUILD_ID trong file .env!")
        return
    
    # Create and run bot
    bot = DiscordBot()
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        print("\n🛑 Bot đã được dừng bởi người dùng")
    except Exception as e:
        print(f"❌ Lỗi khi chạy bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
