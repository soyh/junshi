from fastapi import APIRouter

from app.api.routes.action_decision import router as action_decision_router
from app.api.routes.action_feedback import router as action_feedback_router
from app.api.routes.action_outcome import router as action_outcome_router
from app.api.routes.action_plan import router as action_plan_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.conversations import router as conversations_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.interactions import router as interactions_router
from app.api.routes.messages import (
    conversation_messages_router,
    router as messages_router,
)
from app.api.routes.person_profiles import router as person_profiles_router
from app.api.routes.persons import router as persons_router
from app.api.routes.recommendation import router as recommendation_router
from app.api.routes.relationships import router as relationships_router
from app.api.routes.relationship_state import router as relationship_state_router
from app.api.routes.strategic_reply import router as strategic_reply_router
from app.api.routes.text_imports import router as text_imports_router
from app.api.routes.timeline import router as timeline_router


api_router = APIRouter(
    prefix="/api/v1",
)

api_router.include_router(persons_router)
api_router.include_router(person_profiles_router)
api_router.include_router(relationships_router)
api_router.include_router(relationship_state_router)
api_router.include_router(recommendation_router)
api_router.include_router(strategic_reply_router)
api_router.include_router(action_plan_router)
api_router.include_router(action_decision_router)
api_router.include_router(action_outcome_router)
api_router.include_router(action_feedback_router)
api_router.include_router(interactions_router)
api_router.include_router(messages_router)
api_router.include_router(conversation_messages_router)
api_router.include_router(conversations_router)
api_router.include_router(timeline_router)
api_router.include_router(text_imports_router)
api_router.include_router(analysis_router)
api_router.include_router(evidence_router)
