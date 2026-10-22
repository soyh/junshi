import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.analysis_strategic_reply import (
    _auto_send_authorized,
    _auto_send_boundary,
    _resolve_profile,
    _resolve_rules,
)
from app.services.user_profile import UserProfileService
from app.schemas.user_profile import UserProfilePayload


def _conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE user_profiles (
            user_id TEXT PRIMARY KEY,
            nickname TEXT NOT NULL DEFAULT '',
            gender TEXT NOT NULL DEFAULT '',
            birth_year TEXT NOT NULL DEFAULT '',
            city TEXT NOT NULL DEFAULT '',
            hometown TEXT NOT NULL DEFAULT '',
            current_location TEXT NOT NULL DEFAULT '',
            work_address TEXT NOT NULL DEFAULT '',
            job TEXT NOT NULL DEFAULT '',
            hobbies TEXT NOT NULL DEFAULT '',
            relationship_status TEXT NOT NULL DEFAULT '',
            about TEXT NOT NULL DEFAULT '',
            reply_rules TEXT NOT NULL DEFAULT '',
            auto_send_authorized INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def test_profile_route_starts_empty():
    with TestClient(app) as client:
        response = client.get("/api/v1/settings/profile")

    assert response.status_code == 200
    body = response.json()
    assert body["nickname"] == ""
    assert body["reply_rules"] == ""


def test_profile_route_round_trips_and_trims():
    payload = {
        "nickname": "  小林 ",
        "gender": "男",
        "birth_year": "1996",
        "city": "杭州",
        "job": "产品经理",
        "hobbies": "跑步、看展",
        "relationship_status": "单身",
        "about": "晚上回消息慢",
        "reply_rules": "  短句、口语，允许倒装。  ",
    }
    with TestClient(app) as client:
        saved = client.put("/api/v1/settings/profile", json=payload)
        reloaded = client.get("/api/v1/settings/profile")

    assert saved.status_code == 200
    body = reloaded.json()
    assert body["nickname"] == "小林"
    assert body["city"] == "杭州"
    assert body["reply_rules"] == "短句、口语，允许倒装。"
    assert body["updated_at"]


def test_profile_route_accepts_the_legacy_relationship_key():
    """Build 244 desktop clients send "relationship" instead of "relationship_status"."""
    with TestClient(app) as client:
        saved = client.put(
            "/api/v1/settings/profile",
            json={"nickname": "小林", "relationship": "暧昧中"},
        )
        reloaded = client.get("/api/v1/settings/profile")

    assert saved.status_code == 200
    assert reloaded.json()["relationship_status"] == "暧昧中"


def test_reply_templates_are_served_to_the_web_page():
    with TestClient(app) as client:
        response = client.get("/api/v1/settings/reply-templates")

    assert response.status_code == 200
    templates = response.json()["templates"]
    assert len(templates) >= 5
    assert templates[0]["name"].startswith("真人感优先")
    assert templates[0]["text"].strip()


def test_draft_context_falls_back_to_the_account_profile():
    conn = _conn()
    conn.execute(
        "INSERT INTO user_profiles (user_id, nickname, city, reply_rules)"
        " VALUES (?, ?, ?, ?)",
        ("user-1", "小林", "杭州", "短句、口语。"),
    )

    profile = _resolve_profile(conn, "user-1", None)
    rules = _resolve_rules(conn, "user-1", "")

    assert profile == {"nickname": "小林", "city": "杭州"}
    assert rules == "短句、口语。"


def test_channel_override_wins_over_the_account_profile():
    conn = _conn()
    conn.execute(
        "INSERT INTO user_profiles (user_id, nickname, city, reply_rules)"
        " VALUES (?, ?, ?, ?)",
        ("user-1", "小林", "杭州", "全局规则"),
    )

    profile = _resolve_profile(conn, "user-1", {"city": "上海"})
    rules = _resolve_rules(conn, "user-1", "本通道规则")

    assert profile == {"city": "上海"}
    assert rules == "本通道规则"


def test_web_and_desktop_reply_templates_do_not_drift():
    """The packaged PC ships its own copy; the web copies must match it."""
    import importlib.util

    repo = Path(__file__).resolve().parents[2]
    source = repo / "desktop" / "reply_rules.py"
    if not source.is_file():
        return
    spec = importlib.util.spec_from_file_location("desktop_reply_rules", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    from app.services.reply_templates import TEMPLATES

    assert [name for name, _note, _text in module.TEMPLATES] == [
        name for name, _note, _text in TEMPLATES
    ]
    assert [text for _name, _note, text in module.TEMPLATES] == [
        text for _name, _note, text in TEMPLATES
    ]


def test_profile_keeps_the_three_place_fields():
    payload = {
        "nickname": "小林",
        "city": "杭州",
        "hometown": "台州",
        "current_location": "杭州市西湖区",
        "work_address": "文三路 100 号",
    }
    with TestClient(app) as client:
        client.put("/api/v1/settings/profile", json=payload)
        body = client.get("/api/v1/settings/profile").json()

    assert body["hometown"] == "台州"
    assert body["current_location"] == "杭州市西湖区"
    assert body["work_address"] == "文三路 100 号"


def test_location_falls_back_to_coordinates_when_geocoding_fails(monkeypatch):
    import app.api.routes.user_profile as route

    def boom(*args, **kwargs):
        raise OSError("no network")

    monkeypatch.setattr(route.urllib.request, "urlopen", boom)
    with TestClient(app) as client:
        body = client.get("/api/v1/settings/location?lat=30.2741&lng=120.1551").json()

    assert body["fallback"] is True
    assert "30.2741" in body["label"] and "120.1551" in body["label"]


def test_location_shortens_the_geocoder_label(monkeypatch):
    import app.api.routes.user_profile as route

    class Fake:
        def read(self, size):
            return ('{"display_name": "文三路, 西湖区, 杭州市, 浙江省, 中国"}').encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(route.urllib.request, "urlopen", lambda *a, **k: Fake())
    with TestClient(app) as client:
        body = client.get("/api/v1/settings/location?lat=30.0&lng=120.0").json()

    assert body["label"] == "文三路西湖区杭州市"
    assert body["fallback"] is False


def test_location_uses_the_keyless_geocoder_first(monkeypatch):
    import app.api.routes.user_profile as route

    class Fake:
        def read(self, size):
            return (
                '{"principalSubdivision": "浙江省", "city": "杭州市", "locality": "拱墅区",'
                ' "countryName": "中华人民共和国"}'
            ).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    calls = []

    def fake_urlopen(request, *a, **k):
        calls.append(str(getattr(request, "full_url", request)))
        return Fake()

    monkeypatch.setattr(route.urllib.request, "urlopen", fake_urlopen)
    with TestClient(app) as client:
        body = client.get("/api/v1/settings/location?lat=30.2741&lng=120.1551").json()

    assert body["label"] == "浙江省杭州市拱墅区"
    assert body["fallback"] is False
    assert len(calls) == 1 and "bigdatacloud" in calls[0]


def test_auto_send_is_off_until_the_user_opts_in():
    conn = _conn()
    service = UserProfileService()
    service.save(conn, "u1", UserProfilePayload(nickname="小林"))

    assert _auto_send_authorized(conn, "u1") is False
    assert _auto_send_boundary(False) == {
        "must_not_auto_send": True,
        "auto_send_authorized": False,
    }

    service.save(
        conn, "u1", UserProfilePayload(nickname="小林", auto_send_authorized=True)
    )

    assert _auto_send_authorized(conn, "u1") is True
    assert _auto_send_boundary(True) == {
        "must_not_auto_send": False,
        "auto_send_authorized": True,
    }


def test_profile_route_round_trips_the_auto_send_flag():
    with TestClient(app) as client:
        saved = client.put(
            "/api/v1/settings/profile",
            json={"nickname": "小林", "auto_send_authorized": True},
        )
        reread = client.get("/api/v1/settings/profile")

    assert saved.status_code == 200
    assert saved.json()["auto_send_authorized"] is True
    assert reread.json()["auto_send_authorized"] is True
