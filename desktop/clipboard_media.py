"""Explicit clipboard snapshots only: text, images, and local media files."""
import io
from pathlib import Path

from PIL import Image, ImageGrab

MAX_FILE = 50 * 1024 * 1024
MIMES = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
         '.webp': 'image/webp', '.gif': 'image/gif', '.mp4': 'video/mp4',
         '.webm': 'video/webm', '.mov': 'video/quicktime'}


def files_snapshot(names):
    if len(names) > 4:
        raise ValueError('一次最多选择 4 个媒体文件')
    result = []
    for name in names:
        path = Path(name)
        mime = MIMES.get(path.suffix.lower())
        if not mime or not path.is_file() or path.is_symlink():
            raise ValueError('只支持本地 PNG/JPG/WebP/GIF 图片和 MP4/WebM/MOV 视频；请先保存聊天软件里的附件')
        if path.stat().st_size > MAX_FILE:
            raise ValueError('单个附件不能超过 50 MiB')
        with path.open('rb') as stream:
            content = stream.read(MAX_FILE + 1)
        if not content or len(content) > MAX_FILE:
            raise ValueError('附件为空或过大')
        result.append({'name': path.name, 'mime': mime, 'content': content})
    return result


def image_snapshot(image):
    if image.width * image.height > 25_000_000:
        raise ValueError('截图过大，请裁剪聊天区域后重试')
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    content = stream.getvalue()
    if len(content) > MAX_FILE:
        raise ValueError('截图超过 50 MiB')
    return [{'name': 'clipboard.png', 'mime': 'image/png', 'content': content}]


def capture(text_reader):
    value = ImageGrab.grabclipboard()
    if isinstance(value, Image.Image):
        return '', image_snapshot(value)
    if isinstance(value, list):
        return '', files_snapshot(value)
    try:
        text = text_reader()
    except Exception:
        text = ''
    if not text.strip():
        raise ValueError('剪贴板没有可读取的文字、图片或本地视频文件；请先复制或使用“选择附件”')
    if len(text) > 200000:
        raise ValueError('文字过长，请在主页面分批导入')
    return text, []
