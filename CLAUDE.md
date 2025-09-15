# CLAUDE.md

- 所有log都写在logs目录下
- 非必要不写try
- 在完成任务后查看 `TODO.md` 补充后续任务，已完成的在文件中打勾

## Recent Changes (Last 3)
1. **2025-09-15**: ✅ COMPLETED All 27 tasks for quota-aware download skipping feature
2. **Full TDD Cycle**: 📋 Contract tests → 🧪 Integration tests → ⚡ Performance tests → 🔧 Implementation
3. **Production Ready**: QuotaManager, enhanced DownloadStage, Pipeline integration with complete test coverage

## Current System Status
- ✅ **Complete Pipeline**: 20-state workflow handles Douban → Z-Library → Calibre sync
- ✅ **Quota-Aware Processing**: Intelligent download skipping when Z-Library quota exhausted
- ✅ **Error Recovery**: Handles 403 errors, network issues, quota exhaustion, state persistence
- ✅ **Format Support**: epub, mobi, azw3, pdf with configurable priority
- ✅ **Scheduling**: Both `--once` and `--daemon` modes available
- ✅ **Duplicate Detection**: Calibre integration with match threshold
- ✅ **Production Ready**: Active use with comprehensive logging and monitoring

### Quota Management Features (COMPLETE ✅)
- 🎯 **QuotaManager**: Real-time Z-Library quota tracking with intelligent caching (5min cache)
- 🎯 **Smart Skipping**: Books skip download when quota=0, resume when quota recovers
- 🎯 **New Status**: `SEARCH_COMPLETE_QUOTA_EXHAUSTED` for quota-exhausted books
- 🎯 **Pipeline Integration**: Automatic quota checking and stage pause/resume (every 10 cycles)
- 🎯 **Recovery System**: Auto-resume processing when quota refreshes (24h cycle)
- 🎯 **Error Handling**: Graceful degradation when quota API fails
- 🎯 **Performance**: Sub-millisecond quota checks, minimal API calls
- 🎯 **Test Coverage**: Contract, integration, unit, and performance tests (23 + 18 + 4 tests)

### Usage Examples & Performance
```bash
# 查看系统状态（包含配额信息）
python main.py --status

# 运行一次同步（配额感知）
python main.py --once

# 运行契约测试验证功能
python -m pytest tests/contract/ -v

# 运行性能测试（缓存效率）
python -m pytest tests/performance/ -v
```

**Performance Metrics**:
- 📊 配额检查: <0.01ms/次 (缓存命中)
- 📊 100次连续检查: <50ms总耗时
- 📊 API缓存命中率: >95% (5分钟缓存)

## test
- 测试写在tests目录下，使用pytest风格
- 使用真实配置进行测试，不使用mock

# Common Development Commands

### Testing
- **Run all tests**: `python run_tests.py` or `pytest tests/`
- **Run unit tests only**: `python run_tests.py unit` or `pytest tests/unit/`
- **Run integration tests only**: `python run_tests.py integration` or `pytest tests/integration/`
- **Run with coverage**: `pytest --cov=. tests/`

### Code Quality
- **Format code**: `yapf -r -i .` (auto-format all Python files)
- **Sort imports**: `isort .` (organize import statements)
- **Lint code**: `flake8 .` (check code style and potential issues)
- **Type checking**: `mypy .` (static type analysis)

### Application
- **Run once**: `python main.py --once` (execute sync once and exit)
- **Run as daemon**: `python main.py --daemon` (run continuously with scheduler)
- **Setup project**: `python setup.py` (install dependencies and initialize database)
- **Clean temporary files**: `python main.py --cleanup`

### Database
- **Initialize database**: `python -c "from db.database import Database; db = Database('sqlite:///data/douban_books.db'); db.init_db()"`

## High-Level Architecture

This is a book synchronization automation tool that syncs books from Douban wishlist to Calibre library via Z-Library downloads.

### Core Workflow
1. **Douban Scraping**: Scrapes user's "想读" (wish to read) list from Douban using cookie authentication
2. **Database Storage**: Stores book metadata in SQLite database with status tracking
3. **Calibre Check**: Queries Calibre content server to avoid duplicate downloads
4. **Z-Library Download**: Searches and downloads books from Z-Library with format priority (epub > mobi > pdf)
5. **Calibre Upload**: Uploads downloaded books to Calibre library
6. **Notifications**: Sends status updates via Lark (Feishu) webhook
7. **Scheduling**: Runs automatically on configured schedule (daily/weekly/interval)

### Key Components V2 (Pipeline架构)

**Main Application V2** (`main_v2.py`):
- Pipeline架构的入口点和编排器
- 支持 `--once`, `--daemon` 模式
- 豆瓣403错误智能处理：保留当前状态并重试，继续处理已获取详情的书籍

