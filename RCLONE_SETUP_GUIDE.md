# 📘 HƯỚNG DẪN SETUP RCLONE CHI TIẾT (Tiếng Việt)

## 🎯 Mục tiêu
Cài đặt Rclone và kết nối với Google Drive để upload/download files từ VPS

---

## 📦 PHẦN 1: CÀI ĐẶT RCLONE

### **Trên Linux/VPS (Ubuntu/Debian):**

```bash
# Cách 1: Script tự động (Khuyên dùng)
curl https://rclone.org/install.sh | sudo bash

# Cách 2: Manual download
cd ~
wget https://downloads.rclone.org/rclone-current-linux-amd64.zip
unzip rclone-current-linux-amd64.zip
cd rclone-*-linux-amd64
sudo cp rclone /usr/bin/
sudo chown root:root /usr/bin/rclone
sudo chmod 755 /usr/bin/rclone
```

### **Trên Windows:**

```powershell
# Cách 1: Dùng Chocolatey
choco install rclone

# Cách 2: Download manual
# 1. Vào: https://rclone.org/downloads/
# 2. Download Windows version
# 3. Giải nén vào C:\Program Files\rclone\
# 4. Thêm vào PATH (System Environment Variables)
```

### **Kiểm tra cài đặt:**

```bash
rclone version
# Nếu hiện version là OK!
```

---

## 🔧 PHẦN 2: CẤU HÌNH RCLONE VỚI GOOGLE DRIVE

### **Bước 1: Bắt đầu config**

```bash
rclone config
```

Bạn sẽ thấy menu:

```
No remotes found, make a new one?
n) New remote
s) Set configuration password
q) Quit config
n/s/q>
```

**→ Gõ `n` và Enter** (tạo remote mới)

---

### **Bước 2: Đặt tên remote**

```
Enter name for new remote.
name>
```

**→ Gõ `gdrive` và Enter** (hoặc tên bạn thích, ví dụ: `mydrive`, `googledrive`)

---

### **Bước 3: Chọn loại storage**

```
Option Storage.
Type of storage to configure.
Choose a number from below, or type in your own value.
...
18 / Google Drive
   \ (drive)
...
Storage>
```

**→ Gõ `drive` và Enter** (hoặc số `18` tùy phiên bản)

---

### **Bước 4: Google Application Client ID (Optional)**

```
Option client_id.
Google Application Client Id
Setting your own is recommended.
See https://rclone.org/drive/#making-your-own-client-id for how to create your own.
If you leave this blank, it will use an internal key which is low performance.
Enter a value. Press Enter to leave empty.
client_id>
```

**→ Nhấn Enter** (bỏ qua, dùng default key của rclone)

*Lưu ý: Nếu bạn muốn hiệu suất tốt hơn, xem phần "Tạo OAuth Client ID" ở dưới*

---

### **Bước 5: Google Application Client Secret (Optional)**

```
Option client_secret.
OAuth Client Secret.
Leave blank normally.
Enter a value. Press Enter to leave empty.
client_secret>
```

**→ Nhấn Enter** (bỏ qua)

---

### **Bước 6: Chọn scope (quyền truy cập)**

```
Option scope.
Scope that rclone should use when requesting access from drive.
Choose a number from below, or type in your own string value.
Press Enter for the default (drive).
 1 / Full access all files, excluding Application Data Folder.
   \ (drive)
 2 / Read-only access to file metadata and file contents.
   \ (drive.readonly)
...
scope>
```

**→ Gõ `1` và Enter** (Full access - cần thiết để upload/download/delete)

---

### **Bước 7: Root folder ID (Optional)**

```
Option root_folder_id.
ID of the root folder.
Leave blank normally.
Fill in to access "Computers" folders (see docs), or for rclone to use
a non root folder as its starting point.
Enter a string value. Press Enter for the default ("").
root_folder_id>
```

