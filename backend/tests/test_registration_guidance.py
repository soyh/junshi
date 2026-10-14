import pytest
from pydantic import ValidationError
from app.schemas.auth_account import AuthRegisterRequest
from app.ui.auth_account import AUTH_ACCOUNT_HTML
from app.ui.product_shell import PRODUCT_SHELL_HTML


@pytest.mark.parametrize('username,password,valid', [
    ('A._', 'a'*12, True), ('a'*64, '密'*256, True),
    ('user-01', '😀'*12, True), ('ab', 'a'*12, False),
    ('a'*65, 'a'*12, False), ('用户名', 'a'*12, False),
    ('abc def', 'a'*12, False), ('abc@def', 'a'*12, False),
    ('abc', '😀'*6, False), ('abc', 'a'*257, False),
])
def test_registration_guidance_matches_server_contract(username, password, valid):
    if valid:
        AuthRegisterRequest(username=username, password=password)
    else:
        with pytest.raises(ValidationError):
            AuthRegisterRequest(username=username, password=password)


@pytest.mark.parametrize('html,prefix', [(AUTH_ACCOUNT_HTML, 'register-'), (PRODUCT_SHELL_HTML, '')])
def test_registration_help_is_persistent_and_accessibly_associated(html, prefix):
    for field in ('username', 'password'):
        assert f'aria-describedby="{prefix}{field}-rules"' in html
        assert f'id="{prefix}{field}-rules" class="registration-rule"' in html
    assert '3–64' in html and '12–256' in html
    assert 'Array.from(password).length' in html
