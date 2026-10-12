import json
import urllib.error
import urllib.parse
import urllib.request
from uuid import uuid4


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def browser_url(self):
        if not self.token:
            return self.base + '/app'
        result = self.request('POST', '/auth/browser-handoff', timeout=15)
        ticket = result.get('ticket', '') if isinstance(result, dict) else ''
        import re
        if not re.fullmatch(r'[A-Za-z0-9_-]{43}', ticket):
            raise ValueError('服务器未返回有效登录衔接，请确认服务器已更新。')
        return self.base + '/app#desktop-login=' + ticket

    def __init__(self, base, token=None):
        parts = urllib.parse.urlsplit(base.strip())
        if parts.username or parts.password or parts.query or parts.fragment or parts.path not in ('', '/'):
            raise ValueError('服务器地址只能包含协议、主机和端口，例如 https://example.com')
        if parts.scheme != 'https' and not (parts.scheme == 'http' and parts.hostname in ('localhost', '127.0.0.1', '::1')):
            raise ValueError('远程服务器必须使用 HTTPS；HTTP 仅限本机')
        if not parts.hostname:
            raise ValueError('请输入服务器地址')
        self.base = base.strip().rstrip('/')
        self.token = token
        self.opener = urllib.request.build_opener(NoRedirect())

    def request(self, method, path, payload=None, media=None, timeout=300):
        headers = {}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        data = None
        if media is not None:
            boundary = 'junshi' + uuid4().hex
            chunks = []
            for key, value in (payload or {}).items():
                chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
            # Never put user-supplied paths or control characters in MIME headers.
            extension = {'image/png': 'png', 'image/jpeg': 'jpg', 'image/gif': 'gif', 'image/webp': 'webp',
                         'video/mp4': 'mp4', 'video/webm': 'webm', 'video/quicktime': 'mov'}[media['mime']]
            chunks += [f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="attachment.{extension}"\r\nContent-Type: {media["mime"]}\r\n\r\n'.encode(), media['content'], f'\r\n--{boundary}--\r\n'.encode()]
            data = b''.join(chunks)
            headers['Content-Type'] = 'multipart/form-data; boundary=' + boundary
        elif payload is not None:
            data = json.dumps(payload).encode()
            headers['Content-Type'] = 'application/json'
        request = urllib.request.Request(self.base + '/api/v1' + path, data=data, headers=headers, method=method)
        try:
            with self.opener.open(request, timeout=timeout) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read()).get('detail')
            except Exception:
                detail = None
            raise ValueError(detail if isinstance(detail, str) else f'服务器返回 HTTP {exc.code}，请确认已安装 TEST-216 或更新版本') from None
        except (OSError, urllib.error.URLError):
            raise ValueError('网络请求失败或超时。已保存的内容不会自动删除；本次窗口内可重试，重复请求使用相同操作编号。') from None
