import inspect

from app.api.routes import media_attachments as media_routes
from app.repositories.media_attachment import MediaAttachmentRepository
from app.services.media_attachment import MediaAttachmentService


def test_media_service_has_no_legacy_analysis_entrypoint():
    assert not hasattr(MediaAttachmentService, "analyze")
    assert hasattr(MediaAttachmentService, "claim_analysis")
    assert hasattr(MediaAttachmentService, "prepare_claimed_analysis")
    assert hasattr(MediaAttachmentService, "analyze_claimed_media")
    assert hasattr(MediaAttachmentService, "complete_claimed_analysis")
    assert hasattr(MediaAttachmentService, "fail_claimed_analysis")


def test_media_repository_requires_claim_token_for_analysis_state_transitions():
    assert not hasattr(MediaAttachmentRepository, "mark_completed")
    assert not hasattr(MediaAttachmentRepository, "mark_failed")
    assert hasattr(MediaAttachmentRepository, "mark_completed_claimed")
    assert hasattr(MediaAttachmentRepository, "mark_failed_claimed")

    completed_signature = inspect.signature(
        MediaAttachmentRepository.mark_completed_claimed
    )
    failed_signature = inspect.signature(
        MediaAttachmentRepository.mark_failed_claimed
    )

    assert "claim_token" in completed_signature.parameters
    assert "claim_token" in failed_signature.parameters


def test_http_analysis_route_uses_only_claim_aware_service_flow():
    source = inspect.getsource(media_routes.analyze_media_attachment)

    assert "service.claim_analysis(" in source
    assert "service.prepare_claimed_analysis(" in source
    assert "service.analyze_claimed_media(" in source
    assert "service.complete_claimed_analysis(" in source
    assert "_fail_media_analysis_claim_best_effort(" in source

    assert "service.analyze(" not in source
    assert "repository.mark_completed(" not in source
    assert "repository.mark_failed(" not in source


def test_claimed_completion_is_the_only_service_path_that_creates_media_evidence():
    source = inspect.getsource(MediaAttachmentService)

    marker = 'f"[媒体证据:{row[\'media_type\']}] {analysis_text}"'
    assert source.count(marker) == 1

    completion_source = inspect.getsource(
        MediaAttachmentService.complete_claimed_analysis
    )
    assert marker in completion_source
    assert "self.repository.get_claimed(" in completion_source
    assert "self.repository.mark_completed_claimed(" in completion_source
