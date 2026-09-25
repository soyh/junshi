from app.ui.media_upload_workspace import MEDIA_UPLOAD_WORKSPACE_SCRIPT
from app.ui.routes import PRODUCT_SHELL_WITH_CONTENT_HTML


def test_test194_media_time_uses_editable_datetime_local_with_current_default():
    script = MEDIA_UPLOAD_WORKSPACE_SCRIPT

    assert "sentAtInput.type = 'datetime-local';" in script
    assert "sentAtInput.step = '1';" in script
    assert "sentAtInput.value = clientCurrentLocalDateTimeValue();" in script
    assert "证据时间（默认当前本地时间）" in script
    assert "可直接修改日期或时分秒" in script
    assert "clientCurrentLocalDateTimeValue(now = new Date())" in script


def test_test194_media_time_converts_local_value_to_offset_iso_before_upload():
    script = MEDIA_UPLOAD_WORKSPACE_SCRIPT

    assert "function clientLocalDateTimeToIsoWithOffset(value)" in script
    assert "const offsetMinutes = -localDate.getTimezoneOffset();" in script
    assert "${sign}${offsetHours}:${offsetRemainder}" in script
    assert "const sentAt = localSentAt ? clientLocalDateTimeToIsoWithOffset(localSentAt) : null;" in script
    assert "if (sentAt) form.append('sent_at', sentAt);" in script
    assert "toISOString()" not in script


def test_test194_successful_upload_resets_time_to_new_current_local_value():
    script = MEDIA_UPLOAD_WORKSPACE_SCRIPT

    assert "function clientResetMediaSentAtToNow()" in script
    assert "clientResetMediaSentAtToNow();" in script
    assert "if (sentAtInput) sentAtInput.value = '';" not in script


def test_test194_product_shell_contains_new_media_datetime_contract():
    html = PRODUCT_SHELL_WITH_CONTENT_HTML

    assert "sentAtInput.type = 'datetime-local';" in html
    assert "sentAtInput.step = '1';" in html
    assert "证据时间（默认当前本地时间）" in html
    assert "function clientLocalDateTimeToIsoWithOffset(value)" in html
    assert "clientResetMediaSentAtToNow();" in html
    assert "2026-09-24T00:00:00+08:00" not in html
