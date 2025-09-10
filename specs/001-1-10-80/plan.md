# Implementation Plan: Event Contract Trading System

**Branch**: `001-1-10-80` | **Date**: 2025-09-10 | **Spec**: /home/mikewong/proj/event-contract-v1/specs/001-1-10-80/spec.md
**Input**: Feature specification from `/specs/001-1-10-80/spec.md`

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
Event Contract Trading System for Binance binary prediction contracts. System analyzes 1-minute K-line data with multi-timeframe indicators to generate probability-based trading signals. Compares model predictions with platform odds to identify positive expected value opportunities. Provides risk management, backtesting capabilities, and manual trading decision support. Core value: "probability advantage manager" that helps traders identify high-probability scenarios while avoiding emotional betting.

## Technical Context
**Language/Version**: Python 3.11+ (specified for backtesting and runtime components)  
**Primary Dependencies**: FastAPI (dashboard backend), React + TailwindCSS (dashboard frontend), pandas/numpy (data analysis), websocket libraries (real-time data)  
**Storage**: Time-series database for market data, PostgreSQL for trading signals and risk parameters, file-based storage for backtest results  
**Testing**: pytest for Python components, Jest for React frontend  
**Target Platform**: Linux server deployment, web browser access
**Project Type**: web - multi-component system (dashboard + notification + backtesting + runtime)  
**Performance Goals**: <1s signal generation latency, real-time 1-minute K-line processing, efficient backtesting on historical data  
**Constraints**: Real-time data processing requirements, accurate probability calculations, risk management enforcement  
**Scale/Scope**: Single trader focus initially, 4 core components (dashboard, notifications, backtesting, runtime), strategy abstraction for backtest/live compatibility

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 4 (dashboard-backend, dashboard-frontend, backtesting, runtime) - EXCEEDS MAX OF 3
- Using framework directly? YES (FastAPI, React without wrappers)
- Single data model? YES (shared entities across components)
- Avoiding patterns? YES (direct database access initially)

**Architecture**:
- EVERY feature as library? YES (signal-generation, risk-management, backtesting, data-ingestion libraries)
- Libraries listed: signal-generation (probability calculations), risk-management (position limits), backtesting (historical simulation), data-ingestion (market data processing)
- CLI per library: YES (each library will have CLI with --help/--version/--format)
- Library docs: YES (llms.txt format planned)

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? YES (test MUST fail first)
- Git commits show tests before implementation? YES (will enforce)
- Order: Contract→Integration→E2E→Unit strictly followed? YES
- Real dependencies used? YES (actual databases, real market data APIs)
- Integration tests for: YES (all cross-component interactions, shared schemas)
- FORBIDDEN: Implementation before test, skipping RED phase - ACKNOWLEDGED

**Observability**:
- Structured logging included? YES (comprehensive logging across all components)
- Frontend logs → backend? YES (unified logging stream)
- Error context sufficient? YES (detailed error tracking for trading decisions)

**Versioning**:
- Version number assigned? YES (0.1.0 - initial version)
- BUILD increments on every change? YES (will enforce)
- Breaking changes handled? YES (parallel tests, migration plan for strategy compatibility)

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
   - Run `/scripts/update-agent-context.sh [claude|gemini|copilot]` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Trading API contract → FastAPI contract tests [P]
- WebSocket API contract → WebSocket integration tests [P]
- Each data model entity (7 entities) → SQLAlchemy model creation tasks [P]
- Core libraries: signal-generation, risk-management, backtesting, data-ingestion [P]
- Dashboard components: backend API, frontend React app
- Runtime engine for real-time processing
- Integration tests for component communication
- End-to-end tests for complete user workflows
- Implementation tasks to make all tests pass

**Ordering Strategy**:
- TDD order: Contract tests → Integration tests → E2E tests → Unit tests → Implementation
- Dependency order: Data models → Libraries → Services → APIs → UI → Runtime engine
- Infrastructure first: databases, message queues, then application code
- Mark [P] for parallel execution (independent libraries, isolated components)

**Component-Specific Task Breakdown**:
1. **Data Layer** (5-7 tasks): Models, migrations, repositories
2. **Core Libraries** (8-10 tasks): Signal generation, risk management, backtesting, data ingestion
3. **API Layer** (6-8 tasks): REST endpoints, WebSocket handlers, validation
4. **Dashboard** (8-10 tasks): React components, API integration, real-time updates
5. **Runtime Engine** (4-6 tasks): Market data streaming, signal processing, alert generation
6. **Testing & Integration** (6-8 tasks): Contract tests, integration tests, E2E tests
7. **Deployment** (3-4 tasks): Docker configuration, service orchestration, health checks

**Estimated Output**: 40-50 numbered, ordered tasks in tasks.md (higher count due to 4-component architecture)

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 4th project (runtime component) | Real-time market data processing requires separate runtime from backtesting for performance isolation | Combining with backtesting would create memory conflicts and different scaling requirements |
| Dashboard split (backend/frontend) | Web architecture requirement for user interaction with complex trading data visualization | Single project cannot serve both API and web UI efficiently for real-time trading signals |


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
- [x] Initial Constitution Check: PASS (with documented exceptions)
- [x] Post-Design Constitution Check: PASS (design maintains constitutional principles despite complexity)
- [x] All NEEDS CLARIFICATION resolved (research phase addressed all technical unknowns)
- [x] Complexity deviations documented (4 projects justified for performance and architectural isolation)

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*