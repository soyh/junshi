from app.api.routes import analysis, analysis_recommendation
from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository
from app.repositories.action_execution import ActionExecutionRepository
from app.repositories.action_outcome import ActionOutcomeRepository
from app.services.auth_session import AuthSessionService


auth_session_service = AuthSessionService()


class FakeAnalysisContextService:
    def __init__(self):
        self.calls = []

    def get_context(self, conn, user_id, conversation_id):
        self.calls.append((user_id, conversation_id))
        return {
            "conversation": {"id": conversation_id, "person_id": "person-146"},
            "person": {"id": "person-146", "user_id": user_id},
            "messages": [],
            "facts": [],
            "inferences": [],
            "unknowns": [],
            "recommendations": [],
            "learning_strategy": {
                "learning_inputs": {
                    "action_feedback": [
                        {
                            "recommendation_id": "recommendation-146",
                            "learning_status": "observed_feedback",
                            "observed_outcome_count": 1,
                            "outcome_unknown_count": 0,
                            "unknowns": ["relationship_impact"],
                            "source": {"observed_outcomes": 1, "unknown_outcomes": 0},
                        }
                    ],
                    "memory_updates": [],
                    "strategy_decision": {"items": []},
                },
                "strategy_constraints": {
                    "must_be_source_backed": True,
                    "must_preserve_unknowns": True,
                    "must_not_infer_success": True,
                    "must_not_call_llm": True,
                },
            },
        }


class FakeRecommendationContextService:
    def __init__(self):
        self.calls = []

    def build_context(self, conn, user_id, conversation_id, *, provider=None, structured_analysis=None):
        self.calls.append((user_id, conversation_id))
        return {
            "person": {"id": "person-146", "user_id": user_id},
            "relationship": {"person_id": "person-146", "status": "active", "stage": "dating"},
            "current_state": {"status": "active", "stage": "dating"},
            "evidence": [{"id": "evidence-146", "type": "message"}],
            "facts": [],
            "inferences": [],
            "unknowns": [],
            "recommendations": [
                {
                    "id": "recommendation-fresh-146",
                    "recommendation": "Fresh source-backed recommendation",
                    "evidence_source_ids": ["evidence-146"],
                    "action": "observe",
                    "reply": None,
                    "priority": "medium",
                    "time_horizon": "short",
                    "provenance": {"source": "strategy_candidate"},
                }
            ],
            "learning_strategy": {
                "candidates": [],
                "strategy_decision_learning": {},
                "constraints": {"must_not_auto_select": True},
            },
            "structured_analysis": {
                "summary": "Fresh derived re-analysis",
                "observed_facts": [],
                "inferences": [],
                "unknowns": [],
                "hypotheses": [],
                "emotional_signals": [],
                "relationship_signals": [],
                "risk_signals": [],
                "intent_signals": [],
                "evidence_links": [],
                "analysis_constraints": ["must_preserve_unknowns"],
            },
            "recommendation_constraints": {
                "must_be_evidence_backed": True,
                "must_preserve_unknowns": True,
                "must_treat_llm_output_as_derived": True,
                "must_preserve_evidence_provenance": True,
                "must_not_auto_select": True,
                "must_not_auto_execute": True,
            },
        }


def _session(user_id: str) -> str:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
        return auth_session_service.create(conn, user_id).access_token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_person_relationship_conversation(client, token: str, name: str = "TEST-146 Person"):
    person_response = client.post(
        "/api/v1/persons",
        headers=_auth(token),
        json={"name": name},
    )
    assert person_response.status_code == 201
    person = person_response.json()

    relationship_response = client.post(
        "/api/v1/relationships",
        headers=_auth(token),
        json={"person_id": person["id"], "status": "active", "stage": "dating"},
    )
    assert relationship_response.status_code == 201

    conversation_response = client.post(
        "/api/v1/conversations",
        headers=_auth(token),
        json={"person_id": person["id"], "title": "TEST-146 Re-analysis"},
    )
    assert conversation_response.status_code == 201
    return person, relationship_response.json(), conversation_response.json()


def _reanalysis_script(html: str) -> str:
    start = html.index("const actionReanalysisInputStatus = byId('action-reanalysis-input-status')")
    end = html.index("const actionLearningStatus = byId('action-learning-status')")
    return html[start:end]


