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
from app.ui.card_client_automation import CARD_CLIENT_AUTOMATION_SCRIPT
from app.ui.card_client_compact_surface import (
    CARD_CLIENT_COMPACT_SURFACE_SCRIPT,
    CARD_CLIENT_COMPACT_SURFACE_STYLE,
)
from app.ui.card_client_generation_recovery import (
    CARD_CLIENT_GENERATION_RECOVERY_SCRIPT,
    CARD_CLIENT_GENERATION_RECOVERY_STYLE,
)
from app.ui.card_client_experience import (
    CARD_CLIENT_EXPERIENCE_SCRIPT,
    CARD_CLIENT_EXPERIENCE_STYLE,
)
from app.ui.card_client_unified_import import (
    CARD_CLIENT_UNIFIED_IMPORT_SCRIPT,
    CARD_CLIENT_UNIFIED_IMPORT_STYLE,
)
from app.ui.conversation_content_workspace import (
    CONVERSATION_CONTENT_HTML,
    CONVERSATION_CONTENT_SCRIPT,
)
from app.ui.conversation_controls_workspace import (
    CONVERSATION_CONTROLS_SCRIPT,
    CONVERSATION_CONTROLS_STYLE,
)
from app.ui.conversation_session_workspace import (
    CONVERSATION_SESSION_SCRIPT,
    CONVERSATION_SESSION_STYLE,
)
from app.ui.dual_model_settings_workspace import (
    DUAL_MODEL_SETTINGS_SCRIPT,
    DUAL_MODEL_SETTINGS_STYLE,
)
from app.ui.guided_workflow_workspace import (
    GUIDED_WORKFLOW_HTML,
    GUIDED_WORKFLOW_SCRIPT,
    GUIDED_WORKFLOW_STYLE,
)
from app.ui.lifecycle_v2_workspace import (
    LIFECYCLE_V2_SCRIPT,
    LIFECYCLE_V2_STYLE,
)
from app.ui.media_upload_workspace import (
    MEDIA_UPLOAD_WORKSPACE_SCRIPT,
    MEDIA_UPLOAD_WORKSPACE_STYLE,
)
from app.ui.message_history_window_workspace import MESSAGE_HISTORY_WINDOW_SCRIPT
from app.ui.multi_provider_settings_workspace import (
    MULTI_PROVIDER_SETTINGS_SCRIPT,
    MULTI_PROVIDER_SETTINGS_STYLE,
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
from app.ui.settings_tab_workspace import (
    SETTINGS_TAB_WORKSPACE_SCRIPT,
    SETTINGS_TAB_WORKSPACE_STYLE,
)
from app.ui.single_open_interaction_workspace import (
    SINGLE_OPEN_INTERACTION_SCRIPT,
    SINGLE_OPEN_INTERACTION_STYLE,
)
from app.ui.strategic_reply_workspace import (
    STRATEGIC_REPLY_HTML,
    STRATEGIC_REPLY_SCRIPT,
)
from app.ui.strategy_recommendation_workspace import (
    STRATEGY_RECOMMENDATION_HTML,
    STRATEGY_RECOMMENDATION_SCRIPT,
)
from app.ui.user_presentation_workspace import (
    USER_PRESENTATION_SCRIPT,
    USER_PRESENTATION_STYLE,
)
from app.ui.visual_theme_workspace import (
    VISUAL_THEME_SCRIPT,
    VISUAL_THEME_STYLE,
)


router = APIRouter(tags=["ui"])


OLD_PRODUCT_NOTE = (
    "TEST-136 只把 Person、Relationship、Conversation 的既有 API 接入统一 "
    "authenticated shell。Recommendation 及后续生命周期仍不伪造尚未完成的业务页面。"
)
NEW_PRODUCT_NOTE = (
    "页面按真实使用顺序组织完整生命周期：选择人物 → 维护关系 → 录入会话与证据 → AI 分析与回复 → "
    "行动计划与用户决定 → 结果、学习与复盘。所有写入、确认、执行和发送边界继续由用户显式控制。"
    "现有 Person、Relationship、Conversation、Recommendation、Action Plan、Execution、Outcome、"
    "Feedback、Learning 与 Re-analysis 能力继续复用 canonical API；对于未来能力仍不伪造尚未完成的业务页面。"
)

OLD_PRODUCT_NAV = '''  <nav aria-label="Product sections">
    <a href="#account">Account</a>
    <a href="#workspace">Workspace</a>
    <a href="#provider">LLM Provider</a>
    <a href="#analysis">Structured Analysis</a>
  </nav>'''

NEW_PRODUCT_NAV = '''  <nav aria-label="主要功能">
    <a href="#account">账号登录</a>
    <a href="#guided-step-1">1 选择人物</a>
    <a href="#guided-step-2">2 维护关系</a>
    <a href="#guided-step-3">3 会话与证据</a>
    <a href="#guided-step-4">4 AI 分析与回复</a>
    <a href="#guided-step-5">5 行动计划与执行</a>
    <a href="#guided-step-6">6 结果、学习与复盘</a>
  </nav>
  <nav aria-label="Legacy product anchors" hidden>
    <a href="#account-security">Account security</a>
    <a href="#product-management">Product management</a>
    <a href="#conversation-content">Conversation content</a>
    <a href="#relationship-evidence">Relationship evidence</a>
    <a href="#strategy-recommendation">Strategy recommendation</a>
    <a href="#strategic-reply-workspace">Strategic reply</a>
    <a href="#action-plan-workspace">Action plan</a>
    <a href="#action-decision-workspace">Action decision</a>
    <a href="#action-execution-workspace">Action execution</a>
    <a href="#action-outcome-workspace">Action outcome</a>
    <a href="#action-feedback-workspace">Action feedback</a>
    <a href="#action-learning-workspace">Action learning</a>
    <a href="#action-reanalysis-workspace">Action re-analysis</a>
  </nav>'''

OLD_PROVIDER_SELECT = '''    <select id="provider-name">
      <option value="openai_compatible">OpenAI-compatible</option>
    </select>'''

NEW_PROVIDER_SELECT = '''    <select id="provider-name">
      <option value="qwen">Qwen / 阿里云百炼</option>
      <option value="deepseek">DeepSeek</option>
      <option value="kimi">Kimi / Moonshot</option>
      <option value="openai">OpenAI</option>
      <option value="gemini">Gemini / Google</option>
      <option value="openai_compatible">其他 OpenAI-compatible</option>
    </select>'''


def build_product_shell_html() -> str:
    provider_marker = '  <fieldset id="provider" class="wide">'
    script_marker = "  clearSession();\n})();"
    style_marker = "  </style>"

    if provider_marker not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell provider insertion marker not found")
    if script_marker not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell script insertion marker not found")
    if style_marker not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell style insertion marker not found")
    if OLD_PRODUCT_NOTE not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell stale-note replacement marker not found")
    if OLD_PRODUCT_NAV not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell navigation replacement marker not found")
    if OLD_PROVIDER_SELECT not in PRODUCT_SHELL_HTML:
        raise RuntimeError("Product shell provider select replacement marker not found")

    base_html = PRODUCT_SHELL_HTML.replace(
        OLD_PRODUCT_NOTE,
        NEW_PRODUCT_NOTE,
        1,
    ).replace(
        OLD_PRODUCT_NAV,
        NEW_PRODUCT_NAV,
        1,
    ).replace(
        OLD_PROVIDER_SELECT,
        NEW_PROVIDER_SELECT,
        1,
    ).replace(
        style_marker,
        (
            f"{GUIDED_WORKFLOW_STYLE}\n"
            f"{VISUAL_THEME_STYLE}\n"
            f"{USER_PRESENTATION_STYLE}\n"
            f"{LIFECYCLE_V2_STYLE}\n"
            f"{CONVERSATION_SESSION_STYLE}\n"
            f"{CARD_CLIENT_EXPERIENCE_STYLE}\n"
            f"{CARD_CLIENT_UNIFIED_IMPORT_STYLE}\n"
            f"{MEDIA_UPLOAD_WORKSPACE_STYLE}\n"
            f"{CARD_CLIENT_COMPACT_SURFACE_STYLE}\n"
            f"{CARD_CLIENT_GENERATION_RECOVERY_STYLE}\n"
            f"{SINGLE_OPEN_INTERACTION_STYLE}\n"
            f"{SETTINGS_TAB_WORKSPACE_STYLE}\n"
            f"{MULTI_PROVIDER_SETTINGS_STYLE}\n"
            f"{DUAL_MODEL_SETTINGS_STYLE}\n"
            f"{CONVERSATION_CONTROLS_STYLE}\n"
            f"{style_marker}"
        ),
        1,
    )

    workspace_html = (
        f"{GUIDED_WORKFLOW_HTML}\n"
        f"{ACCOUNT_SECURITY_HTML}\n"
        f"{PRODUCT_MANAGEMENT_HTML}\n"
        f"{CONVERSATION_CONTENT_HTML}\n"
        f"{RELATIONSHIP_EVIDENCE_HTML}\n"
        f"{STRATEGY_RECOMMENDATION_HTML}\n"
        f"{STRATEGIC_REPLY_HTML}\n"
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

    # Composition/presentation/orchestration run before business fragments.
    # Function declarations from the later fragments are hoisted inside the
    # same IIFE, while keeping each verified fragment's suffix contract clean.
    workspace_script = (
        f"{GUIDED_WORKFLOW_SCRIPT}\n\n"
        f"{VISUAL_THEME_SCRIPT}\n\n"
        f"{USER_PRESENTATION_SCRIPT}\n\n"
        f"{LIFECYCLE_V2_SCRIPT}\n\n"
        f"{CARD_CLIENT_EXPERIENCE_SCRIPT}\n\n"
        f"{SINGLE_OPEN_INTERACTION_SCRIPT}\n\n"
        f"{SETTINGS_TAB_WORKSPACE_SCRIPT}\n\n"
        f"{MULTI_PROVIDER_SETTINGS_SCRIPT}\n\n"
        f"{DUAL_MODEL_SETTINGS_SCRIPT}\n\n"
        f"{CARD_CLIENT_AUTOMATION_SCRIPT}\n\n"
        f"{CARD_CLIENT_UNIFIED_IMPORT_SCRIPT}\n\n"
        f"{MEDIA_UPLOAD_WORKSPACE_SCRIPT}\n\n"
        f"{CONVERSATION_SESSION_SCRIPT}\n\n"
        f"{CARD_CLIENT_COMPACT_SURFACE_SCRIPT}\n\n"
        f"{CARD_CLIENT_GENERATION_RECOVERY_SCRIPT}\n\n"
        f"{CONVERSATION_CONTENT_SCRIPT}\n\n"
        f"{CONVERSATION_CONTROLS_SCRIPT}\n\n"
        f"{MESSAGE_HISTORY_WINDOW_SCRIPT}\n\n"
        f"{RELATIONSHIP_EVIDENCE_SCRIPT}\n\n"
        f"{PRODUCT_MANAGEMENT_SCRIPT}\n\n"
        f"{ACCOUNT_SECURITY_SCRIPT}\n\n"
        f"{ACTION_REANALYSIS_SCRIPT}\n\n"
        f"{ACTION_LEARNING_SCRIPT}\n\n"
        f"{ACTION_FEEDBACK_SCRIPT}\n\n"
        f"{ACTION_OUTCOME_SCRIPT}\n\n"
        f"{ACTION_EXECUTION_SCRIPT}\n\n"
        f"{ACTION_DECISION_SCRIPT}\n\n"
        f"{ACTION_PLAN_SCRIPT}\n\n"
        f"{STRATEGIC_REPLY_SCRIPT}\n\n"
        f"{STRATEGY_RECOMMENDATION_SCRIPT}\n\n"
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