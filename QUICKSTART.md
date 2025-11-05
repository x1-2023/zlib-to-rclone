# 🚀 Quick Start - Discord Bot với Z-Library

## 📝 TÓM TẮT NHANH

Bot Discord tự động download sách từ Z-Library và upload lên Google Drive.

### **Workflow:**
```
Discord: !download <url>
    ↓
Download từ Z-Library (.ec, .se, .is, .sk)
    ↓
Upload lên Google Drive (Rclone)
    ↓
Share public link
    ↓
Tự động xóa file trên VPS
```

---

## ⚡ QUICK START (5 phút)

### **1. Setup cơ bản**

```bash
# Clone project
git clone <repo>
cd Auto-Book-Management

# Cài packages
pip install -r requirements.txt

# Copy config
cp config.example.yaml config.yaml
```

### **2. Sửa config.yaml**

```yaml
zlibrary:
  username: "your_email@gmail.com"  # ← SỬA
  password: "your_password"         # ← SỬA
  proxy_list: []
```

### **3. Test download trước (không cần Discord/Rclone)**

```bash
# Sửa URL trong test_download_single_book.py
# Dòng 18: DIRECT_DOWNLOAD_URL = "https://z-library.ec/dl/YOUR_BOOK_ID/HASH"

python test_download_single_book.py
```

✅ Nếu download thành công → Tiếp tục bước 4  
❌ Nếu thất bại → Kiểm tra lại config.yaml

### **4. Setup Discord Bot**

1. Vào: https://discord.com/developers/applications
2. **New Application** → Đặt tên
3. **Bot** tab → **Add Bot** → **Copy Token**
4. **OAuth2 → URL Generator:**
   - Scopes: `bot`
   - Permissions: `Send Messages`, `Embed Links`
   - Copy URL và invite bot vào server

5. **Sửa `discord_bot.py` dòng 25:**
   ```python
   DISCORD_TOKEN = "YOUR_BOT_TOKEN_HERE"  # ← Paste token
   ```

### **5. (Optional) Setup Rclone**

Nếu muốn upload lên Google Drive:

```bash
# Cài rclone
curl https://rclone.org/install.sh | sudo bash

# Config
rclone config
# Làm theo RCLONE_SETUP_GUIDE.md
```

Hoặc **BỎ QUA** nếu chỉ muốn download:
- Bot vẫn download được
- Chỉ không upload lên Drive
- File sẽ ở folder local

### **6. Chạy bot**

```bash
# Local test (không cần Discord)
python test_discord_bot.py
# Chọn option 1 để test download

# Chạy bot thật
python discord_bot.py
```

---

## 🎮 CÁCH DÙNG

### **Trên Discord:**

```
!download https://z-library.ec/dl/11948830/b88232
```

Bot sẽ:
1. ✅ Download sách (230MB)
2. ✅ Upload lên Drive (nếu có Rclone)
3. ✅ Trả về thông tin + link
4. ✅ Xóa file local

### **Commands:**

| Command | Mô tả |
|---------|-------|
| `!download <url>` | Download và upload sách |
| `!quota` | Xem quota Z-Library còn lại |
| `!ping` | Test bot |
| `!help_bot` | Xem hướng dẫn |

---

## 📚 TÀI LIỆU CHI TIẾT

### **Đã đọc chưa?**

- 📘 **RCLONE_SETUP_GUIDE.md** - Hướng dẫn setup Rclone chi tiết
- 📗 **DISCORD_BOT_SETUP.md** - Hướng dẫn deploy bot lên VPS
- 📙 **README.md** - Tổng quan project

### **Files quan trọng:**

```
discord_bot.py              # Bot chính
test_discord_bot.py         # Test bot local (không cần Discord)
test_download_single_book.py # Test download đơn giản
config.yaml                 # Config (Z-Library credentials)
```

---

## 🔧 TROUBLESHOOTING

### **Lỗi: "config.yaml not found"**
```bash
cp config.example.yaml config.yaml
# Sửa username/password Z-Library
```

### **Lỗi: "Discord Token invalid"**
- Kiểm tra lại token từ Discord Developer Portal
- Đảm bảo không có dấu cách thừa
- Token phải bắt đầu bằng ký tự như `MTEx...`

### **Lỗi: "Download failed"**
```bash
# Test download standalone
python test_download_single_book.py

# Kiểm tra log
tail -f logs/discord_bot.log
```

