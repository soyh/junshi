from unittest.mock import Mock
import pytest
from app.api.routes import account_identity as routes
from app.services.email_challenge import EmailChallengeService
from app.core.database import get_connection

@pytest.fixture
def mail(monkeypatch):
    mail=Mock()
    service=EmailChallengeService('s'*32,mail)
    monkeypatch.setattr(routes,'challenge_service',lambda:service)
    return mail

def test_email_registration_and_failed_attempts_persist(client,mail):
    response=client.post('/api/v1/auth/email/code',json={'email':'a@example.com','purpose':'register'})
    assert response.status_code==200
    identifier=response.json()['challenge_id'];code=mail.send.call_args.args[1]
    payload={'username':'email_api','password':'password-12345','email':'a@example.com','challenge_id':identifier,'code':'000000' if code!='000000' else '000001'}
    assert client.post('/api/v1/auth/email/register',json=payload).status_code==400
    with get_connection() as conn:
        assert conn.execute('SELECT attempts FROM email_challenges WHERE id=?',(identifier,)).fetchone()[0]==1
    payload['code']=code
    registered=client.post('/api/v1/auth/email/register',json=payload)
    assert registered.status_code==201
    assert 'access_token' in registered.json()
    assert client.post('/api/v1/auth/email/register',json=payload).status_code==400

def test_disabled_account_blocks_new_and_existing_login(client):
    result=client.post('/api/v1/auth/register',json={'username':'disabled_user','password':'password-12345'})
    token=result.json()['access_token']
    with get_connection() as conn:
        user=conn.execute('SELECT user_id FROM user_credentials WHERE username=?',('disabled_user',)).fetchone()[0]
        conn.execute('INSERT INTO account_identities(user_id,disabled) VALUES(?,1)',(user,))
    assert client.post('/api/v1/auth/login',json={'username':'disabled_user','password':'password-12345'}).status_code==401
    assert client.get('/api/v1/persons',headers={'Authorization':'Bearer '+token}).status_code==401

def test_binding_cannot_issue_without_password(client,mail):
    assert client.post('/api/v1/auth/email/code',json={'email':'a@example.com','purpose':'bind'}).status_code in (401,403)
    mail.send.assert_not_called()
