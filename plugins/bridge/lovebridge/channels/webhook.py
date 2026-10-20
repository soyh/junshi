"""Generic HTTP webhook channel.

Works with any WeChat bridge that can POST inbound messages and accept an
outbound POST. This is the recommended shape for personal WeChat: run the
bridge (e.g. a wcferry/Wechaty sidecar on Windows) on the machine that has
WeChat, and point it at this service.

Inbound  POST {path}          {"contact_id","contact_name","text","message_id","is_group"}
Outbound POST {send_url}      {"contact_id","text","is_group"}

Both directions carry the shared secret in X-Bridge-Secret.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

from .base import Handler, InboundEvent


class WebhookChannel:
    def __init__(
        self,
        listen_host: str = "127.0.0.1",
        listen_port: int = 18200,
        path: str = "/inbound",
        secret: str | None = None,
        send_url: str | None = None,
        send_timeout: float = 30.0,
        verify_tls: bool = True,
    ) -> None:
        self._host = listen_host
        self._port = int(listen_port)
        self._path = path
        self._secret = secret
        self._send_url = send_url
        self._send_timeout = float(send_timeout)
        self._client = httpx.AsyncClient(timeout=send_timeout, verify=verify_tls)
        self._handler: Handler | None = None
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def set_handler(self, handler: Handler) -> None:
        self._handler = handler

    async def start(self) -> None:
        channel = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, fmt: str, *args) -> None:  # keep console clean
                return

            def do_POST(self) -> None:  # noqa: N802
                if self.path != channel._path:
                    self._reply(404, {"detail": "not found"})
                    return
                if channel._secret and self.headers.get("X-Bridge-Secret") != channel._secret:
                    self._reply(401, {"detail": "bad secret"})
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    payload = json.loads(self.rfile.read(length) or b"{}")
                except (ValueError, TypeError):
                    self._reply(400, {"detail": "invalid json"})
                    return

                text = str(payload.get("text") or "")
                contact_id = str(payload.get("contact_id") or payload.get("contact_name") or "")
                if not contact_id or not text.strip():
                    self._reply(400, {"detail": "contact_id and text are required"})
                    return

                platform = str(payload.get("platform") or "").strip().lower()
                if platform and ":" not in contact_id:
                    contact_id = f"{platform}:{contact_id}"

                event = InboundEvent(
                    contact_id=contact_id,
                    contact_name=str(payload.get("contact_name") or contact_id),
                    text=text,
                    message_id=str(payload.get("message_id") or f"wh-{uuid.uuid4().hex}"),
                    is_group=bool(payload.get("is_group", False)),
                    timestamp=time.time(),
                    raw=payload,
                )
                if channel._handler:
                    channel._handler(event)
                self._reply(202, {"status": "accepted"})

            def _reply(self, status: int, body: dict) -> None:
                data = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self._server = ThreadingHTTPServer((self._host, self._port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    async def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        await self._client.aclose()

    async def send(self, contact_id: str, text: str, is_group: bool = False) -> None:
        if not self._send_url:
            raise RuntimeError("webhook channel has no send_url configured")
        headers = {"X-Bridge-Secret": self._secret} if self._secret else {}
        response = await self._client.post(
            self._send_url,
            json={"contact_id": contact_id, "text": text, "is_group": is_group},
            headers=headers,
        )
        if response.status_code >= 400:
            raise RuntimeError(
                f"bridge send failed: HTTP {response.status_code} {response.text[:200]}"
            )
