# Feature Specification: Event Contract Trading System

**Feature Branch**: `001-1-10-80`  
**Created**: 2025-09-10  
**Status**: Draft  
**Input**: User description: "# 事件合约交易系统需求文档

## 一、背景与目标

我们计划开发一个**事件合约交易系统**，交易对象为币安事件合约。该系统不进行自动化下单，而是通过实时信号分析、概率判断、风险管理和回测复盘，辅助交易者在人工下单时做出更理性的决策。目标是构建一个"概率优势管理器"，帮助用户识别并把握高概率场景，避免情绪化下注。

---

## 二、币安事件合约运行机制（必要解释）

1. **基本定义**：

   * 事件合约是一种二元预测产品，下注未来某时间点（如 10 分钟后）的价格是高于还是低于当前价格。
   * 若预测正确：返还本金 + 固定收益（通常为本金的 80% 左右）。
   * 若预测错误：亏损全部本金。

2. **赔率机制**：

   * 以"80% 收益"为例，下注 5 USDT，赢则返还 9 USDT（含本金），输则归零。
   * 对应隐含概率约为 55.6%。换言之，若胜率低于 55.6%，长期期望为负。

3. **风险特征**：

   * 盈亏对称，赔率固定 → 本质是赌场式二元分类问题。
   * 短周期波动和趋势反转点往往决定胜负。
   * 成功的关键是：长期保持 **实际胜率 > 隐含概率**。

---

## 三、系统要做什么

1. **生成信号**：基于 1 分钟 K 线和多周期指标，实时给出价格方向的概率判断。
2. **概率与赔率对比**：将模型预测胜率与平台赔率隐含概率比较，提示是否值得下注。
3. **人工提示**：在触发条件时，清晰告知用户：方向、预测胜率、概率优势大小、到期时间。
4. **风险管理**：控制下注频率、单次金额、并行仓位数，避免过度暴露和情绪化操作。
5. **回测与复盘**：利用历史数据模拟下注过程，统计胜率、期望收益、资金曲线，支持多种执行模式（首信号、连续信号、增强信号）。

---

## 四、核心功能特性与必要性

### 1. 信号处理与概率输出

* **功能**：输入市场数据，输出未来 T 分钟方向的胜率（如 62%）。
* **必要性**：事件合约是二元判定，概率预测是唯一的决策依据。

### 2. 概率与赔率比较

* **功能**：换算平台赔率隐含概率，并与模型预测胜率对比。
* **必要性**：确保只在"概率优势"存在时下注，避免负期望下注。

### 3. 风险管理模块

* **功能**：设定下注上限、频率限制、并行仓位数控制。
* **必要性**：降低连续错误信号导致的资金曲线崩溃，保持交易纪律。

### 4. 回测与复盘

* **功能**：基于历史数据模拟策略，输出胜率、期望收益、不同市况下表现。
* **必要性**：检验策略是否具有长期优势，避免过拟合和错觉。

### 5. 用户界面提示

* **功能**：在信号触发时直观显示"方向、概率、优势、剩余时间"。
* **必要性**：人工下单需要快速、透明的参考信息，减少认知负担。

---

## 五、开发与使用策略

* **开发策略**：

  * MVP 阶段聚焦信号生成、概率对比和简单回测。
  * 迭代阶段增加风险管理、复盘日志和多指标组合。
* **使用策略**：

  * 不追求高频交易，只在概率优势显著时下注。
  * 保持策略可解释性，帮助用户理解信号背后的逻辑。
* **回测策略**：

  * 使用 1 分钟 K 线生成 10 分钟事件结果。
  * 采用滚动验证，确保不出现"看未来"偏差。
  * 输出胜率、期望收益、资金曲线和覆盖率。

---

## 六、总结

本系统的价值不在于"自动下单"，而在于：

* **识别概率优势** → 提升长期期望。
* **限制风险暴露** → 保持资金曲线可控。
* **支持复盘学习** → 持续迭代策略。"

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies  
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a cryptocurrency trader, I want to receive probability-based signals for Binance event contracts so that I can make more informed manual trading decisions and avoid emotional betting. The system should analyze market data in real-time, compare prediction probabilities with platform odds, and provide clear trading recommendations with risk management guidance.

### Acceptance Scenarios
1. **Given** market data is flowing and the system detects a high-probability opportunity, **When** the predicted win rate exceeds the platform's implied probability by the minimum threshold, **Then** the system displays a clear signal showing direction, probability percentage, advantage size, and remaining time until contract expiry
2. **Given** the user has configured risk management parameters, **When** multiple signals trigger simultaneously, **Then** the system prevents exceeding the maximum parallel positions limit and enforces frequency restrictions
3. **Given** historical market data is available, **When** the user requests backtesting of the strategy, **Then** the system simulates trading decisions and outputs win rate, expected returns, and equity curve for the specified time period
4. **Given** the user wants to understand strategy performance, **When** accessing the review dashboard, **Then** the system displays comprehensive statistics including win rates across different market conditions and detailed trade logs

### Edge Cases
- What happens when market data feed is interrupted or delayed?
- How does the system handle conflicting signals from different timeframes?
- What occurs when the contract expires before the user can act on a signal?
- How does the system respond when risk limits are reached mid-session?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST analyze 1-minute candlestick data and multi-timeframe indicators to generate directional probability predictions
- **FR-002**: System MUST calculate platform odds implied probability and compare it with model predictions
- **FR-003**: System MUST display trading signals only when predicted win rate exceeds implied probability by [NEEDS CLARIFICATION: minimum advantage threshold not specified]
- **FR-004**: Users MUST be able to configure risk management parameters including bet limits, frequency restrictions, and maximum parallel positions
- **FR-005**: System MUST track all signal generations and outcomes for performance analysis
- **FR-006**: System MUST provide backtesting functionality using historical data with rolling validation to prevent look-ahead bias
- **FR-007**: System MUST display real-time signals showing direction, probability percentage, advantage size, and time remaining
- **FR-008**: System MUST enforce risk management rules preventing excessive exposure
- **FR-009**: System MUST generate performance reports including win rates, expected returns, and equity curves
- **FR-010**: System MUST support multiple execution modes: first signal only, continuous signals, and enhanced signals
- **FR-011**: System MUST maintain interpretable strategy logic to help users understand signal reasoning
- **FR-012**: System MUST handle [NEEDS CLARIFICATION: what specific market data sources - Binance API, websockets, etc.?]
- **FR-013**: System MUST store [NEEDS CLARIFICATION: data retention period not specified] of trading signals and market data for analysis

### Key Entities *(include if feature involves data)*
- **Trading Signal**: Represents a directional prediction with probability, timestamp, expiry time, and confidence level
- **Market Data**: 1-minute candlestick data including open, high, low, close, volume across multiple timeframes
- **Event Contract**: Binary prediction contract with strike price, expiry time, payout ratio, and implied probability
- **Risk Parameters**: User-configured limits including maximum bet size, daily frequency limits, and parallel position limits
- **Backtest Result**: Historical simulation output containing win rate, profit/loss, equity curve, and performance metrics
- **Performance Metrics**: Aggregated statistics including overall win rate, expected value, maximum drawdown, and market condition breakdowns

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain (3 clarifications needed)
- [x] Requirements are testable and unambiguous  
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed (pending clarifications)

---
