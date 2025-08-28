# Discord Bot với Slash Commands

## 📋 Mô tả
Bot Discord được viết bằng Python sử dụng discord.py với:
- ✅ Class-based structure
- ✅ Slash commands support  
- ✅ Cogs system để load modules
- ✅ Environment variables từ .env file
- ✅ Auto-sync commands

## 🚀 Cài đặt

1. **Clone/Download project**
2. **Cài đặt dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình file .env:**
   ```
   TOKEN=your_bot_token_here
   APPLICATION_ID=your_application_id_here  
   GUILD_ID=your_guild_id_here
   ```

## 🎮 Slash Commands có sẵn

### Commands trong Bot chính:
- `/hello` - Test slash command, chào hỏi người dùng
- `/botinfo` - Hiển thị thông tin về bot
- `/upload_cog` - Upload file .py để tạo cog mới (🆕 với approval system)
- `/check_pending` - [OWNER] Kiểm tra các cog đang chờ duyệt (🆕)
- `/approve_cog` - [OWNER] Duyệt cog theo index (🆕)
- `/delete_pending` - [ADMIN] Xóa file trong waiting_cogs theo index (🆕)

### Commands từ Cogs:
- `/ping` - Kiểm tra ping của bot (improved với embed)
- `/level` - Xem level hiện tại (Level System)
- `/leaderboard` - Bảng xếp hạng level (Level System)
- `/reset_level` - [ADMIN] Reset level user (Level System)

## 📁 Cấu trúc Project

```
bot_discord/
├── bot.py                    # File chính chứa DiscordBot class
├── .env                     # Environment variables (TOKEN, IDs)
├── requirements.txt         # Python dependencies
├── test_simple.py          # Test script cơ bản
├── test_cog.py            # File cog mẫu để test upload (🆕)
├── test_approval_cog.py   # File test approval system (🆕)
├── UPLOAD_COG_GUIDE.md    # Hướng dẫn upload cog (🆕)
├── APPROVAL_SYSTEM_GUIDE.md # Hướng dẫn approval system (🆕)
├── MONGODB_SETUP_GUIDE.md # Hướng dẫn setup MongoDB (🆕)
├── migrate_levels_to_mongo.py # Script chuyển data JSON→MongoDB (🆕)
├── cogs/                   # Thư mục chứa các cogs
│   ├── hiworld1.py        # Cog với /hi command  
│   ├── slash.py           # Cog với /ping command (improved)
│   ├── level_system.py    # Level system với JSON file
│   ├── level_system_mongo.py # Level system với MongoDB (🆕)
│   └── steam_deals.py     # Steam deals notification (🆕)
├── waiting_cogs/          # Cog chờ duyệt từ non-owner (🆕)
├── uploads/               # File uploads tạm
└── __pycache__/           # Python cache files
```

## 🔧 Chạy Bot

### Chạy trực tiếp:
```bash
python bot.py
```

### Chạy với virtual environment:
```bash
# Windows
.venv\Scripts\python.exe bot.py

# Linux/Mac  
.venv/bin/python bot.py
```

## 🧪 Testing

### Test cơ bản:
```bash
python test_simple.py
```

### Test với pytest:
```bash
pytest test_bot_new.py -v
```

## 📝 Tính năng chính

### 🏗️ DiscordBot Class
- Kế thừa từ `commands.Bot`
- Auto-load tất cả cogs từ thư mục `cogs/`
- Auto-sync slash commands khi bot ready
- Built-in slash commands

### 🔧 Cogs System
- Load tự động các file .py từ thư mục `cogs/`
- Hỗ trợ hot-reload (có thể thêm sau)
- Mỗi cog có thể chứa nhiều slash commands

### ⚡ Slash Commands
- Sync tự động khi bot khởi động
- Sử dụng **guild-specific commands** (xuất hiện ngay lập tức)
- Rich embeds với thông tin chi tiết

## 🛠️ Thêm Commands mới

### Trong Bot chính:
1. Tạo callback function trong class `DiscordBot`
2. Thêm command trong `setup_hook()`:
```python
guild_obj = discord.Object(id=self.guild_id)
new_cmd = app_commands.Command(
    name="tên_command",
    description="Mô tả command", 
    callback=self._callback_function
)
self.tree.add_command(new_cmd, guild=guild_obj)  # Thêm vào guild tree
```

### Trong Cogs:
1. Tạo file mới trong `cogs/`
2. Sử dụng `@app_commands.command` decorator
3. Thêm `@app_commands.guilds(guild_id)` để restrict vào guild
4. Implement `setup()` function để load cog

