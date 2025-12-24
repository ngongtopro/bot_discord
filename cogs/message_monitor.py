import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONITOR_CHANNEL_ID = int(os.getenv('MONITOR_CHANNEL_ID', 0))


class MessageMonitor(commands.Cog):
    """Cog để theo dõi tin nhắn trong một channel cụ thể"""
    
    def __init__(self, bot):
        self.bot = bot
        self.monitor_channel_id = MONITOR_CHANNEL_ID
        
        if self.monitor_channel_id:
            print(f"📝 Message Monitor đã được kích hoạt cho channel ID: {self.monitor_channel_id}")
        else:
            print("⚠️ MONITOR_CHANNEL_ID chưa được cấu hình trong .env file")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Lắng nghe tất cả tin nhắn và in ra nếu đúng channel"""
        
        # Bỏ qua tin nhắn từ bot
        if message.author.bot:
            return
        
        # Kiểm tra xem có phải channel được theo dõi không
        if self.monitor_channel_id and message.channel.id == self.monitor_channel_id:
            # In thông tin tin nhắn
            print("\n" + "="*60)
            print(f"📨 TIN NHẮN MỚI TỪ CHANNEL: {message.channel.name}")
            print("="*60)
            print(f"👤 Người gửi: {message.author.name} ({message.author.id})")
            print(f"� Thời gian: {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"�💬 Nội dung gốc: {message.content}")
            
            # Thử parse JSON nếu nội dung là JSON
            try:
                if message.content.strip().startswith('{') and message.content.strip().endswith('}'):
                    json_data = json.loads(message.content)
                    print("\n📋 PARSED JSON DATA:")
                    print(json.dumps(json_data, indent=2, ensure_ascii=False))
                    
                    # In từng field của JSON một cách rõ ràng
                    print("\n📝 CHI TIẾT:")
                    for key, value in json_data.items():
                        print(f"  • {key}: {value}")
            except json.JSONDecodeError:
                # Nếu không phải JSON, chỉ in nội dung bình thường
                pass
            except Exception as e:
                print(f"⚠️ Lỗi khi parse JSON: {e}")
            
            # Nếu có attachments (file, hình ảnh)
            if message.attachments:
                print(f"\n📎 Attachments: {len(message.attachments)}")
                for attachment in message.attachments:
                    print(f"  - {attachment.filename} ({attachment.url})")
            
            # Nếu có embeds
            if message.embeds:
                print(f"📋 Embeds: {len(message.embeds)}")
            
            # Nếu có stickers
            if message.stickers:
                print(f"😀 Stickers: {len(message.stickers)}")
                for sticker in message.stickers:
                    print(f"  - {sticker.name}")
            
            # Nếu có reactions
            if message.reactions:
                print(f"👍 Reactions: {len(message.reactions)}")
            
            print("="*60 + "\n")


async def setup(bot):
    await bot.add_cog(MessageMonitor(bot))
