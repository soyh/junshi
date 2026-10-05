import hashlib

from app.core.database import get_connection
from tests.test_197_reference_skills_context import _conversation, _upload, OTHER_USER_ID


def revision(content):
    return hashlib.sha256(content.encode()).hexdigest()


def test_edit_directory_preserves_identity_settings_and_refreshes_retrieval(client):
    convo = _conversation(client)
    directory = _upload(client, "目录.md", "# 主题指南".encode(), priority=7)
    target = _upload(client, "冲突.md", "冲突修复与道歉".encode())
    client.put(f"/api/v1/conversations/{convo['id']}/references/{directory['id']}",
               json={"enabled": True, "priority": 3})
    editor = client.get(f"/api/v1/references/{directory['id']}/editor")
    assert editor.status_code == 200
    assert editor.headers["cache-control"] == "no-store"
    assert editor.json()["revision"] == revision("# 主题指南")
    content = "# 主题指南\n\n- 冲突与修复：`冲突.md`\n"
    saved = client.put(f"/api/v1/references/{directory['id']}/content",
                       json={"content": content, "expected_revision": editor.json()["revision"]})
    assert saved.status_code == 200
    assert saved.headers["cache-control"] == "no-store"
    assert saved.json() == {"id": directory["id"], "content": content, "revision": revision(content)}
    assert client.get(f"/api/v1/references/{directory['id']}/content").json()["content"] == content
    listed = client.get(f"/api/v1/references?conversation_id={convo['id']}").json()
    updated = next(x for x in listed if x["id"] == directory["id"])
    assert updated["priority"] == 7 and updated["effective_priority"] == 3
    assert updated["reference_type"] == "document"
    assert updated["original_filename"] == "目录.md"
    assert updated["content_chars"] == len(content)
    preview = client.get(f"/api/v1/conversations/{convo['id']}/references/context").json()
    assert preview["retrieval"]["guide_count"] == 1
    assert "冲突与修复" in next(x for x in preview["catalog"] if x["reference_id"] == target["id"])["topics"]


def test_stale_editor_is_409_and_cannot_overwrite_new_content(client):
    doc = _upload(client, "guide.md", b"original")
    url = f"/api/v1/references/{doc['id']}/content"
    assert client.put(url, json={"content": "new version", "expected_revision": revision("original")}).status_code == 200
    response = client.put(url, json={"content": "stale overwrite", "expected_revision": revision("original")})
    assert response.status_code == 409
    assert client.get(url).json()["content"] == "new version"


def test_editor_is_user_scoped_and_rejects_missing_or_deleted_files(client):
    doc = _upload(client, "private.md", b"PRIVATE CONTENT")
    prefix = f"/api/v1/references/{doc['id']}"
    headers = {"X-User-ID": OTHER_USER_ID}
    assert client.get(prefix + "/editor", headers=headers).status_code == 404
    response = client.put(prefix + "/content", headers=headers,
                          json={"content": "overwrite", "expected_revision": revision("PRIVATE CONTENT")})
    assert response.status_code == 404 and "PRIVATE CONTENT" not in response.text
    assert client.delete(prefix).status_code == 204
    assert client.put(prefix + "/content", json={"content": "new", "expected_revision": revision("PRIVATE CONTENT")}).status_code == 404


def test_editor_rejects_blank_oversized_and_missing_revision_without_mutation(client):
    doc = _upload(client, "guide.md", b"original")
    url = f"/api/v1/references/{doc['id']}/content"
    for payload in (
        {"content": "new"},
        {"content": "   \n", "expected_revision": revision("original")},
        {"content": "中" * 180000, "expected_revision": revision("original")},
        {"content": "new", "expected_revision": "invalid"},
    ):
        assert client.put(url, json=payload).status_code == 422
    assert client.get(url).json()["content"] == "original"


def test_text_skill_edits_keep_skill_type(client):
    doc = _upload(client, "SKILL.md", b"method")
    url = f"/api/v1/references/{doc['id']}/content"
    assert client.put(url, json={"content": "updated method", "expected_revision": revision("method")}).status_code == 200
    assert client.get("/api/v1/references").json()[0]["reference_type"] == "skill"


def test_binary_source_cannot_be_rewritten_as_text_by_editor(client):
    doc = _upload(client, "guide.md", b"original")
    with get_connection() as conn:
        conn.execute("UPDATE model_references SET original_filename = ? WHERE id = ?", ("guide.docx", doc["id"]))
    assert client.get(f"/api/v1/references/{doc['id']}/editor").status_code == 422
    response = client.put(f"/api/v1/references/{doc['id']}/content",
                          json={"content": "new", "expected_revision": revision("original")})
    assert response.status_code == 422
    assert client.get(f"/api/v1/references/{doc['id']}/content").json()["content"] == "original"