def test_product_shell_exposes_reanalysis_workspace_after_learning(client):
    html = client.get("/app").text
    for control_id in (
        "action-reanalysis-workspace",
        "load-action-reanalysis-inputs",
        "action-reanalysis-input-status",
        "action-reanalysis-learning",
        "action-reanalysis-constraints",
        "run-action-reanalysis",
        "action-reanalysis-run-status",
        "action-reanalysis-analysis",
        "action-reanalysis-recommendations",
        "action-reanalysis-recommendation-constraints",
    ):
        assert f'id="{control_id}"' in html
    assert "Load re-analysis inputs" in html
    assert "Run re-analysis" in html
    assert html.index('id="action-learning-workspace"') < html.index('id="action-reanalysis-workspace"')
    assert html.index('id="action-reanalysis-workspace"') < html.index('id="provider"')


def test_reanalysis_fragment_uses_existing_canonical_read_and_llm_endpoints_only(client):
    script = _reanalysis_script(client.get("/app").text)
    assert "`/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/analysis/context`" in script
    assert "`/api/v1/conversations/${encodeURIComponent(selectedConversationId)}/recommendation/context`" in script
    assert "/re-analysis" not in script
    assert "/analysis/structured" not in script
    assert "/strategy/context" not in script
    assert "method: 'POST'" not in script
    assert "method: 'PATCH'" not in script
    assert "method: 'DELETE'" not in script


def test_reanalysis_requires_separate_explicit_preflight_and_run_and_learning_does_not_trigger_it(client):
    html = client.get("/app").text
    script = _reanalysis_script(html)
    assert "bind('load-action-reanalysis-inputs', loadActionReanalysisInputs" in script
    assert "bind('run-action-reanalysis', runActionReanalysis" in script

    conversation_listener = script[script.index("byId('conversation-select').addEventListener('change'"):]
    assert "resetActionReanalysisWorkspace" in conversation_listener
    assert "loadActionReanalysisInputs()" not in conversation_listener
    assert "runActionReanalysis()" not in conversation_listener

    learning_start = html.index("const actionLearningStatus = byId('action-learning-status')")
    learning_end = html.index("const actionFeedbackStatus = byId('action-feedback-status')")
    learning_script = html[learning_start:learning_end]
    assert "loadActionReanalysisInputs" not in learning_script
    assert "runActionReanalysis" not in learning_script
    assert "/recommendation/context" not in learning_script


def test_reanalysis_preserves_unknowns_llm_boundary_derived_status_and_safe_dom(client):
    html = client.get("/app").text
    script = _reanalysis_script(html)
    assert "must_not_call_llm" in html
    assert "learning_status" in script
    assert "outcome_unknown_count" in script
    assert "source_unknown_outcomes" in script
    assert "Unknown Outcome remains unknown" in script
    assert "No LLM/provider call was made" in script
    assert "Fresh derived analysis completed" in script
    assert "Nothing was auto-selected, planned, executed, sent, or applied to Relationship" in script
    assert "document.createElement('div')" in script
    assert "replaceChildren()" in script
    assert "innerHTML" not in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html


def test_real_bearer_identity_flows_into_reanalysis_preflight_without_provider(client, monkeypatch):
    token = _session("test146-preflight-user")
    _, _, conversation = _create_person_relationship_conversation(client, token)
    fake = FakeAnalysisContextService()
    monkeypatch.setattr(analysis, "service", fake)

    response = client.get(
        f"/api/v1/conversations/{conversation['id']}/analysis/context",
        headers=_auth(token),
    )
    assert response.status_code == 200
    assert response.json()["learning_strategy"]["strategy_constraints"]["must_not_call_llm"] is True
    assert fake.calls == [(conversation["user_id"], conversation["id"])]


def test_real_bearer_identity_flows_into_explicit_reanalysis_run(client, monkeypatch):
    token = _session("test146-run-user")
    _, _, conversation = _create_person_relationship_conversation(client, token)
    fake = FakeRecommendationContextService()
    monkeypatch.setattr(analysis_recommendation, "service", fake)
    monkeypatch.setattr(analysis_recommendation, "_build_provider", lambda conn, user_id: object())

    response = client.get(
        f"/api/v1/conversations/{conversation['id']}/recommendation/context",
        headers=_auth(token),
    )
    assert response.status_code == 200
    assert response.json()["structured_analysis"]["summary"] == "Fresh derived re-analysis"
    assert response.json()["recommendations"][0]["provenance"]["source"] == "strategy_candidate"
    assert fake.calls == [(conversation["user_id"], conversation["id"])]


