# Data Model: Douban to Calibre Auto Sync System

**Feature**: Douban to Calibre Auto Sync System  
**Date**: 2025-09-13

## Overview

Based on research findings, the existing data model already supports the complete sync workflow. This document maps the current model to the feature requirements and identifies no changes are needed.

## Current Entity Analysis

### Core Entities (Existing)

#### DoubanBook
**Purpose**: Represents a book from Douban with complete lifecycle tracking  
**Location**: `db/models.py:49-88`

**Key Attributes**:
```python
id = Column(Integer, primary_key=True)
title = Column(String(255), nullable=False, index=True)
subtitle = Column(String(255))
author = Column(String(255), index=True)
isbn = Column(String(20), index=True)
douban_id = Column(String(20), unique=True, index=True)
douban_url = Column(String(255), unique=True)
douban_rating = Column(Float)
cover_url = Column(String(255))
description = Column(Text)
search_title = Column(String(255))      # For Z-Library search
search_author = Column(String(255))     # For Z-Library search
status = Column(Enum(BookStatus), default=BookStatus.NEW, index=True)
zlib_dl_url = Column(String(255))       # Z-Library download URL
created_at = Column(DateTime, default=datetime.now)
updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
```

**Relationships**:
- `download_records`: One-to-many with download history
- `zlibrary_books`: One-to-many with Z-Library search results  
- `status_history`: One-to-many with complete state transition log

#### BookStatus (Existing)
**Purpose**: 19-state enum covering complete Pipeline workflow  
**Location**: `db/models.py:18-47`

**Pipeline States** (maps perfectly to sync requirements):
```python
# Data Collection (Douban scraping)
NEW = "new"
DETAIL_FETCHING = "detail_fetching" 
DETAIL_COMPLETE = "detail_complete"

# Search Phase (Z-Library)  
SEARCH_QUEUED = "search_queued"
SEARCH_ACTIVE = "search_active"
SEARCH_COMPLETE = "search_complete"
SEARCH_NO_RESULTS = "search_no_results"

# Download Phase (Z-Library)
DOWNLOAD_QUEUED = "download_queued"
DOWNLOAD_ACTIVE = "download_active"
DOWNLOAD_COMPLETE = "download_complete" 
DOWNLOAD_FAILED = "download_failed"

# Upload Phase (Calibre)
UPLOAD_QUEUED = "upload_queued"
UPLOAD_ACTIVE = "upload_active"
UPLOAD_COMPLETE = "upload_complete"
UPLOAD_FAILED = "upload_failed"

# Terminal States
COMPLETED = "completed"
SKIPPED_EXISTS = "skipped_exists"    # Handles duplicates
FAILED_PERMANENT = "failed_permanent"
```

#### ZLibraryBook (Existing)
**Purpose**: Stores Z-Library search results and metadata  
**Location**: `db/models.py:142-173`

**Key Attributes**:
```python
id = Column(Integer, primary_key=True)
douban_book_id = Column(Integer, ForeignKey('douban_books.id'))
zlibrary_id = Column(String(50), unique=True)
title = Column(String(255))
author = Column(String(255))
file_format = Column(String(10))     # epub, mobi, pdf, etc.
file_size = Column(Integer)
quality_score = Column(Float)        # For format selection
download_url = Column(String(255))
language = Column(String(50))
year = Column(Integer)
```

#### DownloadRecord (Existing) 
**Purpose**: Tracks download operations and file management  
**Location**: `db/models.py:90-114`

**Key Attributes**:
```python
id = Column(Integer, primary_key=True) 
book_id = Column(Integer, ForeignKey('douban_books.id'))
zlibrary_id = Column(String(50))
file_format = Column(String(10))
file_size = Column(Integer) 
file_path = Column(String(255))      # Local storage path
download_url = Column(String(255))
downloaded_at = Column(DateTime, default=datetime.now)
upload_status = Column(String(20))   # pending, success, failed
uploaded_at = Column(DateTime)
```

