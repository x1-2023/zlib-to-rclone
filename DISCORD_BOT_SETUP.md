# 🤖 Discord Bot - Z-Library Downloader với Rclone

## 📋 Tổng quan

Bot Discord tự động:
1. Nhận link Z-Library từ user
2. Download sách về VPS
3. Upload lên Google Drive bằng Rclone
4. Trả về link share
5. Tự động xóa file trên VPS

## 🛠️ Cài đặt trên VPS

### **Bước 1: Cài đặt dependencies**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Cài Python 3.11+
sudo apt install python3 python3-pip -y

# Clone project
git clone <your-repo>
cd Auto-Book-Management

# Cài Python packages
pip3 install -r requirements.txt
pip3 install discord.py

# Hoặc thêm vào requirements.txt:
echo "discord.py>=2.0.0" >> requirements.txt
pip3 install -r requirements.txt
```

### **Bước 2: Cài đặt Rclone**

```bash
# Cài rclone
curl https://rclone.org/install.sh | sudo bash

# Kiểm tra version
rclone version

# Cấu hình rclone với Google Drive
rclone config
```

**Hướng dẫn cấu hình Rclone:**

```
n) New remote
name> gdrive
Storage> drive (chọn Google Drive)
client_id> (Enter để bỏ qua hoặc nhập custom OAuth)
client_secret> (Enter)
scope> 1 (Full access)
root_folder_id> (Enter)
service_account_file> (Enter)

# Nếu VPS không có GUI, chọn:
Use auto config? n

# Copy link và mở trên máy local có browser
# Paste code authorization vào

# Test:
rclone lsd gdrive:
```

### **Bước 3: Tạo Discord Bot**

1. **Truy cập:** https://discord.com/developers/applications
2. **New Application** → Đặt tên bot
3. **Bot** tab → **Add Bot**
4. **Copy Token** (giữ bí mật!)
5. **OAuth2** → **URL Generator:**
   - Scopes: `bot`
   - Bot Permissions: 
     - Send Messages
     - Embed Links
     - Attach Files
     - Read Message History
6. **Copy URL** và mở để invite bot vào server

### **Bước 4: Cấu hình Bot**

Sửa file `discord_bot.py`:

```python
# Dòng 25-28
DISCORD_TOKEN = "YOUR_BOT_TOKEN_HERE"  # ← Paste token từ Discord Developer Portal
RCLONE_REMOTE = "gdrive"               # ← Tên remote trong rclone config
RCLONE_FOLDER = "ZLibrary-Books"       # ← Folder trên Google Drive (tự động tạo)
DOWNLOAD_DIR = "data/downloads/discord" # ← Folder tạm trên VPS
AUTO_DELETE_AFTER_UPLOAD = True        # ← True = tự động xóa sau khi upload
```

Đảm bảo file `config.yaml` có thông tin Z-Library:

```yaml
zlibrary:
  username: "your_email@gmail.com"
  password: "your_password"
  proxy_list: []  # Thêm proxy nếu cần
```

### **Bước 5: Chạy Bot**

```bash
# Chạy trực tiếp
python3 discord_bot.py

# Hoặc dùng screen để chạy background
screen -S discord-bot
python3 discord_bot.py
# Ctrl+A+D để detach

