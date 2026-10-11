import unittest
from unittest.mock import Mock, patch

import start_local as launcher
import windows_start


class CustomerEnvironmentTests(unittest.TestCase):
    @patch.object(windows_start.sys, "version_info", (3, 10))
    def test_old_python_rejected(self):
        self.assertEqual(windows_start.main(), 1)

    @patch.object(windows_start.importlib.metadata, "version", side_effect=windows_start.importlib.metadata.PackageNotFoundError)
    @patch.object(windows_start.subprocess, "run")
    def test_missing_dependencies_do_not_change_environment(self, run, version):
        self.assertEqual(windows_start.main(), 1)
        run.assert_not_called()

    @patch.object(windows_start.importlib.metadata, "version", return_value="installed")
    @patch.object(windows_start.Path, "exists", return_value=True)
    @patch.object(windows_start.subprocess, "run")
    @patch.object(launcher, "main", return_value=0)
    def test_existing_configuration_not_reinitialized(self, launch, run, exists, version):
        self.assertEqual(windows_start.main(), 0)
        run.assert_not_called()
        launch.assert_called_once()

    @patch.object(windows_start.importlib.metadata, "version", return_value="installed")
    @patch.object(windows_start.Path, "exists", return_value=False)
    @patch.object(windows_start.subprocess, "run", return_value=Mock(returncode=1))
    @patch.object(launcher, "main")
    def test_initialization_refusal_stops_startup(self, launch, run, exists, version):
        self.assertEqual(windows_start.main(), 1)
        launch.assert_not_called()


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
