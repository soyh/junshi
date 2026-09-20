from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.ui.account_security_workspace import (
    ACCOUNT_SECURITY_HTML,
    ACCOUNT_SECURITY_SCRIPT,
)
from app.ui.action_decision_workspace import (
    ACTION_DECISION_HTML,
    ACTION_DECISION_SCRIPT,
)
from app.ui.action_execution_workspace import (
    ACTION_EXECUTION_HTML,
    ACTION_EXECUTION_SCRIPT,
)
from app.ui.action_feedback_workspace import (
    ACTION_FEEDBACK_HTML,
    ACTION_FEEDBACK_SCRIPT,
)
from app.ui.action_learning_workspace import (
    ACTION_LEARNING_HTML,
    ACTION_LEARNING_SCRIPT,
)
from app.ui.action_outcome_workspace import (
    ACTION_OUTCOME_HTML,
    ACTION_OUTCOME_SCRIPT,
)
from app.ui.action_plan_workspace import ACTION_PLAN_HTML, ACTION_PLAN_SCRIPT
from app.ui.action_reanalysis_workspace import (
    ACTION_REANALYSIS_HTML,
    ACTION_REANALYSIS_SCRIPT,
)
from app.ui.conversation_content_workspace import (
    CONVERSATION_CONTENT_HTML,
    CONVERSATION_CONTENT_SCRIPT,
)
from app.ui.product_management_workspace import (
    PRODUCT_MANAGEMENT_HTML,
    PRODUCT_MANAGEMENT_SCRIPT,
)
from app.ui.product_shell import PRODUCT_SHELL_HTML
from app.ui.relationship_evidence_workspace import (
    RELATIONSHIP_EVIDENCE_HTML,
    RELATIONSHIP_EVIDENCE_SCRIPT,
)
from app.ui.strategy_recommendation_workspace import (
    STRATEGY_RECOMMENDATION_HTML,
    STRATEGY_RECOMMENDATION_SCRIPT,
)


router = APIRouter(tags=["ui"])


OLD_PRODUCT_NOTE = (
    "TEST-136 只把 Person、Relationship、Conversation 的既有 API 接入统一 "
    "authenticated shell。Recommendation 及后续生命周期仍不伪造尚未完成的业务页面。"
)
NEW_PRODUCT_NOTE = (
    "统一 authenticated shell 已覆盖核心资料管理、Conversation evidence、Strategy / "
    "Recommendation 与 Action Plan → Decision → Execution → Outcome → Feedback → "
    "Learning → Re-analysis 完整生命周期。"
)

OLD_PRODUCT_NAV = '''  <nav aria-label="Product sections">
    <a href="#account">Account</a>
    <a href="#workspace">Workspace</a>
    <a href="#provider">LLM Provider</a>
    <a href="#analysis">Structured Analysis</a>
  </nav>'''

NEW_PRODUCT_NAV = '''  <nav aria-label="Product sections">
    <a href="#account">Account</a>
    <a href="#account-security">Security</a>
    <a href="#workspace">Workspace</a>
    <a href="#product-management">Records</a>
    <a href="#conversation-content">Conversation</a>
    <a href="#relationship-evidence">Evidence</a>
    <a href="#analysis">Structured Analysis</a>
    <a href="#strategy-recommendation">Strategy</a>
    <a href="#action-plan-workspace">Action Plan</a>
    <a href="#action-decision-workspace">Decision</a>
    <a href="#action-execution-workspace">Execution</a>
    <a href="#action-outcome-workspace">Outcome</a>
    <a href="#action-feedback-workspace">Feedback</a>
    <a href="#action-learning-workspace">Learning</a>
    <a href="#action-reanalysis-workspace">Re-analysis</a>
    <a href="#provider">LLM Provider</a>
  </nav>'''


def build_product_shell_html() -> str:
    provider_marker = '  <fieldset id="provider" class="wide">'
    script_marker = "  clearSession();\n})();"

    if provider_marker not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell provider insertion marker not found")
    if script_marker not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell script insertion marker not found")
    if OLD_PRODUCT_NOTE not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell stale-note replacement marker not found")
    if OLD_PRODUCT_NAV not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell navigation replacement marker not found")

    base_html = PRODUCT_SHELL_HTML.replace(
        OLD_PRODUCT_NOTE,
        NEW_PRODUCT_NOTE,
        1,
    ).replace(
        OLD_PRODUCT_NAV,
        NEW_PRODUCT_NAV,
        1,
    )

    workspace_html = (
        f"{ACCOUNT_SECURITY_HTML}\n"
        f"{PRODUCT_MANAGEMENT_HTML}\n"
        f"{CONVERSATION_CONTENT_HTML}\n"
        f"{RELATIONSHIP_EVIDENCE_HTML}\n"
        f"{STRATEGY_RECOMMENDATION_HTML}\n"
        f"{ACTION_PLAN_HTML}\n"
        f"{ACTION_DECISION_HTML}\n"
        f"{ACTION_EXECUTION_HTML}\n"
        f"{ACTION_OUTCOME_HTML}\n"
        f"{ACTION_FEEDBACK_HTML}\n"
        f"{ACTION_LEARNING_HTML}\n"
        f"{ACTION_REANALYSIS_HTML}\n"
        f"{provider_marker}"
    )
    html = base_html.replace(
        provider_marker,
        workspace_html,
        1,
    )
    workspace_script = (
        f"{CONVERSATION_CONTENT_SCRIPT}\n\n"
        f"{RELATIONSHIP_EVIDENCE_SCRIPT}\n\n"
        f"{ACTION_REANALYSIS_SCRIPT}\n\n"
        f"{ACTION_LEARNING_SCRIPT}\n\n"
        f"{ACTION_FEEDBACK_SCRIPT}\n\n"
        f"{ACTION_OUTCOME_SCRIPT}\n\n"
        f"{ACTION_EXECUTION_SCRIPT}\n\n"
        f"{ACTION_DECISION_SCRIPT}\n\n"
        f"{ACTION_PLAN_SCRIPT}\n\n"
        f"{STRATEGY_RECOMMENDATION_SCRIPT}\n\n"
        f"{PRODUCT_MANAGEMENT_SCRIPT}\n\n"
        f"{ACCOUNT_SECURITY_SCRIPT}\n\n"
        f"{script_marker}"
    )
    return html.replace(
        script_marker,
        workspace_script,
        1,
    )


PRODUCT_SHELL_WITH_CONTENT_HTML = build_product_shell_html()


@router.get(
    "/app",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def get_product_shell():
    return HTMLResponse(PRODUCT_SHELL_WITH_CONTENT_HTML)
