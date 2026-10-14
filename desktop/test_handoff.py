import unittest
from unittest.mock import Mock
from client import Client


class HandoffTests(unittest.TestCase):
    def test_logged_in_uses_ticket_not_session_token(self):
        client = Client('https://example.com', 'private-session')
        client.request = Mock(return_value={'ticket': 'a' * 43})
        self.assertEqual(client.browser_url(), 'https://example.com/app#desktop-login=' + 'a' * 43)
        client.request.assert_called_once_with('POST', '/auth/browser-handoff', timeout=15)
        self.assertNotIn(client.token, client.browser_url())

    def test_anonymous_and_invalid_response(self):
        client = Client('https://example.com')
        self.assertEqual(client.browser_url(), 'https://example.com/app')
        client.token = 'token'
        client.request = Mock(return_value={'ticket': 'https://attacker.invalid'})
        with self.assertRaises(ValueError): client.browser_url()


if __name__ == '__main__': unittest.main()
