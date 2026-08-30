# AI Love Strategist Development Handover

更新时间：2026-08-30
当前阶段：TEST-085 — Action Plan → Action Decision Bridge — VERIFIED
当前 Branch：test-085-action-plan-decision-bridge
当前 HEAD：51d8237c1aca56b3c993aa9254fe82efec4f7d86
上一阶段：TEST-084 — Recommendation → Action Plan Orchestration Bridge — VERIFIED

---

## 信息检索优先级（强制）

凡是需要检索、确认或定位的内容，首先从 GitHub 仓库 `soyh/junshi` 当前开发分支及历史代码、测试、文档中查找。只有 GitHub 找不到时，才能要求服务器端查询，并必须说明原因及命令。

不得在尚未完成 GitHub 检索前，要求用户通过服务器端 grep、sed、日志或数据库查询来确认本可由仓库确认的信息。

---

## 产品最终目标与实现路线

本项目不是单纯聊天机器人或回复生成器，而是长期关系管理 + AI 恋爱决策辅助系统。

最终核心闭环：

`关系对象 → 人物档案 → 聊天/现实互动 → 时间线 → Canonical Evidence → Fact / Inference / Unknown → 关系状态 → Recommendation → Action Plan → User Decision / Confirmation → Execution → Outcome / Feedback → Learning / Memory Update → 重新判断`

必须严格区分：

- Fact：canonical data / canonical evidence 支持的现实信息。
- Inference：基于事实形成的 derived interpretation，必须保留 provenance。
- Unknown：证据不足时保持未知，不得由模型猜测补全。
- Recommendation：基于当前证据、推断、未知及关系状态形成的决策建议；不等同于事实、推断或 action candidate。

最终系统目标是形成“AI 恋爱军师”，而不是“AI 回复生成器”。

### 后续总路线

开发策略从“持续堆叠功能”切换为“优先打通真实可运行的关系决策闭环”。不再以 schema / service / test 数量作为主要进度指标，而以真实用户能否完成一次可追踪、可解释、可反馈的关系决策循环作为 MVP 核心验收标准。

Phase 1 — Core Data Foundation：基本完成。

Phase 2 — Evidence / Analysis / Strategy：主体已完成，持续完善边界。

Phase 3 — Decision → Execution Closure：已完成 TEST-082，后续只补齐真正进入闭环所需的最小连接。

Phase 4 — End-to-End AI Relationship Loop：当前重点。已打通 Analysis → Strategy → Recommendation → Action Plan → Action Decision 的主要 orchestration / contract bridge，下一步应继续根据真实闭环缺口推进，而不是预设新增架构层。

Phase 5 — Real LLM + Real User Workflow：在闭环稳定后接入真实 LLM 与真实用户工作流，确保 LLM 只负责解释、归纳、推断和候选建议，系统负责事实、provenance、状态、确认、执行和结果记录。

Phase 6 — Relationship Memory / Learning：基于现实执行结果和用户确认形成长期关系记忆与状态更新；禁止把 AI 推断自动当成事实或长期记忆。

Phase 7 — Optimization / Scale：在 MVP 闭环稳定后，再增加人物画像增强、关系趋势、风险检测、策略优化、多候选策略、策略效果统计等高级能力。

### 六条持续原则

1. 不为 schema 而 schema。
2. 不为 test 数量而 test。
3. 不让 LLM 直接成为事实来源。
4. 不让 inference 自动变成 memory。
5. 不让 Recommendation 绕过 User Confirmation。
6. 每增加一个能力，都必须回答它如何进入完整关系闭环。

---

## 架构冻结

正式契约：`docs/ANALYSIS_LLM_STRATEGY_CONTRACT.md`

主链：

`Canonical Data → Canonical Evidence / Domain Context → AnalysisContext → LLM Analysis → StructuredAnalysis → Strategy → Recommendation → Human Confirmation → Execution / Outcome`

冻结规则：

- AnalysisContext 是 deterministic、source-backed、read-only 的 LLM 输入。
- LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- StructuredAnalysis 中 inference / hypothesis / material signal 必须保留 evidence provenance。
- unknown 不得被模型猜测自动提升为事实。
- Strategy、Strategic Reply、Action Plan 只能消费既有 derived analysis，不建立第二套生命周期。
- Recommendation Producer 只接受显式的 Recommendation candidate，不直接接受 StructuredAnalysis。
- Strategy → Recommendation 必须经过显式 candidate contract；candidate 必须携带 recommendation identity、evidence_source_ids 和 provenance。
- Action Plan → Action Decision 必须消费既有 Action Plan 中的 recommendation identity；Decision persistence 仍受 confirmation boundary 约束。
- LLM 不得自动确认 decision、执行 action、发送消息、修改 relationship state、写入 learning history 或伪造 outcome。
- StructuredAnalysis 当前为 request-scoped output；如未来持久化，必须独立设计并新增 migration。
- Provider：Qwen / DashScope OpenAI-compatible API；provider adapter 与上层 contract 解耦。

