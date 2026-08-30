# AI Love Strategist Development Handover

更新时间：2026-08-30
当前阶段：TEST-080 — StructuredAnalysis → Action Plan Candidate Boundary — VERIFIED
当前 Branch：test-080-structured-analysis-action-plan-candidate-contract
当前 HEAD：e7b431bf7364b9f5c2aa4861f90c9c1b66456090
上一阶段：TEST-079 — Learning Strategy → Action Plan HTTP Response Contract — VERIFIED
最近一次服务器验收：全量 480 passed；TEST-080 专项回归 23 passed；无 action_decisions / action_executions / action_outcomes side effect。

---

## 信息检索优先级（强制）

凡是需要检索、确认或定位的内容，首先从 GitHub 仓库 `soyh/junshi` 当前开发分支及其历史代码、测试、文档中查找。只有 GitHub 找不到时，才能要求服务器端查询，并必须说明原因及命令。

不得在尚未完成 GitHub 检索前，直接要求用户通过服务器端 grep、sed、日志或数据库查询提供本可由 GitHub 确认的信息。

---

## 产品核心目标

本项目不是单纯聊天机器人或回复生成器，而是长期关系管理 + AI 恋爱决策辅助系统。

核心闭环：

```text
关系对象
  ↓
人物档案
  ↓
聊天记录 / 现实互动
  ↓
关系时间线
  ↓
Canonical Evidence
  ↓
Fact / Inference / Unknown
  ↓
关系状态与变化判断
  ↓
Recommendation
  ↓
Action Candidate
  ↓
User Confirmation
  ↓
Execution
  ↓
Outcome / Feedback
  ↓
Learning / Memory Update
  ↓
重新判断
```

必须长期严格区分：

```text
Fact
事实：canonical data / canonical evidence 支持的现实信息。

Inference
推断：基于事实形成的 derived interpretation，必须保留 evidence provenance。

Unknown
未知：证据不足时必须显式保持未知，不得由模型猜测补全。

Recommendation
建议：基于事实、推断、未知及关系状态给出的决策建议，不等同于事实、推断或 action candidate。
```

---

## 架构冻结：Analysis → LLM → StructuredAnalysis → Strategy

正式契约：`docs/ANALYSIS_LLM_STRATEGY_CONTRACT.md`

主链：

`Canonical Data → Canonical Evidence / Domain Context → AnalysisContext → LLM Analysis → StructuredAnalysis → Strategy → Human Confirmation → Execution / Outcome`

冻结边界：
- AnalysisContext 是 deterministic、source-backed、read-only 的 LLM 输入。
- LLM 不访问 Repository / SQLite，不修改 canonical data，不执行 action，不发送消息。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- StructuredAnalysis 的 inference / hypothesis / material signal 应保留 canonical evidence provenance。
- unknown 不得被模型猜测自动提升为事实。
- Strategy、Strategic Reply、Action Plan 只消费 derived analysis，不建立第二套生命周期。
- LLM 不得自动确认 decision、执行 action、发送消息、修改 relationship state、写入 learning history 或伪造 outcome。
- deterministic Context / Evidence / Learning / Persistence / Decision / Execution 层保持 no-LLM。
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

## TEST-077 ~ TEST-080 状态摘要

### TEST-077 — Strategic Reply downstream boundary

Branch：`test-077-strategic-reply-downstream-boundary`
HEAD：`994ebb4bcd83c29f892572f23bf199e9751bfdf3`
全量：471 passed。
实际 Qwen HTTP 200；`structured_analysis` / `reply_inputs` 返回；`analysis_is_derived=true`；`draft=null`；无 decision / execution / outcome side effect。

### TEST-078 — StructuredAnalysis → Action Plan

建立现有 Action Plan 生命周期内的最小 derived-analysis consumption boundary。

正式入口：
`GET /api/v1/conversations/{conversation_id}/action-plan/context`

核心规则：
- StructuredAnalysis 保留为 request-scoped derived output。
- analysis buckets 投影到 `action_plan_inputs.signals`。
- 保留 `evidence_source_ids` provenance。
- unknown 保持 unknown。
- 不因 LLM 分析自动新增 `action_plan` proposal。
- `requires_user_confirmation=true`。
- `must_not_auto_execute=true`。
- 不自动确认、不执行、不发送消息、不修改 relationship。
- 不新增数据库表。

### TEST-079 — Learning Strategy HTTP Response Contract

Commit：`bdedc820c99590b642a419f8b5bff1e05a72d5ab`

全量：478 passed。
锁定 Action Plan Context 中 `learning_strategy` 的 HTTP response contract，并保持：derived=true、action_plan=[]、no auto execution、no auto send、no decision/execution/outcome side effect。

### TEST-080 — StructuredAnalysis → Action Plan Candidate Boundary

Commit：`e7b431bf7364b9f5c2aa4861f90c9c1b66456090`

