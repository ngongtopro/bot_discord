import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test environment variables"""
    print("🔍 Kiểm tra các biến môi trường...")
    
    token = os.getenv('TOKEN')
    application_id = os.getenv('APPLICATION_ID')
    guild_id = os.getenv('GUILD_ID')
    
    if not token:
        print("❌ TOKEN không được tìm thấy trong .env")
        return False
    else:
        print(f"✅ TOKEN: {token[:20]}...")
    
    if not application_id:
        print("❌ APPLICATION_ID không được tìm thấy trong .env")
        return False
    else:
        print(f"✅ APPLICATION_ID: {application_id}")
    
    if not guild_id:
        print("❌ GUILD_ID không được tìm thấy trong .env")
        return False
    else:
        print(f"✅ GUILD_ID: {guild_id}")
    
    return True

async def test_bot_creation():
    """Test bot creation without connecting"""
    print("\n🤖 Kiểm tra tạo bot...")
    
    try:
        from bot import DiscordBot
        bot = DiscordBot()
        print("✅ Bot được tạo thành công")
        print(f"✅ Command prefix: {bot.command_prefix}")
        print(f"✅ Application ID: {bot.application_id}")
        print(f"✅ Guild ID: {bot.guild_id}")
        return True
    except Exception as e:
        print(f"❌ Lỗi tạo bot: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Bắt đầu test bot...\n")
    
    # Test environment
    if not test_environment():
        return
    
    # Test bot creation
    if not await test_bot_creation():
        return
    
    print("\n✅ Tất cả test cơ bản đã pass!")
    print("\n📝 Để test bot thực tế:")
    print("1. Chạy: python bot.py")
    print("2. Kiểm tra slash commands trên Discord server")
    print("3. Thử /hello và /botinfo commands")

if __name__ == "__main__":
    asyncio.run(main())
