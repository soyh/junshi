import base64
import hashlib
import json
import shutil
import sqlite3
import subprocess
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
import imageio_ffmpeg

from app.config.settings import get_settings
from app.domain.errors import ConversationNotFoundError, MessageNotFoundError
from app.repositories.media_attachment import MediaAttachmentRepository
from app.services.conversation import ConversationService
from app.services.llm import LLMAnalysisError
from app.services.llm_provider_config import LLMProviderConfigService
from app.services.message import MessageService
from app.services.openai_chat_provider import OpenAIChatProvider
from app.services.vision_llm_provider import LLMVisionProviderService


class MediaAttachmentError(ValueError):
    pass


class MediaAnalysisInProgressError(MediaAttachmentError):
    pass


_ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_ALLOWED_VIDEOS = {"video/mp4", "video/webm", "video/quicktime"}
_ANALYSIS_CLAIM_TTL_SECONDS = 10 * 60


class MediaAttachmentService:
    def __init__(
        self,
        repository: MediaAttachmentRepository | None = None,
        conversation_service: ConversationService | None = None,
        message_service: MessageService | None = None,
        provider_config_service: LLMProviderConfigService | None = None,
    ):
        self.repository = repository or MediaAttachmentRepository()
        self.conversation_service = conversation_service or ConversationService()
        self.message_service = message_service or MessageService()
        self.provider_config_service = provider_config_service or LLMProviderConfigService()
        self.vision_provider_service = LLMVisionProviderService(
            self.provider_config_service
        )

    @staticmethod
    def _storage_root() -> Path:
        root = Path(get_settings().media_storage_directory)
        root.mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _kind_for_mime(mime_type: str) -> str:
        if mime_type in _ALLOWED_IMAGES:
            return "image"
        if mime_type in _ALLOWED_VIDEOS:
            return "video"
        raise MediaAttachmentError("unsupported media type")

    @staticmethod
    def _row_value(row, key: str, default=None):
        try:
            return row[key]
        except (KeyError, IndexError, TypeError):
            return default

    @staticmethod
    def _analysis_stale_before() -> str:
        return (
            datetime.now(timezone.utc)
            - timedelta(seconds=_ANALYSIS_CLAIM_TTL_SECONDS)
        ).isoformat()

    def cleanup_unreferenced_blob(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        storage_path: str,
    ) -> bool:
        if self.repository.count_for_storage_path(conn, user_id, storage_path) > 0:
            return False
        try:
            Path(storage_path).unlink(missing_ok=True)
        except OSError:
            return False
        return True

    def create(
        self,
        conn: sqlite3.Connection,
        *,
        user_id: str,
        conversation_id: str,
        original_filename: str,
        mime_type: str,
        content: bytes,
        sent_at: str | None,
    ) -> sqlite3.Row:
        if not content:
            raise MediaAttachmentError("media file is empty")
        max_bytes = get_settings().media_max_upload_bytes
        if len(content) > max_bytes:
            raise MediaAttachmentError("media file exceeds upload size limit")

        media_type = self._kind_for_mime(mime_type)
        conversation = self.conversation_service.get(conn, user_id, conversation_id)
        digest = hashlib.sha256(content).hexdigest()
        suffix = Path(original_filename or "upload").suffix.lower()[:12]
        storage_name = f"{digest}{suffix}"
        user_dir = self._storage_root() / user_id / conversation_id
        user_dir.mkdir(parents=True, exist_ok=True)
        path = user_dir / storage_name
        blob_created = False
        if not path.exists():
            path.write_bytes(content)
            blob_created = True

        try:
            return self.repository.create(
                conn,
                user_id=user_id,
                person_id=conversation["person_id"],
                conversation_id=conversation_id,
                media_type=media_type,
                mime_type=mime_type,
                original_filename=(Path(original_filename).name or "upload")[:255],
                storage_path=str(path),
                sha256=digest,
                size_bytes=len(content),
                sent_at=sent_at,
            )
        except Exception:
            if blob_created:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
            raise

    def list_for_conversation(self, conn, user_id: str, conversation_id: str):
        self.conversation_service.get(conn, user_id, conversation_id)
        return self.repository.list_for_conversation(conn, user_id, conversation_id)

    def delete(
        self,
        conn,
        user_id: str,
        attachment_id: str,
        *,
        defer_blob_cleanup: bool = False,
    ) -> str | None:
        row = self.repository.get(conn, user_id, attachment_id)
        if row is None:
            raise MediaAttachmentError("media attachment not found")

        path = Path(row["storage_path"])
        evidence_message_id = self._row_value(row, "message_id")
        if evidence_message_id:
            try:
                self.message_service.delete(conn, user_id, evidence_message_id)
            except MessageNotFoundError:
                pass

        self.repository.delete(conn, user_id, attachment_id)
        storage_path = str(path)
        if defer_blob_cleanup:
            return storage_path
        self.cleanup_unreferenced_blob(conn, user_id, storage_path)
        return storage_path

    @staticmethod
    def _data_url(path: Path, mime_type: str) -> str:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    @staticmethod
    def _ffmpeg_executable() -> str:
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            return system_ffmpeg

        try:
            bundled_ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        except (RuntimeError, OSError):
            bundled_ffmpeg = None

        if bundled_ffmpeg and Path(bundled_ffmpeg).is_file():
            return bundled_ffmpeg

        raise MediaAttachmentError("ffmpeg is required for video analysis")

    @staticmethod
    def _video_frames(path: Path) -> list[Path]:
        ffmpeg = MediaAttachmentService._ffmpeg_executable()
        temp_dir = Path(tempfile.mkdtemp(prefix="junshi-media-"))
        pattern = temp_dir / "frame-%02d.jpg"
        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-vf",
            "fps=1/3,scale='min(1280,iw)':-2",
            "-frames:v",
            "6",
            str(pattern),
        ]
        try:
            subprocess.run(command, check=True, timeout=60)
        except (subprocess.SubprocessError, OSError):
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise MediaAttachmentError("video frame extraction failed") from None
        frames = sorted(temp_dir.glob("frame-*.jpg"))
        if not frames:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise MediaAttachmentError("video contains no decodable frames")
        return frames

    @staticmethod
    def _safe_media_prompt() -> str:
        return (
            "Analyze this media as conversation evidence for a relationship-advice system. "
            "Describe only visible evidence. Distinguish observations from inference. "
            "Pay attention to visible text, emoji/sticker meaning, facial expression, body language, "
            "scene/context, and interaction tone when supported. Do not identify unknown people. "
            "Return concise JSON with keys: media_summary, visible_text, emotional_signals, "
            "interaction_signals, uncertainty. Values may be strings or arrays."
        )

    def _analyze_with_provider(
        self,
        provider: OpenAIChatProvider,
        row: sqlite3.Row | dict,
    ) -> str:
        if not provider.api_key:
            raise MediaAttachmentError("configured provider API key is missing")

        path = Path(row["storage_path"])
        cleanup_dir: Path | None = None
        if row["media_type"] == "image":
            image_urls = [self._data_url(path, row["mime_type"])]
        else:
            frames = self._video_frames(path)
            cleanup_dir = frames[0].parent
            image_urls = [self._data_url(frame, "image/jpeg") for frame in frames]

        content: list[dict[str, object]] = [
            {"type": "text", "text": self._safe_media_prompt()},
        ]
        content.extend(
            {"type": "image_url", "image_url": {"url": url}}
            for url in image_urls
        )
        payload = {
            "model": provider.model,
            "messages": [{"role": "user", "content": content}],
            "response_format": {"type": "json_object"},
            "max_tokens": 900,
        }
        headers = {
            "Authorization": f"Bearer {provider.api_key}",
            "Content-Type": "application/json",
        }
        try:
            response = provider._post(payload, headers)
            response.raise_for_status()
            body = response.json()
            text = body["choices"][0]["message"]["content"]
            if not isinstance(text, str) or not text.strip():
                raise ValueError
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError
            return json.dumps(parsed, ensure_ascii=False, sort_keys=True)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError, LLMAnalysisError):
            raise MediaAttachmentError("configured model could not analyze this media") from None
        finally:
            if cleanup_dir is not None:
                shutil.rmtree(cleanup_dir, ignore_errors=True)

    def claim_analysis(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        attachment_id: str,
    ) -> tuple[sqlite3.Row, str | None, str | None]:
        row = self.repository.get(conn, user_id, attachment_id)
        if row is None:
            raise MediaAttachmentError("media attachment not found")

        existing_message_id = self._row_value(row, "message_id")
        if (
            self._row_value(row, "analysis_status") == "completed"
            and existing_message_id
        ):
            return row, None, existing_message_id

        now = datetime.now(timezone.utc)
        claimed_at = now.isoformat()
        stale_before = (
            now - timedelta(seconds=_ANALYSIS_CLAIM_TTL_SECONDS)
        ).isoformat()
        claim_token = str(uuid.uuid4())
        claimed = self.repository.try_claim_analysis(
            conn,
            user_id,
            attachment_id,
            claim_token=claim_token,
            claimed_at=claimed_at,
            stale_before=stale_before,
        )
        if claimed is not None:
            return claimed, claim_token, None

        latest = self.repository.get(conn, user_id, attachment_id)
        latest_message_id = self._row_value(latest, "message_id")
        if (
            latest is not None
            and self._row_value(latest, "analysis_status") == "completed"
            and latest_message_id
        ):
            return latest, None, latest_message_id

        raise MediaAnalysisInProgressError("media analysis already in progress")

    def prepare_claimed_analysis(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        attachment_id: str,
        claim_token: str,
    ) -> tuple[dict, OpenAIChatProvider]:
        row = self.repository.get_claimed(
            conn,
            user_id,
            attachment_id,
            claim_token,
            stale_before=self._analysis_stale_before(),
        )
        if row is None:
            raise MediaAnalysisInProgressError("media analysis claim lost or expired")

        provider = self.vision_provider_service.build_provider(conn, user_id)
        if not isinstance(provider, OpenAIChatProvider):
            raise MediaAttachmentError("configured provider does not support media analysis")
        return dict(row), provider

    def analyze_claimed_media(
        self,
        provider: OpenAIChatProvider,
        row: dict,
    ) -> str:
        return self._analyze_with_provider(provider, row)

    def complete_claimed_analysis(
        self,
        conn: sqlite3.Connection,
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

        evidence = self.message_service.create(
            conn,
            user_id,
            row["conversation_id"],
            "system",
            f"[媒体证据:{row['media_type']}] {analysis_text}",
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

    def fail_claimed_analysis(
        self,
        conn: sqlite3.Connection,
        user_id: str,
        attachment_id: str,
        claim_token: str,
    ) -> None:
        self.repository.mark_failed_claimed(
            conn,
            user_id,
            attachment_id,
            claim_token,
            stale_before=self._analysis_stale_before(),
        )
