"""
DownloadStage增强合约定义

定义增强后的DownloadStage接口规范，支持配额感知处理。
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from db.models import BookStatus, DoubanBook


class EnhancedDownloadStageContract(ABC):
    """增强的下载阶段合约接口"""
    
    @abstractmethod
    async def process_book(self, book: DoubanBook) -> bool:
        """
        处理单本书籍的下载
        
        Args:
            book: 待处理的书籍对象，状态应为SEARCH_COMPLETE
            
        Returns:
            bool: True表示处理成功（下载或跳过），False表示处理失败
            
        Side Effects:
            - 如果配额充足：执行下载，状态转换为DOWNLOAD_QUEUED -> DOWNLOAD_ACTIVE -> DOWNLOAD_COMPLETE
            - 如果配额不足：跳过下载，状态转换为SEARCH_COMPLETE_QUOTA_EXHAUSTED
            - 记录相应的日志信息
            
        Raises:
            ProcessingError: 处理过程中的业务逻辑错误
            NetworkError: 网络相关错误
        """
        pass
    
    @abstractmethod
    async def check_quota_before_download(self) -> bool:
        """
        在开始下载前检查配额可用性
        
        Returns:
            bool: True如果有可用配额，False如果配额已耗尽
        """
        pass
    
    @abstractmethod
    async def handle_quota_exhausted(self, book: DoubanBook) -> None:
        """
        处理配额耗尽的情况
        
        Args:
            book: 当前处理的书籍
            
        Side Effects:
            - 更新书籍状态为SEARCH_COMPLETE_QUOTA_EXHAUSTED
            - 记录跳过下载的日志
            - 通知相关监控系统
        """
        pass
    
    @abstractmethod
    async def resume_quota_exhausted_books(self) -> int:
        """
        恢复处理之前因配额不足而跳过的书籍
        
        Returns:
            int: 重新加入处理队列的书籍数量
            
        Side Effects:
            - 查询状态为SEARCH_COMPLETE_QUOTA_EXHAUSTED的书籍
            - 检查当前配额状态
            - 将符合条件的书籍状态更新为DOWNLOAD_QUEUED
        """
        pass


# Contract Test Scenarios
CONTRACT_TEST_SCENARIOS = [
    {
        "name": "process_book_with_quota",
        "description": "配额充足时正常处理书籍下载",
        "setup": {
            "book_status": "SEARCH_COMPLETE",
            "quota_available": True,
            "download_result": "success"
        },
        "expected": {
            "return_value": True,
            "final_status": "DOWNLOAD_COMPLETE",
            "quota_consumed": 1
        }
    },
    {
        "name": "process_book_without_quota",
        "description": "配额不足时跳过书籍下载", 
        "setup": {
            "book_status": "SEARCH_COMPLETE",
            "quota_available": False
        },
        "expected": {
            "return_value": True,
            "final_status": "SEARCH_COMPLETE_QUOTA_EXHAUSTED",
            "quota_consumed": 0,
            "log_message": "跳过下载：配额不足"
        }
    },
    {
        "name": "check_quota_before_download_available",
        "description": "下载前检查配额可用",
        "setup": {
            "remaining_quota": 5
        },
        "expected": {
            "return_value": True,
            "api_called": True
        }
    },
    {
        "name": "check_quota_before_download_exhausted",
        "description": "下载前检查配额已耗尽",
        "setup": {
            "remaining_quota": 0
        },
        "expected": {
            "return_value": False,
            "api_called": True
        }
    },
    {
        "name": "handle_quota_exhausted",
        "description": "处理配额耗尽情况",
        "setup": {
            "book_status": "SEARCH_COMPLETE"
        },
        "expected": {
            "final_status": "SEARCH_COMPLETE_QUOTA_EXHAUSTED",
            "log_level": "INFO",
            "notification_sent": True
        }
    },
    {
        "name": "resume_quota_exhausted_books_success",
        "description": "配额恢复后重新处理跳过的书籍",
        "setup": {
            "quota_exhausted_count": 3,
            "current_quota": 8
        },
        "expected": {
            "return_value": 3,
            "books_status_updated": 3,
            "final_status": "DOWNLOAD_QUEUED"
        }
    },
    {
        "name": "resume_quota_exhausted_books_still_no_quota",
        "description": "配额仍不足时不恢复书籍",
        "setup": {
            "quota_exhausted_count": 3,
            "current_quota": 0
        },
        "expected": {
            "return_value": 0,
            "books_status_updated": 0
        }
    }
]