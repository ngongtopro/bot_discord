# Hướng dẫn sử dụng `/upload_cog` command

## 📖 Mô tả
Command `/upload_cog` cho phép user upload file Python (.py) chứa Discord cog để thêm slash commands mới vào bot.

## 🎯 Cách sử dụng

### 1. **Tạo file cog**
Tạo file `.py` với cấu trúc sau:

```python
import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

class YourCogName(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="your_command", description="Mô tả command")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))  # Bắt buộc cho guild commands
    async def your_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello from your command!")

# BẮT BUỘC: Function setup
async def setup(bot):
    await bot.add_cog(YourCogName(bot))
```

### 2. **Upload trên Discord**
1. Vào Discord server nơi bot đang hoạt động
2. Gõ `/upload_cog`
3. Chọn file `.py` của bạn và upload
4. Đợi bot xử lý

## ✅ Các trường hợp xử lý

### **Cog mới:**
- ✅ File được lưu vào `./cogs/`
- ✅ Cog được load tự động
- ✅ Slash commands được sync
- ✅ Thông báo thành công với embed

### **Cog đã tồn tại:**
- 🔄 Unload cog cũ
- 🗑️ Xóa file cũ
- ✅ Upload file mới
- ✅ Load cog mới
- ✅ Sync commands

### **Lỗi:**
- ❌ File bị xóa nếu không load được
- ❌ Thông báo lỗi chi tiết
- ❌ Rollback nếu cần

## 🚫 Các hạn chế

- **File type**: Chỉ chấp nhận `.py`
- **File size**: Tối đa 1MB
- **Syntax**: Phải là Python hợp lệ
- **Setup function**: Bắt buộc có `async def setup(bot):`
- **Guild**: Commands phải có `@app_commands.guilds()` decorator

## 📋 Ví dụ file hợp lệ

File: `example_cog.py`
```python
import discord
from discord import app_commands
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="greet", description="Chào hỏi user")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))
    async def greet(self, interaction: discord.Interaction, name: str = None):
        user_name = name or interaction.user.display_name
        await interaction.response.send_message(f"👋 Xin chào {user_name}!")

    @app_commands.command(name="calculate", description="Tính toán đơn giản")
    @app_commands.guilds(int(os.getenv('GUILD_ID')))
    async def calculate(self, interaction: discord.Interaction, 
                       operation: str, num1: float, num2: float):
        if operation == "add":
            result = num1 + num2
        elif operation == "multiply":
            result = num1 * num2
        else:
            await interaction.response.send_message("❌ Operation không hỗ trợ!")
            return
        
        await interaction.response.send_message(f"🧮 {num1} {operation} {num2} = {result}")

async def setup(bot):
    await bot.add_cog(ExampleCog(bot))
```

## 🔍 Debug

Nếu upload thất bại, kiểm tra:
1. ✅ File có extension `.py`?
2. ✅ Syntax Python đúng?
3. ✅ Có function `async def setup(bot):`?
4. ✅ Commands có `@app_commands.guilds()` decorator?
5. ✅ Import statements đúng?

## 🎮 Test upload

Bạn có thể test với file `test_cog.py` đã được tạo sẵn trong project folder.
