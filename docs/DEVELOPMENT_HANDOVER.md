# Development Handover

更新时间：2026-08-30
当前阶段：TEST-087 — Outcome → Re-analysis Closure — VERIFIED
当前 Branch：test-087-outcome-reanalysis-closure
当前 HEAD：e139b860d31e765c42f2025162f6c6353faa6b60
上一阶段：TEST-086 — Action Decision → Execution Bridge — VERIFIED
下一阶段：TEST-088 — Real LLM + Real User Workflow — ACCEPTANCE

## 信息检索优先级（强制执行）

凡是需要检索、确认或定位的内容，必须首先从 GitHub 仓库 `soyh/junshi` 当前开发分支及其相关历史代码、测试、文档中查找。只有 GitHub 仓库中找不到所需信息时，才能要求用户从服务器端查找，并明确说明需要执行的服务器端命令及原因。

不得在尚未完成 GitHub 仓库检索的情况下，直接要求用户通过服务器端 `grep`、`sed`、日志或数据库查询来提供本应可以从 GitHub 确认的信息。

## 产品目标与架构冻结

本项目不是单纯聊天机器人或回复生成器，而是长期关系管理 + AI 恋爱决策辅助系统。

核心闭环：

`关系对象 → 人物档案 → 聊天/现实互动 → 时间线 → Canonical Evidence → Fact / Inference / Unknown → 关系状态 → Recommendation → Action Plan → User Decision / Confirmation → Execution → Outcome / Feedback → Learning / Memory Update → 重新判断`

主链实现：

`Canonical Data → Canonical Evidence / Domain Context → AnalysisContext → LLM Analysis → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis input`

冻结规则：

- AnalysisContext 是 deterministic、source-backed、read-only 的 LLM 输入。
- LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- inference / hypothesis / material signal 必须保留 evidence provenance。
- unknown 不得被模型猜测提升为事实。
- Strategy、Strategic Reply、Action Plan 只能消费既有 derived analysis，不建立第二套生命周期。
- Recommendation Producer 只接受显式 Recommendation candidate，不直接接受 StructuredAnalysis。
- Strategy → Recommendation 必须经过显式 candidate contract；candidate 必须携带稳定 identity、evidence_source_ids 和 provenance。
- Action Plan → Action Decision 必须消费既有 Action Plan 中的 recommendation identity，并受 confirmation boundary 约束。
- LLM 不得自动确认 decision、执行 action、发送消息、修改 relationship state、写入 learning history 或伪造 outcome。
- StructuredAnalysis 当前为 request-scoped output；如未来持久化，必须独立设计并新增 migration。
- Provider：Qwen / DashScope OpenAI-compatible API；provider adapter 与上层 contract 解耦。

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
TEST-086 Action Decision → Execution Bridge — VERIFIED
TEST-087 Outcome → Re-analysis Closure — VERIFIED

## TEST-086 — Action Decision → Execution Bridge

正式链路：

`Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis input`

TEST-086 的最小连接是在 Action Plan 命名空间下暴露既有 execution lifecycle，复用既有 `StrategyDecisionExecutionService`、execution schema 与 repository，不新增第二套 execution 生命周期，不新增 migration，不改变 action_decision / execution / outcome 表结构。

验收结论：TEST-086 已完成服务器验收并正式 VERIFIED。既有 confirmed-only execution、explicit execution、execution → outcome → feedback → learning 链路保持成立。

## TEST-087 — Outcome → Re-analysis Closure

### 目标

验证一次真实的 `Decision → Execution → Outcome → Feedback → Learning` 结果能够重新进入 Analysis，并继续进入 Recommendation，而不是停留在 outcome / learning 层。

TEST-087 的目标是补齐闭环连接，而不是新增第二套 analysis、learning 或 recommendation 生命周期。

### GitHub 变更范围

TEST-086 → TEST-087 的代码变更仅涉及：

- `backend/app/services/action_feedback_learning_synthesis.py`
- `backend/app/services/analysis_recommendation.py`
- `backend/app/services/learning_strategy_synthesis.py`
- `backend/tests/test_outcome_reanalysis_closure.py`

其中生产代码只有上述三个文件发生修改；没有 migration / database schema 变化，没有新增 repository / service lifecycle。

