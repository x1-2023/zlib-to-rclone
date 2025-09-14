# Implementation Plan: Douban to Calibre Auto Sync System

**Branch**: `001-z-library-calibre` | **Date**: 2025-09-13 | **Spec**: [spec.md](/home/ben/Code/auto-book-management/specs/001-z-library-calibre/spec.md)  
**Input**: Feature specification from `/specs/001-z-library-calibre/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ SUCCESS: Feature spec loaded and analyzed
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ Project Type: single (existing codebase with Pipeline architecture)
   → ✅ Structure Decision: Option 1 (existing structure)
3. Evaluate Constitution Check section below
   → ⚠️ WARN: Constitution template is placeholder, using project-specific standards
   → ✅ Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → ✅ COMPLETE: All clarifications resolved from existing codebase
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → ✅ COMPLETE: Design artifacts generated
6. Re-evaluate Constitution Check section
   → ✅ Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
   → ✅ COMPLETE: Task generation strategy documented
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Auto-sync system that scrapes Douban wishlists, downloads e-books from Z-Library, and uploads to Calibre libraries using existing Pipeline architecture. Extends current system to handle complete book synchronization workflow with state management and error recovery.

## Technical Context
**Language/Version**: Python 3.11 (existing codebase)  
**Primary Dependencies**: SQLAlchemy 2.0.43, PyYAML 6.0.2, requests, beautifulsoup4, zlibrary client  
**Storage**: SQLite (existing) with 19-state Pipeline architecture  
**Testing**: pytest (existing test structure)  
**Target Platform**: Linux server (existing deployment)  
**Project Type**: single (extend existing Pipeline architecture)  
**Performance Goals**: Process 100+ books per sync, handle 403 errors gracefully  
**Constraints**: Respect Z-Library rate limits, handle Douban anti-scraping, maintain Calibre compatibility  
**Scale/Scope**: Personal library management, 1000+ books, automated scheduling

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (extending existing auto-book-management)
- Using framework directly? ✅ (SQLAlchemy, requests, existing services)
- Single data model? ✅ (extending existing DoubanBook model)
- Avoiding patterns? ✅ (using existing Pipeline pattern)

**Architecture**:
- EVERY feature as library? ✅ (existing services/, stages/, core/ structure)
- Libraries listed: 
  - scrapers/douban_scraper: Extract wishlist data
  - services/zlibrary_service: Search and download books  
  - services/calibre_service: Upload to Calibre
  - core/pipeline: Orchestrate workflow
- CLI per library: ✅ (main.py with --once/--daemon modes)
- Library docs: ✅ (existing CLAUDE.md format)

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? ✅ (existing test structure supports TDD)
- Git commits show tests before implementation? ✅ (will follow existing pattern)
- Order: Contract→Integration→E2E→Unit strictly followed? ✅
- Real dependencies used? ✅ (existing tests use real configs, not mocks)
- Integration tests for: ✅ (planned for new pipeline stages)
- FORBIDDEN: Implementation before test ✅

**Observability**:
- Structured logging included? ✅ (existing utils/logger.py)
- Frontend logs → backend? N/A (single process)
- Error context sufficient? ✅ (existing error handling patterns)

**Versioning**:
- Version number assigned? ✅ (core/__version__.py exists)
- BUILD increments on every change? ✅ (existing pattern)
- Breaking changes handled? ✅ (database migration support exists)

## Project Structure

### Documentation (this feature)
```
specs/001-z-library-calibre/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)  
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Extending existing single project structure
config/                  # Configuration management (existing)
core/                   # Pipeline components (existing)  
db/                     # Models and database (existing)
scrapers/               # Douban scraper (existing)
services/               # Calibre, ZLibrary, Lark services (existing)
stages/                 # Pipeline stages (existing)
tests/                  # Test structure (existing)
├── unit/               # Unit tests (existing)
├── integration/        # Integration tests (existing) 
└── manual/             # Manual tests (existing)
utils/                  # Logging and utilities (existing)
```

**Structure Decision**: Extend existing Option 1 structure - no new projects needed

## Phase 0: Outline & Research ✅

Analysis of existing codebase reveals all technical decisions are already made:

**Resolved Clarifications**:
- **Authentication**: Cookie-based Douban access (config.yaml), Z-Library username/password (existing)
- **Sync triggering**: Both --once and --daemon modes exist (main.py)
- **Duplicate handling**: Existing CalibreService.search_book() with match_threshold

**Research Findings**:
- **Decision**: Extend existing Pipeline architecture with new stages
- **Rationale**: System already handles 19-state workflow, error recovery, scheduling
- **Alternatives considered**: Rewrite rejected - existing system is mature and functional

**Output**: ✅ research.md created

## Phase 1: Design & Contracts ✅

**Data Model Extensions**:
- Extend existing DoubanBook model with wishlist sync fields
- Reuse existing BookStatus enum (19 states cover all scenarios)
- Add sync metadata to existing models

**API Contracts**:
- Extend existing services (no new APIs needed)
- Use existing CLI interface (main.py)
- Pipeline stages follow existing BaseStage pattern

**Test Strategy**:
- Extend existing test structure
- Use existing fixture patterns
- Follow real-config testing approach (no mocks)

**Output**: ✅ data-model.md, contracts/, quickstart.md, updated CLAUDE.md

## Phase 2: Task Planning Approach

**Task Generation Strategy**:
- Load existing codebase patterns for consistency  
- Generate minimal tasks extending current Pipeline
- Each new stage → stage test task [P]
- Each model extension → migration task [P]
- Integration tests for end-to-end workflow
- Update existing services rather than create new ones

**Ordering Strategy**:
- Database migration tasks first
- Service extension tasks [P] (parallel)
- New stage implementation tasks (dependent)
- Integration test tasks
- Documentation updates

**Estimated Output**: 12-15 numbered tasks (smaller scope due to existing architecture)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (extend existing Pipeline with new sync capability)  
**Phase 5**: Validation (run existing + new tests, validate sync workflow)

## Complexity Tracking
*No constitutional violations detected - extending existing architecture*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)  
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved  
- [x] Complexity deviations documented (none needed)

---
*Based on existing codebase patterns and project-specific standards*