**→ Nhấn Enter** (bỏ qua, dùng root folder)

---

### **Bước 8: Service Account Credentials (Optional)**

```
Option service_account_file.
Service Account Credentials JSON file path.
Leave blank normally.
Needed only if you want use SA instead of interactive login.
Leading `~` will be expanded in the file name as will environment variables such as `${RCLONE_CONFIG_DIR}`.
Enter a string value. Press Enter for the default ("").
service_account_file>
```

**→ Nhấn Enter** (bỏ qua)

---

### **Bước 9: Advanced config**

```
Edit advanced config?
y) Yes
n) No (default)
y/n>
```

**→ Gõ `n` và Enter** (không cần config nâng cao)

---

### **Bước 10: Auto config (QUAN TRỌNG)**

```
Use auto config?
 * Say Y if not sure
 * Say N if you are working on a remote or headless machine

y) Yes (default)
n) No
y/n>
```

#### **A. Nếu bạn đang setup trên máy local (có GUI/Browser):**

**→ Gõ `y` và Enter**

- Browser sẽ tự động mở
- Đăng nhập Google Account
- Cho phép Rclone truy cập Drive
- Xong quay lại terminal

#### **B. Nếu bạn đang setup trên VPS (không có GUI):**

**→ Gõ `n` và Enter**

Rclone sẽ hiện:

```
For this to work, you will need rclone available on a machine that has
a web browser available.

For more help and alternate methods see: https://rclone.org/remote_setup/

Execute the following on the machine with the web browser (same rclone
version recommended):

    rclone authorize "drive" "eyJzY29wZSI6ImRyaXZlIn0"

Then paste the result.
Enter a value.
config_token>
```

**→ Làm theo hướng dẫn:**

1. **Trên máy local (Windows/Mac) có Browser**, mở Terminal/CMD:
   ```bash
   # Copy đúng lệnh mà VPS hiện ra, ví dụ:
   rclone authorize "drive" "eyJzY29wZSI6ImRyaXZlIn0"
   ```

2. Browser sẽ mở, đăng nhập Google và cho phép

3. Terminal sẽ hiện token dạng:
   ```json
   {"access_token":"ya29.xxx...","token_type":"Bearer","refresh_token":"1//xxx...","expiry":"2024-11-05T..."}
   ```

4. **Copy toàn bộ đoạn JSON đó**

5. **Quay lại VPS Terminal**, paste vào và Enter

---

### **Bước 11: Configure as Shared Drive (Team Drive)?**

```
Configure this as a Shared Drive (Team Drive)?

y) Yes
n) No (default)
y/n>
```

**→ Gõ `n` và Enter** (trừ khi bạn dùng Google Workspace Team Drive)

---

### **Bước 12: Xác nhận config**

```
Configuration complete.
Options:
- type: drive
- scope: drive
- token: {"access_token":"xxx"...}
- team_drive: 
Keep this "gdrive" remote?
y) Yes this is OK (default)
e) Edit this remote
d) Delete this remote
y/e/d>
```

**→ Gõ `y` và Enter** (xác nhận)

---

### **Bước 13: Thoát config**

```
Current remotes:

Name                 Type
====                 ====
gdrive               drive

e) Edit existing remote
n) New remote
d) Delete remote
r) Rename remote
c) Copy remote
s) Set configuration password
q) Quit config
e/n/d/r/c/s/q>
```

**→ Gõ `q` và Enter** (thoát)

---

## ✅ PHẦN 3: TEST RCLONE

### **Test 1: List folders/files**

```bash
rclone lsd gdrive:
# Hiện danh sách folders trong Google Drive root

rclone ls gdrive:
# Hiện danh sách tất cả files
```

### **Test 2: Tạo folder test**

```bash
rclone mkdir gdrive:TestFolder
```

Vào Google Drive web kiểm tra có folder `TestFolder` không.

### **Test 3: Upload file test**

