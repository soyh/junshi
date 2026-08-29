from typing import Any

from app.schemas.action_plan import ActionPlanContextResponse
from app.schemas.structured_analysis import StructuredAnalysis


class AnalysisActionPlanContextResponse(ActionPlanContextResponse):
    structured_analysis: StructuredAnalysis
    action_plan_inputs: dict[str, Any]
