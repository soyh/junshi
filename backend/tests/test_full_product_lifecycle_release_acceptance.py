from __future__ import annotations

from pathlib import Path

from app.api.routes import analysis_action_plan, analysis_recommendation
from app.config.settings import Settings, get_settings
from app.core.backup_manifest import create_managed_backup
from app.core.database import get_connection
from app.core.deployment import build_release_runbook
from app.core.preflight import check_release_preflight


PASSWORD = "correct-horse-battery-staple"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register(client, username: str = "test147-user") -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": PASSWORD},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def _derived_analysis(evidence_id: str, *, summary: str, hypothesis: str) -> dict:
    return {
        "summary": summary,
        "observed_facts": [
            {
                "content": "A real conversation message is available as canonical evidence",
                "confidence": 1.0,
                "evidence_source_ids": [evidence_id],
            }
        ],
        "inferences": [],
        "unknowns": [
            {
                "content": "Long-term relationship impact remains unknown",
                "confidence": 1.0,
                "evidence_source_ids": [evidence_id],
            }
        ],
        "hypotheses": [
            {
                "content": hypothesis,
                "confidence": 0.7,
                "evidence_source_ids": [evidence_id],
                "action": hypothesis,
            }
        ],
        "emotional_signals": [],
        "relationship_signals": [],
        "risk_signals": [],
        "intent_signals": [],
        "evidence_links": [{"evidence_id": evidence_id, "type": "message"}],
        "analysis_constraints": ["must_preserve_unknowns"],
    }


class LifecycleProvider:
    def __init__(self, evidence_id: str):
        self.evidence_id = evidence_id
        self.calls: list[dict] = []

    def analyze(self, context):
        learning = context["learning_strategy"]["learning_inputs"]
        self.calls.append(learning)

        if len(self.calls) == 1:
            assert learning["action_feedback"] == []
            return _derived_analysis(
                self.evidence_id,
                summary="Initial derived analysis",
                hypothesis="Send a low-pressure check-in",
            )

        feedback = learning["action_feedback"]
        assert len(feedback) == 1
        assert feedback[0]["learning_status"] == "observed_feedback"
        assert feedback[0]["observed_outcome_count"] == 1
        assert feedback[0]["outcome_unknown_count"] == 0
        assert feedback[0]["outcome_counts"]["completed"] == 1
        assert len(learning["memory_updates"]) == 1
        assert learning["memory_updates"][0]["learning_provenance"]["status"] == "observed_outcome"

        return _derived_analysis(
            self.evidence_id,
            summary="Fresh re-analysis consumed observed outcome learning",
            hypothesis="Use the observed outcome for the next low-pressure step",
        )


