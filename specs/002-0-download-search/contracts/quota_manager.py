"""
QuotaManager合约定义

定义配额管理组件的接口规范，用于contract testing。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from dataclasses import dataclass


@dataclass
class DownloadQuota:
    """下载配额数据模型"""
    remaining_downloads: int
    daily_limit: int = 10
    last_checked: datetime = None
    next_reset: Optional[datetime] = None
    
    def has_quota_available(self) -> bool:
        """检查是否有可用配额"""
        return self.remaining_downloads > 0
    
    def is_expired(self, cache_minutes: int = 5) -> bool:
        """检查配额信息是否过期"""
        if self.last_checked is None:
            return True
        from datetime import timedelta
        return datetime.now() - self.last_checked > timedelta(minutes=cache_minutes)


class QuotaManagerContract(ABC):
    """配额管理器合约接口"""
    
    @abstractmethod
    async def get_current_quota(self, force_refresh: bool = False) -> DownloadQuota:
        """
        获取当前下载配额信息
        
        Args:
            force_refresh: 是否强制从API刷新，忽略缓存
            
        Returns:
            DownloadQuota: 当前配额信息
            
        Raises:
            NetworkError: API调用失败
            AuthenticationError: 认证失败
        """
        pass
    
    @abstractmethod
    def has_quota_available(self) -> bool:
        """
        检查是否有可用下载配额 (使用缓存)
        
        Returns:
            bool: True如果有可用配额，False如果配额为0
        """
        pass
    
    @abstractmethod
    def consume_quota(self, count: int = 1) -> bool:
        """
        消费下载配额 (本地记录)
        
        Args:
            count: 消费的配额数量
            
        Returns:
            bool: True如果成功消费，False如果配额不足
        """
        pass
    
    @abstractmethod
    def reset_cache(self) -> None:
        """
        重置配额缓存，下次查询将从API获取
        """
        pass


# Contract Test Scenarios
CONTRACT_TEST_SCENARIOS = [
    {
        "name": "get_current_quota_success",
        "description": "成功获取当前配额信息",
        "setup": "API返回有效配额数据",
        "expected": "返回DownloadQuota对象，remaining_downloads >= 0"
    },
    {
        "name": "get_current_quota_network_error", 
        "description": "网络错误时的处理",
        "setup": "API调用超时或连接失败",
        "expected": "抛出NetworkError异常"
    },
    {
        "name": "has_quota_available_with_cache",
        "description": "使用缓存检查配额可用性",
        "setup": "缓存中有有效配额信息",
        "expected": "返回布尔值，不调用API"
    },
    {
        "name": "has_quota_available_expired_cache",
        "description": "缓存过期时自动刷新",
        "setup": "缓存过期超过5分钟",
        "expected": "自动调用API刷新，返回最新状态"
    },
    {
        "name": "consume_quota_sufficient",
        "description": "配额充足时的消费",
        "setup": "remaining_downloads > 0",
        "expected": "返回True，本地配额减少"
    },
    {
        "name": "consume_quota_insufficient", 
        "description": "配额不足时的消费",
        "setup": "remaining_downloads = 0",
        "expected": "返回False，配额不变"
    }
]