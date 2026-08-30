# AI Love Strategist Development Handover

更新时间：2026-08-30
当前阶段：TEST-083 — Strategy → Recommendation Candidate Contract — IMPLEMENTED / AWAITING SERVER VALIDATION
当前 Branch：test-083-strategy-recommendation-candidate-contract
上一阶段：TEST-082 — Execution / Action Decision Closure — VERIFIED

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

Phase 4 — End-to-End AI Relationship Loop：当前重点。建立 Person → Conversation / Interaction → Timeline → Evidence → Analysis → Strategy → Recommendation → Action Plan → Decision → Execution → Outcome → Feedback → Re-analysis 的系统级闭环。

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

### TEST-083 已实现内容

新增：

- `backend/app/services/strategy_recommendation_candidate.py`：Strategy → Recommendation candidate adapter。
- `backend/app/services/analysis_recommendation.py`：Analysis → Strategy → Recommendation orchestration。
- `backend/app/schemas/analysis_recommendation.py`：request-scoped response contract。
- `backend/app/api/routes/analysis_recommendation.py`：`GET /api/v1/conversations/{conversation_id}/recommendation/context`。
- 对应 TEST-083 candidate / orchestration contract tests。

修改：

- `backend/app/api/router.py` 注册新的 analysis recommendation route。

明确未修改：

- Recommendation schema 的核心 typed boundary。
- RecommendationProducer 的 evidence validation。
- Strategy Decision persistence / confirmation / execution / outcome lifecycle。
- 数据库 schema / migration。
- Action Decision / Execution / Outcome 生命周期。

### TEST-083 验收门槛

服务器端拉取本分支后必须至少验证：

1. `pytest -q backend/tests/test_strategy_recommendation_candidate.py backend/tests/test_analysis_recommendation.py backend/tests/test_recommendation_producer.py`
2. `pytest -q`
3. `git diff --check`
4. `git status --short` 必须为空。
5. 新 endpoint 可以在真实 conversation 上返回 typed recommendations，且 recommendation 的 evidence_source_ids 能在返回 evidence 中找到。
6. 无证据 candidate 被 RecommendationProducer 丢弃。
7. recommendation 不自动进入 confirmation / execution。
8. 未发生 migration / database schema 变化。

TEST-083 在服务器完整回归通过前，不得标记 VERIFIED，也不得进入 TEST-084。

---

## 数据库与运行约束

当前 migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。

TEST-045 ~ 当前阶段默认不新增 migration，不改变 action_decisions、action_executions、action_outcomes 的既有生命周期。

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

## 下一步执行规则

TEST-083 已在 GitHub 当前分支完成实现，当前只等待服务器端验证。服务器验证通过后，先更新 TEST-083 为 VERIFIED，再根据真实 end-to-end 链路缺口决定 TEST-084；不得在 TEST-083 未验收时继续堆叠下一层功能。