```bash
# Tạo file test
echo "Hello Rclone!" > test.txt

# Upload lên Drive
rclone copy test.txt gdrive:TestFolder/

# Kiểm tra
rclone ls gdrive:TestFolder/
```

### **Test 4: Download file**

```bash
rclone copy gdrive:TestFolder/test.txt ./downloaded/
cat downloaded/test.txt
```

### **Test 5: Tạo public link**

```bash
rclone link gdrive:TestFolder/test.txt
# Nếu hiện link là OK!
# Nếu lỗi "not supported", xem phần troubleshooting
```

---

## 🚀 PHẦN 4: SỬ DỤNG VỚI DISCORD BOT

Sau khi setup xong, sửa file `discord_bot.py`:

```python
# Dòng 26
RCLONE_REMOTE = "gdrive"  # ← Đổi thành tên remote bạn đặt
RCLONE_FOLDER = "ZLibrary-Books"  # ← Folder sẽ lưu sách
```

Test bot:
```bash
python3 discord_bot.py
```

Trên Discord:
```
!download https://z-library.se/dl/12345/abcdef
```

---

## 🔥 PHẦN 5: LỆNH RCLONE HỮU ÍCH

### **Upload file/folder:**
```bash
# Upload 1 file
rclone copy /path/to/file.pdf gdrive:MyFolder/

# Upload cả folder
rclone copy /path/to/folder/ gdrive:MyFolder/ --progress

# Upload với báo progress real-time
rclone copy /path/to/file gdrive:/ --progress --stats 1s
```

### **Download:**
```bash
# Download 1 file
rclone copy gdrive:MyFolder/file.pdf ./downloads/

# Download cả folder
rclone copy gdrive:MyFolder/ ./downloads/ --progress
```

### **Sync (2 chiều):**
```bash
# Sync local → remote
rclone sync /local/folder/ gdrive:RemoteFolder/

# Sync remote → local
rclone sync gdrive:RemoteFolder/ /local/folder/
```

### **List files:**
```bash
# List folders only
rclone lsd gdrive:

# List files với size
rclone ls gdrive:MyFolder/

# List files với details
rclone lsl gdrive:MyFolder/

# Tree view
rclone tree gdrive:MyFolder/
```

### **Delete:**
```bash
# Xóa file
rclone delete gdrive:MyFolder/file.pdf

# Xóa folder (và nội dung)
rclone purge gdrive:MyFolder/

# Xóa files rỗng
rclone rmdirs gdrive: --leave-root
```

### **Public link:**
```bash
rclone link gdrive:path/to/file.pdf
```

### **Mount Drive như ổ đĩa (Linux):**
```bash
# Cài fuse
sudo apt install fuse -y

# Mount
mkdir ~/gdrive-mount
rclone mount gdrive: ~/gdrive-mount --daemon

# Unmount
fusermount -u ~/gdrive-mount
```

---

## 🛠️ PHẦN 6: TROUBLESHOOTING

### **Lỗi: "command not found: rclone"**

```bash
# Kiểm tra rclone có tồn tại không
which rclone

# Nếu không có, cài lại
curl https://rclone.org/install.sh | sudo bash
```

### **Lỗi: "Failed to create file system: couldn't find root directory"**

```bash
# Config lại remote
rclone config reconnect gdrive:
```

### **Lỗi: "Token expired"**

```bash
# Re-authenticate
rclone config reconnect gdrive:
```

### **Lỗi: "rclone link not supported"**

Google Drive API cần được enable:

1. Vào: https://console.cloud.google.com/
2. Enable Google Drive API
3. Tạo OAuth 2.0 credentials
4. Re-config rclone với client_id/secret mới

**Hoặc dùng cách khác tạo link:**

```bash
# Upload và lấy file ID
FILE_ID=$(rclone lsjson gdrive:path/to/file.pdf | jq -r '.[0].ID')

# Tạo link manual
echo "https://drive.google.com/file/d/$FILE_ID/view?usp=sharing"
```

