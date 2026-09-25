from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone

from app.services.media_attachment import (
    MediaAnalysisInProgressError,
    MediaAttachmentService,
)


_WEEKDAY_INDEX = {
    "一": 0,
    "二": 1,
    "三": 2,
    "四": 3,
    "五": 4,
    "六": 5,
    "日": 6,
    "天": 6,
}

_DAY_PERIODS_PM = {"下午", "傍晚", "晚上", "夜里", "夜间"}
_DAY_PERIODS_AM = {"凌晨", "早上", "早晨", "上午"}


class TimedMediaAttachmentService(MediaAttachmentService):
    """Media analysis service with deterministic chat-time extraction.

    The vision model only reports raw, visible time labels. This class resolves
    those labels against the attachment evidence time and writes the resulting
    timestamps into canonical user/person messages. Unparseable or ambiguous
    labels never replace the fallback evidence time.
    """

    @staticmethod
    def _safe_media_prompt() -> str:
        return (
            MediaAttachmentService._safe_media_prompt()
            + " Also extract chat-relevant visible date/time evidence. Exclude phone status-bar "
            "clocks, app chrome clocks, and any time that is not clearly part of the chat history. "
            "Add a top-level time_markers array. Each item must contain before_message_index, the "
            "zero-based index of the first conversation_messages item governed by that marker, and "
            "text containing only the raw visible label, for example '9月23日 13:42', '昨天 下午3:05', "
            "'星期二 11:42', or '23:30'. For each conversation_messages item also include "
            "timestamp_text when a time is printed directly beside or inside that bubble, otherwise "
            "null; date_context_text may contain the raw visible date/day separator governing that "
            "bubble, otherwise null. Never invent, normalize, infer, or repair a missing date or time."
        )

    @staticmethod
    def _anchor_datetime(anchor: str | None) -> datetime:
        parsed: datetime | None = None
        if anchor:
            candidate = anchor[:-1] + "+00:00" if anchor.endswith("Z") else anchor
            try:
                parsed = datetime.fromisoformat(candidate)
            except ValueError:
                parsed = None
        if parsed is None:
            parsed = datetime.now(timezone.utc)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    @staticmethod
    def _conversation_message_items_from_analysis(analysis_text: str) -> list[dict[str, str | None]]:
        try:
            parsed = json.loads(analysis_text)
        except (TypeError, ValueError):
            return []
        if not isinstance(parsed, dict):
            return []

        raw_messages = parsed.get("conversation_messages")
        if not isinstance(raw_messages, list):
            return []

        items: list[dict[str, str | None]] = []
        for raw in raw_messages[:200]:
            if not isinstance(raw, dict):
                continue
            sender_type = raw.get("sender_type")
            content = raw.get("content")
            if sender_type not in {"user", "person"} or not isinstance(content, str):
                continue
            normalized_content = content.strip()
            if not normalized_content:
                continue

            timestamp_text = raw.get("timestamp_text")
            date_context_text = raw.get("date_context_text")
            items.append(
                {
                    "sender_type": sender_type,
                    "content": normalized_content[:4000],
                    "timestamp_text": (
                        timestamp_text.strip()[:120]
                        if isinstance(timestamp_text, str) and timestamp_text.strip()
                        else None
                    ),
                    "date_context_text": (
                        date_context_text.strip()[:120]
                        if isinstance(date_context_text, str) and date_context_text.strip()
                        else None
                    ),
                }
            )
        return items

    @staticmethod
    def _time_markers_from_analysis(analysis_text: str) -> list[dict[str, int | str]]:
        try:
            parsed = json.loads(analysis_text)
        except (TypeError, ValueError):
            return []
        if not isinstance(parsed, dict):
            return []

        raw_markers = parsed.get("time_markers")
        if not isinstance(raw_markers, list):
            return []

        markers: list[dict[str, int | str]] = []
        for order, raw in enumerate(raw_markers[:200]):
            if not isinstance(raw, dict):
                continue
            before = raw.get("before_message_index")
            text = raw.get("text")
            if not isinstance(before, int) or before < 0:
                continue
            if not isinstance(text, str) or not text.strip():
                continue
            markers.append(
                {
                    "before_message_index": before,
                    "text": text.strip()[:120],
                    "_order": order,
                }
            )
        markers.sort(key=lambda item: (int(item["before_message_index"]), int(item["_order"])))
        return markers

    @staticmethod
    def _parse_visible_time_label(
        text: str | None,
        *,
        anchor: datetime,
        current: datetime,
    ) -> datetime | None:
        if not text or not str(text).strip():
            return None

        raw = str(text).strip().replace("：", ":")
        target_date = current.date()
        date_found = False

        full_cn = re.search(r"(?<!\d)(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日", raw)
        full_numeric = re.search(
            r"(?<!\d)(\d{4})\s*[-/.]\s*(\d{1,2})\s*[-/.]\s*(\d{1,2})(?!\d)",
            raw,
        )
        month_day = re.search(r"(?<!\d)(\d{1,2})月\s*(\d{1,2})日", raw)

        try:
            if full_cn:
                target_date = datetime(
                    int(full_cn.group(1)),
                    int(full_cn.group(2)),
                    int(full_cn.group(3)),
                    tzinfo=anchor.tzinfo,
                ).date()
                date_found = True
            elif full_numeric:
                target_date = datetime(
                    int(full_numeric.group(1)),
                    int(full_numeric.group(2)),
                    int(full_numeric.group(3)),
                    tzinfo=anchor.tzinfo,
                ).date()
                date_found = True
            elif month_day:
                target_date = datetime(
                    anchor.year,
                    int(month_day.group(1)),
                    int(month_day.group(2)),
                    tzinfo=anchor.tzinfo,
                ).date()
                date_found = True
            elif "前天" in raw:
                target_date = (anchor - timedelta(days=2)).date()
                date_found = True
            elif "昨天" in raw:
                target_date = (anchor - timedelta(days=1)).date()
                date_found = True
            elif "今天" in raw:
                target_date = anchor.date()
                date_found = True
            else:
                weekday = re.search(r"(?:周|星期|礼拜)\s*([一二三四五六日天])", raw)
                if weekday:
                    weekday_index = _WEEKDAY_INDEX[weekday.group(1)]
                    days_back = (anchor.weekday() - weekday_index) % 7
                    target_date = (anchor - timedelta(days=days_back)).date()
                    date_found = True
        except ValueError:
            return None

        period_match = re.search(
            r"(凌晨|早上|早晨|上午|中午|下午|傍晚|晚上|夜里|夜间)?\s*(\d{1,2})\s*:\s*(\d{2})",
            raw,
        )
        point_match = None
        if not period_match:
            point_match = re.search(
                r"(凌晨|早上|早晨|上午|中午|下午|傍晚|晚上|夜里|夜间)?\s*(\d{1,2})\s*点(?:\s*(\d{1,2})\s*分?)?",
                raw,
            )

        time_found = bool(period_match or point_match)
        if period_match:
            period = period_match.group(1)
            hour = int(period_match.group(2))
            minute = int(period_match.group(3))
        elif point_match:
            period = point_match.group(1)
            hour = int(point_match.group(2))
            minute = int(point_match.group(3) or "0")
        else:
            period = None
            hour = current.hour
            minute = current.minute

        if not date_found and not time_found:
            return None
        if hour > 23 or minute > 59:
            return None

        if period in _DAY_PERIODS_PM and hour < 12:
            hour += 12
        elif period == "中午" and 1 <= hour < 12:
            hour += 12
        elif period in _DAY_PERIODS_AM and hour == 12:
            hour = 0

        try:
            return datetime(
                target_date.year,
                target_date.month,
                target_date.day,
                hour,
                minute,
                0 if time_found else current.second,
                0 if time_found else current.microsecond,
                tzinfo=anchor.tzinfo,
            )
        except ValueError:
            return None

    @classmethod
    def _resolved_message_sent_ats(
        cls,
        analysis_text: str,
        anchor: str | None,
    ) -> list[str]:
        items = cls._conversation_message_items_from_analysis(analysis_text)
        if not items:
            return []

        base = cls._anchor_datetime(anchor)
        cursor = base
        previous: datetime | None = None
        markers = cls._time_markers_from_analysis(analysis_text)
        marker_offset = 0
        resolved: list[str] = []

        for index, item in enumerate(items):
            while (
                marker_offset < len(markers)
                and int(markers[marker_offset]["before_message_index"]) <= index
            ):
                parsed_marker = cls._parse_visible_time_label(
                    str(markers[marker_offset]["text"]),
                    anchor=base,
                    current=cursor,
                )
                if parsed_marker is not None:
                    cursor = parsed_marker
                marker_offset += 1

            date_context = item.get("date_context_text")
            if isinstance(date_context, str):
                parsed_date_context = cls._parse_visible_time_label(
                    date_context,
                    anchor=base,
                    current=cursor,
                )
                if parsed_date_context is not None:
                    cursor = parsed_date_context

            timestamp_text = item.get("timestamp_text")
            if isinstance(timestamp_text, str):
                parsed_timestamp = cls._parse_visible_time_label(
                    timestamp_text,
                    anchor=base,
                    current=cursor,
                )
                if parsed_timestamp is not None:
                    cursor = parsed_timestamp

            candidate = cursor
            if previous is not None and candidate <= previous:
                candidate = previous + timedelta(seconds=1)

            resolved.append(candidate.isoformat())
            previous = candidate
            cursor = candidate + timedelta(seconds=1)

        return resolved

    def complete_claimed_analysis(
        self,
        conn,
        user_id: str,
        attachment_id: str,
        claim_token: str,
        analysis_text: str,
    ):
        row = self.repository.get_claimed(
            conn,
            user_id,
            attachment_id,
            claim_token,
            stale_before=self._analysis_stale_before(),
        )
        if row is None:
            raise MediaAnalysisInProgressError("media analysis claim lost or expired")

        extracted_items = self._conversation_message_items_from_analysis(analysis_text)
        resolved_sent_ats = self._resolved_message_sent_ats(analysis_text, row["sent_at"])
        for item, sent_at in zip(extracted_items, resolved_sent_ats, strict=True):
            self.message_service.create(
                conn,
                user_id,
                row["conversation_id"],
                str(item["sender_type"]),
                str(item["content"]),
                sent_at,
            )

        evidence = self.message_service.create(
            conn,
            user_id,
            row["conversation_id"],
            "system",
            f"[媒体证据:{row['media_type']}] {self._evidence_analysis_text(analysis_text)}",
            row["sent_at"],
        )
        updated = self.repository.mark_completed_claimed(
            conn,
            user_id,
            attachment_id,
            claim_token,
            analysis_text,
            evidence["id"],
            stale_before=self._analysis_stale_before(),
        )
        if updated is None:
            raise MediaAnalysisInProgressError("media analysis claim lost or expired")
        return updated, evidence["id"]
