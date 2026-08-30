# AI Love Strategist Development Handover

更新时间：2026-08-30
当前阶段：TEST-081 — Recommendation Producer Contract — IMPLEMENTED, PENDING SERVER ACCEPTANCE
当前 Branch：test-081-recommendation-producer-contract
当前 HEAD：9aadc18e37581c42d932cc5da5bd7373e6511b11
上一阶段：TEST-080 — StructuredAnalysis → Action Plan Candidate Boundary — VERIFIED

---

## 信息检索优先级（强制）

凡是需要检索、确认或定位的内容，首先从 GitHub 仓库 `soyh/junshi` 当前开发分支及历史代码、测试、文档中查找。只有 GitHub 找不到时，才能要求服务器端查询，并必须说明原因及命令。

不得在尚未完成 GitHub 检索前，要求用户通过服务器端 grep、sed、日志或数据库查询来确认本可由仓库确认的信息。

---

## 产品核心目标

本项目不是单纯聊天机器人或回复生成器，而是长期关系管理 + AI 恋爱决策辅助系统。

核心闭环：

`关系对象 → 人物档案 → 聊天/现实互动 → 时间线 → Canonical Evidence → Fact / Inference / Unknown → 关系状态 → Recommendation → Action Candidate → User Confirmation → Execution → Outcome / Feedback → Learning / Memory Update → 重新判断`

必须严格区分：

- Fact：canonical data / canonical evidence 支持的现实信息。
- Inference：基于事实形成的 derived interpretation，必须保留 provenance。
- Unknown：证据不足时保持未知，不得由模型猜测补全。
- Recommendation：基于当前证据、推断、未知及关系状态形成的决策建议；不等同于事实、推断或 action candidate。

最终系统目标是形成“AI 恋爱军师”，而不是“AI 回复生成器”。

---

## 架构冻结

正式契约：`docs/ANALYSIS_LLM_STRATEGY_CONTRACT.md`

主链：

`Canonical Data → Canonical Evidence / Domain Context → AnalysisContext → LLM Analysis → StructuredAnalysis → Strategy → Human Confirmation → Execution / Outcome`

冻结规则：

- AnalysisContext 是 deterministic、source-backed、read-only 的 LLM 输入。
- LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- StructuredAnalysis 中 inference / hypothesis / material signal 必须保留 evidence provenance。
- unknown 不得被模型猜测自动提升为事实。
- Strategy、Strategic Reply、Action Plan 只能消费既有 derived analysis，不建立第二套生命周期。
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

---

## TEST-080 正式边界

Commit：`e7b431bf7364b9f5c2aa4861f90c9c1b66456090` — `test: enforce analysis action candidate boundary`

TEST-080 focused regression：23 passed；full regression：480 passed。

锁定规则：

- StructuredAnalysis 是 derived interpretation。
- StructuredAnalysis 不能直接成为 Recommendation。
- StructuredAnalysis 不能直接成为 Action Candidate / proposal。
- 即使 hypothesis / intent signal 高置信度且文本具有 action-like 内容，也不能自动进入 `recommendations` 或 `action_plan`。
- 只有 explicit、evidence-backed recommendation 才能进入既有 Action Plan promotion。
- 不新增 migration，不修改 Action Plan / Decision / Execution 生命周期。

---

## TEST-081 — Recommendation Producer Contract

### 审计结论

TEST-080 后从 GitHub 当前分支完成 Recommendation 全量审计，确认：

1. `RecommendationService.get_context()` 原先只是 Recommendation Context façade，`recommendations` 固定为空。
2. `backend/app/schemas/recommendation.py` 原先没有 Recommendation Item schema，仅有 `recommendations: list[Any]`。
3. Strategic Reply 与 Action Plan 都消费 `RecommendationService` 输出，但不存在真实 typed producer。
4. Action Plan 唯一 promotion 边界已经存在于 `ActionPlanService.build_action_plan()`：必须有非空 action、非空 evidence_source_ids，且所有 source id 必须命中 canonical evidence；生成 proposal 后必须 user confirmation。
5. Strategic Reply 也要求 reply + evidence_source_ids，并且不会自动发送。
6. Learning Strategy candidates 是学习层 candidate，不得被误认为 Recommendation。
7. Confirmation / Decision / Execution 已保持独立生命周期，TEST-081 不应修改这些层。

因此 TEST-081 的真实缺口确定为：建立 typed、evidence-backed、显式 candidate 驱动的 Recommendation Producer，而不是把 StructuredAnalysis 自动转换为 Recommendation。

### TEST-081 实现

新增/修改：

- `backend/app/schemas/recommendation.py`
- `backend/app/services/recommendation_producer.py`
- `backend/app/services/recommendation.py`
- `backend/tests/test_recommendation_producer.py`

核心 schema：`Recommendation`

字段：

