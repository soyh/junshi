from app.core.database import get_connection
from app.services.reference_context import ReferenceContextService


def test_full_content_is_not_truncated_or_added_to_listing(client):
    content = "# Reference\n" + "长文内容\n" * 1000 + "<script>alert(1)</script>"
    response = client.post('/api/v1/references',
        files={'file': ('long.md', content.encode(), 'text/markdown')},
        data={'enabled_by_default': 'false'})
    assert response.status_code == 201
    item = response.json()
    full = client.get(f"/api/v1/references/{item['id']}/content")
    assert full.status_code == 200
    assert full.json() == {'id': item['id'], 'content': content}
    assert full.headers['cache-control'] == 'no-store'
    listed = client.get('/api/v1/references').json()[0]
    assert 'content' not in listed
    assert len(listed['content_preview']) < len(content)
    assert listed['enabled_by_default'] is False


def test_full_content_is_user_scoped_and_missing_is_404(client):
    item = client.post('/api/v1/references',
        files={'file': ('private.md', b'private text', 'text/markdown')}).json()
    foreign = client.get(f"/api/v1/references/{item['id']}/content",
        headers={'X-User-ID': '11111111-1111-1111-1111-111111111111'})
    assert foreign.status_code == 404
    assert 'private text' not in foreign.text
    assert client.get('/api/v1/references/missing/content').status_code == 404
    assert client.delete(f"/api/v1/references/{item['id']}").status_code == 204
    assert client.get(f"/api/v1/references/{item['id']}/content").status_code == 404
