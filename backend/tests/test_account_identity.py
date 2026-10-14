import pytest
from app.core.database import get_connection
from app.services.account_identity import AccountIdentityService, AccountIdentityError
from app.services.auth_account import AuthAccountService
from app.services.auth_session import AuthSessionService


def test_verified_registration_and_reset_revoke_old_session(client):
    identity=AccountIdentityService()
    with get_connection() as conn:
        session=identity.register_verified(conn,'email_user','old-password-123','a@example.com')
        identity.reset_verified(conn,'a@example.com','new-password-123')
        assert AuthSessionService().resolve(conn,session.access_token) is None
        assert AuthAccountService().login(conn,'email_user','new-password-123').access_token


def test_admin_boundary_disable_and_audit(client):
    identity=AccountIdentityService()
    with get_connection() as conn:
        a=AuthAccountService().register(conn,'admin_user','password-12345')
        b=AuthAccountService().register(conn,'normal_user','password-12345')
        admin=AuthSessionService().resolve(conn,a.access_token)
        normal=AuthSessionService().resolve(conn,b.access_token)
        with pytest.raises(AccountIdentityError): identity.require_admin(conn,normal)
        conn.execute('INSERT INTO account_identities(user_id,administrator) VALUES(?,1)',(admin,))
        identity.disable(conn,admin,normal,True,'违规处理')
        assert AuthSessionService().resolve(conn,b.access_token) is None
        assert conn.execute('SELECT reason FROM account_management_audit').fetchone()[0]=='违规处理'
        with pytest.raises(AccountIdentityError): identity.disable(conn,admin,admin,True,'自禁用')
