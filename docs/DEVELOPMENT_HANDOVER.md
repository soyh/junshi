# Development Handover

更新时间：2026-08-30
当前阶段：TEST-086 — Action Decision → Execution Bridge — IMPLEMENTED / AWAITING SERVER VALIDATION
当前 Branch：test-086-action-decision-execution-bridge
当前 HEAD：bcc43c41da747dab79669560bffbb619c4a25dbf
上一阶段：TEST-085 — Action Plan → Action Decision Bridge — VERIFIED

## 信息检索优先级（强制执行）

凡是需要检索、确认或定位的内容，必须首先从 GitHub 仓库 `soyh/junshi` 当前开发分支及其相关历史代码、测试、文档中查找。只有 GitHub 仓库中找不到所需信息时，才能要求用户从服务器端查找，并明确说明需要执行的服务器端命令及原因。

不得在尚未完成 GitHub 仓库检索的情况下，直接要求用户通过服务器端 `grep`、`sed`、日志或数据库查询来提供本应可以从 GitHub 确认的信息。

## 架构冻结

主链：`Canonical Data → Canonical Evidence / Domain Context → AnalysisContext → LLM Analysis → StructuredAnalysis → Strategy → Recommendation → Action Plan → Human Confirmation → Execution / Outcome → Feedback / Learning`

AnalysisContext 保持 deterministic、source-backed、read-only。LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。StructuredAnalysis 始终是 derived interpretation，不是 canonical truth；inference / hypothesis / material signal 必须保留 evidence provenance；unknown 不得被猜测提升为事实。Strategy / Strategic Reply / Action Plan 必须保持既有 decision / confirmation / execution 生命周期。

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 ~ TEST-064：VERIFIED
TEST-065 ~ TEST-069：Analysis Context bridges / evidence contract — VERIFIED
TEST-070 Analysis LLM Service — VERIFIED
TEST-071 Structured Analysis Strategy Bridge — VERIFIED
TEST-072 Analysis → Strategy Orchestration — VERIFIED
TEST-073 Qwen Provider Integration — VERIFIED
TEST-074 Analysis → Strategy formal entrypoint — VERIFIED
TEST-075 StructuredAnalysis → Strategy Decision 最小消费契约 — VERIFIED
TEST-076 StructuredAnalysis → Strategic Reply 消费契约 — VERIFIED
TEST-077 Strategic Reply downstream boundary — VERIFIED
TEST-078 StructuredAnalysis → Action Plan 消费契约 — VERIFIED
TEST-079 Learning Strategy → Action Plan HTTP Response Contract — VERIFIED
TEST-080 StructuredAnalysis → Action Plan Candidate Boundary — VERIFIED
TEST-081 Recommendation Producer Contract — VERIFIED
TEST-082 Execution / Action Decision Closure — VERIFIED
TEST-083 Strategy → Recommendation Candidate Contract — VERIFIED
TEST-084 Recommendation → Action Plan Orchestration Bridge — VERIFIED
TEST-085 Action Plan → Action Decision Bridge — VERIFIED
TEST-086 Action Decision → Execution Bridge — IMPLEMENTED / AWAITING SERVER VALIDATION

## TEST-083 — Strategy → Recommendation Candidate Contract

目标：补齐 Analysis → Strategy → Recommendation 的真实连接点，但不重写 Strategy、Evidence 或 Recommendation Producer 生命周期。

正式契约：

`StructuredAnalysis → Strategy boundary → explicit StrategyRecommendationCandidate → RecommendationProducer → Recommendation`

candidate 必须携带：

- `id`：稳定、确定性的 candidate identity；
- `recommendation`：显式建议文本；
- `evidence_source_ids`：直接依赖的 source identity；
- `provenance`：至少包含 `source=strategy_candidate`、candidate type、source evidence ids，并保留 unknowns。

RecommendationProducer 仍是最终 typed / evidence-backed boundary。StructuredAnalysis 不得直接进入 RecommendationProducer；无效 evidence / provenance 的 candidate 不得进入 Recommendation。

### TEST-083 服务器验收

- 定向 candidate / orchestration / producer 测试：`17 passed`
- 全量回归：`499 passed`
- working tree clean
- HEAD 与 origin 一致：`aeb5d53`
- 无 migration / database schema 变化

TEST-083 正式标记为 VERIFIED。

## TEST-084 — Recommendation → Action Plan Orchestration Bridge

目标：在不建立第二套 Action Plan 生命周期的前提下，补齐 Recommendation → Action Plan 的真实 orchestration bridge。

正式链路：

`Analysis → Strategy → Recommendation → existing Action Plan context → Action Plan`

最小修改面：仅在既有 `AnalysisActionPlanService` 上建立 recommendation 到 action-plan 的 orchestration bridge，不新增第二套 Action Plan 生命周期，不绕过 evidence / confirmation boundary。

核心语义：

- 获取既有 AnalysisContext 与 StructuredAnalysis；
- 通过既有 AnalysisRecommendationService 获取 typed recommendations；
- 获取既有 ActionPlanService context；
- recommendation 存在时调用既有 `ActionPlanService.build_action_plan(recommendations, evidence)`；
- 无 recommendation 时保持既有 action plan context，不凭空创建 proposal；
- Action Plan 继续遵守 evidence-backed、`requires_user_confirmation=true`、`must_not_auto_execute=true`、`must_not_change_relationship=true`；
- 不自动创建 Action Decision，不执行 action，不产生 outcome。

### TEST-084 服务器验收

- `backend/tests/test_analysis_action_plan.py`：`8 passed`
- 全量回归：`500 passed`
- working tree clean
- HEAD：`33a605ee093dbf82ae8723438a32d0880a7effcc`
- 无 migration / database schema 变化

TEST-084 正式标记为 VERIFIED。

