import builtins
import importlib
import queue
import unittest
from unittest import mock

from gui import CookieRunBotGUI


class GuiMailboxStartCommandTests(unittest.TestCase):
    def test_send_mailbox_hearts_uses_separate_worker_without_play_options(self):
        gui = object.__new__(CookieRunBotGUI)
        gui.process = None
        gui._base_command = lambda mode: ["worker", mode]
        gui._append_log = lambda _line: None

        launched = []
        gui._launch_process = lambda command, mode: launched.append((command, mode))

        gui._send_mailbox_hearts()

        self.assertEqual(launched, [(["worker", "--mailbox-hearts"], "mailbox")])
        command_text = " ".join(launched[0][0])
        for play_option in ("--fast-start", "--cookie-relay", "--boost-index", "--max-runs"):
            self.assertNotIn(play_option, command_text)

    def test_mailbox_logs_cannot_change_play_session_stats(self):
        gui = object.__new__(CookieRunBotGUI)
        gui.events = queue.Queue()
        gui.events.put(
            ("log", "[STATS] attempts=9 completed=9 coins=999 exp=999 "
                    "[MAILBOX_HEARTS] processed=5\n")
        )
        gui.process_mode = "mailbox"
        gui._heart_sent_count = None
        gui.root = mock.Mock()
        gui._append_log = mock.Mock()
        gui._update_session_stats = mock.Mock()
        gui._update_box_stats = mock.Mock()

        gui._poll_events()

        gui._append_log.assert_called_once()
        gui._update_session_stats.assert_not_called()
        gui._update_box_stats.assert_not_called()
        self.assertEqual(gui._heart_sent_count, 5)
        gui.root.after.assert_called_once_with(100, gui._poll_events)

    def test_mailbox_worker_exit_reports_success_error_and_user_stop(self):
        cases = (
            (0, False, 5, "รับหัวใจจากกล่องจดหมายแล้ว 5 รายการ", "success"),
            (1, False, None, "รับหัวใจไม่สำเร็จ", "error"),
            (1, True, None, "หยุดรับหัวใจจากกล่องจดหมายแล้ว", "idle"),
        )
        for return_code, stop_requested, heart_count, expected_text, expected_kind in cases:
            with self.subTest(return_code=return_code, stop_requested=stop_requested):
                gui = object.__new__(CookieRunBotGUI)
                process = object()
                gui.events = queue.Queue()
                gui.events.put(("bot_exit", (process, return_code)))
                gui.process = process
                gui.process_mode = "mailbox"
                gui._heart_sent_count = heart_count
                gui.stop_requested = stop_requested
                gui.root = mock.Mock()
                gui._set_running_controls = mock.Mock()
                gui._set_status = mock.Mock()
                gui._append_log = mock.Mock()

                gui._poll_events()

                self.assertIsNone(gui.process)
                gui._set_running_controls.assert_called_once_with(False)
                gui._set_status.assert_called_once_with(expected_text, expected_kind)


class MainWorkerMailboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original_print = builtins.print
        cls.main_module = importlib.import_module("main")
        builtins.print = original_print

    def test_mailbox_hearts_mode_calls_one_shot_worker(self):
        with mock.patch.object(
            self.main_module,
            "receive_and_send_mailbox_hearts",
            return_value=3,
        ) as receive:
            exit_code = self.main_module.main(
                [
                    "--mailbox-hearts",
                    "--device-ip",
                    "127.0.0.9",
                    "--device-port",
                    "5566",
                ]
            )

        self.assertEqual(exit_code, 0)
        receive.assert_called_once_with(
            device_ip="127.0.0.9",
            device_port=5566,
        )

    def test_mailbox_hearts_exception_returns_error_instead_of_escaping(self):
        with (
            mock.patch.object(
                self.main_module,
                "receive_and_send_mailbox_hearts",
                side_effect=RuntimeError("open the Friends leaderboard"),
            ),
            mock.patch("builtins.print") as output,
        ):
            exit_code = self.main_module.main(["--mailbox-hearts"])

        self.assertEqual(exit_code, 1)
        self.assertTrue(
            any(
                "Mailbox hearts stopped safely" in str(call.args[0])
                and "open the Friends leaderboard" in str(call.args[0])
                for call in output.call_args_list
            )
        )


if __name__ == "__main__":
    unittest.main()
