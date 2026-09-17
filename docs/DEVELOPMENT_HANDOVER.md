# Development Handover

更新时间：2026-09-17
当前阶段：TEST-104 — User-selectable LLM Provider / API Configuration — GITHUB SELF-TEST PASSED, SERVER VALIDATION PENDING
当前 Branch：test-104-provider-api-contract

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-090：按既有交接记录 VERIFIED；TEST-091 CONTRACT LOCKED；TEST-092 VERIFIED；TEST-093 VERIFIED；TEST-094 CONTRACT LOCKED。

TEST-095 VERIFIED — 真实 Recommendation / Action Plan 跨请求 persistence bridge；新增 migration 008 `action_plan_snapshots`，保持 evidence freshness validation，不放宽 Action Decision validation。

TEST-096 VERIFIED — confirmed Decision → explicit Execution → Outcome safety；scope / duplicate / conflict gates 完成。

TEST-097 VERIFIED — evidence-backed proposal freshness；stale snapshots 排除但不删除。

TEST-098 VERIFIED — Action Plan snapshot user/person isolation。

TEST-099 VERIFIED — Action Plan persistence gate；只有真实 Recommendation 对应 item 可持久化。

TEST-100 VERIFIED — proposal gate + execution gate；Decision 必须引用 proposed、requires-user-confirmation 的真实 Action Plan item；Execution 必须来自 confirmed Decision。

TEST-101 VERIFIED — Execution 精确 user/person/decision scope isolation；服务器 full pytest 526 passed；历史 migration diff blank。

TEST-102 VERIFIED — DB-level Outcome idempotency；新增 migration 009 `uq_action_outcomes_decision`，未修改历史 migration 005；服务器 full pytest 528 passed；migration diff blank。

TEST-103 VERIFIED — `sqlite3.IntegrityError → HTTP 409 Conflict`；服务器 targeted 1 passed、full 529 passed；migration diff blank。

## TEST-104 — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

目标：让用户能够按 user scope 保存自己的 OpenAI-compatible API Key、Base URL、Model、Timeout，并让现有 Analysis / Strategy / Recommendation / Strategic Reply / Action Plan analysis routes 使用该配置；没有用户配置时保持原有 Qwen 默认行为。

### 已实现

- 新增 migration 010：`user_llm_provider_configs`，`user_id` 为唯一 scope。
- 新增 `LLMProviderConfigRepository`，所有读写均按 user_id 隔离。
- 新增 `LLMProviderConfigService`，使用 Fernet 加密 API key；response 永不返回 plaintext key。
- 新增 `LLMProviderConfigUpdate` / `LLMProviderConfigResponse`。
- 新增 API：
  - `GET /api/v1/settings/llm`
  - `PUT /api/v1/settings/llm`
  - `DELETE /api/v1/settings/llm`
- 新增 server secret：`LLM_CONFIG_ENCRYPTION_KEY`。没有该 secret 时禁止保存用户 API key。
- 当前 provider 类型锁定为 `openai_compatible`；用户可以指定 Base URL + Model + API Key。
- Structured Analysis / Strategy / Recommendation / Strategic Reply / Action Plan analysis routes 优先读取 user config；无配置时继续使用 `QwenProvider()` 默认路径。
- 保留原有模块级 `QwenProvider` injection seam，避免破坏既有 route tests。
- `.env.example` 已记录加密 key 配置方式。
- `cryptography==46.0.5` 已加入 backend requirements。

### 安全边界

1. API key 不返回给客户端。
2. API key 不以 plaintext 写入 SQLite，仅保存 Fernet ciphertext。
3. 加密 master key 只来自服务器环境变量，不由用户 API 提供。
4. provider config 严格按 user_id 隔离。
5. 当前 MVP 仍使用 `X-User-ID` context；正式认证不是 TEST-104 的目标。
6. TEST-104 不自动调用第三方 provider 做 connection test，不自动切换模型、不自动扣费、不自动选择 provider。

### GitHub 自测

第一次 full pytest 暴露 8 个既有 route tests 依赖模块级 `QwenProvider` monkeypatch；未修改测试掩盖问题。

修复为兼容注入 seam 后，GitHub Actions run `35192147144`：
- targeted `backend/tests/test_llm_provider_config.py`：1 passed
- full pytest：530 passed，1 warning
- 临时 TEST-104 workflow 已删除。

### 服务器验收节点

服务器切换到 `test-104-provider-api-contract` 后执行：

1. `git status --short` 应为空。
2. migration 010 应正常应用。
3. `pytest -q backend/tests/test_llm_provider_config.py` → 1 passed。
4. `pytest -q` → 预期 530 passed。
5. 不修改历史 migration 001~009。
6. 设置 `LLM_CONFIG_ENCRYPTION_KEY` 后进行 HTTP GET / PUT / GET / DELETE 验收，并确认 API response 不包含原始 key。
7. 不需要真实第三方模型调用。

## 产品化下一阶段

TEST-104 server VERIFIED 后，再进入独立 productization 阶段：

1. provider connection-test API；
2. provider/model 列表与能力声明；
3. 前端用户设置页与模型选择；
4. 前端 Person / Relationship / Conversation / Analysis / Recommendation / Action Plan / Decision / Outcome 工作流页面；
5. 正式认证与真实用户身份替换 `X-User-ID`。

前端当前不应被假设为已完成；TEST-104 只负责把 user-selectable model/API 的后端契约建立并接入现有 AI analysis chain。

## 架构与持续禁止事项

- AnalysisContext deterministic、source-backed、read-only。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Recommendation 必须经过 StrategyRecommendationCandidate → RecommendationProducer。
- Action Plan 必须 evidence-backed 且等待用户确认。
- Action Decision 必须来自显式 user decision；不得自动确认、执行、发送消息、修改 relationship 或伪造 Outcome。
- Outcome → Feedback → Learning → Re-analysis 必须继续沿唯一 canonical lifecycle。
- 所有数据必须 user_id 隔离；Person / Relationship / Conversation 不得跨 scope 混用。
- 不修改历史 migration；不建立第二套 lifecycle。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB；不得使用或修改 8899。
- GitHub 能确认的信息不得先要求服务器端查询。
