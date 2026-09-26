from app.schemas.reference_context import ModelReferenceContextResponse
from app.schemas.strategy_decision import StrategyDecisionContextResponse
from app.schemas.structured_analysis import StructuredAnalysis


class AnalysisStrategyContextResponse(StrategyDecisionContextResponse):
    structured_analysis: StructuredAnalysis
    # Legacy analysis contexts may not carry reference metadata.
    model_references: ModelReferenceContextResponse | None = None
