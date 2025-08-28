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
        intents.members = True
        
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

    async def check_mongodb_connection(self):
        """Kiểm tra kết nối MongoDB trước khi load cogs"""
        try:
            from pymongo import MongoClient
            import os
            from dotenv import load_dotenv
            
            # Load environment variables
            load_dotenv()
            
            # MongoDB Configuration
            MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/')
            
            print("🔍 Đang kiểm tra kết nối MongoDB...")
            
            # Test connection với timeout ngắn
            client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
            
            # Thử ping MongoDB server
            client.admin.command('ping')
            client.close()
            
            print("✅ MongoDB kết nối thành công!")
            return True
            
        except Exception as e:
            error_msg = str(e)
            print("❌ Lỗi kết nối MongoDB:")
            
            if 'ServerSelectionTimeoutError' in error_msg or 'Could not reach any servers' in error_msg:
                print("   📋 Hướng dẫn khắc phục:")
                print("   1. Kiểm tra Docker MongoDB container:")
                print("      docker ps -a")
                print("   2. Khởi động MongoDB nếu chưa chạy:")
                print("      docker compose -f docker_compose.yml up -d")
                print("   3. Khởi tạo Replica Set:")
                print("      docker exec -it mongodb mongosh --eval \"rs.initiate()\"")
                print("   4. Kiểm tra connection string trong .env:")
                print("      MONGODB_URL=mongodb://localhost:27017/?replicaSet=rs0")
                print("   5. Đợi 30-60 giây để MongoDB replica set hoàn tất khởi tạo")
            else:
                print(f"   Chi tiết lỗi: {error_msg}")
            
            return False
        
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
        
        # Kiểm tra MongoDB connection trước khi load cogs
        mongodb_ok = await self.check_mongodb_connection()
        if not mongodb_ok:
            print("⚠️  MongoDB không khả dụng - một số cogs có thể không load được!")
            print("   Bot vẫn sẽ khởi động với các chức năng cơ bản...")
        
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
                    # Check for MongoDB connection errors
                    error_msg = str(e)
                    if 'ServerSelectionTimeoutError' in error_msg or 'Could not reach any servers' in error_msg:
                        print(f'❌ Lỗi kết nối MongoDB khi load cog {filename}:')
                        print(f'   MongoDB server không thể kết nối!')
                        print(f'   Hãy kiểm tra:')
                        print(f'   - Docker MongoDB container đã chạy chưa: docker ps')
                        print(f'   - Replica set đã được khởi tạo chưa: docker exec -it mongodb mongosh --eval "rs.initiate()"')
                        print(f'   - Connection string đúng chưa: mongodb://localhost:27017/?replicaSet=rs0')
                    else:
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
        error_msg = str(e)
        
        # Check for MongoDB related errors
        if ('ServerSelectionTimeoutError' in error_msg or 
            'Could not reach any servers' in error_msg or
            'CommandInvokeError' in error_msg):
            print(f"❌ Lỗi MongoDB khi chạy bot:")
            print(f"   {error_msg}")
            print(f"   📋 Hướng dẫn khắc phục:")
            print(f"   1. Đảm bảo MongoDB container đang chạy:")
            print(f"      docker ps | grep mongodb")
            print(f"   2. Khởi động lại MongoDB:")
            print(f"      docker compose -f docker_compose.yml down && docker compose -f docker_compose.yml up -d")
            print(f"   3. Khởi tạo replica set:")
            print(f"      docker exec -it mongodb mongosh --eval \"rs.initiate()\"")
            print(f"   4. Đợi 30-60 giây rồi khởi động bot lại")
        else:
            print(f"❌ Lỗi khi chạy bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
