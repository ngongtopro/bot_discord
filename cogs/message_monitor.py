import discord
from discord.ext import commands
import os
import json
import sys
import asyncio
import platform
from dotenv import load_dotenv

# Load environment variables từ .env (chỉ dùng khi không có trong system env) test pull
load_dotenv()

# Ưu tiên lấy từ system environment variables (từ systemd) trước
MONITOR_CHANNEL_ID = int(os.environ.get('MONITOR_CHANNEL_ID') or os.getenv('MONITOR_CHANNEL_ID', 0))
AUTO_DEPLOY_ENABLED = (os.environ.get('AUTO_DEPLOY_ENABLED') or os.getenv('AUTO_DEPLOY_ENABLED', 'false')).lower() == 'true'


class MessageMonitor(commands.Cog):
    """Cog để theo dõi tin nhắn trong một channel cụ thể"""
    
    def __init__(self, bot):
        self.bot = bot
        self.monitor_channel_id = MONITOR_CHANNEL_ID
        self.auto_deploy_enabled = AUTO_DEPLOY_ENABLED
        self.is_ubuntu = self.check_is_ubuntu()
        
        if self.monitor_channel_id:
            print(f"Message Monitor đã được kích hoạt cho channel ID: {self.monitor_channel_id}")
            print(f"Auto Deploy: {'Enabled' if self.auto_deploy_enabled else 'Disabled'}")
            print(f"Platform: {platform.system()} (Ubuntu: {self.is_ubuntu})")
        else:
            print("MONITOR_CHANNEL_ID chưa được cấu hình trong .env file")
    
    def check_is_ubuntu(self):
        """Kiểm tra xem có đang chạy trên Ubuntu server không"""
        print("Kiểm tra hệ điều hành...")
        try:
            if platform.system() != 'Linux':
                return False
            
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if 'ubuntu' in content:
                        return True
            return False
        except:
            return False
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Lắng nghe tất cả tin nhắn và in ra nếu đúng channel"""
        
        # Kiểm tra xem có phải channel được theo dõi không
        if self.monitor_channel_id and message.channel.id == self.monitor_channel_id:
            # In thông tin tin nhắn
            print("\n" + "="*60)
            print(f"TIN NHẮN MỚI TỪ CHANNEL: {message.channel.name}")
            print("="*60)
            print(f"Người gửi: {message.author.name} ({message.author.id})")
            print(f"Thời gian: {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Nội dung gốc: {message.content}")

            # Thử parse JSON nếu nội dung là JSON
            try:
                # Làm sạch content - loại bỏ ```json, backticks, và newlines
                content = message.content.strip()
                
                # Loại bỏ code block markdown nếu có
                if content.startswith('```'):
                    # Loại bỏ ```json hoặc ```
                    lines = content.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]  # Bỏ dòng đầu (```json hoặc ```)
                    if lines and lines[-1].strip() == '```':
                        lines = lines[:-1]  # Bỏ dòng cuối (```)
                    content = '\n'.join(lines).strip()
                
                # Kiểm tra xem có phải JSON không
                if content.startswith('{') and content.endswith('}'):
                    json_data = json.loads(content)
                    print("\nPARSED JSON DATA:")
                    print(json.dumps(json_data, indent=2, ensure_ascii=False))
                    
                    # In từng field của JSON một cách rõ ràng
                    print("\nCHI TIẾT:")
                    for key, value in json_data.items():
                        print(f"  • {key}: {value}")
                    
                    # Kiểm tra nếu là GitHub push webhook và thực hiện auto deploy
                    if (json_data.get('type') == 'github_push' and 
                        self.auto_deploy_enabled and 
                        self.is_ubuntu):
                        
                        repo = json_data.get('repo', '')
                        branch = json_data.get('branch', '')

                        # Chỉ deploy nếu là repo ngongtopro/bot_discord và branch main
                        if 'ngongtopro/bot_discord' in repo.lower() and branch == 'main':
                            print("\nTRIGGER AUTO DEPLOY!")
                            await self.auto_deploy()
                        else:
                            print(f"\nBỏ qua deploy - Repo: {repo}, Branch: {branch}")
                    
            except json.JSONDecodeError:
                # Nếu không phải JSON, chỉ in nội dung bình thường
                pass
            except Exception as e:
                print(f"Lỗi khi parse JSON: {e}")
    
    async def auto_deploy(self):
        """Tự động pull code và restart bot"""
        try:
            print("="*60)
            print("BẮT ĐẦU AUTO DEPLOY")
            print("="*60)
            
            # Git pull
            print("Đang pull code từ GitHub...")
            process = await asyncio.create_subprocess_exec(
                'git', 'pull', 'origin', 'main',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                output = stdout.decode('utf-8', errors='ignore')
                print(f"Pull thành công:\n{output}")
                
                if 'Already up to date' in output or 'Already up-to-date' in output:
                    print("ℹCode đã là phiên bản mới nhất")
                    return
                
                # Cài đặt dependencies nếu có thay đổi requirements.txt
                if 'requirements.txt' in output:
                    print("Đang cài đặt dependencies...")
                    pip_process = await asyncio.create_subprocess_exec(
                        sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await pip_process.communicate()
                    print("Đã cài đặt dependencies")
                
                # Restart bot
                print("\nĐANG RESTART BOT...")
                await asyncio.sleep(2)
                os.execv(sys.executable, [sys.executable] + sys.argv)
                
            else:
                error = stderr.decode('utf-8', errors='ignore')
                print(f"Lỗi khi pull code:\n{error}")
                
        except Exception as e:
            print(f"Lỗi auto deploy: {e}")


async def setup(bot):
    await bot.add_cog(MessageMonitor(bot))