---

## 已完成阶段

TEST-008 ~ TEST-044：VERIFIED
TEST-045 Strategy Decision Lifecycle — VERIFIED
TEST-046 Strategy Decision Lifecycle Synthesis — VERIFIED
TEST-047 Strategy Decision Learning Input — VERIFIED
TEST-048 Strategy Decision Learning Synthesis — VERIFIED
TEST-049 Strategy Decision Learning Bridge — VERIFIED
TEST-050 Strategy Decision Learning Synthesis Bridge — VERIFIED
TEST-051 Learning Strategy Recommendation Bridge — VERIFIED
TEST-052 Learning Strategy Strategic Reply Bridge — VERIFIED
TEST-053 Learning Strategy Action Plan Bridge — VERIFIED
TEST-054 Learning Strategy Downstream Candidate Contract — VERIFIED
TEST-055 Learning Strategy Downstream Constraint Contract — VERIFIED
TEST-056 Learning Strategy Downstream Memory Update Semantics — VERIFIED
TEST-057 Learning Strategy Downstream Candidate Parity — VERIFIED
TEST-058 Learning Strategy Source Provenance — VERIFIED
TEST-059 Learning Strategy Provenance Immutability — VERIFIED
TEST-060 Learning Strategy Source Provenance Completeness — VERIFIED
TEST-061 Learning Strategy Provenance Parity — VERIFIED
TEST-062 Learning Strategy Decision Provenance Parity — VERIFIED
TEST-063 Learning Strategy Decision Constraint Parity — VERIFIED
TEST-064 Learning Strategy Decision Learning Evidence Completeness — VERIFIED
TEST-065 Analysis Context learning-strategy bridge — VERIFIED
TEST-066 Analysis Context relationship-state bridge — VERIFIED
TEST-067 Analysis Context canonical evidence bridge — VERIFIED
TEST-068 Analysis Context conversation evidence bridge — VERIFIED
TEST-069 Analysis Context evidence contract sync — VERIFIED
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

---

## TEST-082 正式状态

TEST-082 已完成服务器验收：在执行边界正式要求 execution 先于 action outcome 后，所有 downstream outcome / learning / provenance 测试已对齐；完整回归最终为 `491 passed`；`git diff --check` 通过；working tree clean；无 migration / database schema 变化。

正式生命周期：

`Recommendation → Action Plan → Action Decision → User Confirmation → Execution → Outcome`

未确认 decision 不得执行；未执行不得产生 outcome；Execution 与 Outcome 保持独立记录；不得由 analysis / recommendation / decision 文本伪造真实执行结果。

---

## TEST-083 — Strategy → Recommendation Candidate Contract

### 目标

补齐 Analysis → Strategy → Recommendation 的真实连接点，但不重写 Strategy、Evidence 或 Recommendation Producer 生命周期。

当前仓库审计确认：现有 learning strategy candidate 主要是历史反馈/学习 candidate，字段以 `recommendation_id`、outcome counts、memory update count、unknowns、source 为主，不能直接满足 Recommendation Producer 所要求的 `id / recommendation / evidence_source_ids / provenance` contract。因此 TEST-083 不把 learning candidate 强行伪装成 Recommendation。

### 正式契约

`StructuredAnalysis → Strategy boundary → explicit StrategyRecommendationCandidate → RecommendationProducer → Recommendation`

Strategy → Recommendation 的最小 candidate contract：

- `id`：稳定、确定性的 candidate identity。
- `recommendation`：显式建议文本。
- `evidence_source_ids`：该建议直接依赖的 source identity。
- `provenance`：至少标记 `source=strategy_candidate`、candidate type、source evidence ids，并保留 unknowns。

`RecommendationProducer` 仍是最终 typed / evidence-backed boundary：

- source id 不存在于 evidence 时，candidate 不得进入 Recommendation。
- provenance 缺失时，candidate 不得进入 Recommendation。
- StructuredAnalysis 不得直接作为 Recommendation 输入。
- Recommendation 不自动选择、不自动执行、不自动确认 decision。

### TEST-083 验收状态

服务器已完成验证：

- 定向 candidate / orchestration / producer 测试：`17 passed`
- 全量回归：`499 passed`
- working tree clean
- HEAD 与 origin 一致：`aeb5d53`

TEST-083 正式标记为 VERIFIED。

---

## TEST-084 — Recommendation → Action Plan Orchestration Bridge

