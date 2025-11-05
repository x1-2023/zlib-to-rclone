# 🎯 Discord Slash Commands - Hướng Dẫn Đầy Đủ

## 📋 Tổng Quan

Bot đã được nâng cấp để hỗ trợ **Slash Commands** (/) - chuẩn Discord hiện đại của năm 2025!

### ✨ Tính Năng Mới

- ✅ **Slash Commands** (/) - Giao diện hiện đại với autocomplete
- ✅ **Prefix Commands** (!) - Vẫn hoạt động để backward compatible
- ✅ **Auto-sync** - Commands tự động sync khi bot khởi động
- ✅ **Better UX** - Discord hiển thị gợi ý parameters ngay trong chat

---

## 🎮 Slash Commands (Khuyên Dùng)

### 1️⃣ `/download <url>`
Download sách từ Z-Library và upload lên Google Drive

**Cách dùng:**
```
/download https://z-library.ec/book/11948830/2c2f55
/download https://z-library.ec/dl/11948830/b88232
```

**Hỗ trợ domains:** `.ec`, `.se`, `.is`, `.sk`

**Output:**
- Progress messages: [1/4], [2/4], [3/4], [4/4]
- Download status
- Upload status
- Share link (nếu có)

---

### 2️⃣ `/quota`
Kiểm tra quota Z-Library còn lại

**Output:**
- Daily Limit: Số lượng download tối đa
- Remaining: Số lượng còn lại
- Next Reset: Thời gian reset quota

---

### 3️⃣ `/ping`
Kiểm tra bot có hoạt động không

**Output:**
```
🏓 Pong! Latency: 45ms
```

---

### 4️⃣ `/help`
Hiển thị hướng dẫn đầy đủ với embed đẹp

**Output:**
- Danh sách Slash Commands
- Danh sách Prefix Commands (legacy)
- Supported URLs
- Ví dụ sử dụng

---

## 🔧 Prefix Commands (Legacy - Vẫn Hoạt Động)

Để backward compatible, các prefix commands cũ vẫn hoạt động:

| Command | Slash Equivalent | Mô Tả |
|---------|-----------------|-------|
| `!download <url>` | `/download <url>` | Download sách |
| `!quota` | `/quota` | Check quota |
| `!ping` | `/ping` | Test bot |
| `!help_bot` | `/help` | Xem hướng dẫn |

**Lưu ý:** Prefix commands sẽ gợi ý dùng slash commands thay thế!

---

## 🚀 Setup & Deploy

### Bước 1: Kiểm Tra Code

File `discord_bot.py` đã được cập nhật với:

```python
# Bot config
bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None  # Custom help command
)

# On ready event
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
```

### Bước 2: Cấu Hình Discord Bot Token

