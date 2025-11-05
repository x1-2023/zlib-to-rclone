# 🎯 Quick Commands - Rclone với Discord Bot

## ✅ Bạn đã setup xong: `discord:` remote

### **Test nhanh Rclone:**

```bash
# List root
rclone lsd discord:

# Tạo folder cho bot
rclone mkdir discord:ZLibrary-Books

# List folder
rclone ls discord:ZLibrary-Books/

# Test upload
echo "test" > test.txt
rclone copy test.txt discord:ZLibrary-Books/
rclone ls discord:ZLibrary-Books/

# Test download
rclone copy discord:ZLibrary-Books/test.txt ./downloaded/
cat downloaded/test.txt
```

### **Hoặc chạy script tự động:**

```bash
# Make script executable
chmod +x test_rclone.sh

# Run test
./test_rclone.sh
```

---

## 🤖 Setup Discord Bot

### **1. Sửa config trong `discord_bot.py`:**

```python
# Dòng 25-29
DISCORD_TOKEN = "YOUR_BOT_TOKEN"    # ← Paste Discord Bot Token
RCLONE_REMOTE = "discord"           # ✅ Already set!
RCLONE_FOLDER = "ZLibrary-Books"    # ← Tên folder trên Drive
```

### **2. Kiểm tra `config.yaml`:**

```bash
cat config.yaml | grep -A 3 "zlibrary:"
```

Đảm bảo có:
```yaml
zlibrary:
  username: "your_email@gmail.com"
  password: "your_password"
```

### **3. Test bot components:**

```bash
# Test download component (không cần Discord)
python3 test_discord_bot.py
# Chọn option 1: Test Download only
```

### **4. Chạy bot:**

```bash
# Trực tiếp (foreground)
python3 discord_bot.py

# Hoặc dùng screen (background)
screen -S discord-bot
python3 discord_bot.py
# Ctrl+A+D để detach

# Xem lại
screen -r discord-bot
```

---

## 🎮 Sử dụng trên Discord

### **Commands:**

```
!download https://z-library.ec/dl/11948830/b88232
!quota
!ping
!help_bot
```

### **Workflow khi user gõ !download:**

```
User: !download <url>
    ↓
Bot: ⏳ Đang xử lý request...
    ↓
Bot: 📥 [1/4] Đang download từ Z-Library...
    ↓
Bot: ☁️ [2/4] Đang upload lên discord:ZLibrary-Books/...
    ↓
Bot: 📋 [3/4] Đang tạo thông tin chia sẻ...
    ↓
Bot: ✅ Download & Upload Thành Công!
     📖 File: Oxford English Grammar Course.pdf
     📊 Size: 266.46 MB
     ☁️ Remote: discord:ZLibrary-Books/Oxford...pdf
     🔗 Link: https://drive.google.com/... (nếu có)
    ↓
Bot: 🗑️ [4/4] Đã xóa file tạm trên VPS
```

---

## 🔧 Troubleshooting

### **Lỗi: "rclone: command not found"**
```bash
curl https://rclone.org/install.sh | sudo bash
```

### **Lỗi: "Failed to create file system for discord:"**
```bash
# Kiểm tra config
rclone config show discord

# Re-connect
rclone config reconnect discord:
```

### **Lỗi: "Token expired"**
```bash
rclone config reconnect discord:
```

### **Bot chạy nhưng không upload được:**

Check logs:
```bash
tail -f logs/discord_bot.log

# Hoặc nếu dùng systemd
sudo journalctl -u discord-zlib-bot -f
```

Test manual upload:
```bash
echo "test" > test.txt
rclone copy test.txt discord:ZLibrary-Books/ -vv
```

---

## 📊 Monitoring

### **Xem files trên Drive:**

```bash
# List all files
rclone ls discord:ZLibrary-Books/

# List với details (size, date)
rclone lsl discord:ZLibrary-Books/

# Tree view
rclone tree discord:ZLibrary-Books/

# Check disk usage
rclone size discord:ZLibrary-Books/
```

### **Bot logs:**

```bash
# Real-time logs
tail -f logs/discord_bot.log

# Last 50 lines
tail -50 logs/discord_bot.log

# Search for errors
grep -i error logs/discord_bot.log
```

---

## 🚀 Production Setup

### **Chạy bot như systemd service:**

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
User=ditcotf
WorkingDirectory=/home/ditcotf/Auto-Book-Management
ExecStart=/usr/bin/python3 /home/ditcotf/Auto-Book-Management/discord_bot.py
Restart=always
RestartSec=10
Environment="PATH=/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=multi-user.target
```

Enable và start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable discord-zlib-bot
sudo systemctl start discord-zlib-bot

# Check status
sudo systemctl status discord-zlib-bot

# View logs
sudo journalctl -u discord-zlib-bot -f
```

---

## ✅ Final Checklist

- [x] Rclone installed: `rclone version`
- [x] Remote configured: `rclone lsd discord:`
- [x] Test folder created: `rclone mkdir discord:ZLibrary-Books`
- [ ] Discord Bot Token added to `discord_bot.py`
- [ ] Z-Library credentials in `config.yaml`
- [ ] Python packages installed: `pip3 install -r requirements.txt`
- [ ] Test download: `python3 test_discord_bot.py`
- [ ] Bot running: `python3 discord_bot.py`
- [ ] Bot invited to Discord server
- [ ] Test command: `!ping`
- [ ] Test download: `!download <url>`

---

## 🎉 You're Ready!

Bot setup hoàn tất với config:
- ✅ Rclone remote: `discord:`
- ✅ Upload folder: `ZLibrary-Books`
- ✅ Auto cleanup: `True`

Chỉ cần:
1. Thêm Discord Bot Token
2. Chạy bot
3. Test với `!download`

Happy downloading! 📚
