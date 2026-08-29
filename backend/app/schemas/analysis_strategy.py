from app.schemas.strategy_decision import StrategyDecisionContextResponse
from app.schemas.structured_analysis import StructuredAnalysis


class AnalysisStrategyContextResponse(StrategyDecisionContextResponse):
    structured_analysis: StructuredAnalysis