### 目标

在不建立第二套 Action Plan 生命周期的前提下，补齐 Recommendation → Action Plan 的真实 orchestration bridge。

### 正式链路

`Analysis → Strategy → Recommendation → existing Action Plan context → Action Plan`

### 最小修改面

TEST-084 只在既有 `AnalysisActionPlanService` 上建立 recommendation 到 action-plan 的 orchestration bridge；不新增第二套 Action Plan service，不绕过既有 evidence / confirmation boundary。

核心语义：

- AnalysisActionPlanService 获取现有 AnalysisContext 与 StructuredAnalysis。
- 通过既有 AnalysisRecommendationService 获取 typed recommendations。
- 获取既有 ActionPlanService context。
- 当 recommendation 存在时，调用既有 ActionPlanService 的 `build_action_plan(recommendations, evidence)`。
- 没有 recommendation 时保持既有 action plan context，不凭空创建 proposal。
- Action Plan 仍必须遵守 evidence-backed 与 `requires_user_confirmation=true` / `must_not_auto_execute=true` / `must_not_change_relationship=true` 约束。
- 不自动创建 Action Decision，不执行 action，不产生 outcome。

### TEST-084 验收状态

服务器已完成验证：

- `backend/tests/test_analysis_action_plan.py`：`8 passed`
- 全量回归：`500 passed`
- working tree clean
- HEAD：`33a605ee093dbf82ae8723438a32d0880a7effcc`

TEST-084 正式标记为 VERIFIED。

---

## TEST-085 — Action Plan → Action Decision Bridge

### 目标

锁定 Action Plan → Action Decision 的最小真实连接契约，不新增 Decision 生命周期，不绕过 user confirmation / execution boundary。

### 正式链路

`Recommendation → Action Plan → Action Decision Context / Decision persistence → User Confirmation → Execution → Outcome`

### 正式契约

- Action Decision Context 消费既有 Action Plan，而不是重新生成 recommendation。
- Decision 中的 `recommendation_id` 必须属于当前 Action Plan 的 recommendation 集合。
- 非当前 Action Plan 的 recommendation 不得进入 Decision persistence。
- confirmed decision 必须显式携带 recommendation identity。
- Decision persistence 前仍必须经过既有 confirmation boundary。
- TEST-085 不自动确认、不执行 action、不生成 outcome。

### 最小修改面

TEST-085 不修改生产 Action Decision 生命周期；只新增边界测试 `backend/tests/test_action_decision.py`，验证已有 bridge 的真实契约。

Git commit：`51d8237c1aca56b3c993aa9254fe82efec4f7d86`

### TEST-085 服务器验收

服务器已完成正式验收：

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

---

## 当前系统已打通的主链

截至 TEST-085，代码与测试已经形成：

`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Execution → Outcome`

其中 TEST-083 / TEST-084 / TEST-085 分别补齐了：

- Strategy → Recommendation candidate contract；
- Recommendation → Action Plan orchestration bridge；
- Action Plan → Action Decision bridge contract。

这些阶段均未建立第二套生命周期，也未引入新的数据库 migration。

---

## 数据库与运行约束

当前 migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。

TEST-045 ~ TEST-085 默认不新增 migration，不改变 action_decisions、action_executions、action_outcomes 的既有生命周期。

Route → Service → Repository → SQLite。

所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

---

## 持续禁止事项

- 不得让 RecommendationProducer 直接消费 StructuredAnalysis。
- 不得把 inference 自动写入 canonical evidence 或 memory。
- 不得自动确认 decision、执行 action、发送消息、修改 relationship 或伪造 outcome。
- 不得为了测试方便绕过 user / person / conversation isolation。
- 不得建立第二套 Strategy / Decision / Strategic Reply / Action Plan 生命周期。
- 不得为了填充 Action Plan 而绕过 canonical evidence → recommendation → confirmation 链。
- 不得在 GitHub 已能确认时要求服务器端查询。

---

## 下一阶段执行规则

TEST-085 已完成并 VERIFIED。下一阶段必须先从 GitHub 当前 `test-085-action-plan-decision-bridge` 分支审计真实代码、测试与文档，重点检查：

1. Recommendation → Action Plan → Action Decision 是否已经形成可验证的 request-scoped / persistence-safe 闭环；
2. User Confirmation → Execution → Outcome 是否仍保持真实状态边界；
3. Execution / Outcome → Feedback / Learning 的现有连接点是否存在真实缺口；
4. 是否存在无需新增架构、只需最小 orchestration / contract test 即可补齐的下一项闭环缺口。

不得预先假定下一项一定是新 schema、新 service 或自动执行能力。必须先审计，再锁定下一个 TEST 的最小真实产品边界。
