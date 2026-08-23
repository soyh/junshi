from app.services.text_import_parser import parse_text, validate_candidates


def _text_import_test_helpers(client):
    person_response = client.post(
        "/api/v1/persons",
        json={"name": "Text Import测试对象"},
    )
    assert person_response.status_code == 201
    return person_response.json()["id"]


def test_text_import_creates_conversation_and_messages(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "title": "导入聊天",
            "text": (
                "2026-08-23T10:00:00+00:00 | user | 你好\n"
                "2026-08-23T10:01:00+00:00 | person | 你好呀\n"
                "2026-08-23T10:02:00+00:00 | user | 最近怎么样？"
            ),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["person_id"] == person_id
    assert body["imported_count"] == 3
    assert len(body["message_ids"]) == 3
    assert body["candidates"][1]["sender_type"] == "person"

    conversations = client.get(f"/api/v1/conversations?person_id={person_id}")
    assert conversations.status_code == 200
    assert len(conversations.json()) == 1
    assert conversations.json()[0]["title"] == "导入聊天"

    messages = client.get(
        f"/api/v1/conversations/{body['conversation_id']}/messages"
    )
    assert messages.status_code == 200
    assert [item["content"] for item in messages.json()] == [
        "你好",
        "你好呀",
        "最近怎么样？",
    ]
    assert [item["sent_at"] for item in messages.json()] == [
        "2026-08-23T10:00:00+00:00",
        "2026-08-23T10:01:00+00:00",
        "2026-08-23T10:02:00+00:00",
    ]


def test_text_import_accepts_blank_lines(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": (
                "2026-08-23T10:00:00+00:00 | user | 第一条\n\n"
                "2026-08-23T10:01:00+00:00 | person | 第二条"
            ),
        },
    )

    assert response.status_code == 201
    assert response.json()["imported_count"] == 2
    assert [
        item["line_number"] for item in response.json()["candidates"]
    ] == [1, 3]


def test_text_import_accepts_equal_timestamps(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": (
                "2026-08-23T10:00:00+00:00 | user | 第一条\n"
                "2026-08-23T10:00:00+00:00 | person | 第二条"
            ),
        },
    )

    assert response.status_code == 201
    assert response.json()["imported_count"] == 2


def test_text_import_rejects_invalid_format(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": "这不是支持的聊天格式",
        },
    )

    assert response.status_code == 422


def test_text_import_rejects_invalid_timestamp(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": "not-a-timestamp | user | 你好",
        },
    )

    assert response.status_code == 422
    assert "Invalid timestamp" in response.json()["detail"]


def test_text_import_rejects_invalid_sender_type(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": "2026-08-23T10:00:00+00:00 | stranger | 你好",
        },
    )

    assert response.status_code == 422


def test_text_import_rejects_empty_message_content(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": "2026-08-23T10:00:00+00:00 | user |    ",
        },
    )

    assert response.status_code == 422
    assert "Message content cannot be empty" in response.json()["detail"]


def test_text_import_rejects_out_of_order_messages(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": (
                "2026-08-23T10:01:00+00:00 | user | 第二条\n"
                "2026-08-23T10:00:00+00:00 | person | 第一条"
            ),
        },
    )

    assert response.status_code == 422


def test_text_import_rejects_unknown_person(client):
    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": "00000000-0000-0000-0000-000000000099",
            "text": "2026-08-23T10:00:00+00:00 | user | 你好",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Person not found"}


def test_text_import_isolated_by_user(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        headers={"X-User-ID": "11111111-1111-1111-1111-111111111111"},
        json={
            "person_id": person_id,
            "text": "2026-08-23T10:00:00+00:00 | user | 你好",
        },
    )

    assert response.status_code == 404


def test_text_import_empty_text_does_not_create_conversation(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={"person_id": person_id, "text": "   "},
    )

    assert response.status_code == 422


def test_text_import_parser_preserves_line_numbers():
    candidates = parse_text(
        "2026-08-23T10:00:00+00:00 | user | 第一条\n\n"
        "2026-08-23T10:01:00+00:00 | person | 第二条"
    )

    assert [candidate.line_number for candidate in candidates] == [1, 3]
    assert candidates[0].content == "第一条"
    assert candidates[1].sender_type == "person"


