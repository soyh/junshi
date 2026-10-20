"""Thin client for the AI Love Strategist HTTP API.

Only stable canonical endpoints are used:
  POST /api/v1/auth/login
  GET  /api/v1/persons
  POST /api/v1/persons
  GET  /api/v1/conversations?person_id=...
  POST /api/v1/conversations
  POST /api/v1/messages
  GET  /api/v1/conversations/{id}/strategic-reply/context
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx


class AppError(RuntimeError):
    def __init__(self, status: int, detail: Any, path: str):
        super().__init__(f"HTTP {status} {path}: {detail}")
        self.status = status
        self.detail = detail
        self.path = path


PLATFORM_LABELS = {
    "wechat": "微信",
    "wx": "微信",
    "xhs": "小红书",
    "tt": "探探",
    "soul": "Soul",
    "qq": "QQ",
}


def contact_marker(contact_id: str) -> str:
    """Stable per-platform identity written into Person.notes."""
    return contact_id if ":" in contact_id else f"wechat:{contact_id}"


def platform_of(contact_id: str) -> str:
    return contact_id.split(":", 1)[0] if ":" in contact_id else "wechat"


def platform_label(contact_id: str) -> str:
    return PLATFORM_LABELS.get(platform_of(contact_id), platform_of(contact_id))


class AppClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_tls: bool = True,
        timeout_seconds: float = 120.0,
    ):
        self._base = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._timeout = timeout_seconds
        self._client = httpx.AsyncClient(
            base_url=self._base,
            verify=verify_tls,
            timeout=httpx.Timeout(timeout_seconds, connect=15.0),
            follow_redirects=False,
        )
        self._token: str | None = None

    async def close(self) -> None:
        await self._client.aclose()

    # -- auth -------------------------------------------------------------
    async def login(self) -> str:
        response = await self._client.post(
            "/api/v1/auth/login",
            json={"username": self._username, "password": self._password},
        )
        if response.status_code != 200:
            raise AppError(response.status_code, _detail(response), "/api/v1/auth/login")
        token = response.json().get("access_token")
        if not token:
            raise AppError(500, "login response has no access_token", "/api/v1/auth/login")
        self._token = str(token)
        return self._token

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        retry_auth: bool = True,
        timeout: float | None = None,
    ) -> Any:
        if self._token is None:
            await self.login()

        response = await self._client.request(
            method,
            path,
            json=json,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=timeout,
        )
        if response.status_code == 401 and retry_auth:
            await self.login()
            return await self._request(
                method, path, json=json, retry_auth=False, timeout=timeout
            )
        if response.status_code == 204:
            return None
        if response.status_code >= 400:
            raise AppError(response.status_code, _detail(response), path)
        return response.json()

    # -- canonical resources ---------------------------------------------
    async def list_persons(self) -> list[dict]:
        return await self._request("GET", "/api/v1/persons")

    async def create_person(self, name: str, nickname: str | None = None, notes: str | None = None) -> dict:
        return await self._request(
            "POST", "/api/v1/persons", json={"name": name, "nickname": nickname, "notes": notes}
        )

    async def list_conversations(self, person_id: str) -> list[dict]:
        return await self._request("GET", f"/api/v1/conversations?person_id={person_id}")

    async def create_conversation(
        self, person_id: str, title: str | None = None, status: str = "active"
    ) -> dict:
        return await self._request(
            "POST",
            "/api/v1/conversations",
            json={"person_id": person_id, "title": title, "status": status},
        )

    async def add_message(
        self,
        conversation_id: str,
        sender_type: str,
        content: str,
        sent_at: str | None = None,
    ) -> dict:
        return await self._request(
            "POST",
            "/api/v1/messages",
            json={
                "conversation_id": conversation_id,
                "sender_type": sender_type,
                "content": content,
                "sent_at": sent_at or datetime.now().astimezone().isoformat(timespec="seconds"),
            },
        )

    async def add_message_once(
        self,
        conversation_id: str,
        sender_type: str,
        content: str,
        operation_id: str,
        sent_at: str | None = None,
        platform: str | None = None,
        platform_account_id: str | None = None,
    ) -> dict:
        """Idempotent ingest via /pc/messages (safe to retry after a crash)."""
        payload = {
            "conversation_id": conversation_id,
            "sender_type": sender_type,
            "content": content,
            "sent_at": sent_at or datetime.now().astimezone().isoformat(timespec="seconds"),
            "operation_id": operation_id,
        }
        if platform:
            payload["platform"] = platform
        if platform_account_id:
            payload["platform_account_id"] = platform_account_id
        return await self._request("POST", "/api/v1/pc/messages", json=payload)

    async def ensure_primary_conversation(self, person_id: str) -> dict:
        """One conversation per person; the server creates or promotes it."""
        return await self._request(
            "GET", f"/api/v1/persons/{person_id}/primary-conversation"
        )

    async def consolidate_person_conversations(self, person_id: str) -> dict:
        return await self._request(
            "POST", f"/api/v1/persons/{person_id}/consolidate", json={}
        )

    async def ensure_platform_source(
        self,
        person_id: str,
        conversation_id: str,
        platform: str,
        account_handle: str,
        display_name: str = "",
    ) -> str | None:
        """Register the platform identity on the person and return its id.

        With one conversation per person, conversations are no longer bound to a
        single platform source; the person-level account is the source of truth.
        """
        try:
            accounts = await self._request(
                "GET", f"/api/v1/persons/{person_id}/platform-accounts"
            )
        except AppError:
            return None
        account = next(
            (a for a in accounts if a.get("platform") == platform and a.get("account_handle") == account_handle),
            None,
        )
        if account is None:
            try:
                account = await self._request(
                    "POST",
                    f"/api/v1/persons/{person_id}/platform-accounts",
                    json={
                        "platform": platform,
                        "account_handle": account_handle,
                        "display_name": display_name or account_handle,
                    },
                )
            except AppError:
                return None
        return account.get("id")

    async def heartbeat(
        self,
        channel: str,
        status: str = "online",
        replies_today: int = 0,
        detail: str = "",
    ) -> None:
        await self._request(
            "POST",
            "/api/v1/bridge/heartbeat",
            json={
                "channel": channel,
                "status": status,
                "replies_today": replies_today,
                "detail": detail[:500],
            },
            timeout=15.0,
        )

    async def get_reply_context(self, conversation_id: str, rules: str = "") -> dict:
        """Calls the LLM chain; may take tens of seconds.

        Extra per-channel rules travel in a POST body because they can be long;
        without rules the plain GET keeps the previous behaviour.
        """
        path = f"/api/v1/conversations/{conversation_id}/strategic-reply/context"
        timeout = max(self._timeout, 180.0)
        if rules.strip():
            return await self._request("POST", path, json={"rules": rules}, timeout=timeout)
        return await self._request("GET", path, timeout=timeout)

    # -- relationship scoping ---------------------------------------------
    async def list_relationships(self) -> list[dict]:
        return await self._request("GET", "/api/v1/relationships")

    async def ensure_relationship(self, person_id: str) -> dict:
        """Analysis requires a Relationship; a person has at most one."""
        for relationship in await self.list_relationships():
            if relationship.get("person_id") == person_id:
                return relationship
        return await self._request(
            "POST",
            "/api/v1/relationships",
            json={"person_id": person_id, "status": "unknown", "stage": "unknown"},
        )

    async def ensure_scoped(self, conversation_id: str, person_id: str) -> dict:
        """Make sure the conversation carries a relationship_id."""
        conversation = await self._request("GET", f"/api/v1/conversations/{conversation_id}")
        if conversation.get("relationship_id"):
            return conversation
        relationship = await self.ensure_relationship(person_id)
        return await self._request(
            "PATCH",
            f"/api/v1/conversations/{conversation_id}",
            json={"relationship_id": relationship["id"]},
        )

    # -- mapping helpers --------------------------------------------------
    async def find_or_create_person(
        self, contact_name: str, contact_id: str, auto_merge_same_name: bool = False
    ) -> dict:
        marker = contact_marker(contact_id)
        persons = await self.list_persons()
        for person in persons:
            if marker in (person.get("notes") or ""):
                return person
        if auto_merge_same_name:
            for person in persons:
                if person.get("name") == contact_name or person.get("nickname") == contact_name:
                    return person
        return await self.create_person(contact_name, notes=f"{marker} 自动创建")

    async def find_or_create_conversation(
        self, person_id: str, contact_name: str, contact_id: str
    ) -> dict:
        conversations = await self.list_conversations(person_id)
        active = [c for c in conversations if c.get("status") == "active"]
        if active:
            return active[0]
        return await self.create_conversation(
            person_id, title=f"{platform_label(contact_id)} · {contact_name}"
        )


def _detail(response: httpx.Response) -> Any:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:300]
    if isinstance(payload, dict) and "detail" in payload:
        return payload["detail"]
    return payload