def test_canonical_observed_feedback_reaches_fresh_reanalysis_and_recommendation_without_relationship_mutation(client, monkeypatch):
    token = _session("test146-closure-user")
    person, relationship, conversation = _create_person_relationship_conversation(client, token)
    message_response = client.post(
        "/api/v1/messages",
        headers=_auth(token),
        json={
            "conversation_id": conversation["id"],
            "sender_type": "user",
            "content": "TEST-146 observed evidence",
            "sent_at": "2026-09-19T04:00:00+00:00",
        },
    )
    assert message_response.status_code == 201
    message = message_response.json()

    with get_connection() as conn:
        decision = ActionDecisionRepository.create(
            conn,
            person["user_id"],
            person["id"],
            "recommendation-before-146",
            "confirmed",
            "confirmed explicitly",
        )
        ActionExecutionRepository.create(
            conn,
            person["user_id"],
            person["id"],
            decision["id"],
            None,
            "executed explicitly",
        )
        ActionOutcomeRepository.create(
            conn,
            person["user_id"],
            person["id"],
            decision["id"],
            "completed",
            "observed completed outcome",
        )

    class Provider:
        def __init__(self):
            self.learning_consumed = None

        def analyze(self, context):
            learning = context["learning_strategy"]["learning_inputs"]["action_feedback"]
            assert len(learning) == 1
            item = learning[0]
            assert item["recommendation_id"] == "recommendation-before-146"
            assert item["learning_status"] == "observed_feedback"
            assert item["observed_outcome_count"] == 1
            assert item["outcome_unknown_count"] == 0
            assert item["source"]["observed_outcomes"] == 1
            self.learning_consumed = item["recommendation_id"]
            return {
                "summary": f"re-analysis-consumed:{self.learning_consumed}",
                "observed_facts": [
                    {
                        "content": "Previous action has an observed outcome",
                        "confidence": 1.0,
                        "evidence_source_ids": [message["id"]],
                    }
                ],
                "inferences": [],
                "unknowns": [
                    {
                        "content": "Long-term relationship impact remains unknown",
                        "confidence": 1.0,
                        "evidence_source_ids": [message["id"]],
                    }
                ],
                "hypotheses": [
                    {
                        "content": "Use the observed outcome for the next low-pressure step",
                        "confidence": 0.7,
                        "evidence_source_ids": [message["id"]],
                    }
                ],
                "emotional_signals": [],
                "relationship_signals": [],
                "risk_signals": [],
                "intent_signals": [],
                "evidence_links": [{"evidence_id": message["id"], "type": "message"}],
                "analysis_constraints": ["must_preserve_unknowns"],
            }

    provider = Provider()
    monkeypatch.setattr(analysis_recommendation, "_build_provider", lambda conn, user_id: provider)

    before = client.get(
        f"/api/v1/persons/{person['id']}/profile",
        headers=_auth(token),
    ).json()
    response = client.get(
        f"/api/v1/conversations/{conversation['id']}/recommendation/context",
        headers=_auth(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert provider.learning_consumed == "recommendation-before-146"
    assert body["structured_analysis"]["summary"] == "re-analysis-consumed:recommendation-before-146"
    assert body["recommendations"][0]["recommendation"] == "Use the observed outcome for the next low-pressure step"
    assert body["recommendations"][0]["evidence_source_ids"] == [message["id"]]
    assert body["recommendations"][0]["provenance"]["source"] == "strategy_candidate"
    assert body["recommendation_constraints"]["must_not_auto_select"] is True
    assert body["recommendation_constraints"]["must_not_auto_execute"] is True

    after = client.get(
        f"/api/v1/persons/{person['id']}/profile",
        headers=_auth(token),
    ).json()
    assert before["relationships"] == after["relationships"]
    assert after["relationships"][0]["id"] == relationship["id"]


def test_reanalysis_keeps_missing_outcome_unknown_and_is_user_scope_isolated(client):
    alice_token = _session("test146-alice")
    bob_token = _session("test146-bob")
    person, _, conversation = _create_person_relationship_conversation(client, alice_token, "Alice Re-analysis Person")

    with get_connection() as conn:
        ActionDecisionRepository.create(
            conn,
            person["user_id"],
            person["id"],
            "recommendation-unknown-146",
            "confirmed",
            "confirmed but no outcome",
        )

    own = client.get(
        f"/api/v1/conversations/{conversation['id']}/analysis/context",
        headers=_auth(alice_token),
    )
    assert own.status_code == 200
    feedback = own.json()["learning_strategy"]["learning_inputs"]["action_feedback"]
    assert len(feedback) == 1
    assert feedback[0]["learning_status"] == "outcome_unknown"
    assert feedback[0]["observed_outcome_count"] == 0
    assert feedback[0]["outcome_unknown_count"] == 1
    assert own.json()["learning_strategy"]["strategy_constraints"]["must_not_infer_success"] is True

    foreign = client.get(
        f"/api/v1/conversations/{conversation['id']}/analysis/context",
        headers=_auth(bob_token),
    )
    assert foreign.status_code == 404
