from app.core.database import get_connection

def test_normal_user_cannot_list_and_admin_views_are_audited(client):
    def register(name):
        return client.post('/api/v1/auth/register',json={'username':name,'password':'password-12345'}).json()['access_token']
    token=register('admin_api');other=register('other_api')
    headers={'Authorization':'Bearer '+token}
    assert client.get('/api/v1/admin/accounts',headers=headers).status_code==403
    with get_connection() as c:
        admin=c.execute('SELECT user_id FROM user_credentials WHERE username=?',('admin_api',)).fetchone()[0]
        target=c.execute('SELECT user_id FROM user_credentials WHERE username=?',('other_api',)).fetchone()[0]
        c.execute('INSERT INTO account_identities(user_id,administrator) VALUES(?,1)',(admin,))
    response=client.get('/api/v1/admin/accounts',headers=headers)
    assert response.status_code==200
    assert 'password_hash' not in response.text and 'access_token' not in response.text
    assert client.get(f'/api/v1/admin/accounts/{target}/data/messages',params={'reason':'用户请求排查'},headers=headers).status_code==200
    with get_connection() as c:
        row=c.execute("SELECT target_id,reason FROM account_management_audit WHERE action='view:messages'").fetchone()
        assert row['target_id']==target and row['reason']=='用户请求排查'
    assert client.patch(f'/api/v1/admin/accounts/{target}/state',json={'disabled':True,'reason':'违规'},headers=headers).status_code==200
    assert client.get('/api/v1/persons',headers={'Authorization':'Bearer '+other}).status_code==401
