from app.services.action_plan import ActionPlanService


def create_person(client, name="行动计划测试对象"):
    response = client.post("/api/v1/persons", json={"name": name})
    assert response.status_code == 201
    return response.json()


def create_relationship(client, person_id, **overrides):
    payload = {
        "person_id": person_id,
        "status": "active",
        "stage": "dating",
        "long_term_goal": "建立长期关系",
        "current_goal": "增加互动",
        "notes": "action plan test",
    }
    payload.update(overrides)
    response = client.post("/api/v1/relationships", json=payload)
    assert response.status_code == 201
    return response.json()


def get_context(client, person_id):
    return client.get(f"/api/v1/persons/{person_id}/action-plan/context")


def test_action_plan_context_locks_shape_and_requires_confirmation(client):
    person = create_person(client)
    relationship = create_relationship(client, person["id"], stage="exclusive")
    response = get_context(client, person["id"])
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "person", "relationship", "current_state", "evidence", "facts",
        "inferences", "unknowns", "recommendations", "action_plan",
        "action_constraints",
    }
    assert body["person"]["id"] == person["id"]
    assert body["relationship"]["id"] == relationship["id"]
    assert body["action_plan"] == []
    assert body["action_constraints"] == {
        "must_be_evidence_backed": True,
        "must_preserve_unknowns": True,
        "requires_user_confirmation": True,
        "must_not_auto_execute": True,
        "must_not_change_relationship": True,
    }


def test_action_plan_context_preserves_analysis_buckets(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    body = get_context(client, person["id"]).json()
    assert body["facts"] == []
    assert body["inferences"] == []
    assert body["unknowns"] == []
    assert body["recommendations"] == []
    assert body["action_plan"] == []


def test_action_plan_context_isolated_by_user(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    response = client.get(
        f"/api/v1/persons/{person['id']}/action-plan/context",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 404


def test_action_plan_context_does_not_mix_other_person_data(client):
    first = create_person(client, "对象A")
    second = create_person(client, "对象B")
    create_relationship(client, first["id"])
    second_relationship = create_relationship(client, second["id"])
    interaction = client.post("/api/v1/interactions", json={
        "person_id": second["id"], "relationship_id": second_relationship["id"],
        "type": "meeting", "occurred_at": "2026-08-23T12:00:00+00:00", "content": "B",
    })
    assert interaction.status_code == 201
    body = get_context(client, first["id"]).json()
    assert body["evidence"] == []


def test_action_plan_context_is_read_only(client):
    person = create_person(client)
    create_relationship(client, person["id"])
    before = get_context(client, person["id"])
    after = get_context(client, person["id"])
    assert before.status_code == 200
    assert after.status_code == 200
    assert after.json() == before.json()


def test_action_plan_context_missing_person_returns_404(client):
    response = get_context(client, "99999999-9999-9999-9999-999999999999")
    assert response.status_code == 404


def test_action_plan_context_without_relationship_returns_404(client):
    person = create_person(client)
    response = get_context(client, person["id"])
    assert response.status_code == 404


def test_build_action_plan_promotes_only_explicit_evidence_backed_actions():
    evidence = [
        {"source_id": "e1", "source_type": "interaction"},
        {"source_id": "e2", "source_type": "message"},
    ]
    recommendations = [
        {
            "id": "r1",
            "action": "在合适时机发起轻量互动",
            "evidence_source_ids": ["e2"],
            "priority": "medium",
            "time_horizon": "near_term",
        },
        {"id": "r2", "action": "没有证据引用", "evidence_source_ids": []},
        {"id": "r3", "action": "引用不存在证据", "evidence_source_ids": ["missing"]},
        {"id": "r4", "reason": "只有理由，没有明确行动", "evidence_source_ids": ["e1"]},
    ]

    result = ActionPlanService.build_action_plan(recommendations, evidence)

    assert result == [
        {
            "recommendation_id": "r1",
            "action": "在合适时机发起轻量互动",
            "evidence_source_ids": ["e2"],
            "status": "proposed",
            "requires_user_confirmation": True,
            "priority": "medium",
            "time_horizon": "near_term",
        }
    ]


def test_build_action_plan_preserves_recommendation_order_and_does_not_mutate_inputs():
    evidence = [{"source_id": "e1"}, {"source_id": "e2"}]
    recommendations = [
        {"id": "r2", "action": "第二项", "evidence_source_ids": ["e2"]},
        {"id": "r1", "action": "第一项", "evidence_source_ids": ["e1"]},
    ]
    original = [item.copy() for item in recommendations]

    result = ActionPlanService.build_action_plan(recommendations, evidence)

    assert [item["recommendation_id"] for item in result] == ["r2", "r1"]
    assert recommendations == original
    assert result[0]["evidence_source_ids"] is not recommendations[0]["evidence_source_ids"]


def test_build_action_plan_skips_non_dict_and_malformed_recommendations():
    evidence = [{"source_id": "e1"}]
    recommendations = [
        None,
        "not a recommendation",
        {"id": "r1", "action": "   ", "evidence_source_ids": ["e1"]},
        {"id": "r2", "action": "缺少引用"},
        {"id": "r3", "action": "引用类型错误", "evidence_source_ids": "e1"},
    ]

    assert ActionPlanService.build_action_plan(recommendations, evidence) == []


def test_get_context_synthesizes_only_valid_recommendations():
    class FakeStrategicReplyService:
        def get_context(self, conn, user_id, person_id):
            return {
                "person": {"id": person_id},
                "relationship": {"id": "rel-1"},
                "current_state": {},
                "evidence": [{"source_id": "e1"}],
                "facts": [],
                "inferences": [],
                "unknowns": [{"text": "尚不确定"}],
                "recommendations": [
                    {"id": "r1", "action": "提出轻量邀请", "evidence_source_ids": ["e1"]},
                    {"id": "r2", "action": "无证据行动", "evidence_source_ids": ["missing"]},
                ],
            }

    context = ActionPlanService(FakeStrategicReplyService()).get_context(None, "user-1", "person-1")

    assert context["action_plan"] == [
        {
            "recommendation_id": "r1",
            "action": "提出轻量邀请",
            "evidence_source_ids": ["e1"],
            "status": "proposed",
            "requires_user_confirmation": True,
        }
    ]
    assert context["unknowns"] == [{"text": "尚不确定"}]
    assert context["action_constraints"]["must_not_auto_execute"] is True
    assert context["action_constraints"]["requires_user_confirmation"] is True
