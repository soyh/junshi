import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from clipboard_media import capture, files_snapshot
from client import Client
from pc_workflow import new_job, generate, confirm_sent


class ClipboardTests(unittest.TestCase):
    @patch('clipboard_media.ImageGrab.grabclipboard', return_value=None)
    def test_text_requires_explicit_capture(self, grab):
        reader = Mock(return_value='synthetic message')
        self.assertEqual(capture(reader), ('synthetic message', []))
        reader.assert_called_once()

    @patch('clipboard_media.ImageGrab.grabclipboard')
    def test_clipboard_image_is_png_and_not_uploaded(self, grab):
        grab.return_value = Image.new('RGB', (4, 4), 'white')
        text, files = capture(Mock())
        self.assertEqual(text, '')
        self.assertTrue(files[0]['content'].startswith(b'\x89PNG'))

    @patch('clipboard_media.ImageGrab.grabclipboard')
    def test_copied_video_file_and_unsupported_file(self, grab):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / 'synthetic.mp4'; video.write_bytes(b'synthetic video')
            grab.return_value = [str(video)]
            self.assertEqual(capture(Mock())[1][0]['mime'], 'video/mp4')
            text = Path(directory) / 'private.env'; text.write_text('never upload')
            with self.assertRaises(ValueError): files_snapshot([text])


class WorkflowTests(unittest.TestCase):
    def test_retry_skips_saved_message_and_media_analysis(self):
        client = Mock()
        attempts = []
        def request(method, path, *args, **kwargs):
            attempts.append(path)
            if path.endswith('/media'): return {'id': 'media1'}
            if path.endswith('/context') and attempts.count(path) == 1: raise ValueError('model failure')
            return {'draft': 'synthetic reply'}
        client.request.side_effect = request
        job = new_job('p', 'c', 'text', [{'mime': 'image/png', 'content': b'png'}], '2026-10-11T10:00:00+08:00')
        with self.assertRaises(ValueError): generate(client, job, Mock())
        self.assertEqual(generate(client, job, Mock()), 'synthetic reply')
        self.assertEqual(attempts.count('/pc/messages'), 1)
        self.assertEqual(attempts.count('/media/media1/analyze'), 1)

    def test_confirm_is_separate_and_idempotent(self):
        client = Mock()
        job = new_job('p', 'c', 'text', [], 'time')
        self.assertFalse(job['confirmed'])
        self.assertTrue(confirm_sent(client, job, 'final edited reply', 'sent-time'))
        self.assertFalse(confirm_sent(client, job, 'final edited reply', 'sent-time'))
        client.request.assert_called_once()
        self.assertEqual(client.request.call_args.args[2]['sender_type'], 'user')

    def test_uncertain_confirmation_cannot_change_payload(self):
        client = Mock(); client.request.side_effect = ValueError('timeout')
        job = new_job('p', 'c', 'text', [], 'time')
        with self.assertRaises(ValueError): confirm_sent(client, job, 'final', 'sent')
        with self.assertRaises(ValueError): confirm_sent(client, job, 'changed', 'sent')
        self.assertEqual(client.request.call_count, 1)

    def test_remote_http_and_credential_urls_rejected(self):
        for url in ('http://example.com', 'https://user:password@example.com', 'https://example.com/?token=private'):
            with self.assertRaises(ValueError): Client(url)
        self.assertEqual(Client('http://127.0.0.1:18080').base, 'http://127.0.0.1:18080')


if __name__ == '__main__':
    unittest.main()
