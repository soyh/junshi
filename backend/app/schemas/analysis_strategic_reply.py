from typing import Any

from app.schemas.strategic_reply import StrategicReplyContextResponse
from app.schemas.structured_analysis import StructuredAnalysis


class AnalysisStrategicReplyContextResponse(StrategicReplyContextResponse):
    structured_analysis: StructuredAnalysis
    reply_inputs: dict[str, Any]
