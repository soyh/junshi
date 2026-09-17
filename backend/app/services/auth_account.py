import base64
import hashlib
import hmac
import os
import sqlite3
import uuid

from app.services.auth_session import AuthSessionService, CreatedAuthSession


SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 32
PASSWORD_SCHEME = "scrypt_v1"


class AuthAccountError(ValueError):
    pass


class AuthAccountConflict(AuthAccountError):
    pass


class AuthAccountInvalidCredentials(AuthAccountError):
    pass


def normalize_username(username: str) -> str:
    return username.strip().lower()


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    password_salt = salt or os.urandom(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=password_salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    return "$".join(
        (
            PASSWORD_SCHEME,
            str(SCRYPT_N),
            str(SCRYPT_R),
            str(SCRYPT_P),
            _b64encode(password_salt),
            _b64encode(derived),
        )
    )


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        scheme, n_raw, r_raw, p_raw, salt_raw, digest_raw = encoded_hash.split("$", 5)
        if scheme != PASSWORD_SCHEME:
            return False
        n = int(n_raw)
        r = int(r_raw)
        p = int(p_raw)
        if (n, r, p) != (SCRYPT_N, SCRYPT_R, SCRYPT_P):
            return False
        salt = _b64decode(salt_raw)
        expected = _b64decode(digest_raw)
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(actual, expected)


_DUMMY_PASSWORD_HASH = hash_password(
    "dummy-password-not-used-for-authentication",
    salt=b"junshi-auth-dummy",
)


class AuthAccountService:
    def __init__(self, *, session_service: AuthSessionService | None = None):
        self.session_service = session_service or AuthSessionService()

    def register(
        self,
        conn: sqlite3.Connection,
        username: str,
        password: str,
    ) -> CreatedAuthSession:
        normalized_username = normalize_username(username)
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)

        try:
            conn.execute(
                "INSERT INTO users (id) VALUES (?)",
                (user_id,),
            )
            conn.execute(
                """
                INSERT INTO user_credentials (
                    user_id,
                    username,
                    password_hash
                )
                VALUES (?, ?, ?)
                """,
                (user_id, normalized_username, password_hash),
            )
        except sqlite3.IntegrityError:
            raise AuthAccountConflict("username unavailable") from None

        return self.session_service.create(conn, user_id)

    def login(
        self,
        conn: sqlite3.Connection,
        username: str,
        password: str,
    ) -> CreatedAuthSession:
        normalized_username = normalize_username(username)
        row = conn.execute(
            """
            SELECT user_id, password_hash
            FROM user_credentials
            WHERE username = ?
            """,
            (normalized_username,),
        ).fetchone()

        if row is None:
            verify_password(password, _DUMMY_PASSWORD_HASH)
            raise AuthAccountInvalidCredentials("invalid credentials")

        if not verify_password(password, str(row["password_hash"])):
            raise AuthAccountInvalidCredentials("invalid credentials")

        return self.session_service.create(conn, str(row["user_id"]))
