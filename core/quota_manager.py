# -*- coding: utf-8 -*-
"""
配额管理器

管理Z-Library下载配额，提供缓存和实时查询功能。
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from core.pipeline import NetworkError
from services.zlibrary_service import ZLibraryService
from utils.logger import get_logger


@dataclass
class DownloadQuota:
    """下载配额数据模型"""
    remaining_downloads: int
    daily_limit: int = 10
    last_checked: Optional[datetime] = None
    next_reset: Optional[datetime] = None
    
    def has_quota_available(self) -> bool:
        """检查是否有可用配额"""
        return self.remaining_downloads > 0
    
    def is_expired(self, cache_minutes: int = 5) -> bool:
        """检查配额信息是否过期"""
        if self.last_checked is None:
            return True
        return datetime.now() - self.last_checked > timedelta(minutes=cache_minutes)


class QuotaManager:
    """配额管理器"""
    
    def __init__(self, email: str, password: str, cache_minutes: int = 5):
        """
        初始化配额管理器
        
        Args:
            email: Z-Library账号邮箱
            password: Z-Library密码
            cache_minutes: 缓存有效期（分钟）
        """
        self.email = email
        self.password = password
        self.cache_minutes = cache_minutes
        self.logger = get_logger("quota_manager")
        
        # 缓存配额信息
        self._cached_quota: Optional[DownloadQuota] = None
        
        # Z-Library服务实例
        self._zlibrary_service: Optional[ZLibraryService] = None
    
    def _get_zlibrary_service(self) -> ZLibraryService:
        """获取Z-Library服务实例（懒加载）"""
        if self._zlibrary_service is None:
            self._zlibrary_service = ZLibraryService(
                email=self.email,
                password=self.password
            )
        return self._zlibrary_service
    
    async def get_current_quota(self, force_refresh: bool = False) -> DownloadQuota:
        """
        获取当前下载配额信息
        
        Args:
            force_refresh: 是否强制从API刷新，忽略缓存
            
        Returns:
            DownloadQuota: 当前配额信息
            
        Raises:
            NetworkError: API调用失败
        """
        # 检查缓存是否有效
        if not force_refresh and self._cached_quota and not self._cached_quota.is_expired(self.cache_minutes):
            self.logger.debug(f"使用缓存配额信息: {self._cached_quota.remaining_downloads}/{self._cached_quota.daily_limit}")
            return self._cached_quota
        
        # 从API获取最新配额
        try:
            self.logger.info("从Z-Library API获取配额信息")
            quota_info = await self._fetch_quota_from_api()
            self._cached_quota = quota_info
            self.logger.info(f"配额获取成功: 剩余 {quota_info.remaining_downloads}/{quota_info.daily_limit}")
            return quota_info
            
        except Exception as e:
            self.logger.error(f"获取配额失败: {e}")
            raise NetworkError(f"无法获取Z-Library配额信息: {e}")
    
    async def _fetch_quota_from_api(self) -> DownloadQuota:
        """从Z-Library API获取配额信息"""
        try:
            zlibrary_service = self._get_zlibrary_service()
            
            # 调用Z-Library服务获取配额信息
            # 注意：这里需要根据实际的zlibrary服务API调整
            quota_data = await zlibrary_service.get_download_quota()
            
            return DownloadQuota(
                remaining_downloads=quota_data.get('remaining', 0),
                daily_limit=quota_data.get('daily_limit', 10),
                last_checked=datetime.now(),
                next_reset=quota_data.get('next_reset')
            )
            
        except Exception as e:
            raise NetworkError(f"Z-Library API调用失败: {e}")
    
    def has_quota_available(self) -> bool:
        """
        检查是否有可用下载配额 (使用缓存)
        
        Returns:
            bool: True如果有可用配额，False如果配额为0
        """
        if self._cached_quota is None:
            # 如果没有缓存，默认返回False（需要先获取配额信息）
            self.logger.warning("配额信息未初始化，请先调用get_current_quota()")
            return False
        
        # 如果缓存过期，需要刷新
        if self._cached_quota.is_expired(self.cache_minutes):
            self.logger.debug("配额缓存已过期，需要刷新")
            # 这里可以选择异步刷新或返回缓存值
            # 为了简化，暂时返回缓存值
        
        return self._cached_quota.has_quota_available()
    
    def consume_quota(self, count: int = 1) -> bool:
        """
        消费下载配额 (本地记录)
        
        Args:
            count: 消费的配额数量
            
        Returns:
            bool: True如果成功消费，False如果配额不足
        """
        if self._cached_quota is None:
            self.logger.error("配额信息未初始化，无法消费配额")
            return False
        
        if self._cached_quota.remaining_downloads >= count:
            self._cached_quota.remaining_downloads -= count
            self.logger.info(f"消费配额 {count} 个，剩余 {self._cached_quota.remaining_downloads}/{self._cached_quota.daily_limit}")
            return True
        else:
            self.logger.warning(f"配额不足：需要 {count} 个，剩余 {self._cached_quota.remaining_downloads}")
            return False
    
    def reset_cache(self) -> None:
        """重置配额缓存，下次查询将从API获取"""
        self.logger.debug("重置配额缓存")
        self._cached_quota = None