**Ví dụ cog với guild commands:**
```python
@app_commands.command(name="example", description="Example command")
@app_commands.guilds(int(os.getenv('GUILD_ID')))
async def example(self, interaction: discord.Interaction):
    await interaction.response.send_message("Hello!")
```

### 🚀 Upload Cog qua Discord (🆕):
1. Sử dụng `/upload_cog` command trên Discord
2. Attach file `.py` chứa cog code
3. Bot sẽ tự động:
   - ✅ Validate file syntax
   - ✅ Load/reload cog
   - ✅ Sync new commands
   - ✅ Thông báo kết quả

📖 **Chi tiết:** Xem file `UPLOAD_COG_GUIDE.md`

## 🔐 Approval System (Mới)

### Dành cho Non-Owner Users:
- Upload file cog → Lưu vào `waiting_cogs/`
- Chờ owner duyệt mới được load

### Dành cho Owner:
- `/check_pending` - Xem danh sách cog chờ duyệt
- `/approve_cog <index>` - Duyệt cog theo số thứ tự
- `/delete_pending <index>` - Xóa cog chờ duyệt theo số thứ tự
- Upload trực tiếp được load ngay

### Dành cho Admin (có role admin):
- `/delete_pending <index>` - Xóa cog chờ duyệt theo số thứ tự

### Quy trình Approval:
1. User upload cog → File vào `waiting_cogs/`
2. Owner dùng `/check_pending` để xem
3. Owner có thể:
   - `/approve_cog 0` để duyệt file đầu tiên
   - `/delete_pending 0` để xóa file đầu tiên
4. Admin có thể dùng `/delete_pending` để xóa file không phù hợp
5. File được duyệt sẽ move vào `cogs/` và load vào bot

## 🔍 Debug & Troubleshooting

### Kiểm tra environment:
```bash
python test_simple.py
```

### Nếu slash commands không xuất hiện:
1. Kiểm tra bot có quyền `applications.commands`
2. Guild commands xuất hiện ngay lập tức (không cần đợi)
3. Restart Discord client nếu cần
4. Kiểm tra console output để xem sync status

### Log messages quan trọng:
- `✅ Đã load cog: filename.py` - Cog loaded thành công
- `Debug: X commands trong guild tree` - Commands được add vào guild tree
- `Đã sync X guild commands tới guild XXXXX` - Guild commands synced
- `Bot đã sẵn sàng!` - Bot ready để sử dụng

## 📱 Sử dụng trên Discord

1. Invite bot vào server với quyền:
   - `Send Messages`
   - `Use Slash Commands` 
   - `Embed Links`

2. Slash commands sẽ xuất hiện khi gõ `/` trong text channel

3. Test các commands:
   - `/hello` - Kiểm tra bot hoạt động
   - `/ping` - Kiểm tra latency
   - `/botinfo` - Xem thông tin bot
   - `/upload_cog` - Upload file .py để thêm cog mới (🆕)

## 🎯 Kết quả mong đợi

Khi chạy thành công, bạn sẽ thấy:
```
Bot bot_test_1#5998 đã sẵn sàng!
Bot ID: 1407981527585001553
Guild ID: 938465381037801562
Đã xóa global commands
Debug: 5 commands trong guild tree
Debug: 0 commands trong global tree
Guild command trong tree: hi
Guild command trong tree: ping
Guild command trong tree: hello
Guild command trong tree: botinfo
Guild command trong tree: upload_cog
Đã sync 5 guild commands tới guild 938465381037801562
  - /hi: Slash command: chào hỏi
  - /ping: Slash command: kiểm tra ping
  - /hello: Test slash command - chào hỏi
  - /botinfo: Thông tin về bot
  - /upload_cog: Upload file .py để tạo cog mới
```

✅ **Bot hoạt động thành công với guild slash commands!**

## 🔐 Level System với MongoDB (🆕)

### 📊 Features:
- **XP System:** Nhận 10 XP mỗi tin nhắn
- **Level Up:** 100 XP * current_level để lên level
- **Tu Tiên Roles:** Auto gán role theo level (Phàm Nhân → Tiên Đế)
- **Leaderboard:** Top 10 users theo level và XP
- **Admin Commands:** Reset level, quản lý users

### 🚀 Setup MongoDB:
1. **Cài đặt MongoDB:** Follow `MONGODB_SETUP_GUIDE.md`
2. **Migration:** `python migrate_levels_to_mongo.py`
3. **Load Cog:** `level_system_mongo.py` (thay vì `level_system.py`)

### 📈 Performance:
- ✅ **Faster:** MongoDB > JSON file
- ✅ **Scalable:** Handle thousands of users
- ✅ **Safe:** Concurrent access protection
- ✅ **Backup:** Automatic với Atlas