### 正式契约

`Action Execution → Outcome → Feedback → Learning → fresh AnalysisContext → StructuredAnalysis → Strategy → Recommendation`

必须满足：

- outcome 必须来自真实 persisted execution / outcome 生命周期，不能由 analysis 文本伪造；
- action feedback learning 必须保留 recommendation identity、learning status、observed outcome counts 与 source provenance；
- re-analysis 必须重新读取最新 canonical evidence 与 learning input，而不是复用旧的 analysis 结果；
- StructuredAnalysis 仍只是 derived analysis，不得升级为 canonical fact / memory；
- Recommendation 必须继续经过 Strategy candidate → RecommendationProducer 的 evidence-backed boundary；
- Recommendation 不自动选择、不自动确认、不自动执行；
- `must_not_auto_select=true` 与 `must_not_auto_execute=true` 继续成立。

### TEST-086 → TEST-087 回归审计结论

已完成 TEST-086 已锁定契约逐项回归审计。TEST-087 没有破坏 Action Plan-scoped execution、confirmed-only execution、Outcome 前置条件、Feedback / Learning provenance 或 user/person isolation。

对 TEST-087 中删除的 45 行测试覆盖已进行语义审计：删除部分属于重复/旧路径覆盖，不构成已锁定生产契约的缺失；本阶段不重新扩大测试范围。`evidence` fallback 的行为仍保持与现有 downstream contract 一致，不被错误升级为 canonical source。

### TEST-087 验收状态

TEST-087 已完成正式验收并锁定：

- Branch：`test-087-outcome-reanalysis-closure`
- HEAD：`e139b860d31e765c42f2025162f6c6353faa6b60`
- commit message：`fix: preserve canonical unknown outcome field in learning synthesis`
- working tree：验收结论为 clean
- migration / database schema：无变化
- 三个生产代码修改已完成审计，不再修改
- 45 行测试删除已完成回归审计，不重新扩大范围
- Outcome → Feedback → Learning → Re-analysis → Recommendation 闭环已锁定

TEST-087 正式标记为 VERIFIED。

## 当前系统闭环状态

截至 TEST-087，系统已经形成：

`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis input → Recommendation`

这意味着 MVP 的核心技术闭环已经从“生成建议”推进到“执行结果能够反哺下一轮判断”。后续不应为了堆叠 schema / service / test 数量继续扩张，而应验证真实用户工作流是否能够稳定运行。

## 数据库与运行约束

当前 migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。

TEST-045 ~ TEST-087 默认不新增 migration，不改变 action_decisions、action_executions、action_outcomes 的既有生命周期。

Route → Service → Repository → SQLite。

所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

## 持续禁止事项

- 不得让 RecommendationProducer 直接消费 StructuredAnalysis。
- 不得把 inference 自动写入 canonical evidence 或 memory。
- 不得自动确认 decision、执行 action、发送消息、修改 relationship 或伪造 outcome。
- 不得为了测试方便绕过 user / person / conversation isolation。
- 不得建立第二套 Strategy / Decision / Strategic Reply / Action Plan / Execution / Learning 生命周期。
- 不得为了填充 Action Plan 而绕过 canonical evidence → recommendation → confirmation 链。
- 不得在 GitHub 已能确认时要求服务器端查询。

## TEST-088 — Real LLM + Real User Workflow

下一阶段只做真实 LLM + 真实用户工作流验收，不预先新增架构层。

验收重点：

1. 真实用户建立 relationship / person / conversation；
2. 写入真实聊天与现实互动 evidence；
3. 通过 AnalysisContext 进入真实 Qwen / DashScope provider；
4. 生成 StructuredAnalysis，并确认 Fact / Inference / Unknown 与 provenance 边界；
5. 进入 Strategy → Recommendation → Action Plan → Action Decision；
6. 用户显式确认后才允许 Execution；
7. 记录真实 Outcome；
8. Outcome → Feedback → Learning；
9. 下一轮 Analysis 能看到最新 evidence 与 learning input；
10. Recommendation 仍不得自动选择、确认或执行。

TEST-088 的核心不是继续增加代码，而是证明上述闭环在真实 LLM 和真实用户操作下可以完成一次可追踪、可解释、可反馈的关系决策循环。
