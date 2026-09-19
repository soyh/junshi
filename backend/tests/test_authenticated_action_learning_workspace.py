from app.api.routes import memory_learning_synthesis, memory_persistence
from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository
from app.repositories.action_execution import ActionExecutionRepository
from app.repositories.action_outcome import ActionOutcomeRepository
from app.services.auth_session import AuthSessionService


auth_session_service = AuthSessionService()


class FakeLearningService:
    def __init__(self):
        self.calls = []

    def get_context(self, conn, user_id, person_id):
        self.calls.append((user_id, person_id))
        return {
            "person": {"id": person_id, "user_id": user_id},
            "relationship": {"person_id": person_id},
            "memory_constraints": {
                "must_be_source_backed": True,
                "must_preserve_unknowns": True,
                "must_not_auto_persist": True,
                "must_not_infer_success": True,
            },
            "updates": [
                {
                    "id": "learning-update-145",
                    "status": "proposed",
                    "category": "action_feedback",
                    "source_candidate_id": "memory-candidate-145",
                    "source_decision_id": "decision-145",
                    "source_outcome_id": "outcome-145",
                    "source_created_at": "2026-09-19T00:00:00+00:00",
                    "memory": {
                        "action_outcome": "completed",
                        "note": "observed only",
                    },
                    "unknowns": ["long_term_relationship_impact"],
                    "learning_provenance": {
                        "status": "observed_outcome",
                        "recommendation_id": "recommendation-145",
                        "source_decision_id": "decision-145",
                        "source_outcome_id": "outcome-145",
                        "outcome_observed_count": 1,
                        "outcome_unknown_count": 0,
                        "outcome_counts": {"completed": 1, "skipped": 0, "failed": 0},
                    },
                }
            ],
        }


class FakePersistenceService:
    def __init__(self):
        self.calls = []

    def persist_candidate(self, conn, user_id, person_id, candidate_id):
        self.calls.append((user_id, person_id, candidate_id))
        return {
            "id": "persisted-learning-145",
            "status": "persisted",
            "category": "action_feedback",
            "person_id": person_id,
            "source_candidate_id": candidate_id,
            "source_decision_id": "decision-145",
            "source_outcome_id": "outcome-145",
            "memory": {"action_outcome": "completed", "note": "observed only"},
            "created_at": "2026-09-19T00:00:01+00:00",
        }


def _session(user_id: str) -> str:
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
        return auth_session_service.create(conn, user_id).access_token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_person_relationship(client, token: str, name: str = "TEST-145 Person"):
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


def _learning_script(html: str) -> str:
    start = html.index("const actionLearningStatus = byId('action-learning-status')")
    end = html.index("const actionFeedbackStatus = byId('action-feedback-status')")
    return html[start:end]


def test_product_shell_exposes_learning_workspace(client):
    html = client.get("/app").text
    for control_id in (
        "action-learning-workspace",
        "load-action-learning",
        "action-learning-candidate",
        "action-learning-candidate-detail",
        "persist-action-learning",
        "action-learning-status",
        "action-learning-persisted",
    ):
        assert f'id="{control_id}"' in html
    assert "Load learning" in html
    assert "Persist selected learning memory" in html


def test_learning_fragment_uses_only_canonical_learning_and_persist_endpoints(client):
    script = _learning_script(client.get("/app").text)
    assert "`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/memory-updates/learning-synthesis`" in script
    assert "`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/memory-updates/${encodeURIComponent(candidateId)}/persist`" in script
    assert "method: 'POST'" in script
    assert "method: 'PATCH'" not in script
    assert "method: 'DELETE'" not in script
    assert "/learning-strategy" not in script
    assert "/analysis" not in script
    assert "structured-analysis" not in script
    assert "learning-context" not in script


def test_learning_requires_explicit_load_and_explicit_persist(client):
    html = client.get("/app").text
    script = _learning_script(html)
    person_listener = script[script.index("byId('person-select').addEventListener('change'"):]
    assert "resetActionLearningWorkspace" in person_listener
    assert "loadActionLearning()" not in person_listener
    assert "persistSelectedActionLearning()" not in person_listener
    assert "bind('load-action-learning', loadActionLearning" in script
    assert "bind('persist-action-learning', persistSelectedActionLearning" in script

    feedback_start = html.index("const actionFeedbackStatus = byId('action-feedback-status')")
    feedback_end = html.index("const actionOutcomeStatus = byId('action-outcome-status')")
    feedback_script = html[feedback_start:feedback_end]
    assert "loadActionLearning" not in feedback_script
    assert "persistSelectedActionLearning" not in feedback_script
    assert "/memory-updates" not in feedback_script


