# Development Handover

更新时间：2026-09-17
当前阶段：TEST-118 — Login Throttle / Progressive Lockout — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING
当前 Branch：test-118-login-throttle
TEST-117 VERIFIED 服务器代码基线：`af4995a8e5fccd8586e63e3e76191552ecb317b1`

## 项目目标

长期关系管理 + AI 恋爱决策辅助系统，不是单纯聊天机器人。

核心链路：
`Canonical Data → Canonical Evidence / AnalysisContext → StructuredAnalysis → Strategy → StrategyRecommendationCandidate → RecommendationProducer → Recommendation → Action Plan → Action Decision → User Confirmation → Action Execution → Outcome → Feedback → Learning → Re-analysis`

## 阶段状态

TEST-008 ~ TEST-090：按既有交接记录 VERIFIED；TEST-091 CONTRACT LOCKED；TEST-092 VERIFIED；TEST-093 VERIFIED；TEST-094 CONTRACT LOCKED。

TEST-095 VERIFIED — Recommendation / Action Plan persistence bridge；migration 008。
TEST-096 VERIFIED — Decision → Execution → Outcome safety。
TEST-097 VERIFIED — evidence-backed proposal freshness。
TEST-098 VERIFIED — Action Plan snapshot isolation。
TEST-099 VERIFIED — Action Plan persistence gate。
TEST-100 VERIFIED — proposal / execution gate。
TEST-101 VERIFIED — Execution scope isolation；full 526。
TEST-102 VERIFIED — Outcome DB idempotency；migration 009；full 528。
TEST-103 VERIFIED — duplicate Outcome → HTTP 409；full 529。
TEST-104 VERIFIED — user-scoped LLM Provider config；migration 010；full 530。
TEST-105 VERIFIED — Provider Runtime Routing；full 532。
TEST-106 VERIFIED — Provider Runtime Materialization；full 533。
TEST-107 VERIFIED — Provider Connection Test；full 539。
TEST-108 VERIFIED — Provider Error Contract。
TEST-109 VERIFIED — Provider URL Contract。
TEST-110 VERIFIED — Provider Capability / StructuredAnalysis；full 553。
TEST-111 VERIFIED — Provider Timeout / 429 / No-Retry；full 562。
TEST-112 VERIFIED — Provider Log Redaction；full 568。
TEST-113 VERIFIED — Provider Settings UI；服务器 full 571；HEAD `b59b7625ffd8a391835545852ce981871da32580`。
TEST-114 VERIFIED — Production Authentication Boundary；服务器 full 578；HEAD `693946882ca780eafc0367dfa26a3b7f0ea06f84`。
TEST-115 VERIFIED — DB-backed opaque Auth Session；migration 011；服务器 full 585；HEAD `a76c6907fa51afeee0076822601745c8ac3e4fb2`。
TEST-116 VERIFIED — Account credentials / login → server-issued session；migration 012；服务器 full 592；HEAD `bf84a5c068813693715fa0b09ce5458d59b7356e`。
TEST-117 VERIFIED — Multi-device session management / bootstrap retirement；服务器 targeted 7、TEST-116 7、TEST-115 7、TEST-114 7、scope isolation 4、full 599 passed in 103.79s；migration diff blank；HEAD `af4995a8e5fccd8586e63e3e76191552ecb317b1`。
TEST-118 GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING — SQLite login throttle / progressive lockout；GitHub targeted 8、TEST-116 login 7、TEST-117 session management 7、TEST-115 session 7、TEST-114 production auth 7、scope isolation 4、full 607 passed；新增 migration 013，未修改历史 migration 001~012。

## Auth 产品化基线

- TEST-114：production 禁止 `X-User-ID`；静态 `AUTH_BEARER_TOKEN → LOCAL_USER_ID` 仅作迁移 bootstrap。
- TEST-115：opaque session 只存 SHA-256 hash，支持 expiry/revoke，服务端解析到 `users.id`。
- TEST-116：normalized username + scrypt password；服务器生成 user_id；注册/登录签发同一 session。
- TEST-117：session list/current/revoke-other/rotate；`AUTH_BOOTSTRAP_ENABLED=false` 后静态 bootstrap 可退场，DB session 继续工作。