def test_text_import_parser_accepts_zulu_timestamp():
    candidates = parse_text("2026-08-23T10:00:00Z | user | 你好")
    validated = validate_candidates(candidates)

    assert validated[0].sent_at == "2026-08-23T10:00:00Z"


def test_text_import_parser_rejects_empty_input():
    try:
        parse_text("\n\n")
    except ValueError as exc:
        assert str(exc) == "Import text cannot be empty"
    else:
        raise AssertionError("Expected empty import text to be rejected")


def test_text_import_parser_rejects_empty_message_content():
    candidates = parse_text("2026-08-23T10:00:00+00:00 | user |   ")

    try:
        validate_candidates(candidates)
    except ValueError as exc:
        assert str(exc) == "Message content cannot be empty at line 1"
    else:
        raise AssertionError("Expected empty message content to be rejected")


def test_text_import_invalid_format_does_not_create_conversation(client):
    person_id = _text_import_test_helpers(client)

    before = client.get(f"/api/v1/conversations?person_id={person_id}")
    assert before.status_code == 200
    assert before.json() == []

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": "not a valid import line",
        },
    )

    assert response.status_code == 422

    after = client.get(f"/api/v1/conversations?person_id={person_id}")
    assert after.status_code == 200
    assert after.json() == []


def test_text_import_validation_failure_does_not_create_conversation(client):
    person_id = _text_import_test_helpers(client)

    invalid_inputs = [
        "not-a-timestamp | user | 你好",
        "2026-08-23T10:00:00+00:00 | stranger | 你好",
        "2026-08-23T10:00:00+00:00 | user |   ",
        (
            "2026-08-23T10:01:00+00:00 | user | 第二条\n"
            "2026-08-23T10:00:00+00:00 | person | 第一条"
        ),
    ]

    for text in invalid_inputs:
        response = client.post(
            "/api/v1/text-imports",
            json={"person_id": person_id, "text": text},
        )
        assert response.status_code == 422

    conversations = client.get(
        f"/api/v1/conversations?person_id={person_id}"
    )
    assert conversations.status_code == 200
    assert conversations.json() == []


def test_text_import_unknown_person_does_not_create_conversation(client):
    unknown_person_id = "00000000-0000-0000-0000-000000000099"

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": unknown_person_id,
            "text": "2026-08-23T10:00:00+00:00 | user | 你好",
        },
    )

    assert response.status_code == 404

    # The conversations API also rejects an unknown person with 404. The
    # import endpoint has already verified that the person does not exist;
    # the important TEST-009 boundary is that the failed import creates no
    # conversation. Query the database through the existing test connection
    # instead of changing the conversations API contract.
    from app.core.database import get_connection

    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM conversations WHERE person_id = ?",
            (unknown_person_id,),
        ).fetchone()

    assert row["count"] == 0


def test_text_import_accepts_pipe_inside_content(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": "2026-08-23T10:00:00+00:00 | user | A | B | C",
        },
    )

    assert response.status_code == 201
    body = response.json()
    messages = client.get(
        f"/api/v1/conversations/{body['conversation_id']}/messages"
    )
    assert messages.status_code == 200
    assert messages.json()[0]["content"] == "A | B | C"


def test_text_import_accepts_windows_line_endings(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": (
                "2026-08-23T10:00:00+00:00 | user | 第一条\r\n"
                "2026-08-23T10:01:00+00:00 | person | 第二条"
            ),
        },
    )

    assert response.status_code == 201
    assert response.json()["imported_count"] == 2
    assert [
        candidate["line_number"] for candidate in response.json()["candidates"]
    ] == [1, 2]


def test_text_import_normalizes_field_whitespace(client):
    person_id = _text_import_test_helpers(client)

    response = client.post(
        "/api/v1/text-imports",
        json={
            "person_id": person_id,
            "text": (
                "  2026-08-23T10:00:00+00:00  |  user  |  第一条  \n"
                "2026-08-23T10:01:00+00:00 | person | 第二条"
            ),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["candidates"][0] == {
        "line_number": 1,
        "sent_at": "2026-08-23T10:00:00+00:00",
        "sender_type": "user",
        "content": "第一条",
    }
