from app.core.database import get_connection
from app.repositories.action_decision import ActionDecisionRepository
from app.repositories.action_execution import ActionExecutionRepository
from app.repositories.action_outcome import ActionOutcomeRepository


PASSWORD = "persisted-learning-history-password"


def _register(client, username: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_person_relationship(client, token: str):
    person = client.post(
        "/api/v1/persons",
        headers=_auth(token),
        json={"name": "Persisted Learning Person"},
    )
    assert person.status_code == 201
    person_body = person.json()
    relationship = client.post(
        "/api/v1/relationships",
        headers=_auth(token),
        json={
            "person_id": person_body["id"],
            "status": "active",
            "stage": "dating",
        },
    )
    assert relationship.status_code == 201
    return person_body


def _create_observed_outcome(person: dict):
    with get_connection() as conn:
        decision = ActionDecisionRepository.create(
            conn,
            person["user_id"],
            person["id"],
            "persisted-history-recommendation",
            "confirmed",
            "explicit confirmation",
        )
        ActionExecutionRepository.create(
            conn,
            person["user_id"],
            person["id"],
            decision["id"],
            None,
            "explicit execution",
        )
        ActionOutcomeRepository.create(
            conn,
            person["user_id"],
            person["id"],
            decision["id"],
            "completed",
            "observed completion",
        )


def test_learning_workspace_exposes_explicit_persisted_history_load(client):
    html = client.get("/app").text

    for element_id in (
        "load-persisted-action-learning",
        "action-learning-history-status",
        "action-learning-history",
    ):
        assert f'id="{element_id}"' in html

    start = html.index("const actionLearningStatus = byId('action-learning-status')")
    end = html.index("const actionFeedbackStatus = byId('action-feedback-status')")
    script = html[start:end]
    assert "async function loadPersistedActionLearning()" in script
    assert "`/api/v1/persons/${encodeURIComponent(selectedPersonId)}/memory-updates`" in script
    assert "bind('load-persisted-action-learning', loadPersistedActionLearning" in script
    assert "No LLM call or Re-analysis was started." in script

    person_listener = script[script.index("byId('person-select').addEventListener('change'"):]
    assert "resetActionLearningWorkspace();" in person_listener
    assert "loadPersistedActionLearning()" not in person_listener


def test_persisted_learning_history_round_trip_and_scope_isolation(client):
    alice_token = _register(client, "persisted-history-alice")
    bob_token = _register(client, "persisted-history-bob")
    person = _create_person_relationship(client, alice_token)
    _create_observed_outcome(person)

    synthesis = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/learning-synthesis",
        headers=_auth(alice_token),
    )
    assert synthesis.status_code == 200
    updates = synthesis.json()["updates"]
    assert len(updates) == 1
    candidate_id = updates[0]["source_candidate_id"]

    persisted = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/{candidate_id}/persist",
        headers=_auth(alice_token),
    )
    assert persisted.status_code == 201
    persisted_body = persisted.json()

    history = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates",
        headers=_auth(alice_token),
    )
    assert history.status_code == 200
    items = history.json()
    assert len(items) == 1
    assert items[0] == persisted_body
    assert items[0]["status"] == "persisted"
    assert items[0]["source_candidate_id"] == candidate_id
    assert items[0]["memory"]["action_outcome"] == "completed"

    foreign = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates",
        headers=_auth(bob_token),
    )
    assert foreign.status_code == 404


def test_persisted_learning_history_for_owned_person_without_memory_is_empty(client):
    token = _register(client, "persisted-history-empty")
    person = _create_person_relationship(client, token)

    response = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates",
        headers=_auth(token),
    )
    assert response.status_code == 200
    assert response.json() == []
