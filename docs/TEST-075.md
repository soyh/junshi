# TEST-075 — StructuredAnalysis → Strategy Decision 最小消费契约

状态：ACTIVE
基线：TEST-074 verified

目标：让 StructuredAnalysis 作为 derived decision input 被现有 Strategy Decision context 消费，同时不改变 decision / execution 生命周期。

契约：
- StructuredAnalysis 只作为 derived input，不成为 canonical fact。
- Strategy 可消费 observed_facts、inferences、hypotheses、unknowns、signals，但必须保持原字段语义与 evidence provenance。
- unknowns 不得转换为事实、候选确认或 success evidence。
- StructuredAnalysis 不得创建、确认或执行 decision。
- candidate selection 继续 requires_explicit_decision / must_not_auto_select。
- action_decisions、action_executions、action_outcomes 生命周期不变。
- 不新增 StructuredAnalysis persistence。
- user/person isolation 不变。

验收：专项契约测试、Strategy 回归、全量 pytest，随后服务器真实 Qwen smoke test；仅验证 derived decision input 链路，不产生 side effect。
