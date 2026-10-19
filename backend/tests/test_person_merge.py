def _person(client, name):
    response = client.post("/api/v1/persons", json={"name": name, "notes": "merge test"})
    assert response.status_code == 201, response.text
    return response.json()


def _relationship(client, person_id):
    response = client.post(
        "/api/v1/relationships",
        json={"person_id": person_id, "status": "unknown", "stage": "unknown"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _conversation(client, person_id, title):
    response = client.post(
        "/api/v1/conversations",
        json={"person_id": person_id, "title": title},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_merge_moves_conversations_accounts_and_history(client):
    target = _person(client, "合并目标")
    source = _person(client, "合并来源")
    _relationship(client, target["id"])
    _relationship(client, source["id"])

    _conversation(client, target["id"], "微信")
    _conversation(client, source["id"], "小红书")

    interaction = client.post(
        "/api/v1/interactions",
        json={
            "person_id": source["id"],
            "type": "message",
            "occurred_at": "2026-10-19T10:00:00+08:00",
            "content": "hi",
        },
    )
    assert interaction.status_code == 201, interaction.text

    account = client.post(
        f"/api/v1/persons/{source['id']}/platform-accounts",
        json={"platform": "xhs", "account_handle": "xhs-123", "display_name": "小号"},
    )
    assert account.status_code == 201, account.text

    response = client.post(
        f"/api/v1/persons/{target['id']}/merge",
        json={"source_person_id": source["id"]},
    )
    assert response.status_code == 200, response.text
    moved = response.json()["moved"]
    assert moved["conversations"] == 1
    assert moved["interactions"] == 1
    assert moved["platform_accounts"] == 1

    assert client.get(f"/api/v1/persons/{source['id']}").status_code == 404

    conversations = client.get(f"/api/v1/conversations?person_id={target['id']}").json()
    assert sorted(c["title"] for c in conversations) == ["小红书", "微信"]

    accounts = client.get(f"/api/v1/persons/{target['id']}/platform-accounts").json()
    assert [a["account_handle"] for a in accounts] == ["xhs-123"]

    relationships = client.get("/api/v1/relationships").json()
    assert [r["person_id"] for r in relationships] == [target["id"]]


def test_merge_rejects_same_or_missing_person(client):
    person = _person(client, "同人")

    same = client.post(
        f"/api/v1/persons/{person['id']}/merge",
        json={"source_person_id": person["id"]},
    )
    assert same.status_code == 409

    missing = client.post(
        f"/api/v1/persons/{person['id']}/merge",
        json={"source_person_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert missing.status_code == 404
