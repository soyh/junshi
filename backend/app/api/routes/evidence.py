from fastapi import APIRouter, Depends, HTTPException, status

from app.core.context import get_current_user_id
from app.core.database import get_connection
from app.schemas.evidence import EvidenceResponse
from app.services.evidence import EvidenceService


router = APIRouter(
    prefix="/conversations/{conversation_id}/analysis/evidence",
    tags=["evidence"],
)

service = EvidenceService()


@router.get(
    "",
    response_model=EvidenceResponse,
    status_code=status.HTTP_200_OK,
)
def get_evidence(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    with get_connection() as conn:
        result = service.get_conversation_evidence(
            conn,
            user_id,
            conversation_id,
        )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    result_conversation_id, person_id, evidence = result

    return EvidenceResponse(
        conversation_id=result_conversation_id,
        person_id=person_id,
        evidence=evidence,
    )
