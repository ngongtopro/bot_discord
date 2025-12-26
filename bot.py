import discord
from discord.ext import commands
import os
import asyncio
import json
from dotenv import load_dotenv
import logging


# Load environment variables từ .env (chỉ dùng khi không có trong system env)
load_dotenv()

# Setup logging với format đẹp hơn
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

COMMAND_IGNORE_FILE = "data/command_ignore.json"

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
        stage = (os.environ.get('STAGE') or os.getenv('STAGE', 'production')).lower()
        
        # Initialize bot
        super().__init__(
            command_prefix='!',
            intents=intents,
            application_id=application_id
        )
        
        self.guild_id = guild_id
        self.stage = stage
        self.is_dev = stage == 'dev'
        
        self._commands_added = False
        self.ignored_commands = self._load_ignored_commands()
    
    def _load_ignored_commands(self):
        """Load danh sách commands bị ignore từ file JSON"""
        try:
            # Đảm bảo thư mục data tồn tại
            os.makedirs("data", exist_ok=True)
            
            # Nếu file chưa tồn tại, tạo mới với danh sách rỗng
            if not os.path.exists(COMMAND_IGNORE_FILE):
                logging.info("📄 Tạo file command_ignore.json mới")
                with open(COMMAND_IGNORE_FILE, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2)
                return []
            
            # Đọc file nếu đã tồn tại
            with open(COMMAND_IGNORE_FILE, 'r', encoding='utf-8') as f:
                ignored_list = json.load(f)
                if ignored_list:
                    logging.info(f"🚫 Đã load {len(ignored_list)} commands bị ignore: {', '.join(ignored_list)}")
                return ignored_list
        except Exception as e:
            logging.error(f"❌ Lỗi khi load command_ignore.json: {e}")
            return []
    
    def is_command_ignored(self, command_name: str) -> bool:
        """Kiểm tra xem command có bị ignore không"""
        # Loại bỏ prefix "dev_" nếu có để check base name
        base_name = command_name.replace("dev_", "", 1) if command_name.startswith("dev_") else command_name
        return base_name in self.ignored_commands or command_name in self.ignored_commands
        
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
        logging.info("="*60)
        logging.info("BẮT ĐẦU LOAD COGS")
        logging.info("="*60)
        
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    logging.info(f'⏳ Đang load cog: {filename}...')
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logging.info(f'✅ Đã load cog: {filename}')
                except Exception as e:
                    logging.error(f'❌ Lỗi load cog {filename}: {e}')
                    logging.exception(e)
        
        logging.info("="*60)
        logging.info("HOÀN TẤT LOAD COGS")
        logging.info("="*60)

    async def on_ready(self):
        """Called when bot is ready"""
        logging.info(f'Bot {self.user} đã sẵn sàng!')
        logging.info(f'Bot ID: {self.user.id}')
        logging.info(f'Guild ID: {self.guild_id}')
        logging.info(f'Stage: {self.stage.upper()}')
        if self.is_dev:
            logging.info(f'⚠️  CHẾ ĐỘ DEV - Commands sẽ có prefix "dev"')
        
        # Change bot status
        status_text = "dev commands!" if self.is_dev else "slash commands!"
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=status_text
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
                
                # Filter out ignored commands
                commands_to_sync = []
                ignored_count = 0
                
                for cmd in all_commands:
                    if self.is_command_ignored(cmd.name):
                        logging.warning(f"🚫 Bỏ qua command: {cmd.name} (trong ignore list)")
                        ignored_count += 1
                    else:
                        commands_to_sync.append(cmd)
                        logging.info(f"✅ Command sẽ sync: {cmd.name}")
                
                # Xóa tất cả commands và chỉ thêm lại những commands không bị ignore
                self.tree.clear_commands(guild=guild_obj)
                for cmd in commands_to_sync:
                    self.tree.add_command(cmd, guild=guild_obj)
                
                # Sync guild commands
                synced_guild = await self.tree.sync(guild=guild_obj)
                
                logging.info(f"Đã sync {len(synced_guild)} guild commands tới guild {self.guild_id}")
                if ignored_count > 0:
                    logging.info(f"🚫 Đã bỏ qua {ignored_count} commands")
                
                # List all guild commands
                for cmd in synced_guild:
                    logging.info(f"  - /{cmd.name}: {cmd.description}")
                    
                self._commands_added = True
                
                logging.info("="*60)
                logging.info("✅ BOT ĐÃ SẴN SÀNG HOÀN TOÀN!")
                logging.info("="*60)
                
            except Exception as e:
                logging.error(f"Lỗi khi sync guild commands: {e}")
                logging.exception(e)
    
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
    logging.info("🚀 Khởi động bot...")
    asyncio.run(main())