## TEST-085 — Action Plan → Action Decision Bridge

目标：锁定 Action Plan → Action Decision 的最小真实连接契约，不新增 Decision 生命周期，不绕过 user confirmation / execution boundary。

正式链路：

`Recommendation → Action Plan → Action Decision Context / Decision persistence → User Confirmation → Execution → Outcome`

正式契约：

- Action Decision Context 消费既有 Action Plan，而不是重新生成 recommendation；
- Decision 中的 `recommendation_id` 必须属于当前 Action Plan 的 recommendation 集合；
- 非当前 Action Plan 的 recommendation 不得进入 Decision persistence；
- confirmed decision 必须显式携带 recommendation identity；
- Decision persistence 前仍必须经过既有 confirmation boundary；
- TEST-085 不自动确认、不执行 action、不生成 outcome。

### 最小修改面

TEST-085 不修改生产 Action Decision 生命周期；只新增边界测试 `backend/tests/test_action_decision.py`，验证已有 bridge 的真实契约。

Git commit：`51d8237c1aca56b3c993aa9254fe82efec4f7d86`

### TEST-085 服务器验收

- Branch：`test-085-action-plan-decision-bridge`
- HEAD：`51d8237c1aca56b3c993aa9254fe82efec4f7d86`
- HEAD 与 `origin/test-085-action-plan-decision-bridge` 完全一致
- `git status --short`：为空
- `pytest -q backend/tests/test_action_decision.py`：`10 passed`
- `pytest -q`：`502 passed in 74.64s`
- 无生产代码修改
- 无 migration / database schema 修改
- Action Decision / Execution / Outcome 生命周期保持不变

TEST-085 正式标记为 VERIFIED。

## TEST-086 — Action Decision → Execution Bridge

### GitHub 审计结论

TEST-085 完成后，仓库中已经存在可复用的 `StrategyDecisionExecutionService`、`ActionExecutionRepository` 与执行 schema。该 service 已经实现 confirmed decision → explicit execution 的状态边界，并阻止 rejected decision、重复 execution 以及 outcome 已存在时再次 execution。现有执行 API 位于 `strategy-decision` 路径，而 Action Plan → Action Decision 已正式位于 `action-plan` 路径，因此真实产品闭环缺口不是新的 execution 生命周期，而是缺少 Action Plan 命名空间下的 execution bridge。

同时，`ActionOutcomeService` 已要求 decision confirmed 且 execution 已存在后才能记录 outcome；`ActionFeedbackService` 已从 decision + outcome 形成反馈；`ActionFeedbackLearningSynthesisService` 已从反馈形成 source-backed learning candidate；`LearningStrategyContextService` 又把 action feedback learning 接入 learning context，`AnalysisService` 在重新取得 analysis context 时读取该 learning context。因此 Outcome → Feedback → Learning → 后续 Analysis 输入的连接点已经存在，不需要新增第二套 learning 生命周期。

### 正式链路

`Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis input`

### 最小修改面

TEST-086 只做以下最小连接：

- 新增 `backend/app/api/routes/action_execution.py`；
- 复用既有 `StrategyDecisionExecutionService`；
- 复用既有 `StrategyDecisionExecutionCreate / Response / ContextResponse` schema；
- 在 `backend/app/api/router.py` 注册 Action Plan execution route；
- 新增 `backend/tests/test_action_execution_bridge.py` 验证 Action Plan execution context、confirmed-only execution、explicit execution 以及 execution → outcome → feedback → learning 的真实连接。

不新增 service lifecycle，不新增 repository，不新增 migration，不改变 action decision / execution / outcome 表结构，不自动确认、不自动执行、不自动发送、不自动生成 outcome，也不把 inference 写入 memory / canonical evidence。

### GitHub 实施状态

- Branch：`test-086-action-decision-execution-bridge`
- 当前 HEAD：`bcc43c41da747dab79669560bffbb619c4a25dbf`
- 已新增 Action Plan execution route；
- 已复用既有 execution service / schema / repository；
- 已新增 `backend/tests/test_action_execution_bridge.py`；
- 未修改 migration / database schema；
- 尚未进行服务器验收，因此 TEST-086 当前不得标记 VERIFIED。

## 当前系统主链

截至 TEST-086 GitHub 实施后，目标主链为：

`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis input`

其中 TEST-083 / TEST-084 / TEST-085 / TEST-086 分别补齐：

- Strategy → Recommendation candidate contract；
- Recommendation → Action Plan orchestration bridge；
- Action Plan → Action Decision bridge contract；
- Action Decision → Action Plan-scoped Execution bridge。

## 数据库与运行约束

当前 migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。

TEST-045 ~ TEST-086 默认不新增 migration，不改变 action_decisions、action_executions、action_outcomes 的既有生命周期。

Route → Service → Repository → SQLite。

所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

## 持续禁止事项

- 不得让 RecommendationProducer 直接消费 StructuredAnalysis。
- 不得把 inference 自动写入 canonical evidence 或 memory。
- 不得自动确认 decision、执行 action、发送消息、修改 relationship 或伪造 outcome。
- 不得为了测试方便绕过 user / person / conversation isolation。
- 不得建立第二套 Strategy / Decision / Strategic Reply / Action Plan / Execution 生命周期。
- 不得为了填充 Action Plan 而绕过 canonical evidence → recommendation → confirmation 链。
- 不得在 GitHub 已能确认时要求服务器端查询。

## 下一阶段执行规则

TEST-086 在 GitHub 已完成最小实施，但尚未服务器验收。服务器验收通过后，先将 TEST-086 标记 VERIFIED，再重新审计完整闭环是否还存在真实缺口。下一阶段不得预先假定需要新增 schema、service、自动执行能力或 memory 写入能力。