仅修改：`backend/tests/test_analysis_action_plan.py`

focused regression：23 passed。
full regression：480 passed in 74.16s。
`git diff --check`：通过。

TEST-080 锁定的安全边界：
- StructuredAnalysis 是 derived interpretation。
- StructuredAnalysis 不能直接成为 Recommendation。
- StructuredAnalysis 不能直接成为 Action Candidate / proposal。
- 即使 hypothesis / intent signal 高置信度且文本具有 action-like 内容，也不能自动进入 `recommendations` 或 `action_plan`。
- 只有 existing explicit evidence-backed recommendation 才能进入既有 Action Plan promotion。
- 不新增 migration，不修改 Action Plan / Decision / Execution 生命周期。

---

## TEST-080 后关键产品边界

当前 Action Plan promotion 的 deterministic 边界由 `ActionPlanService.build_action_plan()` 控制：
- recommendation 必须是显式 dict。
- `action` 必须是非空字符串。
- `evidence_source_ids` 必须是非空 list。
- 所有 source id 必须命中 canonical evidence 的 `source_id` 集合。
- 合法 recommendation 才能生成 `status="proposed"` action-plan item。
- proposal 必须继续 `requires_user_confirmation=true`。
- StructuredAnalysis 可以作为 derived signal input，但不得冒充 canonical evidence，也不得自行创建 recommendation。

因此，不能继续扩大 `StructuredAnalysis → candidate` 的直接映射。下一步必须先确认 Recommendation 的真实生产边界。

---

## TEST-080 后审计结论

审计结论：当前下一步不是继续扩展 StructuredAnalysis，而是审计 Recommendation Producer / Provenance / Candidate Promotion 的真实闭环。

正式决策链必须保持：

```text
Canonical Evidence
        ↓
Fact
        ↓
Inference / Unknown
        ↓
Recommendation
        ↓
Action Candidate
        ↓
User Confirmation
        ↓
Execution
        ↓
Outcome
        ↓
Learning
        ↓
重新判断
```

禁止把：

```text
StructuredAnalysis → Recommendation → Action Candidate
```

实现成无条件自动转换。

禁止因为 LLM 输出 action-like language 就把模型文本提升为现实世界 action。

---

## TEST-081 启动门槛

暂定方向：`TEST-081 — Recommendation Producer / Provenance / Candidate Promotion Contract`

注意：这只是候选方向。正式 TEST-081 必须在 GitHub 当前分支完成全量审计后锁定。

审计必须确认：

1. Recommendation schema 的真实字段、语义及 provenance 要求。
2. 所有 Recommendation producer / creation entrypoint。
3. Recommendation route / service 是否存在，以及真实输入来源。
4. Recommendation 是否受 canonical evidence / source identity 约束。
5. Recommendation → Action Candidate / Action Plan promotion 的唯一真实入口。
6. provenance / candidate tests 是否覆盖完整生产边界。
7. Action Decision confirmation 与 Recommendation / Candidate 是否存在隐式转换。
8. 是否存在 LLM / StructuredAnalysis 路径绕过 Recommendation 直接生成 proposal。
9. Confirmation、Decision、Execution 是否保持独立生命周期。

在上述审计完成前：
- 不新增 Recommendation schema。
- 不新增 migration。
- 不修改 Action Plan / Decision / Execution 生命周期。
- 不把 StructuredAnalysis 直接转换成 Recommendation。
- 不把 StructuredAnalysis 直接转换成 Action Candidate。
- 不修改业务代码。

---

## 数据库与运行约束

当前 migrations：001 / 002 / 003 / 004 / 005 / 006 / 007。
TEST-045 ~ TEST-080 不新增 migration，不改变 action_decisions、action_executions、action_outcomes 生命周期。

Route → Service → Repository → SQLite。

所有用户数据必须 user_id 隔离；不得自动向第三方发送消息；不得使用 8899；MVP 不引入 PostgreSQL / Redis / Elasticsearch / Vector DB。

---

## 持续禁止事项

- LLM 进入 canonical evidence、persistence、learning context、decision persistence 或 execution 层。
- 模型自动确认 decision、执行 action、发送消息、修改 relationship 或伪造 outcome。
- 为测试方便改变既有业务语义或绕过 user / person / conversation isolation。
- 建立第二套 Strategy / Decision / Strategic Reply / Action Plan 生命周期。
- 为了填充 Action Plan 而绕过 canonical evidence → recommendation → confirmation 链。
- 在没有 GitHub 审计的情况下要求服务器端提供本可由仓库确认的信息。

---

## 下一步

直接从 GitHub 当前分支开始 TEST-081 Recommendation Producer 全量审计。先读取实际 recommendation schema / route / producer、evidence source identity、action-plan promotion、confirmation / decision / execution boundary 及相关 provenance / candidate tests，再锁定 TEST-081 的精确契约、测试范围和最小修改面。
