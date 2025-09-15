# Tasks: 0次下载时跳过下载任务

**Input**: 设计文档来自 `/specs/002-0-download-search/`
**Prerequisites**: research.md, data-model.md, contracts/, quickstart.md

## 执行流程概览
基于现有Pipeline架构，扩展配额感知下载跳过功能。该功能需要：
1. 创建QuotaManager组件管理下载配额
2. 扩展BookStatus枚举添加新状态
3. 增强DownloadStage支持配额检查
4. 实现配额恢复机制和状态转换
5. 完整的测试覆盖和验证

技术栈: Python 3.11, SQLAlchemy, zlibrary, pytest
架构: 扩展现有Pipeline架构，最小化架构改动

## Format: `[ID] [P?] Description`
- **[P]**: 可以并行运行（不同文件，无依赖）
- 包含确切的文件路径

## 第1阶段: 设置和准备
- [ ] T001 [P] 设置项目配额管理模块结构
- [ ] T002 [P] 检查并更新项目依赖（如需要的话）
- [ ] T003 [P] 配置测试环境用于配额相关测试

## 第2阶段: 测试优先 (TDD) ⚠️ 必须在第3阶段前完成
**关键: 这些测试必须先写好并且失败，然后才能进行任何实现**

### 契约测试 [并行执行]
- [ ] T004 [P] QuotaManager契约测试在 tests/contract/test_quota_manager_contract.py
- [ ] T005 [P] DownloadStage增强契约测试在 tests/contract/test_download_stage_contract.py

### 集成测试 [并行执行]
- [ ] T006 [P] 配额充足时正常下载流程集成测试在 tests/integration/test_quota_sufficient_download.py
- [ ] T007 [P] 配额为0时跳过下载集成测试在 tests/integration/test_quota_exhausted_skip.py
- [ ] T008 [P] 配额恢复后重新处理集成测试在 tests/integration/test_quota_recovery_process.py
- [ ] T009 [P] 处理过程中配额耗尽集成测试在 tests/integration/test_quota_exhausted_during_process.py

## 第3阶段: 核心实现 (仅在测试失败后)

### 数据模型扩展 [并行执行]
- [ ] T010 [P] 扩展BookStatus枚举添加SEARCH_COMPLETE_QUOTA_EXHAUSTED状态在 db/models.py
- [ ] T011 [P] 创建DownloadQuota数据模型在 core/quota_manager.py

### 核心组件实现
- [ ] T012 实现QuotaManager类在 core/quota_manager.py (依赖T011)
- [ ] T013 增强DownloadStage支持配额检查在 stages/download_stage.py
- [ ] T014 扩展StateManager支持新状态转换在 core/state_manager.py

### 服务层集成
- [ ] T015 扩展ZLibraryService提供配额查询API在 services/zlibrary_service.py
- [ ] T016 增强Pipeline管理器集成配额管理在 core/pipeline.py
- [ ] T017 扩展ErrorHandler处理配额相关错误在 core/error_handler.py

## 第4阶段: 集成和优化
- [ ] T018 集成QuotaManager到主Pipeline流程
- [ ] T019 添加配额相关日志和监控
- [ ] T020 实现配额缓存机制优化API调用频率
- [ ] T021 添加配额恢复任务调度机制

## 第5阶段: 完善和优化
- [ ] T022 [P] 单元测试QuotaManager在 tests/unit/test_quota_manager.py
- [ ] T023 [P] 单元测试增强DownloadStage在 tests/unit/test_enhanced_download_stage.py
- [ ] T024 [P] 单元测试状态转换逻辑在 tests/unit/test_quota_state_transitions.py
- [ ] T025 [P] 性能测试配额检查频率在 tests/performance/test_quota_check_performance.py
- [ ] T026 执行quickstart.md中的手动验证场景
- [ ] T027 更新相关文档和README

## 依赖关系
- 测试阶段 (T004-T009) 必须在实现阶段 (T010-T021) 之前
- T010 阻塞 T012 (数据模型必须先于管理器)
- T012 阻塞 T013, T018 (QuotaManager必须先于使用它的组件)
- T013 阻塞 T016 (DownloadStage增强必须先于Pipeline集成)
- T014 阻塞 T016 (StateManager扩展必须先于Pipeline集成)
- 实现阶段 (T010-T021) 必须在完善阶段 (T022-T027) 之前

## 并行执行示例

### 契约测试阶段 (T004-T005):
```bash
# 同时启动契约测试任务:
Task: "QuotaManager契约测试在 tests/contract/test_quota_manager_contract.py"
Task: "DownloadStage增强契约测试在 tests/contract/test_download_stage_contract.py"
```

### 集成测试阶段 (T006-T009):
```bash
# 同时启动集成测试任务:
Task: "配额充足时正常下载流程集成测试在 tests/integration/test_quota_sufficient_download.py"
Task: "配额为0时跳过下载集成测试在 tests/integration/test_quota_exhausted_skip.py"
Task: "配额恢复后重新处理集成测试在 tests/integration/test_quota_recovery_process.py"
Task: "处理过程中配额耗尽集成测试在 tests/integration/test_quota_exhausted_during_process.py"
```

### 数据模型扩展阶段 (T010-T011):
```bash
# 同时启动数据模型任务:
Task: "扩展BookStatus枚举添加SEARCH_COMPLETE_QUOTA_EXHAUSTED状态在 db/models.py"
Task: "创建DownloadQuota数据模型在 core/quota_manager.py"
```

### 单元测试阶段 (T022-T025):
```bash
# 同时启动单元测试任务:
Task: "单元测试QuotaManager在 tests/unit/test_quota_manager.py"
Task: "单元测试增强DownloadStage在 tests/unit/test_enhanced_download_stage.py"
Task: "单元测试状态转换逻辑在 tests/unit/test_quota_state_transitions.py"
Task: "性能测试配额检查频率在 tests/performance/test_quota_check_performance.py"
```

## 说明
- [P] 标记的任务操作不同文件，无依赖关系
- 验证测试在实现前失败
- 每个任务完成后都要提交代码
- 避免：模糊任务、同文件冲突

## 任务生成规则
*在执行过程中应用*

1. **基于契约文件**:
   - quota_manager.py → 契约测试任务 [P]
   - download_stage.py → 契约测试任务 [P]

2. **基于数据模型**:
   - DownloadQuota实体 → 数据模型创建任务 [P]
   - BookStatus扩展 → 状态枚举扩展任务 [P]

3. **基于用户场景**:
   - quickstart.md中每个验证场景 → 集成测试 [P]
   - 不同配额情况 → 验证任务

4. **排序规则**:
   - 设置 → 测试 → 模型 → 服务 → 集成 → 完善
   - 依赖关系阻止并行执行

## 验证检查清单
*在返回前由主流程检查*

- [ ] 所有契约都有对应的测试
- [ ] 所有实体都有模型任务
- [ ] 所有测试都在实现之前
- [ ] 并行任务真正独立
- [ ] 每个任务都指定确切的文件路径
- [ ] 没有任务与其他[P]任务修改同一文件

## 完成标准

功能完成需要满足所有条件：
- [ ] 所有测试通过（契约、集成、单元、性能）
- [ ] QuotaManager正确管理下载配额
- [ ] DownloadStage正确处理配额检查和跳过逻辑
- [ ] 新的SEARCH_COMPLETE_QUOTA_EXHAUSTED状态正常工作
- [ ] 配额恢复机制能够重新处理跳过的书籍
- [ ] 日志记录完整准确
- [ ] 性能无明显影响
- [ ] quickstart.md中所有验证场景通过