### **Lỗi: "403 Rate Limit Exceeded"**

Tạo OAuth Client ID riêng (xem phần dưới).

---

## 🔐 PHẦN 7: TẠO OAUTH CLIENT ID RIÊNG (OPTIONAL - Nâng cao)

### **Tại sao cần:**
- Default rclone key bị giới hạn rate limit chung
- Tạo key riêng = unlimited (free tier: 1 tỷ requests/ngày)

### **Các bước:**

1. **Vào Google Cloud Console:**
   - https://console.cloud.google.com/

2. **Tạo project mới:**
   - "New Project" → đặt tên (vd: "Rclone-Project")

3. **Enable Google Drive API:**
   - "APIs & Services" → "Library"
   - Tìm "Google Drive API" → "Enable"

4. **Tạo OAuth consent screen:**
   - "APIs & Services" → "OAuth consent screen"
   - User Type: "External" → Create
   - App name: "My Rclone App"
   - User support email: your_email@gmail.com
   - Developer contact: your_email@gmail.com
   - Save and Continue (bỏ qua scopes)
   - Add test users: your_email@gmail.com
   - Save

5. **Tạo OAuth 2.0 credentials:**
   - "APIs & Services" → "Credentials"
   - "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "Rclone Desktop"
   - Create
   - **Copy Client ID và Client Secret**

6. **Re-config rclone với custom credentials:**

```bash
rclone config

# Chọn: e) Edit existing remote
# Chọn: gdrive
# Chọn: Edit this value: client_id
# Paste Client ID
# Chọn: Edit this value: client_secret
# Paste Client Secret
# y) Yes this is OK
```

7. **Re-authorize:**

```bash
rclone config reconnect gdrive:
```

Xong! Bây giờ bạn có unlimited quota.

---

## 📊 PHẦN 8: MONITORING & LOGS

### **Xem transfer progress:**
```bash
rclone copy file.pdf gdrive:/ --progress --stats 1s -v
```

### **Log vào file:**
```bash
rclone copy file.pdf gdrive:/ --log-file=rclone.log --log-level INFO
```

### **Bandwidth limit:**
```bash
# Giới hạn 10MB/s
rclone copy file.pdf gdrive:/ --bwlimit 10M
```

---

## 🎓 PHẦN 9: BEST PRACTICES

### **1. Dùng config file:**

Tạo file `~/.config/rclone/rclone.conf` (Linux) hoặc `%APPDATA%\rclone\rclone.conf` (Windows)

### **2. Backup config:**
```bash
# Backup
cp ~/.config/rclone/rclone.conf ~/rclone.conf.backup

# Restore
cp ~/rclone.conf.backup ~/.config/rclone/rclone.conf
```

### **3. Encrypt config:**
```bash
rclone config
# Chọn: s) Set configuration password
# Nhập password
```

### **4. Multiple remotes:**

Có thể có nhiều remotes:
- `gdrive1` - Google Drive account 1
- `gdrive2` - Google Drive account 2
- `dropbox` - Dropbox
- `onedrive` - OneDrive

```bash
rclone config
# n) New remote
# Lặp lại bước setup
```

---

## ✅ TÓM TẮT NHANH

```bash
# 1. Cài Rclone
curl https://rclone.org/install.sh | sudo bash

# 2. Config
rclone config
# n → gdrive → drive → Enter x4 → 1 → Enter x3 → n → y/n → n → y → q

# 3. Test
rclone lsd gdrive:

# 4. Upload
rclone copy file.pdf gdrive:MyFolder/

# 5. Dùng trong bot
# Sửa discord_bot.py: RCLONE_REMOTE = "gdrive"
```

---

**🎉 Xong! Giờ bạn đã setup xong Rclone với Google Drive!**

Có thắc mắc gì cứ hỏi nhé! 😊
