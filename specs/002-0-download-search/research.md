# Technical Research: 0次下载时跳过下载任务

## Research Summary

基于用户提供的信息和现有系统分析，本功能需要扩展现有Pipeline架构以支持下载配额感知处理。

## Key Technical Decisions

### 1. 下载配额管理
**Decision**: 使用现有Z-Library API实时查询剩余下载次数  
**Rationale**: 
- 每日10本下载限制，24小时刷新周期
- 现有代码已有查询剩余额度功能
- 实时查询确保准确性，避免缓存不一致

**Alternatives considered**: 
- 本地配额缓存：可能导致不同步
- 配置文件管理：无法反映实际API状态

### 2. 配额检查频率
**Decision**: 在DownloadStage开始前检查配额  
**Rationale**:
- 最小化API调用次数
- 在真正需要下载前检查，避免无效处理
- 符合现有Pipeline阶段分离原则

**Alternatives considered**:
- 每本书前检查：API调用过频
- 批量预检查：可能出现中途配额耗尽

### 3. 新增书籍状态
**Decision**: 扩展BookStatus枚举，增加`SEARCH_COMPLETE_QUOTA_EXHAUSTED`状态  
**Rationale**:
- 区分正常搜索完成和配额不足的搜索完成
- 便于后续配额恢复时识别需重新处理的书籍
- 符合现有19状态精细化管理原则

**Alternatives considered**:
- 复用现有状态：缺乏语义区分
- 增加额外标记字段：破坏状态封装性

### 4. Pipeline集成方案
**Decision**: 增强DownloadStage，增加QuotaManager组件  
**Rationale**:
- 最小化现有架构改动
- 符合单一职责原则
- 便于测试和维护

**Implementation approach**:
```python
class QuotaManager:
    def check_download_quota() -> int
    def has_quota_available() -> bool
    
class DownloadStage:  # 增强现有类
    def process() -> bool:
        if not quota_manager.has_quota_available():
            # 跳过下载，更新状态为SEARCH_COMPLETE_QUOTA_EXHAUSTED
            return True  # 继续处理流程
```

### 5. 错误处理和日志
**Decision**: 扩展现有ErrorHandler，增加配额相关日志  
**Rationale**:
- 配额耗尽是正常业务逻辑，非异常情况
- 需要详细记录跳过的书籍信息
- 便于运维监控和配额使用分析

### 6. 测试策略
**Decision**: 模拟不同配额场景的集成测试  
**Test scenarios**:
- 配额充足时的正常流程
- 配额为0时的跳过流程  
- 处理过程中配额耗尽的场景
- 配额恢复后的重新处理

## Implementation Dependencies

### Required Components
1. **QuotaManager** (core/quota_manager.py): 配额查询和管理
2. **Enhanced DownloadStage** (stages/download_stage.py): 增加配额检查
3. **BookStatus Extension** (db/models.py): 新增状态枚举
4. **Error Handling** (core/error_handler.py): 配额相关错误处理

### Integration Points
- ZLibraryService: 提供配额查询API
- TaskScheduler: 支持配额不足时的任务调度
- StateManager: 支持新状态转换规则
- Logger: 记录配额使用和跳过信息

## Risk Mitigation

### Performance Impact
- **Risk**: 额外API调用影响性能
- **Mitigation**: 仅在DownloadStage前检查，最小化调用频次

### State Consistency
- **Risk**: 新状态可能导致状态机混乱
- **Mitigation**: 严格定义状态转换规则，完整测试覆盖

### Quota Synchronization
- **Risk**: 多实例运行时配额竞争
- **Mitigation**: 文档说明不建议多实例并行运行

## Next Steps for Phase 1
1. 设计QuotaManager接口和实现
2. 定义新的BookStatus状态和转换规则
3. 设计DownloadStage增强方案
4. 制定详细的测试用例