## TEST-118 — Login Throttle / Progressive Lockout — GITHUB SELF-TEST PASSED / SERVER VALIDATION PENDING

目标：在不引入 Redis、不依赖未验证代理 IP 的前提下，限制用户名/密码端点的高频猜测，同时保持 existing/unknown username 的一致错误边界。

已建立：
1. migration 013 `auth_login_throttle`：只持久化 `subject_hash / failed_attempts / window_started_at / locked_until / updated_at`；subject 为 normalized username 的 SHA-256，不存原始未知用户名；
2. 默认 15 分钟失败窗口；前 5 次失败继续返回既有 `401 invalid credentials`；第 5 次失败建立 30 秒锁定；
3. 锁定结束后若同一窗口继续失败，锁定按 30s → 60s → 120s → 240s... 递增，最大 15 分钟；
4. 锁定期间直接返回统一 `429 too many login attempts` 与 `Retry-After`；锁定期间请求不增加 failed_attempts，不允许高频请求自行无限延长锁定；
5. existing username 与 unknown username 使用同一 subject 状态机；unknown username 仍执行 TEST-116 dummy scrypt verification 后记录失败；
6. 成功登录会删除该 normalized subject 的 throttle 状态；
7. throttle 只按服务端规范化 username subject 工作，不读取/信任 `X-Forwarded-For` 等代理 header；
8. 不修改 TEST-116 password/session 实现，不建立第二套认证系统；
9. 不修改历史 migration 001~012，不引入 PostgreSQL/Redis/ES/向量库。

新增 `backend/tests/test_auth_login_throttle.py` 8 个测试：
- existing account failure limit → 429；
- unknown username 同一 throttle contract；
- successful login clears failures；
- normalized subject isolation；
- throttle table 不保存原始 unknown username；
- progressive lock 增长；
- failure window expiry reset；
- locked requests 不延长 failure counter。

GitHub Actions run `35239595475`：
- TEST-118 login throttle：8 passed；
- TEST-116 account login：7 passed；
- TEST-117 session management：7 passed；
- TEST-115 auth session：7 passed；
- TEST-114 production auth：7 passed；
- execution/action-plan scope isolation：4 passed；
- full pytest：607 passed、1 warning in 33.02s；
- 临时 validation workflow 已删除。

当前等待服务器验收后再标记 TEST-118 VERIFIED。

## 下一阶段候选

TEST-118 服务器通过后优先：
1. TEST-119 password change / credential rotation，并定义“修改密码后是否撤销其他 sessions”的明确安全契约；
2. account recovery 边界，不在没有验证渠道前伪造邮件/短信恢复；
3. 逐步将 `AUTH_BOOTSTRAP_ENABLED` 默认关闭并移除静态 bootstrap；
4. release/runtime security：reverse proxy trust、HTTPS/CORS/CSRF/access log；
5. 完整 login/session/account UI。

## 架构与持续禁止事项

- AnalysisContext deterministic、source-backed、read-only。
- StructuredAnalysis 是 derived interpretation，不是 canonical truth。
- Recommendation 必须经过 StrategyRecommendationCandidate → RecommendationProducer。
- Action Plan 必须 evidence-backed 且等待用户确认。
- Action Decision 必须来自显式 user decision；不得自动确认、执行、发送消息、修改 relationship 或伪造 Outcome。
- Outcome → Feedback → Learning → Re-analysis 必须继续沿唯一 canonical lifecycle。
- 所有数据必须 user_id 隔离；Person / Relationship / Conversation 不得跨 scope 混用。
- 不修改历史 migration；新增 schema 必须使用新 migration。
- MVP 不使用 PostgreSQL、Redis、Elasticsearch、Vector DB；不得使用或修改 8899。
- Provider/API/Auth credentials 不得出现在 console/file log 或归一化 exception traceback 中。
- verification tag 只有实际创建并验证存在后才能记录为完成；当前未声称 TEST-113~118 verification tag 已创建。
