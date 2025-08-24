import pytest
from unittest.mock import AsyncMock
from bot import ping

@pytest.mark.asyncio
async def test_ping_command():
    # Tạo mock interaction
    interaction = AsyncMock()
    
    # Gọi trực tiếp command function
    await ping(interaction)
    
    # Kiểm tra bot có gọi đúng send_message hay không
    interaction.response.send_message.assert_called_with("🏓 Pong! (slash trong bot.py)")
