"""Command line entry point: run / doctor / contacts / map / link / window."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import threading
from datetime import datetime
from pathlib import Path

from .app_client import AppClient, AppError, platform_label
from .channels.mock import MockChannel
from .channels.wcferry import WcferryChannel
from .channels.soul import SoulChannel
from .channels.wechatauto import WechatautoChannel
from .channels.webhook import WebhookChannel
from .channels.wxhook import WxhookChannel
from .channels.xhs import XhsChannel
from .config import Config, ConfigError, load_config
from .orchestrator import Orchestrator
from .state import StateStore


def build_channel(config: Config):
    kind = config.channel.kind
    settings = config.channel.settings
    if kind == "mock":
        return MockChannel()
    if kind == "webhook":
        return WebhookChannel(
            listen_host=str(settings.get("listen_host", "127.0.0.1")),
            listen_port=int(settings.get("listen_port", 18200)),
            path=str(settings.get("path", "/inbound")),
            secret=settings.get("secret"),
            send_url=settings.get("send_url"),
            send_timeout=float(settings.get("send_timeout", 30)),
            verify_tls=bool(settings.get("verify_tls", True)),
        )
    if kind == "wcferry":
        return WcferryChannel(poll_interval=float(settings.get("poll_interval", 0.2)))
    if kind == "wxhook":
        return WxhookChannel(faked_version=settings.get("faked_version"))
    if kind == "wechatauto":
        return WechatautoChannel(
            interval=float(settings.get("interval", 1.0)),
            account=settings.get("account"),
            nickname=settings.get("nickname"),
            guard_interval=float(settings.get("guard_interval", 30.0)),
        )
    if kind == "xhs":
        return XhsChannel(
            profile_dir=settings.get("profile_dir"),
            interval=float(settings.get("interval", 4.0)),
            headless=bool(settings.get("headless", False)),
            window_mode=str(settings.get("window_mode", config.bot.browser_window)),
        )
    if kind == "soul":
        return SoulChannel(
            profile_dir=settings.get("profile_dir"),
            interval=float(settings.get("interval", 4.0)),
            headless=bool(settings.get("headless", False)),
            window_mode=str(settings.get("window_mode", config.bot.browser_window)),
        )
    raise ConfigError(f"unknown channel: {kind}")


def build_client(config: Config) -> AppClient:
    return AppClient(
        base_url=config.app.base_url,
        username=config.app.username,
        password=config.app.password,
        verify_tls=config.app.verify_tls,
        timeout_seconds=config.app.timeout_seconds,
    )


class RotatingLogger:
    """Append-only log with size-based rotation (bridge.log -> bridge.log.1 ...)."""

    def __init__(self, path: Path, max_bytes: int = 5 * 1024 * 1024, backups: int = 5):
        self._path = path
        self._max = max_bytes
        self._backups = backups
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = path.open("a", encoding="utf-8", buffering=1)

    def _rotate(self) -> None:
        self._handle.close()
        for index in range(self._backups - 1, 0, -1):
            source = self._path.with_suffix(self._path.suffix + f".{index}")
            target = self._path.with_suffix(self._path.suffix + f".{index + 1}")
            if source.exists():
                if target.exists():
                    target.unlink()
                source.rename(target)
        first = self._path.with_suffix(self._path.suffix + ".1")
        if self._path.exists():
            if first.exists():
                first.unlink()
            self._path.rename(first)
        self._handle = self._path.open("a", encoding="utf-8", buffering=1)

    def write(self, line: str) -> None:
        with self._lock:
            self._handle.write(line + "\n")
            if self._handle.tell() > self._max:
                self._rotate()

    def close(self) -> None:
        with self._lock:
            self._handle.close()


def make_logger(path: Path):
    sink = RotatingLogger(path)

    def log(message: str) -> None:
        line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {message}"
        if sys.stdout is not None:
            print(line, flush=True)
        sink.write(line)

    return log


async def cmd_run(config: Config) -> int:
    client = build_client(config)
    state = StateStore(config.bot.state_path)
    channel = build_channel(config)
    log_path = Path(config.source_path).with_suffix(".log")
    orchestrator = Orchestrator(config, client, channel, state, log=make_logger(log_path))

    try:
        await orchestrator.run()
    except KeyboardInterrupt:
        pass
    finally:
        await orchestrator.stop()
        await client.close()
        state.close()
    return 0


async def cmd_doctor(config: Config) -> int:
    client = build_client(config)
    try:
        token = await client.login()
        print(f"login ok (token {token[:8]}...)")
        persons = await client.list_persons()
        print(f"persons: {len(persons)}")
        for person in persons[:5]:
            conversations = await client.list_conversations(person["id"])
            print(f"  - {person['name']} ({person['id']}): {len(conversations)} conversation(s)")
            for conversation in conversations[:3]:
                print(f"      * {conversation.get('title') or '(untitled)'} [{conversation['status']}] {conversation['id']}")
        if not persons:
            print("  (no persons yet; the bridge will create one on the first message)")
        return 0
    except AppError as exc:
        print(f"app error: {exc}", file=sys.stderr)
        return 2
    finally:
        await client.close()


def cmd_contacts(config: Config) -> int:
    state = StateStore(config.bot.state_path)
    try:
        contacts = state.list_contacts()
        if not contacts:
            print("no contact mappings yet")
        for contact in contacts:
            flag = "on" if contact["enabled"] else "off"
            print(
                f"{contact['contact_id']}  [{flag}]  {contact.get('label') or ''}  "
                f"person={contact['person_id']} conversation={contact['conversation_id']}"
            )
        print(f"paused={state.paused()}")
        return 0
    finally:
        state.close()


def cmd_map(config: Config, args: argparse.Namespace) -> int:
    state = StateStore(config.bot.state_path)
    try:
        state.save_contact(args.contact, args.person_id, args.conversation_id, args.label)
        print(f"mapped {args.contact} -> person={args.person_id} conversation={args.conversation_id}")
        return 0
    finally:
        state.close()


async def cmd_link(config: Config, args: argparse.Namespace) -> int:
    """Bind another platform/account contact to an existing Person."""
    client = build_client(config)
    state = StateStore(config.bot.state_path)
    contact_id = args.contact.strip()
    if ":" not in contact_id and args.platform:
        contact_id = f"{args.platform.strip().lower()}:{contact_id}"
    try:
        conversation_id = args.conversation_id
        if not conversation_id:
            conversation = await client.ensure_primary_conversation(args.person_id)
            conversation_id = conversation["id"]
        state.save_contact(contact_id, args.person_id, conversation_id, args.label)
        print(
            f"linked {contact_id} -> person={args.person_id} "
            f"conversation={conversation_id} ({platform_label(contact_id)})"
        )
        return 0
    finally:
        state.close()
        await client.close()


async def cmd_consolidate(config: Config) -> int:
    """Merge every person's platform conversations into their primary one."""
    client = build_client(config)
    try:
        persons = await client.list_persons()
        for person in persons:
            conversations = await client.list_conversations(person["id"])
            if len(conversations) > 1:
                result = await client.consolidate_person_conversations(person["id"])
                print(f"{person['name']}: merged {result['moved']}")
            else:
                print(f"{person['name']}: single conversation")
        return 0
    finally:
        await client.close()


