# Event Contract Trading System Constitution

## Core Principles

### I. Library-First Architecture
Every feature starts as a standalone library with clear boundaries and responsibilities. Libraries must be self-contained, independently testable, and well-documented. Each library serves a specific purpose in the trading system ecosystem - no organizational-only libraries allowed.

**Requirements:**
- Signal generation library (probability calculations, market analysis)
- Risk management library (position sizing, exposure limits)
- Backtesting engine library (historical simulation, performance metrics)
- Data ingestion library (market data processing, real-time feeds)
- Notification library (third-party API integration for alerts)
- All libraries documented in llms.txt format for AI assistance

### II. CLI Interface Protocol
Every library exposes core functionality via command-line interface following strict text I/O protocols: stdin/args → stdout, errors → stderr. Support both JSON and human-readable formats for all outputs.

**Requirements:**
- `--help`, `--version`, `--format` flags mandatory for all CLI tools
- JSON output for programmatic integration
- Human-readable output for debugging and manual operations
- Backtesting results exportable via CLI in multiple formats
- Signal generation accessible via command line for testing

### III. Test-First Development (NON-NEGOTIABLE)
TDD methodology is mandatory: Tests written → User approved → Tests fail → Then implement. Red-Green-Refactor cycle strictly enforced for all components.

**Requirements:**
- Contract tests for all API endpoints before implementation
- Integration tests for market data processing pipelines
- End-to-end tests for complete trading signal workflows
- Unit tests for probability calculations and risk algorithms
- All tests must initially fail (RED phase) before implementation
- Git commits must show test creation before feature implementation

### IV. Integration Testing Priority
Focus areas requiring comprehensive integration testing due to system complexity and real-time requirements.

**Requirements:**
- New library contract tests (signal generation ↔ risk management)
- Contract changes affecting API consumers
- Inter-service communication (dashboard ↔ backtesting ↔ runtime)
- Shared schemas (market data formats, signal structures)
- Real-time data pipeline integration (WebSocket → processing → UI)
- Third-party API integrations (Binance, Telegram, Feishu)
- Use real dependencies (actual databases, market data APIs, not mocks)

### V. Observability & Performance
Comprehensive logging and monitoring required for real-time trading system reliability. All components must provide structured logging with unified log streaming.

**Requirements:**
- Structured JSON logging for all components
- Frontend logs streamed to backend for unified analysis
- Trading signal generation performance metrics (<1s latency)
- Market data processing latency tracking
- Error context sufficient for debugging in production
- Performance monitoring for backtesting efficiency
- Alert system for critical failures in real-time components

### VI. Versioning & Breaking Changes
MAJOR.MINOR.BUILD format with BUILD increments on every change. Critical for trading system where algorithm changes affect financial outcomes.

**Requirements:**
- Version tracking for all signal generation algorithms
- BUILD increment mandatory for any logic change
- Breaking changes require parallel testing with previous version
- Migration plan required for strategy algorithm updates
- Backtest result versioning to track performance across versions
- API versioning for dashboard and external integrations

### VII. Simplicity & YAGNI Principles
Start simple, add complexity only when proven necessary. Trading systems benefit from transparent, interpretable logic over complex abstractions.

**Requirements:**
- Maximum 4 projects justified by isolation needs (dashboard, backtesting, runtime, notifications)
- Direct framework usage (FastAPI, React) without wrapper abstractions
- Single data model per domain (no DTOs unless serialization differs significantly)
- Avoid Repository/UoW patterns unless proven necessary for testing
- Strategy abstraction must be minimal and interpretable
- No premature optimization of backtesting algorithms

## Security & Compliance

### Financial Data Protection
Trading system handles sensitive financial data and API keys requiring strict security measures.

**Requirements:**
- API keys and secrets never logged or committed to repositories
- Encrypted storage for trading credentials and connection strings
- Input validation for all market data to prevent injection attacks
- Rate limiting for API endpoints to prevent abuse
- Audit logging for all trading-related actions and decisions
- Secure communication channels for all external API integration

### Data Integrity
Market data accuracy is critical for trading decisions and backtesting validity.

**Requirements:**
- Data validation pipelines for all market data ingestion
- Checksums and integrity verification for historical data
- Redundant data sources where possible for critical market feeds
- Data retention policies for regulatory compliance
- Immutable audit trails for all trading signals generated
- Backup and recovery procedures for critical trading data

## Development Workflow

### Implementation Process
Structured development process ensuring quality and reliability for financial applications.

**Requirements:**
- All features begin with specification in `/specs/` directory
- Implementation plan required before coding begins
- Constitutional compliance check at design phase
- Peer review mandatory for all probability calculation changes
- Performance regression testing for backtesting engine updates
- User acceptance criteria must be measurable and testable

### Quality Gates
Quality assurance checkpoints throughout development lifecycle.

**Requirements:**
- Constitution compliance verification in all PRs
- Performance benchmarks must pass for real-time components
- Integration test suite must pass before deployment
- Security scan required for all external API integrations
- Backtesting accuracy validation against known historical scenarios
- Documentation updates required for all user-facing features

### Risk Management
Development practices specific to financial trading system risks.

**Requirements:**
- No automatic trading execution (manual decision support only)
- All probability calculations must be explainable and auditable
- Risk parameter changes require explicit approval process
- Backtesting must include worst-case scenario analysis
- Real-time monitoring dashboards for system health
- Incident response procedures for trading system failures

## Governance

### Constitutional Authority
This constitution supersedes all other development practices and guidelines. Any deviation must be explicitly documented and justified in the project's complexity tracking.

### Amendment Process
Constitutional amendments require:
- Documentation of the change and rationale
- Update of all dependent templates and documentation
- Approval from project stakeholders
- Migration plan for existing implementations
- Version increment and change log entry

### Compliance Verification
- All PRs and code reviews must verify constitutional compliance
- Architectural complexity must be justified in design documents
- Use `/memory/constitution_update_checklist.md` when amending constitution
- Regular constitutional compliance audits for the project
- Training and onboarding materials must include constitutional requirements

### Development Guidance
Use `CLAUDE.md` or equivalent agent-specific files for runtime development guidance that complements these constitutional principles.

**Version**: 1.0.0 | **Ratified**: 2025-09-10 | **Last Amended**: 2025-09-10