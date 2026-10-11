# TEST-075 — StructuredAnalysis → Strategy Decision 最小消费契约

状态：IMPLEMENTATION IN PROGRESS

目标：定义 StructuredAnalysis 作为 derived input 被现有 Strategy Decision 消费的最小契约，不建立新的 Strategy / Decision 生命周期。

主链：
`StructuredAnalysis → Strategy Decision Context → Existing Decision Lifecycle`

当前实现边界：
- `StrategyDecisionContextService.get_context(..., structured_analysis=...)` 接收 request-scoped StructuredAnalysis。
- `StrategyAnalysisBridgeService` 将允许的分析信号投影到 `decision_inputs.structured_analysis`。
- 投影字段固定为 observed_facts / inferences / hypotheses / emotional_signals / relationship_signals / risk_signals / intent_signals / unknowns。
- 每个分析项的 `evidence_source_ids` 原样保留。
- `decision_inputs.analysis_is_derived` 明确标记该输入不是 canonical decision fact。
- 原有 candidate identity、outcome counts、selection_status 保持不变。
- `selection_status` 仍为 `requires_explicit_decision`，不由分析结果确认。

必须保持：
- evidence provenance
- observed facts / inferences / hypotheses / unknowns 语义边界
- unknown 不得升级为确定性 decision fact
- candidate selection 必须显式决策
- LLM 不直接生成、确认或执行 decision
- 不新增 StructuredAnalysis persistence
- 不改变 action_decisions / action_executions / action_outcomes 生命周期
- 不进入 canonical evidence、persistence、learning history 或 execution 层
- user / person isolation 不变

当前专项契约测试覆盖：
- derived analysis 输入被 Strategy Decision Context 消费
- provenance 与 unknown 保留
- candidate identity / explicit decision boundary 保持
- StructuredAnalysis 不创建 decision / execution / outcome side effect
- 现有 decision inputs 不被分析结果覆盖或确认

下一步验收：
1. TEST-075 专项测试
2. 相关 Strategy Decision / Analysis Strategy 回归
3. 全量 pytest
4. 服务器 smoke test
5. 确认 action_decisions / action_executions / action_outcomes 无 side effect
