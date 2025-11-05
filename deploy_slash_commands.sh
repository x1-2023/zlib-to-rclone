#!/bin/bash

# ===========================================
# DISCORD BOT SLASH COMMANDS - QUICK DEPLOY
# ===========================================

echo "🚀 DISCORD BOT SLASH COMMANDS - DEPLOY CHECKLIST"
echo "=================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check Python
echo "1️⃣ Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python installed: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Step 2: Check discord.py
echo ""
echo "2️⃣ Checking discord.py..."
if python3 -c "import discord; print(f'discord.py version: {discord.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✅ discord.py installed${NC}"
else
    echo -e "${RED}❌ discord.py not found${NC}"
    echo "   Install with: pip install discord.py"
    exit 1
fi

# Step 3: Check zlibrary
echo ""
echo "3️⃣ Checking zlibrary..."
if python3 -c "import zlibrary" 2>/dev/null; then
    echo -e "${GREEN}✅ zlibrary installed${NC}"
else
    echo -e "${RED}❌ zlibrary not found${NC}"
    echo "   Install with: pip install zlibrary"
    exit 1
fi

# Step 4: Check Rclone
echo ""
echo "4️⃣ Checking Rclone..."
if command -v rclone &> /dev/null; then
    RCLONE_VERSION=$(rclone version | head -n1)
    echo -e "${GREEN}✅ Rclone installed: $RCLONE_VERSION${NC}"
    
    # Check discord: remote
    if rclone listremotes | grep -q "discord:"; then
        echo -e "${GREEN}✅ Rclone remote 'discord:' found${NC}"
    else
        echo -e "${RED}❌ Rclone remote 'discord:' not found${NC}"
        echo "   Configure with: rclone config"
        exit 1
    fi
else
    echo -e "${RED}❌ Rclone not found${NC}"
    echo "   Install from: https://rclone.org/downloads/"
    exit 1
fi

# Step 5: Check config.yaml
echo ""
echo "5️⃣ Checking config.yaml..."
if [ -f "config.yaml" ]; then
    echo -e "${GREEN}✅ config.yaml found${NC}"
    
    # Check Z-Library credentials
    if grep -q "username:" config.yaml && grep -q "password:" config.yaml; then
        echo -e "${GREEN}✅ Z-Library credentials configured${NC}"
    else
        echo -e "${RED}❌ Z-Library credentials missing in config.yaml${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ config.yaml not found${NC}"
    echo "   Copy from: cp config.example.yaml config.yaml"
    exit 1
fi

# Step 6: Check Discord Bot Token
echo ""
echo "6️⃣ Checking Discord Bot Token..."
if grep -q "YOUR_DISCORD_BOT_TOKEN" discord_bot.py; then
    echo -e "${RED}❌ Discord Bot Token not configured${NC}"
    echo "   Please edit discord_bot.py line 30"
    echo "   Get token from: https://discord.com/developers/applications"
    exit 1
else
    echo -e "${GREEN}✅ Discord Bot Token configured${NC}"
fi

# Step 7: Check downloads directory
echo ""
echo "7️⃣ Checking downloads directory..."
if [ -d "downloads" ]; then
    echo -e "${GREEN}✅ downloads/ directory exists${NC}"
else
    echo -e "${YELLOW}⚠️  downloads/ directory not found. Creating...${NC}"
    mkdir -p downloads
    echo -e "${GREEN}✅ Created downloads/ directory${NC}"
fi

# Final Summary
echo ""
echo "=================================================="
echo "✅ ALL CHECKS PASSED!"
echo "=================================================="
echo ""
echo "🎯 Next Steps:"
echo "1. Upload code to VPS:"
echo "   scp -r discord_bot.py config.yaml ditcotf@india-nebulai:/path/to/project/"
echo ""
echo "2. SSH to VPS and run:"
echo "   python3 discord_bot.py"
echo ""
echo "3. Or use screen for background:"
echo "   screen -S discord_bot"
echo "   python3 discord_bot.py"
echo "   # Press Ctrl+A+D to detach"
echo ""
echo "4. Test slash commands in Discord:"
echo "   /ping"
echo "   /download https://z-library.ec/book/11948830/2c2f55"
echo ""
echo "📚 Read full guide: SLASH_COMMANDS_GUIDE.md"
echo ""
