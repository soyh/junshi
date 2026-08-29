# TEST-075 — StructuredAnalysis → Strategy Decision 最小消费契约

状态：NEXT IMPLEMENTATION STAGE

目标：定义 StructuredAnalysis 作为 derived input 被现有 Strategy Decision 消费的最小契约，不建立新的 Strategy / Decision 生命周期。

主链：
`StructuredAnalysis → Strategy Decision Context → Existing Decision Lifecycle`

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

验收：专项契约测试、相关 Strategy 回归、全量 pytest、服务器 smoke test；确认无 decision / execution / outcome side effect。
