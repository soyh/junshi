import unittest
from unittest.mock import Mock, patch

import start_local as launcher


class LauncherTests(unittest.TestCase):
    @patch.object(launcher, "open_page")
    @patch.object(launcher, "ready", return_value=True)
    @patch.object(launcher, "port_in_use", return_value=True)
    @patch.object(launcher.subprocess, "Popen")
    def test_repeated_start_opens_existing_service(self, spawn, occupied, ready, page):
        self.assertEqual(launcher.launch("127.0.0.1", 18081, "app"), 0)
        spawn.assert_not_called()
        page.assert_called_once_with("http://127.0.0.1:18081/app")

    @patch.object(launcher, "open_page")
    @patch.object(launcher, "ready", return_value=False)
    @patch.object(launcher, "port_in_use", return_value=True)
    @patch.object(launcher.subprocess, "Popen")
    def test_occupied_port_does_not_open_or_stop_other_service(self, spawn, occupied, ready, page):
        self.assertEqual(launcher.launch("127.0.0.1", 18080, "app"), 1)
        spawn.assert_not_called()
        page.assert_not_called()

    @patch.object(launcher, "open_page")
    @patch.object(launcher, "ready", return_value=True)
    @patch.object(launcher, "port_in_use", return_value=False)
    @patch.object(launcher.subprocess, "Popen")
    def test_ready_opens_browser_then_waits_for_server(self, spawn, occupied, ready, page):
        process = spawn.return_value
        process.poll.side_effect = [None, 0]
        process.wait.return_value = 0
        self.assertEqual(launcher.launch("127.0.0.1", 18080, "app"), 0)
        page.assert_called_once_with("http://127.0.0.1:18080/app")
        process.terminate.assert_not_called()

    @patch.object(launcher, "open_page")
    @patch.object(launcher, "port_in_use", return_value=False)
    @patch.object(launcher.subprocess, "Popen")
    def test_timeout_cleans_up_only_new_child(self, spawn, occupied, page):
        spawn.return_value.poll.return_value = None
        self.assertEqual(launcher.launch("127.0.0.1", 18080, "app", timeout=0), 1)
        spawn.return_value.terminate.assert_called_once()
        page.assert_not_called()


if __name__ == "__main__":
    unittest.main()
