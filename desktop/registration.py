"""Registration contract shared with the server's existing account rules."""
import re

ACCOUNT_HINT = '账号 3–64 位：英文字母、数字、. _ -；不区分大小写。'
PASSWORD_HINT = '注册密码 12–256 个字符；区分大小写，无强制特殊符号要求。'

def validate(username, password):
    if not re.fullmatch(r'[A-Za-z0-9._-]{3,64}', username):
        raise ValueError(ACCOUNT_HINT)
    if not 12 <= len(password) <= 256:
        raise ValueError(PASSWORD_HINT)
