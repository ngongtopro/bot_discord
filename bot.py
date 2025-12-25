import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import logging


# Load environment variables từ .env (chỉ dùng khi không có trong system env)
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
        
        # Ưu tiên lấy từ system environment (systemd) trước
        application_id = int(os.environ.get('APPLICATION_ID') or os.getenv('APPLICATION_ID'))
        guild_id = int(os.environ.get('GUILD_ID') or os.getenv('GUILD_ID'))
        
        # Initialize bot
        super().__init__(
            command_prefix='!',
            intents=intents,
            application_id=application_id
        )
        
        self.guild_id = guild_id
        
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
        logging.info(f'{self.user} đã đăng nhập!')
        await self.load_cogs()
        
    async def load_cogs(self):
        """Load all cogs from cogs folder"""
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logging.info(f'✅ Đã load cog: {filename}')
                except Exception as e:
                    logging.error(f'❌ Lỗi load cog {filename}: {e}')

    async def on_ready(self):
        """Called when bot is ready"""
        logging.info(f'Bot {self.user} đã sẵn sàng!')
        logging.info(f'Bot ID: {self.user.id}')
        logging.info(f'Guild ID: {self.guild_id}')
        
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
                logging.info("Đã xóa global commands")
                
                # Debug: kiểm tra số lượng commands trong tree
                guild_obj = discord.Object(id=self.guild_id)
                all_commands = self.tree.get_commands(guild=guild_obj)
                global_commands = self.tree.get_commands()
                
                logging.info(f"Debug: {len(all_commands)} commands trong guild tree")
                logging.info(f"Debug: {len(global_commands)} commands trong global tree")
                
                # List commands trong tree
                for cmd in all_commands:
                    logging.info(f"Guild command trong tree: {cmd.name}")
                for cmd in global_commands:
                    logging.info(f"Global command trong tree: {cmd.name}")
                
                # Sync guild commands
                synced_guild = await self.tree.sync(guild=guild_obj)
                
                logging.info(f"Đã sync {len(synced_guild)} guild commands tới guild {self.guild_id}")
                
                # List all guild commands
                for cmd in synced_guild:
                    logging.info(f"  - /{cmd.name}: {cmd.description}")
                    
                self._commands_added = True
            except Exception as e:
                logging.error(f"Lỗi khi sync guild commands: {e}")
    
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
    # Ưu tiên lấy từ system environment variables (systemd) trước
    token = os.environ.get('TOKEN') or os.getenv('TOKEN')
    if not token:
        logging.error("❌ Không tìm thấy TOKEN trong environment variables!")
        return
    
    application_id = os.environ.get('APPLICATION_ID') or os.getenv('APPLICATION_ID')
    if not application_id:
        logging.error("❌ Không tìm thấy APPLICATION_ID trong environment variables!")
        return
        
    guild_id = os.environ.get('GUILD_ID') or os.getenv('GUILD_ID')
    if not guild_id:
        logging.error("❌ Không tìm thấy GUILD_ID trong environment variables!")
        return
    
    # Create and run bot
    bot = DiscordBot()
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logging.info("\n🛑 Bot đã được dừng bởi người dùng")
    except Exception as e:
        logging.error(f"❌ Lỗi khi chạy bot: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    # Run the bot
    logging.info("🚀 Khởi động bot....")
    asyncio.run(main())
