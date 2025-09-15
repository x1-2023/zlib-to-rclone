# Implementation Plan: 0次下载时跳过下载任务


**Branch**: `002-0-download-search` | **Date**: 2025-09-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-0-download-search/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
实现Z-Library下载配额耗尽时的智能处理机制。当下载次数为0时，系统继续执行书籍搜索以收集资源信息，但跳过下载阶段，避免浪费配额。需要扩展现有Pipeline架构，增加下载配额检查和新的书籍状态管理。

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: SQLAlchemy, zlibrary, requests, beautifulsoup4, APScheduler, loguru  
**Storage**: SQLite (现有数据库) 扩展BookStatus枚举和ProcessingTask表  
**Testing**: pytest, pytest-cov, pytest-mock (现有测试框架)  
**Target Platform**: Linux服务器，支持daemon和one-shot模式
**Project Type**: single - 现有Pipeline架构扩展  
**Performance Goals**: 处理数百本书籍，保持现有处理速度  
**Constraints**: Z-Library每日10本下载额度，24小时刷新周期  
**Scale/Scope**: 扩展现有19状态工作流，增加配额感知处理

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (单一项目扩展现有架构)
- Using framework directly? ✓ (直接扩展现有SQLAlchemy模型和Pipeline)
- Single data model? ✓ (扩展现有DoubanBook和BookStatus)
- Avoiding patterns? ✓ (利用现有Pipeline模式，无需新架构模式)

**Architecture**:
- EVERY feature as library? ✓ (扩展core/和services/模块)
- Libraries listed: core.quota_manager (配额检查), stages.download_stage (增强下载决策)
- CLI per library: ✓ (集成到现有main.py CLI)
- Library docs: ✓ (将更新CLAUDE.md中的组件文档)

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? ✓ (现有项目已遵循TDD)
- Git commits show tests before implementation? ✓ (将遵循现有项目规范)
- Order: Contract→Integration→E2E→Unit strictly followed? ✓
- Real dependencies used? ✓ (现有测试使用真实SQLite和配置)
- Integration tests for: quota check, download stage behavior, state transitions? ✓
- FORBIDDEN: Implementation before test, skipping RED phase ✓

**Observability**:
- Structured logging included? ✓ (现有loguru结构化日志)
- Frontend logs → backend? N/A (无前端)
- Error context sufficient? ✓ (扩展现有ErrorHandler)

**Versioning**:
- Version number assigned? ✓ (现有__version__.py系统)
- BUILD increments on every change? ✓ (遵循现有版本控制)
- Breaking changes handled? N/A (向后兼容扩展)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: [DEFAULT to Option 1 unless Technical Context indicates web/mobile app]

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/bash/update-agent-context.sh claude` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- 基于Phase 1的contracts和data model生成TDD任务序列
- 每个合约接口 → contract test任务 [P]
- QuotaManager实现 → 单元测试 + 实现任务
- DownloadStage增强 → 集成测试 + 修改任务
- BookStatus扩展 → 数据库迁移 + 模型更新任务
- 端到端验证 → quickstart场景测试任务

**具体任务序列**:
1. **Contract Tests** [P]: QuotaManager和DownloadStage合约测试
2. **Data Model**: BookStatus枚举扩展和数据库迁移
3. **Core Implementation**: QuotaManager核心实现
4. **Stage Enhancement**: DownloadStage配额感知增强
5. **Integration**: Pipeline集成和状态管理更新
6. **E2E Tests**: 完整工作流验证测试

**Ordering Strategy**:
- 严格TDD: 每个组件先写失败测试，再实现
- 依赖顺序: 数据模型 → 核心服务 → 阶段集成 → 端到端测试
- 标记[P]表示可并行执行的独立任务
- 集成测试依赖所有实现任务完成

**技术约束**:
- 所有新代码必须有对应测试
- 保持现有Pipeline架构不变
- 向后兼容，不破坏现有功能
- 遵循现有代码规范和日志格式

**预估输出**: 15-20个有序任务，包含完整的测试-实现-验证周期

**IMPORTANT**: 此阶段由 /tasks 命令执行，/plan 命令不创建tasks.md

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [x] Phase 3: Tasks generated (/tasks command) - 26 tasks created
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS  
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (无违规需要记录)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*