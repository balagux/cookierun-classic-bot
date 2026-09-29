import unittest
from unittest import mock

import gui


class GuiProcessTreeTests(unittest.TestCase):
    def _instance(self):
        return gui.CookieRunBotGUI.__new__(gui.CookieRunBotGUI)

    def test_windows_stop_kills_the_complete_worker_tree(self):
        process = mock.Mock(pid=4321)
        taskkill_result = mock.Mock(returncode=0)
        with (
            mock.patch.object(gui.os, "name", "nt"),
            mock.patch.object(gui.subprocess, "run", return_value=taskkill_result) as run,
        ):
            self._instance()._terminate_process(process)

        command = run.call_args.args[0]
        self.assertEqual(command, ["taskkill", "/PID", "4321", "/T", "/F"])
        process.wait.assert_called_once_with(timeout=2)
        process.terminate.assert_not_called()
        process.kill.assert_not_called()

    def test_windows_taskkill_failure_falls_back_to_direct_terminate(self):
        process = mock.Mock(pid=9876)
        taskkill_result = mock.Mock(returncode=1)
        with (
            mock.patch.object(gui.os, "name", "nt"),
            mock.patch.object(gui.subprocess, "run", return_value=taskkill_result),
        ):
            self._instance()._terminate_process(process)

        process.terminate.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=5)

    def test_window_close_uses_the_same_tree_termination_path(self):
        app = self._instance()
        app.process = mock.Mock()
        app.process.poll.return_value = None
        app.process_mode = "bot"
        app.root = mock.Mock()
        app._save_settings = mock.Mock()
        app._terminate_process = mock.Mock()

        with mock.patch.object(gui.messagebox, "askyesno", return_value=True):
            app._on_close()

        app._terminate_process.assert_called_once_with(app.process)
        app.root.destroy.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
