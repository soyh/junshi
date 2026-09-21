from app.api.routes.analysis_strategic_reply import _safe_llm_failure_detail
from app.services.llm import LLMAnalysisError
from app.ui.card_client_generation_recovery import (
    CARD_CLIENT_GENERATION_RECOVERY_SCRIPT,
    CARD_CLIENT_GENERATION_RECOVERY_STYLE,
)
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML


def test_customer_reply_recovery_button_is_always_available():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML
    assert "client-reply-retry" in html
    assert "生成回复建议" in html
    assert "重新生成回复" in html
    assert "clientRunReplyRecovery" in html


def test_automatic_failure_gets_one_customer_retry():
    script = CARD_CLIENT_GENERATION_RECOVERY_SCRIPT
    assert "clientAutoReplyRecoveryKey" in script
    assert "自动跟进未完全完成" in script
    assert "clientRunReplyRecovery({ automatic: true })" in script
    assert "window.setTimeout" in script


def test_recovery_reuses_verified_reply_and_action_functions():
    script = CARD_CLIENT_GENERATION_RECOVERY_SCRIPT
    assert "await loadStrategicReply()" in script
    assert "await generateActionPlan()" in script
    assert "await loadSavedActionPlan()" in script
    assert "await loadActionDecisionContext()" in script
    assert "fetch(" not in script
    assert "method: 'POST'" not in script
    assert "method: 'PATCH'" not in script
    assert "method: 'DELETE'" not in script


def test_recovery_does_not_send_confirm_or_execute():
    script = CARD_CLIENT_GENERATION_RECOVERY_SCRIPT
    assert "prepareStrategicReplyMessageRecord(" not in script
    assert "confirmActionDecision(" not in script
    assert "recordActionExecution(" not in script
    assert "recordActionOutcome(" not in script


def test_recovery_control_has_compact_customer_style():
    assert "#client-reply-retry-wrap" in CARD_CLIENT_GENERATION_RECOVERY_STYLE
    assert "border-radius: 999px" in CARD_CLIENT_GENERATION_RECOVERY_STYLE


def test_safe_llm_failure_category_preserves_no_raw_provider_message():
    assert _safe_llm_failure_detail(
        LLMAnalysisError("LLM provider returned invalid structured analysis")
    ) == "LLM analysis failed: invalid structured response"
    assert _safe_llm_failure_detail(
        LLMAnalysisError("Qwen provider request failed")
    ) == "LLM analysis failed: provider request failed"
    assert _safe_llm_failure_detail(
        LLMAnalysisError("Qwen strategic reply request failed")
    ) == "LLM analysis failed: strategic reply provider request failed"
    assert _safe_llm_failure_detail(
        LLMAnalysisError("secret upstream detail")
    ) == "LLM analysis failed"
