from typing import Any

from pydantic import ConfigDict

from app.schemas.action_plan import ActionPlanConstraints, ActionPlanContextResponse
from app.schemas.structured_analysis import StructuredAnalysis


class AnalysisActionPlanConstraints(ActionPlanConstraints):
    model_config = ConfigDict(extra="forbid")

    must_treat_llm_output_as_derived: bool = True
    must_preserve_evidence_provenance: bool = True


class AnalysisActionPlanContextResponse(ActionPlanContextResponse):
    action_constraints: AnalysisActionPlanConstraints
    structured_analysis: StructuredAnalysis
    action_plan_inputs: dict[str, Any]
