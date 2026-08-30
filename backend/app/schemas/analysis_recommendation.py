from typing import Any

from app.schemas.recommendation import RecommendationContextResponse
from app.schemas.structured_analysis import StructuredAnalysis


class AnalysisRecommendationContextResponse(RecommendationContextResponse):
    structured_analysis: StructuredAnalysis
    recommendation_constraints: dict[str, Any]
