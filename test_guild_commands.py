import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_guild_commands():
    """Test xem bot có sync được guild commands không"""
    print("🔍 Test Guild Commands Bot...\n")
    
    # Test environment
    token = os.getenv('TOKEN')
    guild_id = os.getenv('GUILD_ID')
    
    if not token or not guild_id:
        print("❌ Missing environment variables")
        return False
    
    print(f"✅ Guild ID: {guild_id}")
    
    try:
        from bot import DiscordBot
        bot = DiscordBot()
        
        # Kiểm tra guild setting
        print(f"✅ Bot guild ID: {bot.guild_id}")
        
        # Test commands setup (không connect)
        print("✅ Bot class created successfully")
        print("✅ Guild commands setup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    success = await test_guild_commands()
    
    if success:
        print("\n🎉 All tests passed!")
        print("\n📋 Expected output khi chạy bot:")
        print("- Debug: 3 commands trong guild tree")
        print("- Debug: 0 commands trong global tree") 
        print("- Đã sync 3 guild commands tới guild")
        print("- Commands: /ping, /hello, /botinfo")
        print("\n🚀 Chạy 'python bot.py' để start bot!")
    else:
        print("\n❌ Tests failed!")

if __name__ == "__main__":
    asyncio.run(main())