def test_learning_preserves_provenance_unknowns_memory_token_and_safe_dom(client):
    html = client.get("/app").text
    script = _learning_script(html)
    assert "learning_provenance" in script
    assert "source_candidate_id" in script
    assert "source_decision_id" in script
    assert "source_outcome_id" in script
    assert "unknowns" in script
    assert "No Re-analysis, strategy application, LLM call, message send, or Relationship change was started." in script
    assert "document.createElement('option')" in script
    assert "replaceChildren()" in script
    assert "innerHTML" not in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "X-User-ID" not in html
    assert "headers.set('Authorization', `Bearer ${requireToken()}`)" in html


def test_real_bearer_identity_flows_into_learning_synthesis(client, monkeypatch):
    token = _session("test145-learning-user")
    person, _ = _create_person_relationship(client, token)
    fake = FakeLearningService()
    monkeypatch.setattr(memory_learning_synthesis, "service", fake)

    response = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/learning-synthesis",
        headers=_auth(token),
    )
    assert response.status_code == 200
    assert response.json()["updates"][0]["source_candidate_id"] == "memory-candidate-145"
    assert fake.calls == [(person["user_id"], person["id"])]


def test_real_bearer_identity_flows_into_explicit_memory_persist(client, monkeypatch):
    token = _session("test145-persist-user")
    person, _ = _create_person_relationship(client, token)
    fake = FakePersistenceService()
    monkeypatch.setattr(memory_persistence, "service", fake)

    response = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/memory-candidate-145/persist",
        headers=_auth(token),
    )
    assert response.status_code == 201
    assert response.json()["status"] == "persisted"
    assert fake.calls == [(person["user_id"], person["id"], "memory-candidate-145")]


def test_canonical_learning_requires_observed_outcome_and_persist_is_idempotent(client):
    token = _session("test145-canonical-user")
    person, _ = _create_person_relationship(client, token)

    with get_connection() as conn:
        decision = ActionDecisionRepository.create(
            conn,
            person["user_id"],
            person["id"],
            "recommendation-145",
            "confirmed",
            "confirmed explicitly",
        )

    before_outcome = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/learning-synthesis",
        headers=_auth(token),
    )
    assert before_outcome.status_code == 200
    assert before_outcome.json()["updates"] == []

    with get_connection() as conn:
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

    synthesis = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/learning-synthesis",
        headers=_auth(token),
    )
    assert synthesis.status_code == 200
    update = synthesis.json()["updates"][0]
    assert update["learning_provenance"]["status"] == "observed_outcome"
    candidate_id = update["source_candidate_id"]

    first = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/{candidate_id}/persist",
        headers=_auth(token),
    )
    second = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/{candidate_id}/persist",
        headers=_auth(token),
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json() == second.json()
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM memory_updates WHERE user_id = ? AND person_id = ? AND source_candidate_id = ?",
            (person["user_id"], person["id"], candidate_id),
        ).fetchone()[0]
    assert count == 1


def test_learning_persist_is_scope_isolated_and_does_not_mutate_relationship(client):
    alice_token = _session("test145-alice")
    bob_token = _session("test145-bob")
    person, relationship = _create_person_relationship(client, alice_token, "Alice Learning Person")

    with get_connection() as conn:
        decision = ActionDecisionRepository.create(
            conn,
            person["user_id"],
            person["id"],
            "recommendation-scope-145",
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
            "failed",
            "observed failure",
        )

    candidate_id = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/learning-synthesis",
        headers=_auth(alice_token),
    ).json()["updates"][0]["source_candidate_id"]

    foreign = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/{candidate_id}/persist",
        headers=_auth(bob_token),
    )
    assert foreign.status_code == 404

    before = client.get(
        f"/api/v1/persons/{person['id']}/profile",
        headers=_auth(alice_token),
    ).json()
    created = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/{candidate_id}/persist",
        headers=_auth(alice_token),
    )
    assert created.status_code == 201
    after = client.get(
        f"/api/v1/persons/{person['id']}/profile",
        headers=_auth(alice_token),
    ).json()
    assert before["relationships"] == after["relationships"]
    assert after["relationships"][0]["id"] == relationship["id"]
