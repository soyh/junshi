import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from preferences import OFFICIAL_SERVER, load_server, save_server


class PreferencesTests(unittest.TestCase):
    def test_only_address_is_persisted_and_invalid_url_refused(self):
        with tempfile.TemporaryDirectory() as directory, patch('preferences.settings_path',return_value=Path(directory)/'settings.json'):
            self.assertEqual(load_server(),OFFICIAL_SERVER)
            save_server('https://example.com/')
            self.assertEqual(load_server(),'https://example.com')
            data=json.loads((Path(directory)/'settings.json').read_text())
            self.assertEqual(data,{'server':'https://example.com'})
            with self.assertRaises(ValueError):save_server('https://user:password@example.com')
            self.assertEqual(load_server(),'https://example.com')


if __name__ == '__main__':unittest.main()
