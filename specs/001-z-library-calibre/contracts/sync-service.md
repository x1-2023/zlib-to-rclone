# Sync Service Contracts

**Feature**: Douban to Calibre Auto Sync System  
**Date**: 2025-09-13

## Overview

The existing system implements all required service contracts. This document maps current implementations to feature requirements.

## CLI Interface Contract (Existing)

### Main Application Entry Point
**Implementation**: `main.py` - `DoubanZLibraryCalibrer` class

```bash
# Manual sync (existing)
python main.py --once

# Daemon mode (existing) 
python main.py --daemon

# Debug mode (existing)
python main.py --debug

# Cleanup mode (existing)
python main.py --cleanup
```

**Configuration Contract**: 
- Input: `config.yaml` (existing format)
- Output: Structured logs to `logs/` directory  
- Notifications: Lark webhook (configurable)

## Service Layer Contracts (Existing)

### DoubanScraper Service
**Implementation**: `scrapers/douban_scraper.py`

```python
class DoubanScraper:
    def get_wishlist_books(self, max_pages: int = 0) -> List[Dict[str, Any]]
    def get_book_details(self, book_url: str) -> Optional[Dict[str, Any]]
    def extract_book_id(self, url: str) -> Optional[str]
```

**Contract**:
- Input: Douban cookie, wishlist URL
- Output: List of book metadata dictionaries
- Error Handling: DoubanAccessDeniedException for 403 errors
- Rate Limiting: Built-in delays and retry logic

### ZLibraryService 
**Implementation**: `services/zlibrary_service.py`

```python
class ZLibraryService:
    def search_book(self, title: str, author: str) -> List[Dict[str, Any]]
    def download_book(self, book_info: Dict[str, Any]) -> Optional[str]
    def get_download_url(self, book_id: str) -> Optional[str]
```

**Contract**:
- Input: Book title, author for search
- Output: List of available books with download metadata
- Download: Returns local file path on success
- Format Priority: Configurable (epub > mobi > azw3 > pdf)

### CalibreService
**Implementation**: `services/calibre_service.py` 

```python
class CalibreService:
    def search_book(self, title: str, author: str) -> Optional[Dict[str, Any]]
    def add_book(self, file_path: str, metadata: Dict[str, Any]) -> bool
    def get_library_info(self) -> Dict[str, Any]
```

**Contract**:
- Input: E-book file path + metadata dictionary
- Output: Boolean success status
- Duplicate Detection: Configurable match threshold
- Integration: Content Server API

## Pipeline Stage Contracts (Existing)

### Base Stage Interface
**Implementation**: `stages/` directory pattern

```python
class BaseStage:
    def process(self, book: DoubanBook) -> bool
    def can_process(self, book: DoubanBook) -> bool
    def get_stage_name(self) -> str
```

### Implemented Stages

#### DataCollectionStage
**Implementation**: `stages/data_collection_stage.py`
```python
# Contract: NEW -> DETAIL_COMPLETE
process(book) -> bool  # Fetches Douban details
```

#### SearchStage  
**Implementation**: `stages/search_stage.py`
```python
# Contract: DETAIL_COMPLETE -> SEARCH_COMPLETE/SEARCH_NO_RESULTS
process(book) -> bool  # Z-Library search
```

#### DownloadStage
**Implementation**: `stages/download_stage.py`
```python  
# Contract: SEARCH_COMPLETE -> DOWNLOAD_COMPLETE
process(book) -> bool  # Downloads selected format
```

#### UploadStage
**Implementation**: `stages/upload_stage.py`
```python
# Contract: DOWNLOAD_COMPLETE -> COMPLETED/SKIPPED_EXISTS  
process(book) -> bool  # Uploads to Calibre
```

## State Management Contract (Existing)

### BookStateManager
**Implementation**: `core/state_manager.py`

```python
class BookStateManager:
    def update_status(self, book_id: int, new_status: BookStatus) -> bool
    def can_transition(self, current: BookStatus, target: BookStatus) -> bool  
    def get_next_states(self, current: BookStatus) -> List[BookStatus]
```

**Contract**:
- Input: Book ID, target status
- Output: Boolean success + status history record
- Validation: Enforces valid state transitions
- Audit: Complete change history

## Error Handling Contract (Existing)

### ErrorHandler 
**Implementation**: `core/error_handler.py`

```python
class ErrorHandler:
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> ErrorAction
    def is_retryable(self, error: Exception) -> bool
    def get_retry_delay(self, attempt: int) -> int
```

**Contract**:
- Input: Exception + context information  
- Output: ErrorAction (RETRY/SKIP/FAIL)
- Retry Logic: Exponential backoff
- Classification: Retryable vs permanent errors

## Task Scheduling Contract (Existing)

### TaskScheduler
**Implementation**: `core/task_scheduler.py`

```python
class TaskScheduler:
    def schedule_task(self, task: ScheduledTask) -> bool
    def execute_pending(self) -> int  # Returns count of processed tasks
    def cleanup_completed(self, older_than_days: int) -> int
```

**Contract**:
- Input: ScheduledTask with priority and timing
- Output: Task execution results
- Priority: HIGH/NORMAL/LOW queue management
- Cleanup: Automated old task removal

## Configuration Contract (Existing)

### ConfigManager
**Implementation**: `config/config_manager.py`

```yaml
# Input Contract (config.yaml)
douban:
  cookie: "required_string"
  wishlist_url: "required_url"
  
database:
  type: "sqlite"  # or postgresql
  path: "data/books.db"
  
calibre:
  content_server_url: "required_url"
  username: "required_string" 
  password: "required_string"
  
zlibrary:
  username: "required_string"
  password: "required_string"
  format_priority: ["epub", "mobi", "azw3", "pdf"]
```

## Integration Test Contracts (Existing)

### End-to-End Workflow
**Test Location**: `tests/integration/test_main_workflow.py`

```python
def test_complete_sync_workflow():
    """Tests full Douban -> Z-Library -> Calibre pipeline"""
    
def test_error_recovery():
    """Tests resume after 403/network errors"""
    
def test_duplicate_handling():
    """Tests skip behavior for existing books"""
```

**Contract**:
- Real services (no mocks)
- Complete workflow validation  
- Error scenario testing
- State transition verification

---
**Conclusion**: All service contracts are implemented and production-ready. The existing system provides the complete sync workflow specified in the requirements.