def test_authenticated_full_product_lifecycle_closes_through_explicit_reanalysis(client, monkeypatch):
    token = _register(client)
    headers = _auth(token)

    person_response = client.post(
        "/api/v1/persons",
        headers=headers,
        json={"name": "TEST-147 Full Lifecycle Person"},
    )
    assert person_response.status_code == 201
    person = person_response.json()

    relationship_response = client.post(
        "/api/v1/relationships",
        headers=headers,
        json={"person_id": person["id"], "status": "active", "stage": "dating"},
    )
    assert relationship_response.status_code == 201
    relationship = relationship_response.json()

    conversation_response = client.post(
        "/api/v1/conversations",
        headers=headers,
        json={"person_id": person["id"], "title": "TEST-147 Acceptance Conversation"},
    )
    assert conversation_response.status_code == 201
    conversation = conversation_response.json()

    message_response = client.post(
        "/api/v1/messages",
        headers=headers,
        json={
            "conversation_id": conversation["id"],
            "sender_type": "user",
            "content": "Canonical evidence for the release acceptance lifecycle",
            "sent_at": "2026-09-19T04:40:00+00:00",
        },
    )
    assert message_response.status_code == 201
    message = message_response.json()

    relationship_before = client.get(
        f"/api/v1/persons/{person['id']}/profile",
        headers=headers,
    ).json()["relationships"]

    provider = LifecycleProvider(message["id"])
    monkeypatch.setattr(
        analysis_action_plan,
        "_build_provider",
        lambda conn, user_id: provider,
    )
    monkeypatch.setattr(
        analysis_recommendation,
        "_build_provider",
        lambda conn, user_id: provider,
    )

    generated = client.get(
        f"/api/v1/conversations/{conversation['id']}/action-plan/context",
        headers=headers,
    )
    assert generated.status_code == 200
    generated_body = generated.json()
    assert len(provider.calls) == 1
    assert generated_body["structured_analysis"]["summary"] == "Initial derived analysis"
    assert len(generated_body["action_plan"]) == 1
    proposal = generated_body["action_plan"][0]
    recommendation_id = proposal["recommendation_id"]
    assert proposal["status"] == "proposed"
    assert proposal["requires_user_confirmation"] is True
    assert generated_body["action_constraints"]["must_not_auto_execute"] is True

    execution_before_decision = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/execution-context",
        headers=headers,
    )
    assert execution_before_decision.status_code == 200
    assert execution_before_decision.json()["decisions"] == []

    decision_response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/decisions",
        headers=headers,
        json={
            "recommendation_id": recommendation_id,
            "decision": "confirmed",
            "note": "TEST-147 explicit confirmation",
        },
    )
    assert decision_response.status_code == 201
    decision = decision_response.json()
    assert decision["decision"] == "confirmed"

    premature_outcome = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision['id']}",
        headers=headers,
        json={"outcome": "completed", "note": "must not exist before execution"},
    )
    assert premature_outcome.status_code == 409

    execution_response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/executions/{decision['id']}",
        headers=headers,
        json={"note": "TEST-147 explicit execution"},
    )
    assert execution_response.status_code == 201

    outcome_response = client.post(
        f"/api/v1/persons/{person['id']}/action-plan/outcomes/{decision['id']}",
        headers=headers,
        json={"outcome": "completed", "note": "TEST-147 observed outcome"},
    )
    assert outcome_response.status_code == 201
    outcome = outcome_response.json()

    feedback_response = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/feedback/context",
        headers=headers,
    )
    assert feedback_response.status_code == 200
    feedback = feedback_response.json()
    assert feedback["feedback_synthesis"][0]["feedback_status"] == "outcome_observed"
    assert feedback["feedback_synthesis"][0]["outcome_signal"] == "completed"
    assert feedback["feedback"][0]["outcome_id"] == outcome["id"]

    learning_response = client.get(
        f"/api/v1/persons/{person['id']}/memory-updates/learning-synthesis",
        headers=headers,
    )
    assert learning_response.status_code == 200
    learning = learning_response.json()
    assert len(learning["updates"]) == 1
    update = learning["updates"][0]
    assert update["learning_provenance"]["status"] == "observed_outcome"
    assert update["learning_provenance"]["recommendation_id"] == recommendation_id

    persist_response = client.post(
        f"/api/v1/persons/{person['id']}/memory-updates/{update['source_candidate_id']}/persist",
        headers=headers,
    )
    assert persist_response.status_code == 201
    persisted = persist_response.json()
    assert persisted["status"] == "persisted"
    assert len(provider.calls) == 1

    with get_connection() as conn:
        persisted_count = conn.execute(
            "SELECT COUNT(*) FROM memory_updates WHERE user_id = ? AND person_id = ? AND source_candidate_id = ?",
            (person["user_id"], person["id"], update["source_candidate_id"]),
        ).fetchone()[0]
    assert persisted_count == 1

    reanalysis_response = client.get(
        f"/api/v1/conversations/{conversation['id']}/recommendation/context",
        headers=headers,
    )
    assert reanalysis_response.status_code == 200
    reanalysis = reanalysis_response.json()
    assert len(provider.calls) == 2
    assert reanalysis["structured_analysis"]["summary"] == (
        "Fresh re-analysis consumed observed outcome learning"
    )
    assert reanalysis["recommendations"][0]["recommendation"] == (
        "Use the observed outcome for the next low-pressure step"
    )
    assert reanalysis["recommendations"][0]["evidence_source_ids"] == [message["id"]]
    assert reanalysis["recommendations"][0]["provenance"]["source"] == "strategy_candidate"
    assert reanalysis["recommendation_constraints"]["must_not_auto_select"] is True
    assert reanalysis["recommendation_constraints"]["must_not_auto_execute"] is True

    relationship_after = client.get(
        f"/api/v1/persons/{person['id']}/profile",
        headers=headers,
    ).json()["relationships"]
    assert relationship_after == relationship_before
    assert relationship_after[0]["id"] == relationship["id"]


def test_release_acceptance_passes_on_fully_migrated_database_with_verified_backup(client, tmp_path):
    token = _register(client, "test147-release-user")
    assert client.post(
        "/api/v1/persons",
        headers=_auth(token),
        json={"name": "TEST-147 Release Acceptance Person"},
    ).status_code == 201

    database = Path(get_settings().database_path)
    migration_dir = Path(__file__).resolve().parents[1] / "migrations"
    backup_dir = tmp_path / "managed-backups"
    backup_dir.mkdir()
    backup_path, manifest_path = create_managed_backup(
        database,
        backup_dir / "test147-release.sqlite3",
    )
    assert backup_path.exists()
    assert manifest_path.exists()

    settings = Settings(
        _env_file=None,
        app_env="production",
        app_debug=False,
        host="127.0.0.1",
        port=18080,
        database_path=str(database),
        log_level="INFO",
        auth_bootstrap_enabled=False,
        llm_config_encryption_key="test147-release-encryption-key",
    )
    report = check_release_preflight(
        settings,
        database_path=database,
        migration_dir=migration_dir,
        backup_dir=backup_dir,
    )

    assert report.ready is True
    assert report.configuration["ok"] is True
    assert report.launcher["ok"] is True
    assert report.operations["ready"] is True
    assert report.operations["database"]["ok"] is True
    assert report.operations["migrations"]["ok"] is True
    assert report.operations["backup"]["ok"] is True

    runbook = build_release_runbook(settings)
    assert runbook.sequence == [
        "online_backup",
        "release_preflight",
        "stop_current_process",
        "switch_release",
        "start_candidate_process",
        "verify_liveness",
        "verify_readiness",
    ]
    assert runbook.process["start"]["command"] == ["python", "-m", "app.server"]
    assert runbook.process["start"]["required_bind_scope"] == "loopback"
    assert runbook.verification["steps"][0]["command"] == [
        "python",
        "-m",
        "app.probe",
        "live",
        "--json",
    ]
    assert runbook.verification["steps"][1]["command"] == [
        "python",
        "-m",
        "app.probe",
        "ready",
        "--json",
    ]
    assert runbook.rollback["automatic_database_restore"] is False
    assert runbook.rollback["database_restore"]["manual_only"] is True
    assert runbook.rollback["database_restore"]["requires_application_fully_offline"] is True
    assert runbook.rollback["database_restore"]["requires_verified_backup"] is True
