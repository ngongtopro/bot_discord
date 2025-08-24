import pytest
import pytest_asyncio
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import DiscordBot

class TestDiscordBot:
    """Test class for Discord Bot"""
    
    @pytest_asyncio.fixture
    async def bot(self):
        """Create a test bot instance"""
        bot = DiscordBot()
        yield bot
        if not bot.is_closed():
            await bot.close()
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self, bot):
        """Test bot initialization"""
        assert bot is not None
        assert bot.command_prefix == '!'
        assert bot.application_id == int(os.getenv('APPLICATION_ID'))
        assert bot.guild_id == int(os.getenv('GUILD_ID'))
    
    @pytest.mark.asyncio
    async def test_hello_slash_command(self, bot):
        """Test hello slash command"""
        # Mock interaction
        interaction = MagicMock()
        interaction.user = MagicMock()
        interaction.user.mention = "@testuser"
        interaction.user.id = 123456789
        interaction.guild = MagicMock()
        interaction.guild.name = "Test Guild"
        interaction.response = AsyncMock()
        
        # Test command
        await bot.hello_slash(interaction)
        
        # Verify response was called
        interaction.response.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_botinfo_slash_command(self, bot):
        """Test botinfo slash command"""
        # Mock interaction
        interaction = MagicMock()
        interaction.response = AsyncMock()
        
        # Mock bot user
        bot.user = MagicMock()
        bot.user.name = "TestBot"
        bot.user.id = 987654321
        bot.user.display_avatar = MagicMock()
        bot.user.display_avatar.url = "https://example.com/avatar.png"
        
        # Mock guilds and users
        bot.guilds = [MagicMock()]
        bot.users = [MagicMock(), MagicMock()]
        
        # Test command
        await bot.botinfo_slash(interaction)
        
        # Verify response was called
        interaction.response.send_message.assert_called_once()

@pytest.mark.asyncio
async def test_environment_variables():
    """Test if environment variables are properly loaded"""
    token = os.getenv('TOKEN')
    application_id = os.getenv('APPLICATION_ID')
    guild_id = os.getenv('GUILD_ID')
    
    assert token is not None, "TOKEN không được tìm thấy trong .env"
    assert application_id is not None, "APPLICATION_ID không được tìm thấy trong .env"
    assert guild_id is not None, "GUILD_ID không được tìm thấy trong .env"
    
    # Test if they can be converted to int (except token)
    assert application_id.isdigit(), "APPLICATION_ID phải là số"
    assert guild_id.isdigit(), "GUILD_ID phải là số"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
