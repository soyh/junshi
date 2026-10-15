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
    for kind in ('persons','conversations','relationships','person_memories','person_update_events','model_references','person_platform_accounts','media_attachments'):
        result=client.get(f'/api/v1/admin/accounts/{target}/data/{kind}',params={'reason':'数据核对'},headers=headers)
        assert result.status_code==200,(kind,result.text)
        assert result.headers['cache-control']=='no-store'
    with get_connection() as c:
        row=c.execute("SELECT target_id,reason FROM account_management_audit WHERE action='view:messages'").fetchone()
        assert row['target_id']==target and row['reason']=='用户请求排查'
    assert client.patch(f'/api/v1/admin/accounts/{target}/state',json={'disabled':True,'reason':'违规'},headers=headers).status_code==200
    assert client.get('/api/v1/persons',headers={'Authorization':'Bearer '+other}).status_code==401

def test_user_directory_search_and_complete_pagination(client):
    import uuid
    token=client.post('/api/v1/auth/register',json={'username':'directory_admin','password':'password-12345'}).json()['access_token']
    headers={'Authorization':'Bearer '+token}
    assert client.get('/api/v1/admin/accounts/directory',headers=headers).status_code==403
    with get_connection() as c:
        admin=c.execute("SELECT user_id FROM user_credentials WHERE username='directory_admin'").fetchone()[0]
        c.execute('INSERT INTO account_identities(user_id,administrator) VALUES(?,1)',(admin,))
        expected=set()
        for n in range(55):
            user=str(uuid.uuid4());expected.add(user)
            c.execute('INSERT INTO users(id) VALUES(?)',(user,))
            c.execute('INSERT INTO account_identities(user_id,email) VALUES(?,?)',(user,f'pick_{n}@example.com'))
    seen=set()
    for offset in (0,20,40):
        result=client.get('/api/v1/admin/accounts/directory',params={'q':'pick_','offset':offset},headers=headers)
        assert result.status_code==200 and result.headers['cache-control']=='no-store'
        payload=result.json();assert payload['total']==55
        seen.update(item['id'] for item in payload['items'])
        assert 'password_hash' not in result.text
    assert seen==expected
    assert client.get('/api/v1/admin/accounts/directory',params={'q':'%_not_a_wildcard'},headers=headers).json()['total']==0
    assert client.get('/api/v1/admin/accounts/directory',params={'limit':1000},headers=headers).status_code==422


def test_admin_message_pages_are_chronological_complete_and_audited(client):
    import uuid
    def login(name):
        token=client.post('/api/v1/auth/register',json={'username':name,'password':'password-12345'}).json()['access_token']
        return {'Authorization':'Bearer '+token}
    admin_headers=login('pages_admin');owner_headers=login('pages_owner')
    person=client.post('/api/v1/persons',json={'name':'测试'},headers=owner_headers).json()
    conversation=client.post('/api/v1/conversations',json={'person_id':person['id'],'title':'分页'},headers=owner_headers).json()
    with get_connection() as c:
        admin=c.execute("SELECT user_id FROM user_credentials WHERE username='pages_admin'").fetchone()[0]
        owner=c.execute("SELECT user_id FROM user_credentials WHERE username='pages_owner'").fetchone()[0]
        c.execute('INSERT INTO account_identities(user_id,administrator) VALUES(?,1)',(admin,))
        for i in range(55):
            c.execute('INSERT INTO messages(id,user_id,conversation_id,sender_type,content,sent_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',
                      (str(uuid.uuid4()),owner,conversation['id'],'person',str(i),f'2026-09-20T17:{i:02d}:00','2026-09-21T00:00:00','2026-09-21T00:00:00'))
    url=f'/api/v1/admin/accounts/{owner}/data/messages'
    assert client.get(url,params={'reason':'分页核对','paginated':True},headers=owner_headers).status_code==403
    seen=[]
    for offset in (0,50):
        response=client.get(url,params={'reason':'分页核对','paginated':True,'offset':offset},headers=admin_headers)
        assert response.status_code==200
        data=response.json();assert data['total']==55 and data['offset']==offset and data['limit']==50
        seen.extend(row['content'] for row in data['items'])
    assert seen==list(map(str,range(55)))
    assert isinstance(client.get(url,params={'reason':'旧接口兼容'},headers=admin_headers).json(),list)
    with get_connection() as c:
        assert c.execute("SELECT COUNT(*) FROM account_management_audit WHERE actor_id=? AND target_id=? AND action='view:messages'",(admin,owner)).fetchone()[0]==3
