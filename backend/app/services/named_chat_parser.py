"""Deterministic named transcript parsing; no model or database access."""
import re
from datetime import datetime, timedelta, timezone

from app.schemas.text_import import TextImportCandidate

DATE = re.compile(r"^(\d{4})年(\d{1,2})月(\d{1,2})日\s+(\d{1,2}):(\d{2})(?::(\d{2}))?$")
DATE_LIKE = re.compile(r"^\d{4}年")
OFFSET = re.compile(r"^([+-])(\d{2}):(\d{2})$")


def parse_named_chat(text: str, utc_offset: str = "+08:00") -> dict:
    if len(text) > 1_000_000:
        raise ValueError("聊天记录不能超过 100 万字符")
    offset = OFFSET.fullmatch(utc_offset)
    if not offset:
        raise ValueError("时区应为 +08:00 这样的 UTC 偏移")
    hours, minutes = int(offset[2]), int(offset[3])
    if hours > 14 or minutes > 59 or (hours == 14 and minutes):
        raise ValueError("时区偏移超出范围")
    zone = timezone(timedelta(minutes=(hours * 60 + minutes) * (1 if offset[1] == "+" else -1)))
    lines = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    headers = []
    for i in range(len(lines) - 1):
        name, date = lines[i].strip(), lines[i + 1].strip()
        if not name or not DATE_LIKE.match(date):
            continue
        matched = DATE.fullmatch(date)
        if not matched:
            raise ValueError(f"第 {i + 2} 行日期格式无效，应为 2026年09月26日 10:40")
        try:
            moment = datetime(*(int(v or 0) for v in matched.groups()), tzinfo=zone)
        except ValueError as exc:
            raise ValueError(f"第 {i + 2} 行日期或时间无效") from exc
        headers.append((i, name, moment.isoformat(), "second" if matched[6] else "minute"))
    if not headers:
        raise ValueError("未识别到记录，请使用用户名、日期时间、正文分行的格式")
    if any(line.strip() for line in lines[:headers[0][0]]):
        raise ValueError("首条记录前有无法识别的内容，请检查后重试")
    messages = []
    for pos, (start, name, sent_at, precision) in enumerate(headers):
        end = headers[pos + 1][0] if pos + 1 < len(headers) else len(lines)
        content = "\n".join(lines[start + 2:end]).strip("\n")
        if not content.strip():
            raise ValueError(f"第 {start + 1} 行的消息正文为空")
        messages.append(dict(line_number=start + 1, sender_name=name,
                             sent_at=sent_at, time_precision=precision, content=content))
    return dict(senders=list(dict.fromkeys(m["sender_name"] for m in messages)),
                messages=messages, utc_offset=utc_offset)


def named_candidates(text: str, self_name: str | None, other_name: str | None,
                     utc_offset: str) -> list[TextImportCandidate]:
    parsed = parse_named_chat(text, utc_offset)
    if not self_name or not other_name or self_name == other_name:
        raise ValueError("请选择两个不同的用户名，分别作为我和对方")
    mapping = {self_name: "user", other_name: "person"}
    if set(parsed["senders"]) != set(mapping):
        raise ValueError("记录中的用户名必须全部对应我或对方；请检查第三个用户名或身份选择")
    return [TextImportCandidate(line_number=m["line_number"], sent_at=m["sent_at"],
                                sender_type=mapping[m["sender_name"]], content=m["content"])
            for m in parsed["messages"]]
