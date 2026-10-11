from app.api.routes import action_feedback
from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository
from app.repositories.action_execution import ActionExecutionRepository
from app.repositories.action_outcome import ActionOutcomeRepository
from app.services.auth_session import AuthSessionService


auth_session_service = AuthSessionService()


class FakeFeedbackService:
    def __init__(self):
        self.calls = []

    def _base(self, user_id, person_id):
        return {
            "person": {"id": person_id, "user_id": user_id},
            "relationship": {"person_id": person_id},
        }

    def get_context(self, conn, user_id, person_id):
        self.calls.append(("context", user_id, person_id))
        return {
            **self._base(user_id, person_id),
            "feedback_constraints": {
                "must_be_decision_backed": True,
                "must_be_outcome_backed": False,
                "must_preserve_unknowns": True,
                "must_not_infer_success_from_missing_outcome": True,
                "must_not_change_relationship": True,
                "must_not_auto_execute": True,
                "must_have_explicit_feedback_status": True,
            },
            "feedback": [],
            "feedback_synthesis": [],
        }

    def get_summary(self, conn, user_id, person_id):
        self.calls.append(("summary", user_id, person_id))
        return {
            **self._base(user_id, person_id),
            "feedback_summary_constraints": {
                "must_be_source_backed": True,
                "must_preserve_unknowns": True,
                "must_not_infer_relationship_impact": True,
                "must_not_infer_success_from_missing_outcome": True,
                "must_not_change_relationship": True,
                "must_not_auto_execute": True,
            },
            "summary": {
                "total_decisions": 0,
                "decision_counts": {"confirmed": 0, "rejected": 0},
                "outcome_observed_count": 0,
                "outcome_unknown_count": 0,
                "outcome_counts": {"completed": 0, "skipped": 0, "failed": 0},
                "latest_observed_outcome": None,
            },
        }

    def get_trend(self, conn, user_id, person_id):
        self.calls.append(("trend", user_id, person_id))
        return {
            **self._base(user_id, person_id),
            "feedback_trend_constraints": {
                "must_be_source_backed": True,
                "must_preserve_unknowns": True,
                "must_have_deterministic_ordering": True,
                "must_not_infer_relationship_impact": True,
                "must_not_change_relationship": True,
                "must_not_auto_execute": True,
            },
            "observations": [],
        }

    def get_signals(self, conn, user_id, person_id):
        self.calls.append(("signals", user_id, person_id))
        return {
            **self._base(user_id, person_id),
            "feedback_signal_constraints": {
                "must_be_source_backed": True,
                "must_preserve_unknowns": True,
                "must_group_only_by_recommendation_identity": True,
                "must_not_infer_recommendation_quality": True,
                "must_not_infer_relationship_impact": True,
                "must_not_change_relationship": True,
                "must_not_auto_execute": True,
            },
            "signals": [],
        }


def _session(user_id: str) -> str:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
        return auth_session_service.create(conn, user_id).access_token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_person_relationship(client, token: str, name: str = "TEST-144 Person"):
    person = client.post(
        "/api/v1/persons",
        headers=_auth(token),
        json={"name": name},
    )
    assert person.status_code == 201
    person_body = person.json()
    relationship = client.post(
        "/api/v1/relationships",
        headers=_auth(token),
        json={"person_id": person_body["id"], "status": "active", "stage": "dating"},
    )
    assert relationship.status_code == 201
    return person_body, relationship.json()


def test_product_shell_exposes_feedback_workspace(client):
    html = client.get("/app").text
    for control_id in (
        "action-feedback-workspace",
        "load-action-feedback",
        "action-feedback-status",
        "action-feedback-items",
        "action-feedback-summary",
        "action-feedback-trend",
        "action-feedback-signals",
    ):
        assert f'id="{control_id}"' in html
    assert "Load feedback" in html
    assert "Feedback Summary" in html
    assert "Feedback Trend" in html
    assert "Recommendation Signals" in html


def test_feedback_fragment_uses_read_only_canonical_endpoints_without_learning_context(client):
    html = client.get("/app").text
    start = html.index("const actionFeedbackStatus = byId('action-feedback-status')")
    end = html.index("const actionOutcomeStatus = byId('action-outcome-status')")
    script = html[start:end]

    assert "`${personPath}/context`" in script
    assert "`${personPath}/summary`" in script
    assert "`${personPath}/trend`" in script
    assert "`${personPath}/signals`" in script
    assert "/learning-context" not in script
    assert "method: 'POST'" not in script
    assert "method: 'PATCH'" not in script
    assert "method: 'DELETE'" not in script
    assert "learning-synthesis" not in script
    assert "/re-analysis" not in script.lower()
    assert "loadreanalysis" not in script.lower()
    assert "runreanalysis" not in script.lower()