1. Truy cập [Discord Developer Portal](https://discord.com/developers/applications)
2. Chọn bot của bạn
3. Vào tab **Bot**
4. Copy **Bot Token**
5. Sửa file `discord_bot.py` dòng 30:

```python
DISCORD_TOKEN = "YOUR_ACTUAL_BOT_TOKEN_HERE"
```

### Bước 3: Cấp Quyền Cho Bot

Bot cần các **intents** sau:

```python
intents = discord.Intents.default()
intents.message_content = True  # Đọc nội dung messages
intents.guilds = True            # Truy cập server info
intents.members = True           # Truy cập member info
```

**Cách bật intents:**

1. [Discord Developer Portal](https://discord.com/developers/applications)
2. Chọn bot → **Bot** tab
3. Scroll xuống **Privileged Gateway Intents**
4. Bật:
   - ✅ **MESSAGE CONTENT INTENT**
   - ✅ **SERVER MEMBERS INTENT**
   - ✅ **PRESENCE INTENT** (optional)
5. Nhấn **Save Changes**

### Bước 4: Invite Bot Vào Server

URL mời bot (thay `YOUR_CLIENT_ID`):

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=2147870720&scope=bot%20applications.commands
```

**Permissions:** `2147870720` bao gồm:
- Send Messages
- Embed Links
- Attach Files
- Read Message History
- Use Slash Commands

### Bước 5: Chạy Bot Trên VPS

```bash
# Upload code lên VPS
scp -r discord_bot.py ditcotf@india-nebulai:/path/to/project/

# SSH vào VPS
ssh ditcotf@india-nebulai

# Activate Python environment
cd /path/to/project
source venv/bin/activate  # Nếu dùng venv

# Chạy bot
python3 discord_bot.py
```

**Hoặc dùng screen để chạy background:**

```bash
screen -S discord_bot
python3 discord_bot.py
# Ctrl+A+D để detach
```

---

## 🧪 Testing

### Test Local (Không Cần Discord)

```bash
python3 test_discord_bot.py
```

### Test Slash Commands Trên Discord

1. Gõ `/` trong Discord
2. Chọn bot của bạn
3. Discord sẽ hiển thị danh sách commands
4. Chọn command và nhập parameters

**Ví dụ:**
```
/download https://z-library.ec/book/11948830/2c2f55
```

Discord sẽ autocomplete và hiển thị description của parameters!

---

## 🔍 Troubleshooting

### ❌ Slash Commands Không Hiện

**Nguyên nhân:** Commands chưa sync với Discord

**Giải pháp:**
1. Check bot logs khi khởi động:
   ```
   ✅ Synced 4 slash command(s)
   ```
2. Nếu lỗi, restart bot
3. Đợi vài phút (Discord có thể cache)
4. Kick bot ra server → Mời lại với URL mới có `applications.commands` scope

### ❌ Bot Không Response

**Nguyên nhân:** Message Content Intent chưa bật

**Giải pháp:**
1. [Discord Developer Portal](https://discord.com/developers/applications)
2. Bot → Privileged Gateway Intents
3. Bật **MESSAGE CONTENT INTENT**
4. Restart bot

### ❌ "This interaction failed"

**Nguyên nhân:** Bot mất quá 3 giây để response

**Giải pháp:** Code đã có `await interaction.response.defer()` để extend timeout lên 15 phút

### ❌ Commands Bị Duplicate

**Nguyên nhân:** Bot đang chạy nhiều instances

**Giải pháp:**
```bash
# Check processes
ps aux | grep discord_bot.py

# Kill duplicate processes
kill <PID>
```

---

## 📊 So Sánh: Slash vs Prefix

| Feature | Slash Commands | Prefix Commands |
|---------|---------------|-----------------|
| **Autocomplete** | ✅ Yes | ❌ No |
| **Parameter Hints** | ✅ Yes | ❌ No |
| **Modern** | ✅ 2025 Standard | ⚠️ Legacy |
| **User Experience** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Discord Native** | ✅ Yes | ❌ No |
| **Permissions** | Fine-grained | Basic |

---

## 🎨 Code Architecture

### Helper Function Pattern

```python
async def process_download_request(interaction_or_ctx, url: str, is_slash: bool = False):
    """
    Helper function xử lý download request
    Dùng chung cho cả slash command và prefix command
    """
    # Handle both interaction (slash) and context (prefix)
    if is_slash:
        author = interaction_or_ctx.user
        await interaction_or_ctx.response.defer()  # Extend timeout
    else:
        author = interaction_or_ctx.author
        status_msg = await interaction_or_ctx.send("⏳ Processing...")
    
    # ... shared logic ...
```

### Command Registration

**Slash command:**
```python
@bot.tree.command(name="download", description="📥 Download sách từ Z-Library")
async def slash_download(interaction: discord.Interaction, url: str):
    await process_download_request(interaction, url, is_slash=True)
```

**Prefix command:**
```python
@bot.command(name='download', help='Download sách từ Z-Library')
async def download_command(ctx, url: str = None):
    if not url:
        await ctx.send("❌ Vui lòng cung cấp URL!")
        return
    await process_download_request(ctx, url, is_slash=False)
```

---

## 🔐 Security

### Environment Variables (Khuyên Dùng)

Thay vì hard-code token, dùng environment variable:

```python
import os

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'YOUR_DISCORD_BOT_TOKEN')
```

**Setup:**
```bash
# Linux/Mac
export DISCORD_BOT_TOKEN="your_token_here"

# Windows PowerShell
$env:DISCORD_BOT_TOKEN="your_token_here"
```

### .env File

```bash
# Install python-dotenv
pip install python-dotenv

# Create .env file
echo "DISCORD_BOT_TOKEN=your_token_here" > .env

# Load in code
from dotenv import load_dotenv
load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
```

**⚠️ Lưu ý:** Thêm `.env` vào `.gitignore`!

---

## 📚 Resources

### Official Documentation

- [Discord.py Commands](https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html)
- [Discord.py App Commands](https://discordpy.readthedocs.io/en/stable/interactions/api.html)
- [Discord Developer Portal](https://discord.com/developers/docs)

### Example URLs

**Test URLs (Z-Library):**
```
https://z-library.ec/book/11948830/2c2f55
https://z-library.ec/dl/11948830/b88232
https://z-library.se/book/1234567/abcdef
https://z-library.is/book/7654321/fedcba
```

---

## ✅ Checklist Deploy

- [ ] Discord Bot Token đã cấu hình
- [ ] Message Content Intent đã bật
- [ ] Bot đã được mời với `applications.commands` scope
- [ ] Rclone remote "discord:" đã setup
- [ ] Z-Library credentials đã cấu hình trong `config.yaml`
- [ ] Dependencies đã install (`pip install discord.py zlibrary beautifulsoup4`)
- [ ] Test `/ping` command thành công
- [ ] Test `/download` với 1 URL thành công
- [ ] Rclone upload thành công
- [ ] Public link hoạt động

---

## 🎉 Kết Luận

Bot đã sẵn sàng cho production với:

✅ Modern Slash Commands UI  
✅ Backward compatible Prefix Commands  
✅ Auto-sync commands  
✅ Better error handling  
✅ Extended timeout (15 phút)  
✅ Clean code architecture  

**Happy downloading! 📚🚀**
