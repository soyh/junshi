# TEST-205 supersedes device-local picker presentation with explicit Beijing time.
from app.ui.china_time import CHINA_TIME_SCRIPT
from app.ui.media_upload_workspace import MEDIA_UPLOAD_WORKSPACE_SCRIPT
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML


def test_test194_media_time_uses_editable_beijing_time_with_current_default():
    script = MEDIA_UPLOAD_WORKSPACE_SCRIPT

    assert "sentAtInput.type = 'text';" in script
    assert "sentAtInput.step = '1';" in script
    assert "sentAtInput.value = chinaTimeInputNow();" in script
    assert "证据时间（北京时间，24小时制）" in script
    assert "采用24小时制" in script
    assert "function chinaTimeInputNow()" in CHINA_TIME_SCRIPT


def test_test194_media_time_converts_beijing_value_to_offset_iso_before_upload():
    script = MEDIA_UPLOAD_WORKSPACE_SCRIPT

    assert "function chinaTimeIso(value)" in CHINA_TIME_SCRIPT
    assert "Asia/Shanghai" in CHINA_TIME_SCRIPT
    assert "+08:00" in CHINA_TIME_SCRIPT
    assert "const sentAt = localSentAt ? chinaTimeIso(localSentAt) : null;" in script
    assert "if (sentAt) form.append('sent_at', sentAt);" in script
    assert "toISOString()" not in script


def test_test194_successful_upload_resets_time_to_new_current_local_value():
    script = MEDIA_UPLOAD_WORKSPACE_SCRIPT

    assert "function clientResetMediaSentAtToNow()" in script
    assert "clientResetMediaSentAtToNow();" in script
    assert "if (sentAtInput) sentAtInput.value = '';" not in script


def test_test194_product_shell_contains_new_media_datetime_contract():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "sentAtInput.type = 'text';" in html
    assert "sentAtInput.step = '1';" in html
    assert "证据时间（北京时间，24小时制）" in html
    assert "function chinaTimeIso(value)" in html
    assert "clientResetMediaSentAtToNow();" in html
    assert "2026-09-24T00:00:00+08:00" not in html
