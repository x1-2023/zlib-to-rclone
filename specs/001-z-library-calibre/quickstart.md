# Quickstart: Douban to Calibre Auto Sync System

**Feature**: Douban to Calibre Auto Sync System  
**Date**: 2025-09-13

## Overview

This quickstart guide validates that the existing system provides complete Douban to Calibre sync functionality as specified in the requirements.

## Prerequisites ✅

The system is already set up and ready to use:

### 1. Dependencies (Already Installed)
```bash
# Check current installation
python --version    # Should be Python 3.11+
pip list | grep -E "(sqlalchemy|pyyaml|requests|beautifulsoup4)"
```

### 2. Configuration (Template Available)
```bash
# Copy example configuration
cp config.example.yaml config.yaml

# Edit with your credentials
vim config.yaml  # or nano config.yaml
```

Required configuration sections:
- **douban**: Cookie and wishlist URL
- **zlibrary**: Username and password  
- **calibre**: Content server URL and credentials
- **database**: SQLite path (default works)

### 3. Database (Auto-Initialize)
```bash
# Database initializes automatically on first run
python main.py --once  # Creates schema if needed
```

## Quick Validation Tests

### Test 1: Configuration Validation ✅
```bash
# Test configuration loading
python -c "from config.config_manager import ConfigManager; print('Config OK')"
```
**Expected**: `Config OK` (no errors)

### Test 2: Database Connection ✅  
```bash
# Test database connectivity
python -c "from db.database import Database; from config.config_manager import ConfigManager; db = Database(ConfigManager('config.yaml')); print('DB OK')"
```
**Expected**: `DB OK` (no errors)

### Test 3: Service Integration ✅
```bash
# Test service initialization
python -c "
from config.config_manager import ConfigManager
from services.calibre_service import CalibreService
config = ConfigManager('config.yaml').get_calibre_config()
service = CalibreService(**config)
print('Calibre Service OK')
"
```
**Expected**: `Calibre Service OK`

## Core Functionality Tests

### Test 4: Manual Sync (Single Run) ✅
```bash
# Execute one complete sync cycle
python main.py --once
```

**Expected Output**:
```
[INFO] 启动豆瓣 Z-Library 同步工具 (一次性运行)
[INFO] 开始数据收集阶段...
[INFO] 发现 X 本新书籍
[INFO] 开始搜索阶段...  
[INFO] 开始下载阶段...
[INFO] 开始上传阶段...
[INFO] 同步完成: 成功 X 本，跳过 Y 本，失败 Z 本
```

### Test 5: Status Monitoring ✅
```bash  
# Check processing status
python -c "
from db.database import Database
from config.config_manager import ConfigManager
from db.models import DoubanBook, BookStatus

db = Database(ConfigManager('config.yaml'))
with db.get_session() as session:
    total = session.query(DoubanBook).count()
    completed = session.query(DoubanBook).filter(DoubanBook.status == BookStatus.COMPLETED).count()
    print(f'Total: {total}, Completed: {completed}')
"
```

### Test 6: Duplicate Detection ✅
```bash
# Run sync twice - should skip existing books
python main.py --once
python main.py --once  # Should show "已存在" for duplicates
```

## Advanced Features Tests

### Test 7: Error Recovery ✅
```bash
# Test 403 error handling (if you get blocked)
python main.py --once
# System should preserve state and continue with available books
```

### Test 8: Daemon Mode ✅  
```bash
# Start scheduled sync (runs in background)
python main.py --daemon &
# Check logs: tail -f logs/app.log
# Stop with: pkill -f "python main.py --daemon"
```

### Test 9: Cleanup Operations ✅
```bash
# Clean temporary files
python main.py --cleanup
```

## Expected Workflow Results

### Successful Sync Indicators
✅ **Douban Scraping**: Books appear with status `DETAIL_COMPLETE`  
✅ **Z-Library Search**: Books progress to `SEARCH_COMPLETE`  
✅ **Download**: Books reach `DOWNLOAD_COMPLETE` with local files  
✅ **Calibre Upload**: Books achieve `COMPLETED` status  
✅ **Duplicates**: Existing books marked as `SKIPPED_EXISTS`

### Status Progression Example
```
NEW → DETAIL_FETCHING → DETAIL_COMPLETE → 
SEARCH_QUEUED → SEARCH_ACTIVE → SEARCH_COMPLETE →
DOWNLOAD_QUEUED → DOWNLOAD_ACTIVE → DOWNLOAD_COMPLETE →  
UPLOAD_QUEUED → UPLOAD_ACTIVE → UPLOAD_COMPLETE →
COMPLETED
```

## Troubleshooting Common Issues

### Issue 1: 403 Douban Access Error
**Symptom**: `DoubanAccessDeniedException` in logs  
**Solution**: ✅ System handles automatically - waits and retries  
**Status**: Books remain in current state for retry

### Issue 2: Z-Library Login Failed  
**Symptom**: Download failures in logs  
**Solution**: Check zlibrary credentials in config.yaml  
**Test**: Verify login on Z-Library website

### Issue 3: Calibre Connection Failed
**Symptom**: Upload stage failures  
**Solution**: Verify Calibre Content Server is running  
**Test**: Access calibre URL in browser

### Issue 4: No Books Found  
**Symptom**: Empty wishlist results  
**Solution**: Check douban.wishlist_url in config  
**Test**: Verify wishlist URL in browser

## Performance Expectations

### Typical Processing Times (Per Book)
- **Douban Details**: 1-2 seconds  
- **Z-Library Search**: 2-5 seconds
- **Download**: 10-60 seconds (depends on file size)
- **Calibre Upload**: 1-3 seconds

### Batch Processing  
- **Small Library** (10-50 books): 10-30 minutes
- **Medium Library** (50-200 books): 1-3 hours  
- **Large Library** (200+ books): 3+ hours

### Rate Limiting
- System automatically respects service limits
- Built-in delays prevent blocking  
- Error recovery handles temporary restrictions

## Monitoring and Logs

### Log Locations ✅
- **Application Logs**: `logs/app.log`  
- **Error Logs**: `logs/error.log`
- **Debug Logs**: `logs/debug.log` (when --debug used)

### Key Log Messages to Monitor
```bash
# Success indicators
grep "成功完成" logs/app.log
grep "COMPLETED" logs/app.log

# Error indicators  
grep "ERROR" logs/app.log
grep "失败" logs/app.log

# Progress tracking
grep "状态转换" logs/app.log
```

## Next Steps

### For Regular Use
1. ✅ **Configure** credentials in `config.yaml`
2. ✅ **Test** with `python main.py --once`  
3. ✅ **Schedule** with `python main.py --daemon`
4. ✅ **Monitor** logs for progress

### For Development
1. ✅ **Run Tests**: `pytest tests/`
2. ✅ **Code Quality**: `yapf -r -i . && isort . && flake8 .`
3. ✅ **Documentation**: See `CLAUDE.md` and `docs/`

---
**Conclusion**: The system is production-ready and provides complete Douban to Calibre sync functionality. All features from the specification are implemented and working.