#### BookStatusHistory (Existing)
**Purpose**: Complete audit trail of status changes  
**Location**: `db/models.py:174-194`

**Key Attributes**:
```python
id = Column(Integer, primary_key=True)
book_id = Column(Integer, ForeignKey('douban_books.id'))
old_status = Column(Enum(BookStatus)) 
new_status = Column(Enum(BookStatus))
changed_at = Column(DateTime, default=datetime.now)
reason = Column(String(255))         # Context for change
error_message = Column(Text)         # If change due to error
```

## State Transition Model

### Complete Workflow Mapping

The existing 19-state model perfectly handles the sync requirements:

```
Douban Scraping:
NEW → DETAIL_FETCHING → DETAIL_COMPLETE

Z-Library Search:  
DETAIL_COMPLETE → SEARCH_QUEUED → SEARCH_ACTIVE → 
  SEARCH_COMPLETE (found) / SEARCH_NO_RESULTS (not found)

Z-Library Download:
SEARCH_COMPLETE → DOWNLOAD_QUEUED → DOWNLOAD_ACTIVE →
  DOWNLOAD_COMPLETE (success) / DOWNLOAD_FAILED (retry/fail)

Calibre Upload:
DOWNLOAD_COMPLETE → UPLOAD_QUEUED → UPLOAD_ACTIVE → 
  UPLOAD_COMPLETE (success) / UPLOAD_FAILED (retry/fail)

Terminal States:
UPLOAD_COMPLETE → COMPLETED (success)
[Any stage] → SKIPPED_EXISTS (duplicate detected)
[Any stage] → FAILED_PERMANENT (permanent failure)
```

### Validation Rules (Existing)

**State Transition Validation**: Implemented in `core/state_manager.py`
- Each transition validated against allowed paths
- Invalid transitions raise `ValueError`
- Complete audit trail maintained

**Data Validation**: Built into SQLAlchemy model
- Required fields enforced
- Unique constraints on douban_id, douban_url
- Foreign key relationships maintained

## Entity Relationships

### Primary Relationships (Existing)
```
DoubanBook (1) ←→ (N) ZLibraryBook
  - One book can have multiple Z-Library search results
  - Quality scoring selects best result

DoubanBook (1) ←→ (N) DownloadRecord  
  - Complete download history per book
  - Tracks format preferences and retry attempts

DoubanBook (1) ←→ (N) BookStatusHistory
  - Complete audit trail of state changes
  - Essential for debugging and recovery

ZLibraryBook (1) ←→ (1) DownloadRecord
  - Links specific search result to download
  - Tracks which Z-Library result was used
```

### Data Flow Integration (Existing)
```
Configuration (config.yaml) → 
  Douban credentials → DoubanBook creation →
  Z-Library search → ZLibraryBook results →  
  Download selection → DownloadRecord →
  Calibre upload → Status completion
```

## Schema Extensions Needed

**FINDING**: ✅ **No schema changes required**

The existing model supports all requirements:
- ✅ Douban wishlist scraping (DoubanBook)
- ✅ Z-Library search/download (ZLibraryBook, DownloadRecord)
- ✅ Calibre upload tracking (status transitions)
- ✅ Duplicate detection (unique constraints + status)
- ✅ Error recovery (status history + retry logic)
- ✅ Format preferences (quality scoring)
- ✅ Complete audit trail (BookStatusHistory)

## Migration Requirements

**FINDING**: ✅ **No migrations needed**

Current database schema version handles all sync requirements. The existing pipeline is production-ready.

## Performance Considerations (Current)

**Indexing Strategy** (Already Optimized):
- `douban_books.title` - Fast title searches  
- `douban_books.author` - Author-based queries
- `douban_books.isbn` - ISBN lookups
- `douban_books.douban_id` - Unique book identification
- `douban_books.status` - Pipeline state queries

**Query Patterns** (Already Efficient):
- Status-based book selection for each pipeline stage
- Duplicate detection via indexed unique fields
- History queries for debugging and recovery

---
**Conclusion**: The existing data model is comprehensive and production-ready for the sync requirements. No changes needed.