# Quickstart: 0次下载时跳过下载任务

## 功能验证流程

本quickstart用于验证配额感知下载跳过功能的正确实现。

## 前置条件

1. 现有系统正常运行
2. Z-Library账号配置正确
3. 数据库中有处于`SEARCH_COMPLETE`状态的书籍
4. 测试环境可以控制下载配额

## 验证场景

### 场景1: 配额充足时的正常流程

**步骤**:
1. 确认当前配额 > 0
2. 运行系统处理书籍
3. 验证书籍正常完成下载流程

**预期结果**:
```bash
# 运行命令
python main.py --once

# 期望日志输出
[INFO] 检查下载配额: 剩余 5/10
[INFO] 开始下载书籍: [书名]
[INFO] 下载完成: [文件路径]
[INFO] 书籍状态更新: SEARCH_COMPLETE -> DOWNLOAD_COMPLETE
```

**验证点**:
- [ ] 配额检查日志正确显示
- [ ] 书籍成功下载并上传到Calibre
- [ ] 书籍状态最终为`COMPLETED`
- [ ] 配额正确消费（减1）

### 场景2: 配额为0时的跳过流程

**步骤**:
1. 设置配额为0（或等待配额耗尽）
2. 确保有`SEARCH_COMPLETE`状态的书籍
3. 运行系统处理

**预期结果**:
```bash
# 运行命令  
python main.py --once

# 期望日志输出
[INFO] 检查下载配额: 剩余 0/10
[WARN] 配额不足，跳过下载任务
[INFO] 书籍状态更新: SEARCH_COMPLETE -> SEARCH_COMPLETE_QUOTA_EXHAUSTED
[INFO] 跳过书籍: [书名] (原因: 配额不足)
[INFO] 继续处理下一本书籍
```

**验证点**:
- [ ] 正确检测配额为0
- [ ] 书籍状态更新为`SEARCH_COMPLETE_QUOTA_EXHAUSTED`
- [ ] 没有尝试下载任何文件
- [ ] 系统继续处理其他书籍
- [ ] 记录跳过的书籍信息

### 场景3: 处理过程中配额耗尽

**步骤**:
1. 设置配额为1
2. 准备2本`SEARCH_COMPLETE`状态的书籍
3. 运行系统处理

**预期结果**:
```bash
# 期望日志输出
[INFO] 检查下载配额: 剩余 1/10
[INFO] 开始下载第1本书籍: [书名1]
[INFO] 下载完成: [书名1]
[INFO] 检查下载配额: 剩余 0/10  
[WARN] 配额不足，跳过下载任务
[INFO] 书籍状态更新: [书名2] SEARCH_COMPLETE -> SEARCH_COMPLETE_QUOTA_EXHAUSTED
```

**验证点**:
- [ ] 第1本书籍正常下载完成
- [ ] 第2本书籍被正确跳过
- [ ] 配额消费正确计算
- [ ] 两本书的最终状态不同

### 场景4: 配额恢复后的重新处理

**步骤**:
1. 确保有`SEARCH_COMPLETE_QUOTA_EXHAUSTED`状态的书籍
2. 等待配额刷新（或重置配额为>0）
3. 运行系统处理

**预期结果**:
```bash
# 期望日志输出
[INFO] 检查下载配额: 剩余 10/10 (配额已刷新)
[INFO] 发现配额已恢复，重新处理跳过的书籍
[INFO] 重新加入下载队列: 3本书籍
[INFO] 书籍状态更新: SEARCH_COMPLETE_QUOTA_EXHAUSTED -> DOWNLOAD_QUEUED
```

**验证点**:
- [ ] 正确识别配额恢复
- [ ] 找到所有`SEARCH_COMPLETE_QUOTA_EXHAUSTED`状态的书籍
- [ ] 状态正确更新为`DOWNLOAD_QUEUED`
- [ ] 书籍重新进入正常处理流程

## 数据库验证

### 查询配额耗尽的书籍
```sql
SELECT id, douban_id, title, status, updated_at 
FROM douban_books 
WHERE status = 'search_complete_quota_exhausted';
```

### 查询状态变更历史
```sql  
SELECT book_id, old_status, new_status, changed_at, reason
FROM book_status_history 
WHERE new_status = 'search_complete_quota_exhausted'
ORDER BY changed_at DESC;
```

## 性能验证

### 配额检查频率
- [ ] 配额检查不超过必要频率（每个DownloadStage一次）
- [ ] 缓存机制正常工作（5分钟内不重复查询API）
- [ ] 大量书籍处理时性能无明显下降

### 内存使用
- [ ] QuotaManager不占用过多内存
- [ ] 长时间运行无内存泄漏

## 错误处理验证

### API异常场景
1. Z-Library API不可访问
2. 认证失败
3. 网络超时

**期望行为**: 
- 优雅降级，使用缓存配额信息
- 记录详细错误日志
- 不影响其他功能正常运行

## 集成测试命令

```bash
# 运行所有相关测试
pytest tests/integration/test_quota_aware_download.py -v

# 运行contract测试
pytest tests/contract/test_quota_manager_contract.py -v
pytest tests/contract/test_download_stage_contract.py -v

# 运行端到端测试
pytest tests/e2e/test_quota_exhausted_workflow.py -v
```

## 完成标准

功能完成需要满足所有验证点：

- [ ] 所有验证场景通过
- [ ] 数据库状态正确更新
- [ ] 日志信息完整准确
- [ ] 性能无明显影响
- [ ] 错误处理健壮
- [ ] 集成测试全部通过

## 故障排除

### 常见问题
1. **配额检查失败**: 检查Z-Library API配置和网络连接
2. **状态更新失败**: 检查数据库连接和事务处理
3. **日志信息缺失**: 检查日志级别配置
4. **缓存不生效**: 检查时间同步和缓存超时设置