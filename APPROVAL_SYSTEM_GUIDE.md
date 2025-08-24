# 🔐 Hướng dẫn Approval System

## 📋 Mô tả
Hệ thống phê duyệt cog cho phép owner kiểm soát việc thêm commands mới vào bot.

## 👥 Phân quyền

### 🔥 **Owner (ID: được định nghĩa trong .env)**
- ✅ Upload file → **Load trực tiếp**  
- ✅ Sử dụng `/check_pending` để xem cogs chờ duyệt
- ✅ Sử dụng `/approve_cog <index>` để duyệt cog
- ✅ Nhận thông báo DM khi có cog mới upload

### 👤 **User thường**
- ⏳ Upload file → **Chờ duyệt** (lưu trong `waiting_cogs/`)
- 📩 Nhận thông báo DM khi cog được duyệt
- ❌ Không thể sử dụng owner commands

## 🎮 Commands

### `/upload_cog`
**Mô tả:** Upload file .py để tạo cog mới

**Owner behavior:**
- File được lưu trực tiếp vào `cogs/`
- Cog được load ngay lập tức
- Commands được sync ngay

**User behavior:**
- File được lưu vào `waiting_cogs/`
- Metadata được tạo (.json file)
- Owner được thông báo qua DM

### `/check_pending` [OWNER ONLY]
**Mô tả:** Kiểm tra các cog đang chờ duyệt

**Output:**
- List tất cả cogs trong `waiting_cogs/`
- Thông tin: filename, uploader, size, time, guild
- Index numbers để sử dụng với `/approve_cog`

### `/approve_cog <index>` [OWNER ONLY]
**Mô tả:** Duyệt cog theo index từ `/check_pending`

**Process:**
1. Move file từ `waiting_cogs/` → `cogs/`
2. Load cog và sync commands
3. Xóa metadata files
4. Thông báo owner về kết quả
5. Thông báo uploader qua DM (nếu có thể)

## 📁 File Structure

```
bot_discord/
├── cogs/              # Cogs đã được duyệt và đang hoạt động
│   ├── slash.py       
│   └── ping.py        
├── waiting_cogs/      # Cogs chờ duyệt từ users
│   ├── example.py     # File cog
│   └── example.json   # Metadata
└── .env              # Chứa OWNER_ID
```

## 📋 Metadata Format

File `.json` được tạo cho mỗi cog chờ duyệt:

```json
{
  "filename": "example_cog.py",
  "cog_name": "example_cog", 
  "uploader_id": 123456789,
  "uploader_name": "Username",
  "upload_time": "2025-08-21T10:30:00",
  "file_size": 1024,
  "guild_id": 938465381037801562,
  "guild_name": "Guild Name"
}
```

## 🔄 Workflow

### User uploads cog:
1. User: `/upload_cog` + attach file
2. Bot: Validate file → Save to `waiting_cogs/` → Create metadata
3. Bot: Send confirmation to user
4. Bot: Send DM notification to owner

### Owner reviews pending:
1. Owner: `/check_pending`
2. Bot: Show list with index numbers
3. Owner: `/approve_cog <index>`
4. Bot: Move file → Load cog → Notify both parties

## 🧪 Testing

### Test với user thường:
1. Upload `test_approval_cog.py` với account không phải owner
2. Check response: "⏳ Cog đã được gửi để chờ duyệt!"
3. File sẽ ở trong `waiting_cogs/`

### Test với owner:
1. `/check_pending` → Xem pending cogs
2. `/approve_cog 0` → Duyệt cog đầu tiên
3. Commands mới sẽ xuất hiện: `/test_approval`, `/approval_info`

## ⚠️ Error Handling

### Upload errors:
- ❌ File không phải .py
- ❌ File quá lớn (>1MB)  
- ❌ Syntax Python không hợp lệ
- ❌ Không có `async def setup(bot):`

### Approval errors:
- ❌ Index không hợp lệ
- ❌ File không tồn tại
- ❌ Lỗi load cog → File được chuyển lại waiting_cogs

## 🎯 Benefits

- ✅ **Security**: Owner kiểm soát commands được thêm
- ✅ **Tracking**: Metadata đầy đủ về uploader  
- ✅ **Notification**: DM notifications cho cả owner và user
- ✅ **Rollback**: Error handling với rollback mechanism
- ✅ **Clean**: Automatic cleanup metadata sau khi approve
