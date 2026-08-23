from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.domain.errors import ConversationNotFoundError
from app.schemas.analysis import AnalysisContextResponse
from app.services.analysis import AnalysisService


router = APIRouter(
    prefix="/conversations/{conversation_id}/analysis",
    tags=["analysis"],
)

service = AnalysisService()


@router.get("/context", response_model=AnalysisContextResponse)
def get_analysis_context(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        with get_connection() as conn:
            conversation, person, messages = service.get_context(
                conn,
                user_id,
                conversation_id,
            )
    except ConversationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        ) from exc

    return AnalysisContextResponse(
        conversation=conversation,
        person=person,
        messages=messages,
        facts=[],
        inferences=[],
        unknowns=[],
        recommendations=[],
    )
