#!/bin/bash
# Quick check script - Verify everything is ready

echo "=================================================="
echo "🔍 DISCORD BOT - PRE-FLIGHT CHECK"
echo "=================================================="
echo

# Check 1: Python
echo "1️⃣  Checking Python..."
if command -v python3 &> /dev/null; then
    python3 --version
    echo "   ✅ Python OK"
else
    echo "   ❌ Python not found"
    exit 1
fi
echo

# Check 2: Rclone
echo "2️⃣  Checking Rclone..."
if command -v rclone &> /dev/null; then
    rclone version | head -1
    echo "   ✅ Rclone OK"
else
    echo "   ❌ Rclone not found"
    echo "   Install: curl https://rclone.org/install.sh | sudo bash"
    exit 1
fi
echo

# Check 3: Rclone remote
echo "3️⃣  Checking Rclone remote 'discord'..."
if rclone listremotes | grep -q "discord:"; then
    echo "   ✅ Remote 'discord:' configured"
    echo "   Testing connection..."
    if rclone lsd discord: &> /dev/null; then
        echo "   ✅ Remote 'discord:' accessible"
    else
        echo "   ⚠️  Remote 'discord:' not accessible"
        echo "   Try: rclone config reconnect discord:"
    fi
else
    echo "   ❌ Remote 'discord:' not found"
    echo "   Run: rclone config"
fi
echo

# Check 4: Python packages
echo "4️⃣  Checking Python packages..."
PACKAGES=("requests" "beautifulsoup4" "zlibrary" "discord.py" "pyyaml")
ALL_OK=true

for pkg in "${PACKAGES[@]}"; do
    if python3 -c "import ${pkg//-/_}" 2>/dev/null; then
        echo "   ✅ $pkg"
    else
        echo "   ❌ $pkg not installed"
        ALL_OK=false
    fi
done

if [ "$ALL_OK" = false ]; then
    echo
    echo "   Install missing packages:"
    echo "   pip3 install -r requirements.txt"
fi
echo

# Check 5: Config file
echo "5️⃣  Checking config.yaml..."
if [ -f "config.yaml" ]; then
    echo "   ✅ config.yaml exists"
    
    # Check Z-Library credentials
    if grep -q "your_email@example.com" config.yaml; then
        echo "   ⚠️  Z-Library credentials not set (still using example)"
    else
        echo "   ✅ Z-Library credentials configured"
    fi
else
    echo "   ❌ config.yaml not found"
    echo "   Copy: cp config.example.yaml config.yaml"
fi
echo

# Check 6: Discord token
echo "6️⃣  Checking Discord Bot Token..."
if grep -q "YOUR_DISCORD_BOT_TOKEN" discord_bot.py; then
    echo "   ⚠️  Discord Token not set"
    echo "   Edit discord_bot.py line 25"
else
    echo "   ✅ Discord Token configured"
fi
echo

# Check 7: Rclone folder
echo "7️⃣  Checking Rclone folder..."
if rclone lsd discord:ZLibrary-Books &> /dev/null; then
    echo "   ✅ Folder 'ZLibrary-Books' exists"
else
    echo "   📁 Creating folder 'ZLibrary-Books'..."
    rclone mkdir discord:ZLibrary-Books
    echo "   ✅ Folder created"
fi
echo

# Check 8: Download directory
echo "8️⃣  Checking download directory..."
if [ -d "data/downloads/discord" ]; then
    echo "   ✅ Download directory exists"
else
    echo "   📁 Creating download directory..."
    mkdir -p data/downloads/discord
    echo "   ✅ Directory created"
fi
echo

# Check 9: Logs directory
echo "9️⃣  Checking logs directory..."
if [ -d "logs" ]; then
    echo "   ✅ Logs directory exists"
else
    echo "   📁 Creating logs directory..."
    mkdir -p logs
    echo "   ✅ Directory created"
fi
echo

echo "=================================================="
echo "📊 SUMMARY"
echo "=================================================="
echo

# Summary
READY=true

# Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not installed"
    READY=false
fi

# Rclone
if ! command -v rclone &> /dev/null; then
    echo "❌ Rclone not installed"
    READY=false
fi

# Rclone remote
if ! rclone listremotes | grep -q "discord:"; then
    echo "❌ Rclone remote 'discord:' not configured"
    READY=false
fi

# Config
if [ ! -f "config.yaml" ]; then
    echo "❌ config.yaml not found"
    READY=false
elif grep -q "your_email@example.com" config.yaml; then
    echo "⚠️  Z-Library credentials not set in config.yaml"
    READY=false
fi

# Discord token
if grep -q "YOUR_DISCORD_BOT_TOKEN" discord_bot.py; then
    echo "⚠️  Discord Bot Token not set in discord_bot.py"
    READY=false
fi

echo

if [ "$READY" = true ]; then
    echo "🎉 ALL CHECKS PASSED!"
    echo
    echo "You can now run the bot:"
    echo "  python3 discord_bot.py"
    echo
    echo "Or test components first:"
    echo "  python3 test_discord_bot.py"
else
    echo "⚠️  SOME CHECKS FAILED"
    echo
    echo "Please fix the issues above before running the bot."
    echo
    echo "Quick fixes:"
    echo "  1. Install Python: sudo apt install python3 python3-pip"
    echo "  2. Install Rclone: curl https://rclone.org/install.sh | sudo bash"
    echo "  3. Configure Rclone: rclone config"
    echo "  4. Install packages: pip3 install -r requirements.txt"
    echo "  5. Copy config: cp config.example.yaml config.yaml"
    echo "  6. Edit config.yaml with Z-Library credentials"
    echo "  7. Edit discord_bot.py with Discord Bot Token"
fi

echo
echo "=================================================="