**Core Pipeline System** (`core/`):
- `BookStateManager`: 统一状态管理，支持19种精细化状态和转换验证
- `TaskScheduler`: 优先级队列任务调度，支持重试和错误恢复  
- `PipelineManager`: 分阶段处理管理器，协调各个处理阶段
- `ErrorHandler`: 分类错误处理，支持可重试和永久失败区分

**Pipeline Stages** (`stages/`):
- `DataCollectionStage`: 豆瓣数据收集，支持403时保留状态并重试
- `SearchStage`: Z-Library搜索，自动状态转换和结果保存
- `DownloadStage`: 书籍文件下载，支持多格式和质量选择
- `UploadStage`: Calibre上传，自动去重和元数据同步

**Enhanced Data Models** (`db/models.py`):
- `DoubanBook`: 扩展的书籍实体，新增搜索字段
- `BookStatus`: 19种精细化状态枚举
- `BookStatusHistory`: 完整的状态变更历史跟踪
- `ProcessingTask`: 任务调度和执行记录
- `ZLibraryBook`: Z-Library搜索结果存储

**Services** (`services/`):
- `DoubanScraper`: 增强的豆瓣爬虫，支持403错误处理
- `ZLibraryService`: 重构的Z-Library服务，分离搜索和下载功能
- `CalibreService`: Calibre集成服务  
- `LarkService`: 飞书通知服务，支持实时状态通知

**Configuration & Utils**:
- `ConfigManager`: YAML配置管理，支持数据库和服务配置
- `Logger`: 结构化日志系统，支持文件和控制台输出
- Session管理：统一数据库会话工厂，避免并发冲突

### Book Status Workflow V2 (Pipeline架构)
V2版本采用Pipeline架构，支持19种精细化状态和完整的错误处理机制：

**数据收集阶段**:
- `NEW`: 豆瓣新发现的书籍
- `DETAIL_FETCHING`: 正在获取豆瓣详细信息  
- `DETAIL_COMPLETE`: 详细信息获取完成

**搜索阶段**:
- `SEARCH_QUEUED`: 排队等待Z-Library搜索
- `SEARCH_ACTIVE`: 正在搜索Z-Library
- `SEARCH_COMPLETE`: 搜索完成，找到匹配结果
- `SEARCH_NO_RESULTS`: 搜索完成，无匹配结果

**下载阶段**:
- `DOWNLOAD_QUEUED`: 排队等待下载
- `DOWNLOAD_ACTIVE`: 正在从Z-Library下载
- `DOWNLOAD_COMPLETE`: 下载完成
- `DOWNLOAD_FAILED`: 下载失败

**上传阶段**:
- `UPLOAD_QUEUED`: 排队等待上传到Calibre
- `UPLOAD_ACTIVE`: 正在上传到Calibre  
- `UPLOAD_COMPLETE`: 上传完成
- `UPLOAD_FAILED`: 上传失败

**终态**:
- `COMPLETED`: 整个流程成功完成
- `SKIPPED_EXISTS`: 在Calibre中已存在，跳过处理
- `FAILED_PERMANENT`: 永久失败，不再重试

**完整流程**: `NEW` → `DETAIL_FETCHING` → `DETAIL_COMPLETE` → `SEARCH_QUEUED` → `SEARCH_ACTIVE` → `SEARCH_COMPLETE` → `DOWNLOAD_QUEUED` → `DOWNLOAD_ACTIVE` → `DOWNLOAD_COMPLETE` → `UPLOAD_QUEUED` → `UPLOAD_ACTIVE` → `UPLOAD_COMPLETE` → `COMPLETED`

**豆瓣403特殊处理**: 当遇到豆瓣403错误时，系统保留当前书籍状态并稍后重试，同时继续处理已获取到详细信息的书籍进行Z-Library搜索，确保服务连续性。

**详细状态流程图**: 查看 `docs/book_status_flow_diagram.md` 了解完整的Mermaid流程图和状态转换规则。

### Configuration Structure
The `config.yaml` requires:
- `douban`: Cookie and user credentials for scraping
- `database`: SQLite path or PostgreSQL connection
- `calibre`: Content server URL and authentication
- `zlibrary`: Credentials and download preferences
- `schedule`: Timing configuration (daily/weekly/interval)
- `lark`: Optional webhook notifications

### Testing Structure
- `tests/unit/`: Component-level tests with mocking
- `tests/integration/`: End-to-end workflow tests
- Fixtures in `tests/unit/fixtures/` for HTML parsing tests
- Real network tests marked with `@pytest.mark.real_network`

### Key Dependencies
- `requests` + `beautifulsoup4`: Web scraping
- `sqlalchemy`: Database ORM with SQLite/PostgreSQL support
- `schedule`: Task scheduling
- `zlibrary`: Z-Library API client
- `pyyaml`: Configuration management
- `loguru`: Structured logging
- `pytest`: Testing framework with coverage and mocking

少用try
- 使用uv命令