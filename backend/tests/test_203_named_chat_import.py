import pytest

from app.services.named_chat_parser import parse_named_chat, named_candidates
from app.services.text_import_parser import validate_candidates

SAMPLE = "ID1\n2026年09月26日 10:40\n早早早\n\nID2\n2026年09月26日 10:40\n早呀\n"
AUTH = {"X-User-ID": "named-import-user"}


def test_sample_preserves_names_minute_precision_and_order():
    result = parse_named_chat(SAMPLE)
    assert result["senders"] == ["ID1", "ID2"]
    assert [m["content"] for m in result["messages"]] == ["早早早", "早呀"]
    assert [m["line_number"] for m in result["messages"]] == [1, 5]
    assert all(m["time_precision"] == "minute" for m in result["messages"])
    assert result["messages"][0]["sent_at"] == "2026-09-26T10:40:00+08:00"
    assert [m.sender_type for m in named_candidates(SAMPLE, "ID2", "ID1", "+08:00")] == ["person", "user"]


def test_multiline_bom_crlf_seconds_and_cross_day_sort():
    text = "\ufeffID2\r\n2026年09月27日 00:01:09\r\n第一行 | 正文\r\n\r\n第二行\r\n\r\nID1\r\n2026年09月26日 23:59\r\n昨天"
    result = parse_named_chat(text, "-04:00")
    assert result["messages"][0]["content"] == "第一行 | 正文\n\n第二行"
    assert result["messages"][0]["time_precision"] == "second"
    assert result["messages"][0]["sent_at"].endswith("-04:00")
    ordered = validate_candidates(named_candidates(text, "ID1", "ID2", "-04:00"), auto_sort_by_sent_at=True)
    assert [m.content for m in ordered] == ["昨天", "第一行 | 正文\n\n第二行"]


@pytest.mark.parametrize("text", ["", "普通消息", "前缀\n" + SAMPLE,
    SAMPLE.replace("09月26日", "02月30日"), SAMPLE.replace("10:40", "25:40"),
    SAMPLE.replace("10:40", "xx:40"), "ID1\n2026年09月26日 10:40\n\nID2\n2026年09月26日 10:41\nhello"])
def test_invalid_or_empty_records_are_not_silently_discarded(text):
    with pytest.raises(ValueError):
        parse_named_chat(text)


@pytest.mark.parametrize("offset", ["UTC", "+14:01", "+25:00", "+08:60"])
def test_invalid_timezone_rejected(offset):
    with pytest.raises(ValueError):
        parse_named_chat(SAMPLE, offset)


@pytest.mark.parametrize("me,other", [(None, None), ("ID1", "ID1"), ("ID1", "missing")])
def test_mapping_must_explicitly_cover_both_names(me, other):
    with pytest.raises(ValueError):
        named_candidates(SAMPLE, me, other, "+08:00")


def test_third_sender_previewed_but_import_blocked():
    text = SAMPLE + "\n第三人\n2026年09月26日 10:42\n系统通知或第三人"
    assert parse_named_chat(text)["senders"] == ["ID1", "ID2", "第三人"]
    with pytest.raises(ValueError):
        named_candidates(text, "ID1", "ID2", "+08:00")


def test_preview_requires_login_and_writes_nothing(client, monkeypatch):
    from app.config.settings import get_settings
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_BOOTSTRAP_ENABLED", "false")
    get_settings.cache_clear()
    assert client.post("/api/v1/text-imports/preview", json={"text": SAMPLE}).status_code == 401
    person = client.post("/api/v1/persons", headers=AUTH, json={"name": "对方"}).json()["id"]
    response = client.post("/api/v1/text-imports/preview", headers=AUTH, json={"text": SAMPLE})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json()["senders"] == ["ID1", "ID2"]
    assert client.get(f"/api/v1/conversations?person_id={person}", headers=AUTH).json() == []


def test_import_mapping_append_validation_and_owner_boundary(client):
    person = client.post("/api/v1/persons", headers=AUTH, json={"name": "对方"}).json()["id"]
    payload = dict(person_id=person, text=SAMPLE, source_format="named_chat",
                   self_name="ID2", other_name="ID1", utc_offset="+08:00", auto_sort_by_sent_at=True)
    denied = client.post("/api/v1/text-imports", headers={"X-User-ID": "stranger"}, json=payload)
    assert denied.status_code == 404
    bad = client.post("/api/v1/text-imports", headers=AUTH, json={**payload, "other_name": "ID2"})
    assert bad.status_code == 422
    assert client.get(f"/api/v1/conversations?person_id={person}", headers=AUTH).json() == []
    response = client.post("/api/v1/text-imports", headers=AUTH, json=payload)
    assert response.status_code == 201
    result = response.json()
    assert result["imported_count"] == 2
    assert [m["sender_type"] for m in result["candidates"]] == ["person", "user"]
    conversation = result["conversation_id"]
    appended = client.post("/api/v1/text-imports", headers=AUTH, json={**payload, "conversation_id": conversation})
    assert appended.status_code == 201
    assert appended.json()["conversation_id"] == conversation
    assert len(client.get(f"/api/v1/conversations?person_id={person}", headers=AUTH).json()) == 1
    messages = client.get(f"/api/v1/conversations/{conversation}/messages", headers=AUTH).json()
    assert len(messages) == 4
    assert {m["sent_at"] for m in messages} == {"2026-09-26T10:40:00+08:00"}


def test_preview_rejects_bad_date_with_source_line(client):
    r = client.post("/api/v1/text-imports/preview", headers=AUTH,
                    json={"text": SAMPLE.replace("09月26日", "02月30日")})
    assert r.status_code == 422
    assert "第 2 行" in r.json()["detail"]