# Xem lại screen
screen -r discord-bot
```

## 📝 Cách sử dụng

### **Commands:**

#### 1. **Download sách**
```
!download https://z-library.se/book/12345/abcdef
```
hoặc với direct link:
```
!download https://z-library.se/dl/12345/abcdef
```

Bot sẽ:
- ✅ Download sách về VPS
- ✅ Upload lên Google Drive folder `ZLibrary-Books`
- ✅ Trả về thông tin file + link (nếu có)
- ✅ Tự động xóa file trên VPS

#### 2. **Kiểm tra quota**
```
!quota
```
Xem còn bao nhiêu lượt download Z-Library trong ngày

#### 3. **Ping bot**
```
!ping
```
Kiểm tra bot có hoạt động không

#### 4. **Help**
```
!help_bot
```
Xem hướng dẫn đầy đủ

## 🔧 Troubleshooting

### **Lỗi: "Rclone chưa được cài đặt"**
```bash
# Cài lại rclone
curl https://rclone.org/install.sh | sudo bash
rclone version
```

### **Lỗi: "Không thể tạo public link"**

Rclone cần được cấu hình với quyền tạo link. Thêm vào rclone config:

```bash
rclone config update gdrive --drive-shared-with-me
```

Hoặc dùng Google Drive API:
1. Vào https://console.cloud.google.com/
2. Enable Google Drive API
3. Tạo OAuth credentials
4. Config lại rclone với client_id và client_secret

### **Lỗi: "Discord Forbidden 403"**

Bot thiếu quyền. Vào Discord Developer Portal → Bot → Bot Permissions:
- ✅ Send Messages
- ✅ Embed Links
- ✅ Use External Emojis
- ✅ Add Reactions
- ✅ Read Message History

Reinvite bot với URL mới từ OAuth2 URL Generator.

### **Lỗi: Z-Library connection failed**

Kiểm tra:
```bash
# Test connection
python3 -c "from services.zlibrary_service import ZLibraryService; print('OK')"

# Kiểm tra config
cat config.yaml | grep -A 5 "zlibrary:"
```

## 🚀 Chạy Bot như Service (systemd)

Tạo file `/etc/systemd/system/discord-zlib-bot.service`:

```ini
[Unit]
Description=Discord Z-Library Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Auto-Book-Management
ExecStart=/usr/bin/python3 /path/to/Auto-Book-Management/discord_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Kích hoạt:
```bash
sudo systemctl daemon-reload
sudo systemctl enable discord-zlib-bot
sudo systemctl start discord-zlib-bot

# Xem status
sudo systemctl status discord-zlib-bot

# Xem logs
sudo journalctl -u discord-zlib-bot -f
```

## 📊 Monitoring

Xem logs:
```bash
# Log bot
tail -f logs/discord_bot.log

# Log download
tail -f logs/app.log

# Systemd journal
sudo journalctl -u discord-zlib-bot -f --since "1 hour ago"
```

## 🔐 Bảo mật

1. **Không commit token/password lên Git:**
   ```bash
   # Thêm vào .gitignore
   echo "config.yaml" >> .gitignore
   echo "logs/" >> .gitignore
   ```

2. **Dùng environment variables:**
   ```bash
   export DISCORD_TOKEN="your_token"
   export ZLIB_USERNAME="your_email"
   export ZLIB_PASSWORD="your_password"
   ```

3. **Giới hạn quyền bot:** Chỉ cho phép dùng trong specific channels

## 📈 Tối ưu hóa

### **1. Giới hạn file size**
Thêm vào `discord_bot.py`:
```python
MAX_FILE_SIZE_MB = 500  # Giới hạn 500MB

# Trong download_command:
if file_size_mb > MAX_FILE_SIZE_MB:
    await ctx.send(f"❌ File quá lớn ({file_size_mb:.2f} MB). Giới hạn: {MAX_FILE_SIZE_MB} MB")
    return
```

### **2. Queue system (xử lý nhiều request cùng lúc)**
```python
import asyncio
from collections import deque

download_queue = deque()
MAX_CONCURRENT = 2

async def process_queue():
    while True:
        if download_queue and len(active_downloads) < MAX_CONCURRENT:
            task = download_queue.popleft()
            asyncio.create_task(task)
        await asyncio.sleep(1)
```

### **3. Retry mechanism**
Đã có sẵn trong `ZLibraryService` (max 3 retries)

## 🎯 Workflow hoàn chỉnh

```
User Discord Command
    ↓
!download <url>
    ↓
Bot parse URL → Extract book ID + hash
    ↓
Z-Library login
    ↓
Download sách về /data/downloads/discord/
    ↓
Rclone upload → gdrive:ZLibrary-Books/
    ↓
Tạo public link (optional)
    ↓
Trả message với embed info + link
    ↓
Auto delete file trên VPS
    ↓
✅ Done!
```

## 📞 Support

Nếu có lỗi:
1. Check logs: `tail -f logs/discord_bot.log`
2. Test manual download: `python3 test_download_single_book.py`
3. Test rclone: `rclone lsd gdrive:`
4. Check bot status: `!ping`

---

**Happy downloading! 📚**