- `id`
- `recommendation`
- `evidence_source_ids`
- `action`（可选）
- `reply`（可选）
- `priority`（可选）
- `time_horizon`（可选）
- `provenance`

schema 使用 `extra="forbid"`，Recommendation Context 的 `recommendations` 从 `list[Any]` 收紧为 `list[Recommendation]`。

Producer：`RecommendationProducer.produce(candidates, evidence)`。

Producer 规则：

- 只接受显式 candidate dict，不接受 `StructuredAnalysis` 类型作为输入协议。
- candidate 必须有非空 id、recommendation、evidence_source_ids、provenance。
- 所有 evidence_source_ids 必须命中 canonical evidence 的 `source_id`。
- malformed / unprovenanced / unknown-source candidate 被拒绝。
- 保持 candidate 顺序，输出 deterministic。
- producer 不写数据库、不修改 canonical evidence、不确认 decision、不执行 action、不发送消息。
- producer 不把 unknown 写入 facts，也不把 StructuredAnalysis 的 action-like 文本直接提升为 recommendation。

`RecommendationService.produce_recommendations()` 仅作为既有 Service 层的 producer façade；`get_context()` 的 canonical read-only 行为保持不变。

### TEST-081 下游兼容边界

合法 Recommendation 进入既有 downstream：

`Recommendation → ActionPlanService.build_action_plan() → proposed → requires_user_confirmation`

以及：

`Recommendation → StrategicReplyService.build_draft() → user-controlled draft`

TEST-081 不改变：

`Action Decision → Confirmation → Execution → Outcome`

也不改变 Learning / Memory 生命周期。

### TEST-081 测试覆盖

`backend/tests/test_recommendation_producer.py` 已锁定：

- Recommendation schema typed contract。
- unknown field rejection。
- explicit evidence-backed candidate production。
- missing / unknown / partial evidence provenance rejection。
- StructuredAnalysis 不得直接 promotion。
- Unknown preservation。
- deterministic ordering。
- 与既有 Action Plan / Strategic Reply downstream contract 的兼容性。
- Recommendation Context response 的 typed validation。

### TEST-081 提交记录

`eb649c30c06a1532740744759a6e56e144ff9781` — `feat: add typed recommendation contract`

`408d2cc19590c906392e68a806d88d2687baeaac` — `feat: add recommendation producer boundary`

`84b58d583f45f01f388d912ebdcfb9a5dd69a4c3` — `feat: expose recommendation producer through service`

`9aadc18e37581c42d932cc5da5bd7373e6511b11` — `test: lock recommendation producer contract`

本 handover 更新为独立文档 commit；TEST-081 在服务器完整回归通过前保持 `PENDING SERVER ACCEPTANCE`。

---

## TEST-081 服务器最终验收门槛

用户验收前必须在服务器执行：

1. `git fetch origin`
2. 切换到 `test-081-recommendation-producer-contract`
3. 确认 HEAD 与 GitHub 分支一致，working tree clean。
4. 执行 Recommendation 专项测试：
   - `pytest -q backend/tests/test_recommendation.py backend/tests/test_recommendation_producer.py`
5. 执行 downstream 回归：
   - Recommendation
   - Strategic Reply
   - Action Plan
   - Strategy Decision / Confirmation
   - Execution / Outcome
   - Learning Strategy
6. 执行完整 `pytest -q`。
7. `git diff --check` 必须通过。
8. 验证没有新增 migration、没有数据库 schema 变化。
9. 验证没有 action_decisions / action_executions / action_outcomes 自动 side effect。
10. 验证 `GET /health` 正常，若进行 HTTP 验证则继续使用 `127.0.0.1:18080`，禁止使用 8899。

TEST-081 在上述服务器验收完成前不得标记 VERIFIED。

---

## 数据库与运行约束

当前 migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。

TEST-045 ~ TEST-081 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

Route → Service → Repository → SQLite。

所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

---

## 持续禁止事项

- 不得把 StructuredAnalysis 直接转换为 Recommendation。
- 不得把 StructuredAnalysis 直接转换为 Action Candidate。
- 不得让 LLM 进入 canonical evidence、persistence、learning context、decision persistence 或 execution 层。
- 不得自动确认 decision、执行 action、发送消息、修改 relationship 或伪造 outcome。
- 不得为了测试方便绕过 user / person / conversation isolation。
- 不得建立第二套 Strategy / Decision / Strategic Reply / Action Plan 生命周期。
- 不得为了填充 Action Plan 而绕过 canonical evidence → recommendation → confirmation 链。
- 不得在 GitHub 已能确认时要求服务器端查询。

---

## 下一阶段

TEST-081 服务器验收完成后，先根据实际结果决定是否 VERIFIED，再重新从 GitHub 当前分支审计下一阶段真实产品缺口；不得预先假定继续扩大 LLM、自动执行或新增持久化。