def cmd_pause(config: Config, paused: bool) -> int:
    state = StateStore(config.bot.state_path)
    try:
        state.set_paused(paused)
        print("paused" if paused else "resumed")
        return 0
    finally:
        state.close()


def cmd_window(config: Config, action: str) -> int:
    """Reveal (or re-park) the browser owned by a running bridge.

    The panel has no handle on the browser, but the bridge wrote its pid into
    ``status.json`` next to the config, so the window can be found from there.
    """
    from . import window as window_module

    status_path = config.source_path.parent / "status.json"
    try:
        status = json.loads(status_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("no status.json: start the channel first", file=sys.stderr)
        return 1
    pid = int(status.get("pid") or 0)
    if not pid:
        print("status.json has no pid", file=sys.stderr)
        return 1
    key = f"{config.channel.kind}:{config.source_path.parent.resolve()}"
    count = (
        window_module.show([pid], profile_key=key)
        if action == "show"
        else window_module.hide([pid], profile_key=key)
    )
    print(f"{action}: {count} window(s)")
    return 0 if count else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lovebridge", description="WeChat bridge for AI Love Strategist")
    parser.add_argument("--config", required=True, help="path to config.toml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="start the bridge")
    sub.add_parser("doctor", help="check login and list persons/conversations")
    sub.add_parser("contacts", help="list contact mappings")
    map_parser = sub.add_parser("map", help="bind a WeChat contact to a person/conversation")
    map_parser.add_argument("--contact", required=True, help="WeChat contact id (wxid / room id)")
    map_parser.add_argument("--person-id", required=True)
    map_parser.add_argument("--conversation-id", required=True)
    map_parser.add_argument("--label")
    link_parser = sub.add_parser("link", help="bind another platform contact to an existing person")
    link_parser.add_argument("--contact", required=True, help="platform:id, e.g. xhs:abc123")
    link_parser.add_argument("--platform", help="prefix to add when --contact has no ':'")
    link_parser.add_argument("--person-id", required=True)
    link_parser.add_argument("--conversation-id", help="existing conversation; created when omitted")
    link_parser.add_argument("--title", help="title for the new conversation")
    link_parser.add_argument("--label")
    sub.add_parser("pause", help="stop replying (keeps receiving nothing)")
    sub.add_parser("resume", help="allow replying again")
    sub.add_parser("consolidate", help="merge each person's conversations into one")
    window_parser = sub.add_parser("window", help="show/hide the automation browser window")
    window_parser.add_argument("--action", choices=("show", "hide"), default="show")

    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    if args.command == "run":
        return asyncio.run(cmd_run(config))
    if args.command == "doctor":
        return asyncio.run(cmd_doctor(config))
    if args.command == "contacts":
        return cmd_contacts(config)
    if args.command == "map":
        return cmd_map(config, args)
    if args.command == "link":
        return asyncio.run(cmd_link(config, args))
    if args.command == "pause":
        return cmd_pause(config, True)
    if args.command == "resume":
        return cmd_pause(config, False)
    if args.command == "consolidate":
        return asyncio.run(cmd_consolidate(config))
    if args.command == "window":
        return cmd_window(config, args.action)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
