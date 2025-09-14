# API参考文档

本文档详细描述了系统各个核心组件的API接口和使用方法。

## 目录

- [状态管理API](#状态管理api)
- [任务调度API](#任务调度api)
- [数据服务API](#数据服务api)
- [Pipeline管理API](#pipeline管理api)
- [错误处理API](#错误处理api)
- [配置管理API](#配置管理api)

---

## 状态管理API

### BookStateManager

书籍状态管理器，负责统一管理书籍的生命周期状态。

#### 初始化

```python
from core.state_manager import BookStateManager

state_manager = BookStateManager(
    session_factory=database.session_factory,
    lark_service=lark_service,  # 可选
    task_scheduler=scheduler    # 可选
)
```

#### 主要方法

##### transition_status()

转换书籍状态。

```python
def transition_status(
    self,
    book_id: int,
    to_status: BookStatus,
    change_reason: str,
    error_message: Optional[str] = None,
    processing_time: Optional[float] = None,
    retry_count: Optional[int] = None
) -> bool
```

**参数:**
- `book_id`: 书籍ID
- `to_status`: 目标状态
- `change_reason`: 状态变更原因
- `error_message`: 错误信息（可选）
- `processing_time`: 处理时间（可选）
- `retry_count`: 重试次数（可选）

**返回:** 转换是否成功

**示例:**
```python
success = state_manager.transition_status(
    book_id=123,
    to_status=BookStatus.SEARCH_QUEUED,
    change_reason="详情获取完成，开始搜索"
)
```

##### get_book_status()

获取书籍当前状态。

```python
def get_book_status(self, book_id: int) -> Optional[BookStatus]
```

**示例:**
```python
current_status = state_manager.get_book_status(123)
print(f"当前状态: {current_status.value}")
```

##### is_valid_transition()

验证状态转换的合法性。

```python
def is_valid_transition(
    self, 
    from_status: BookStatus, 
    to_status: BookStatus
) -> bool
```

##### get_status_history()

获取书籍状态历史。

```python
def get_status_history(
    self, 
    book_id: int, 
    limit: int = 10
) -> List[BookStatusHistory]
```

---

## 任务调度API

### TaskScheduler

基于优先级队列的任务调度器。

#### 初始化

```python
from core.task_scheduler import TaskScheduler

scheduler = TaskScheduler(
    database=database,
    max_concurrent_tasks=5,
    default_priority=10
)
```

#### 主要方法

##### schedule_task()

调度新任务。

```python
def schedule_task(
    self,
    book_id: int,
    stage: str,
    priority: int = 10,
    delay_seconds: int = 0,
    max_retries: int = 3
) -> bool
```

**参数:**
- `book_id`: 书籍ID
- `stage`: 处理阶段 ('data_collection', 'search', 'download', 'upload')
- `priority`: 优先级 (数值越小优先级越高)
- `delay_seconds`: 延迟执行时间
- `max_retries`: 最大重试次数

**示例:**
```python
scheduler.schedule_task(
    book_id=123,
    stage='search',
    priority=5,
    delay_seconds=30
)
```

##### get_next_task()

获取下一个待执行任务。

```python
def get_next_task(self) -> Optional[ProcessingTask]
```

##### complete_task()

标记任务完成。

```python
def complete_task(
    self,
    task_id: int,
    success: bool,
    result_message: str = None
) -> bool
```

##### get_pending_tasks_count()

获取待处理任务数量。

```python
def get_pending_tasks_count(self, stage: str = None) -> int
```

---

## 数据服务API

### DoubanScraper

豆瓣网站爬虫服务。

#### 初始化

```python
from services.douban_scraper import DoubanScraper

scraper = DoubanScraper(
    cookie='your_douban_cookie',
    user_id='12345678'
)
```

#### 主要方法

##### get_wishlist_books()

获取想读书单。

```python
def get_wishlist_books(self) -> List[Dict[str, Any]]
```

**返回:** 书籍信息列表

**示例:**
```python
books = scraper.get_wishlist_books()
for book in books:
    print(f"书名: {book['title']}, 作者: {book['author']}")
```

##### get_book_detail()

获取书籍详细信息。

```python
def get_book_detail(self, douban_id: str) -> Dict[str, Any]
```

**参数:**
- `douban_id`: 豆瓣书籍ID

**返回:** 详细书籍信息

---

### ZLibraryService

Z-Library书籍搜索和下载服务。

#### 初始化

```python
from services.zlibrary_service import ZLibraryService

zlib_service = ZLibraryService(
    email='your_email',
    password='your_password',
    download_dir='./downloads',
    format_priority=['epub', 'mobi', 'pdf']
)
```

#### 主要方法

##### search_books()

搜索书籍。

```python
def search_books(
    self,
    title: str,
    author: str = None,
    max_results: int = 10
) -> List[Dict[str, Any]]
```

**参数:**
- `title`: 书名
- `author`: 作者（可选）
- `max_results`: 最大结果数量

**返回:** 搜索结果列表

**示例:**
```python
results = zlib_service.search_books(
    title="Python Programming",
    author="John Doe",
    max_results=5
)
```

##### download_book()

下载书籍文件。

```python
def download_book(
    self,
    book_info: Dict[str, Any],
    target_dir: str = None
) -> Optional[str]
```

**参数:**
- `book_info`: 书籍信息字典
- `target_dir`: 目标下载目录

**返回:** 下载文件路径

---

### CalibreService

Calibre书库管理服务。

#### 初始化

```python
from services.calibre_service import CalibreService

calibre_service = CalibreService(
    server_url='http://localhost:8080',
    username='admin',
    password='password',
    match_threshold=0.6
)
```

#### 主要方法

##### search_book()

在Calibre库中搜索书籍。

```python
def search_book(
    self,
    title: str,
    author: str = None
) -> Optional[Dict[str, Any]]
```

**参数:**
- `title`: 书名
- `author`: 作者（可选）

**返回:** 找到的书籍信息，未找到返回None

##### add_book()

添加书籍到Calibre库。

```python
def add_book(
    self,
    file_path: str,
    metadata: Dict[str, Any] = None
) -> Optional[int]
```

**参数:**
- `file_path`: 书籍文件路径
- `metadata`: 元数据信息

**返回:** 书籍在Calibre库中的ID

**示例:**
```python
book_id = calibre_service.add_book(
    file_path='/path/to/book.epub',
    metadata={
        'title': 'Book Title',
        'authors': ['Author Name'],
        'isbn': '1234567890123'
    }
)
```

---

## Pipeline管理API

### PipelineManager

Pipeline流程管理器。

#### 初始化

```python
from core.pipeline import PipelineManager

pipeline = PipelineManager(config_manager)
```

#### 主要方法

##### run_once()

执行一次完整的Pipeline流程。

```python
def run_once(self) -> Dict[str, Any]
```

**返回:** 执行结果统计

##### run_stage()

执行特定阶段的处理。

```python
def run_stage(
    self,
    stage_name: str,
    book_ids: List[int] = None
) -> int
```

**参数:**
- `stage_name`: 阶段名称
- `book_ids`: 指定处理的书籍ID列表（可选）

**返回:** 处理的书籍数量

**示例:**
```python
processed_count = pipeline.run_stage(
    stage_name='search',
    book_ids=[1, 2, 3]
)
```

---

## 错误处理API

### ErrorHandler

统一错误处理和恢复机制。

#### 初始化

```python
from core.error_handler import ErrorHandler

error_handler = ErrorHandler(state_manager)
```

#### 主要方法

##### handle_error()

处理错误。

```python
def handle_error(
    self,
    book_id: int,
    stage: str,
    error: Exception,
    context: Dict[str, Any] = None
) -> Dict[str, Any]
```

**参数:**
- `book_id`: 书籍ID
- `stage`: 发生错误的阶段
- `error`: 异常对象
- `context`: 上下文信息

**返回:** 处理结果

**示例:**
```python
try:
    # 某些可能出错的操作
    result = risky_operation()
except Exception as e:
    recovery_result = error_handler.handle_error(
        book_id=123,
        stage='download',
        error=e,
        context={'url': 'http://example.com'}
    )
```

##### register_error_callback()

注册错误回调函数。

```python
def register_error_callback(
    self,
    error_type: str,
    callback: Callable
) -> None
```

---

## 配置管理API

### ConfigManager

系统配置管理器。

#### 初始化

```python
from config.config_manager import ConfigManager

config = ConfigManager('config.yaml')
```

#### 主要方法

##### get_douban_config()

获取豆瓣配置。

```python
def get_douban_config(self) -> Dict[str, Any]
```

**返回:**
```python
{
    'cookie': 'your_cookie_string',
    'user_id': '12345678',
    'request_delay': 2,
    'max_retries': 3
}
```

##### get_zlibrary_config()

获取Z-Library配置。

```python
def get_zlibrary_config(self) -> Dict[str, Any]
```

##### get_calibre_config()

获取Calibre配置。

```python
def get_calibre_config(self) -> Dict[str, Any]
```

##### get_database_config()

获取数据库配置。

```python
def get_database_config(self) -> Dict[str, Any]
```

##### get_logging_config()

获取日志配置。

```python
def get_logging_config(self) -> Dict[str, Any]
```

---

## 数据模型API

### 书籍状态枚举

```python
from db.models import BookStatus

# 所有可用状态
states = [
    BookStatus.NEW,                    # 新书
    BookStatus.DETAIL_FETCHING,       # 获取详情中
    BookStatus.DETAIL_COMPLETE,       # 详情完成
    BookStatus.SEARCH_QUEUED,         # 搜索队列中
    BookStatus.SEARCH_ACTIVE,         # 搜索中
    BookStatus.SEARCH_COMPLETE,       # 搜索完成
    BookStatus.SEARCH_NO_RESULTS,     # 搜索无结果
    BookStatus.DOWNLOAD_QUEUED,       # 下载队列中
    BookStatus.DOWNLOAD_ACTIVE,       # 下载中
    BookStatus.DOWNLOAD_COMPLETE,     # 下载完成
    BookStatus.DOWNLOAD_FAILED,       # 下载失败
    BookStatus.UPLOAD_QUEUED,         # 上传队列中
    BookStatus.UPLOAD_ACTIVE,         # 上传中
    BookStatus.UPLOAD_COMPLETE,       # 上传完成
    BookStatus.UPLOAD_FAILED,         # 上传失败
    BookStatus.COMPLETED,             # 完成
    BookStatus.SKIPPED_EXISTS,        # 已存在跳过
    BookStatus.FAILED_PERMANENT       # 永久失败
]
```

---

## 使用示例

### 完整的API调用示例

```python
from config.config_manager import ConfigManager
from core.state_manager import BookStateManager
from core.pipeline import PipelineManager
from db.database import Database

# 1. 初始化配置和数据库
config = ConfigManager('config.yaml')
database = Database(config)

# 2. 初始化状态管理器
state_manager = BookStateManager(
    session_factory=database.session_factory
)

# 3. 初始化Pipeline管理器
pipeline = PipelineManager(config)

# 4. 执行一次完整流程
result = pipeline.run_once()
print(f"处理结果: {result}")

# 5. 查询书籍状态
with database.session_scope() as session:
    from db.models import DoubanBook
    books = session.query(DoubanBook).limit(10).all()
    for book in books:
        print(f"书籍: {book.title}, 状态: {book.status.value}")
```

### 错误处理示例

```python
from core.error_handler import ErrorHandler, ErrorClassifier

# 错误分类
error = ConnectionError("Network timeout")
error_info = ErrorClassifier.classify_error(error)
print(f"错误类型: {error_info.error_type}")
print(f"重试策略: {error_info.retry_strategy}")
print(f"可重试: {error_info.retryable}")

# 处理错误
error_handler = ErrorHandler(state_manager)
recovery_result = error_handler.handle_error(
    book_id=123,
    stage='download',
    error=error
)
```

---

## API返回值说明

### 标准返回格式

大多数API方法遵循以下返回格式：

**成功时:**
```python
{
    'success': True,
    'data': {...},           # 具体数据
    'message': 'Operation successful'
}
```

**失败时:**
```python
{
    'success': False,
    'error': 'Error description',
    'error_code': 'ERROR_CODE'
}
```

### 状态码说明

- `SUCCESS`: 操作成功
- `ERROR_INVALID_PARAMS`: 参数无效
- `ERROR_NOT_FOUND`: 资源未找到
- `ERROR_PERMISSION_DENIED`: 权限不足
- `ERROR_NETWORK`: 网络错误
- `ERROR_SYSTEM`: 系统错误

---

## 注意事项

1. **线程安全**: 大部分API是线程安全的，但建议在并发环境中谨慎使用
2. **错误处理**: 所有API调用都应该包含适当的错误处理逻辑
3. **配置更新**: 某些配置更改需要重启应用才能生效
4. **数据库连接**: 使用session_scope上下文管理器确保正确关闭数据库连接
5. **日志记录**: API调用自动记录到日志系统中，注意日志级别设置

---

## 扩展开发

### 添加新的Pipeline阶段

```python
from stages.base_stage import BaseStage

class CustomStage(BaseStage):
    def __init__(self, config):
        super().__init__('custom', config)
    
    def process_book(self, book_id: int) -> bool:
        # 实现自定义处理逻辑
        return True
```

### 添加新的服务

```python
class CustomService:
    def __init__(self, config):
        self.config = config
    
    def custom_method(self, param):
        # 实现自定义服务逻辑
        pass
```

更多扩展信息请参考[开发指南](development-guide.md)。