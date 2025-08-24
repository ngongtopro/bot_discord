# Admin System Guide

## 🔐 Phân quyền Admin trong Bot

### Cấu hình Admin Role

1. **Thêm Admin Role ID vào .env:**
```env
ADMIN_ROLE_ID = 938465381037801565  # Thay bằng ID role admin thực tế của server
```

2. **Cách lấy Role ID:**
   - Bật Developer Mode trong Discord
   - Vào Server Settings → Roles
   - Right-click vào role admin → Copy ID

### Commands dành cho Admin

#### `/delete_pending <index>`
- **Mục đích:** Xóa file cog khỏi waiting list
- **Quyền:** Owner hoặc user có admin role
- **Cách dùng:**
  1. Dùng `/check_pending` để xem danh sách
  2. Chọn index của file muốn xóa
  3. Dùng `/delete_pending 0` (xóa file đầu tiên)

### Quy trình Admin Review

#### 1. Kiểm tra Pending Cogs
```
/check_pending
```
- Xem tất cả cog đang chờ duyệt
- Thông tin: filename, uploader, upload time, file size

#### 2. Quyết định Approve/Delete
**Approve (chỉ Owner):**
```
/approve_cog 0
```
- File được move vào `cogs/` và load vào bot
- User được thông báo cog đã được duyệt

**Delete (Owner hoặc Admin):**
```
/delete_pending 0
```
- File bị xóa khỏi `waiting_cogs/`
- User được thông báo cog đã bị từ chối

### Thông báo cho User

#### Khi cog được approve:
- ✅ Embed xanh: "Cog của bạn đã được duyệt!"
- Thông tin: filename, cog name, status

#### Khi cog bị delete:
- ❌ Embed đỏ: "Cog của bạn đã bị từ chối"
- Lý do: "Rejected by admin"
- Gợi ý: "Bạn có thể upload lại sau khi sửa đổi cog"

### Best Practices cho Admin

#### Tiêu chí Review:
1. **Code Quality:**
   - Kiểm tra syntax errors
   - Không có malicious code
   - Follows Discord.py best practices

2. **Functionality:**
   - Commands có ý nghĩa
   - Không conflict với existing commands
   - Proper error handling

3. **Security:**
   - Không access sensitive data
   - Không có file operations nguy hiểm
   - Không có network calls suspicious

#### Workflow khuyến nghị:
1. **Check pending** - Xem tất cả submissions
2. **Download & review** - Kiểm tra code manually nếu cần
3. **Test locally** - Test cog trước khi approve (optional)
4. **Approve/Delete** - Quyết định cuối cùng

### Troubleshooting

#### Admin role không work:
- Kiểm tra `ADMIN_ROLE_ID` trong .env
- Verify user có role đúng trong server
- Role phải có đúng ID (không phải role name)

#### Permission errors:
- Chỉ Owner + Admin có thể delete
- Owner có thể approve + delete
- Regular users chỉ upload được

#### File not found errors:
- File có thể đã bị xóa manual
- Metadata file bị corrupt
- Check `waiting_cogs/` folder tồn tại

### Advanced Features

#### Notification System:
- User được notify qua DM khi cog approved/rejected
- Admin thấy thông tin uploader trong embed
- Timestamp tracking cho mọi action

#### File Management:
- Automatic cleanup metadata files
- Safe file operations với error handling
- Backup mechanism nếu approve fails

#### Audit Trail:
- Embed hiển thị ai approve/delete
- Original uploader information preserved
- Action history trong message logs

## 🚀 Setup Admin System

1. **Tạo Admin Role trong Discord server**
2. **Copy Role ID và paste vào .env**
3. **Assign role cho trusted users**
4. **Test commands với admin account**
5. **Review workflow với team**

Admin system giờ đây cho phép distributed moderation while keeping owner control over approvals! 🎯