### **Lỗi: "Rclone not found"**
- Bot vẫn chạy được, chỉ không upload lên Drive
- Để fix: cài Rclone theo RCLONE_SETUP_GUIDE.md

### **Lỗi: "Z-Library connection failed"**
- Kiểm tra username/password trong config.yaml
- Thử thêm proxy nếu Z-Library bị chặn
- Test với script đơn giản trước

---

## 🎯 USE CASES

### **1. Download đơn giản (không cần Discord/Rclone):**

```bash
# Chỉ cần config.yaml
python test_download_single_book.py
```

### **2. Download qua Discord Bot (không upload Drive):**

```python
# Trong discord_bot.py, comment dòng upload:
# upload_result = await uploader.upload_file(file_path)
```

### **3. Full workflow (Discord + Rclone + Drive):**

Setup đầy đủ theo hướng dẫn.

---

## 🚀 DEPLOY LÊN VPS

### **Quick deploy:**

```bash
# 1. SSH vào VPS
ssh user@your-vps-ip

# 2. Clone project
git clone <repo>
cd Auto-Book-Management

# 3. Setup
pip install -r requirements.txt
cp config.example.yaml config.yaml
nano config.yaml  # Sửa credentials

# 4. Test
python test_download_single_book.py

# 5. Setup Rclone (nếu cần)
curl https://rclone.org/install.sh | sudo bash
rclone config

# 6. Chạy bot
screen -S discord-bot
python discord_bot.py
# Ctrl+A+D để detach
```

### **Chạy như service (systemd):**

```bash
sudo nano /etc/systemd/system/discord-zlib-bot.service
```

Nội dung:
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

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable discord-zlib-bot
sudo systemctl start discord-zlib-bot
sudo systemctl status discord-zlib-bot
```

---

## 📊 MONITORING

### **Logs:**

```bash
# Bot logs
tail -f logs/discord_bot.log

# Download logs
tail -f logs/app.log

# Systemd logs (if running as service)
sudo journalctl -u discord-zlib-bot -f
```

### **Check status:**

```bash
# Trên Discord
!ping
!quota
```

---

## ✅ CHECKLIST SETUP

- [ ] Cài Python 3.11+
- [ ] Cài packages: `pip install -r requirements.txt`
- [ ] Tạo `config.yaml` với Z-Library credentials
- [ ] Test download: `python test_download_single_book.py`
- [ ] Tạo Discord Bot + lấy token
- [ ] Sửa `DISCORD_TOKEN` trong `discord_bot.py`
- [ ] Invite bot vào server
- [ ] (Optional) Cài Rclone: `curl https://rclone.org/install.sh | sudo bash`
- [ ] (Optional) Config Rclone với Google Drive
- [ ] Test bot: `python test_discord_bot.py`
- [ ] Chạy bot: `python discord_bot.py`
- [ ] Test trên Discord: `!download <url>`

---

## 🎉 KẾT QUẢ MONG ĐỢI

```
User: !download https://z-library.ec/dl/11948830/b88232

Bot:
⏳ Đang xử lý request của @User...
📥 [1/4] Đang download sách từ Z-Library...
☁️ [2/4] Đang upload Oxford English Grammar Course Basic.pdf (266 MB) lên Google Drive...
📋 [3/4] Đang tạo thông tin chia sẻ...

┌───────────────────────────────────────┐
│ ✅ Download & Upload Thành Công!     │
├───────────────────────────────────────┤
│ 📖 File: Oxford English Grammar...   │
│ 📊 Size: 266.46 MB                   │
│ ☁️ Remote: gdrive:ZLibrary-Books/... │
│ 🔗 Link: https://drive.google.com/...│
└───────────────────────────────────────┘

🗑️ [4/4] Đã xóa file tạm trên VPS
```

---

## 💡 TIPS

1. **Domain Z-Library thay đổi thường xuyên:**
   - Bot hỗ trợ tất cả domain (.ec, .se, .is, .sk)
   - Copy link từ browser là được

2. **Quota Z-Library:**
   - Thường 10 cuốn/ngày
   - Check bằng `!quota`
   - Bot tự động thông báo khi hết quota

3. **File size lớn:**
   - Download + upload mất thời gian
   - Bot có progress tracking
   - Có thể giới hạn max size trong code

4. **Bảo mật:**
   - Không commit `config.yaml` lên Git
   - Token Discord giữ bí mật
   - Có thể giới hạn bot chỉ hoạt động trong specific channels

---

**Happy downloading! 📚**

Questions? Issues? → Xem logs hoặc test từng component riêng biệt!