def test_feedback_requires_explicit_load_and_outcome_does_not_auto_load_feedback(client):
    html = client.get("/app").text
    start = html.index("const actionFeedbackStatus = byId('action-feedback-status')")
    end = html.index("const actionOutcomeStatus = byId('action-outcome-status')")
    script = html[start:end]

    person_listener = script[script.index("byId('person-select').addEventListener('change'"):]
    assert "resetActionFeedbackWorkspace" in person_listener
    assert "loadActionFeedback()" not in person_listener
    assert "bind('load-action-feedback', loadActionFeedback" in script

    outcome_start = html.index("const actionOutcomeStatus = byId('action-outcome-status')")
    outcome_end = html.index("const actionExecutionStatus = byId('action-execution-status')")
    outcome_script = html[outcome_start:outcome_end]
    assert "loadActionFeedback" not in outcome_script
    assert "/action-plan/feedback" not in outcome_script


def test_feedback_preserves_unknowns_source_boundaries_and_safe_dom(client):
    html = client.get("/app").text
    start = html.index("const actionFeedbackStatus = byId('action-feedback-status')")
    end = html.index("const actionOutcomeStatus = byId('action-outcome-status')")
    script = html[start:end]

    assert "item.outcome || 'unknown'" in script
    assert "feedback_status" in script
    assert "unknowns" in script
    assert "Read-only; no Learning or Re-analysis was started." in script
    assert "document.createElement('div')" in script
    assert "replaceChildren()" in script
    assert "innerHTML" not in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html


def test_real_bearer_identity_flows_into_all_feedback_read_views(client, monkeypatch):
    token = _session("test144-feedback-user")
    person, _ = _create_person_relationship(client, token)
    fake = FakeFeedbackService()
    monkeypatch.setattr(action_feedback, "service", fake)

    for suffix in ("context", "summary", "trend", "signals"):
        response = client.get(
            f"/api/v1/persons/{person['id']}/action-plan/feedback/{suffix}",
            headers=_auth(token),
        )
        assert response.status_code == 200

    assert fake.calls == [
        ("context", person["user_id"], person["id"]),
        ("summary", person["user_id"], person["id"]),
        ("trend", person["user_id"], person["id"]),
        ("signals", person["user_id"], person["id"]),
    ]


def test_canonical_feedback_reads_decision_and_observed_outcome_without_new_feedback_write(client):
    token = _session("test144-canonical-user")
    person, _ = _create_person_relationship(client, token)

    with get_connection() as conn:
        decision = ActionDecisionRepository.create(
            conn,
            person["user_id"],
            person["id"],
            "recommendation-144",
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
            "observed outcome",
        )

    context = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/feedback/context",
        headers=_auth(token),
    ).json()
    summary = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/feedback/summary",
        headers=_auth(token),
    ).json()
    trend = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/feedback/trend",
        headers=_auth(token),
    ).json()
    signals = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/feedback/signals",
        headers=_auth(token),
    ).json()

    assert context["feedback"][0]["decision_id"] == decision["id"]
    assert context["feedback_synthesis"][0]["feedback_status"] == "outcome_observed"
    assert context["feedback_synthesis"][0]["outcome_signal"] == "completed"
    assert summary["summary"]["outcome_observed_count"] == 1
    assert trend["observations"][0]["source"]["decision_id"] == decision["id"]
    assert signals["signals"][0]["recommendation_id"] == "recommendation-144"
    assert signals["feedback_signal_constraints"]["must_not_infer_recommendation_quality"] is True


def test_feedback_keeps_missing_outcome_unknown_instead_of_inferring_success(client):
    token = _session("test144-unknown-user")
    person, _ = _create_person_relationship(client, token)
    with get_connection() as conn:
        ActionDecisionRepository.create(
            conn,
            person["user_id"],
            person["id"],
            "recommendation-unknown-144",
            "rejected",
            "not selected",
        )

    context = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/feedback/context",
        headers=_auth(token),
    ).json()
    assert context["feedback_synthesis"][0]["feedback_status"] == "outcome_unknown"
    assert context["feedback_synthesis"][0]["outcome_signal"] == "unknown"
    assert context["feedback_constraints"]["must_not_infer_success_from_missing_outcome"] is True


def test_feedback_scope_isolated_by_authenticated_user(client):
    alice_token = _session("test144-alice")
    bob_token = _session("test144-bob")
    person, _ = _create_person_relationship(client, alice_token, "Alice Feedback Person")

    response = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/feedback/context",
        headers=_auth(bob_token),
    )
    assert response.status_code == 404
