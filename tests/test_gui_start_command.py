import json
import queue
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from gui import CookieRunBotGUI


class _Value:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _Combo:
    def __init__(self, index):
        self.index = index

    def current(self, index=None):
        if index is not None:
            self.index = index
        return self.index


class GuiStartCommandTests(unittest.TestCase):
    def test_start_keeps_item_options_without_any_recorder_arguments(self):
        gui = object.__new__(CookieRunBotGUI)
        gui.process = None
        gui.fast_start_var = _Value(True)
        gui.cookie_relay_var = _Value(True)
        gui.relay_quick_exit_var = _Value(True)
        gui.use_boost_var = _Value(True)
        gui.claim_relic_rewards_var = _Value(False)
        gui.max_runs_var = _Value("7")
        gui.boost_combo = _Combo(2)
        gui._base_command = lambda mode: ["worker", mode]

        launched = []
        gui._launch_process = lambda command, mode: launched.append((command, mode))

        gui._start_bot()

        self.assertEqual(len(launched), 1)
        command, mode = launched[0]
        self.assertEqual(mode, "bot")
        self.assertIn("--fast-start", command)
        self.assertIn("--cookie-relay", command)
        self.assertNotIn("--wait-relay-death", command)
        self.assertEqual(command[command.index("--boost-index") + 1], "3")
        self.assertEqual(command[command.index("--max-runs") + 1], "7")
        self.assertIn("--keep-relic-parts", command)
        command_text = " ".join(command).lower()
        for removed_option in ("record", "replay", "profile", "ldplayer"):
            self.assertNotIn(removed_option, command_text)

    def test_relic_auto_claim_default_does_not_send_keep_parts_flag(self):
        gui = object.__new__(CookieRunBotGUI)
        gui.fast_start_var = _Value(False)
        gui.cookie_relay_var = _Value(False)
        gui.relay_quick_exit_var = _Value(True)
        gui.use_boost_var = _Value(False)
        gui.claim_relic_rewards_var = _Value(True)
        gui.boost_combo = _Combo(0)
        command = []

        gui._append_play_options(command)

        self.assertNotIn("--keep-relic-parts", command)

    def test_disabling_relay_quick_exit_waits_for_natural_death(self):
        gui = object.__new__(CookieRunBotGUI)
        gui.fast_start_var = _Value(False)
        gui.cookie_relay_var = _Value(True)
        gui.relay_quick_exit_var = _Value(False)
        gui.use_boost_var = _Value(False)
        gui.claim_relic_rewards_var = _Value(True)
        gui.boost_combo = _Combo(0)
        command = []

        gui._append_play_options(command)

        self.assertIn("--cookie-relay", command)
        self.assertIn("--wait-relay-death", command)

    def test_relay_death_option_is_ignored_when_cookie_relay_is_off(self):
        gui = object.__new__(CookieRunBotGUI)
        gui.fast_start_var = _Value(False)
        gui.cookie_relay_var = _Value(False)
        gui.relay_quick_exit_var = _Value(False)
        gui.use_boost_var = _Value(False)
        gui.claim_relic_rewards_var = _Value(True)
        gui.boost_combo = _Combo(0)
        command = []

        gui._append_play_options(command)

        self.assertNotIn("--cookie-relay", command)
        self.assertNotIn("--wait-relay-death", command)

    def test_relay_quick_exit_setting_defaults_on_and_is_persisted(self):
        gui = object.__new__(CookieRunBotGUI)
        gui.ip_var = _Value("127.0.0.1")
        gui.port_var = _Value("5555")
        gui.fast_start_var = _Value(False)
        gui.cookie_relay_var = _Value(False)
        gui.relay_quick_exit_var = _Value(False)
        gui.use_boost_var = _Value(False)
        gui.claim_relic_rewards_var = _Value(True)
        gui.max_runs_var = _Value("0")
        gui.boost_combo = _Combo(0)
        gui._append_log = mock.Mock()

        with tempfile.TemporaryDirectory() as directory:
            settings_file = Path(directory) / "gui_settings.json"
            settings_file.write_text("{}", encoding="utf-8")
            with mock.patch("gui.SETTINGS_FILE", settings_file):
                gui._load_settings()
                self.assertTrue(gui.relay_quick_exit_var.get())

                gui.relay_quick_exit_var.set(False)
                gui._save_settings()

            saved = json.loads(settings_file.read_text(encoding="utf-8"))
            self.assertFalse(saved["relay_quick_exit"])

    def test_send_hearts_uses_separate_worker_without_play_options(self):
        gui = object.__new__(CookieRunBotGUI)
        gui.process = None
        gui._base_command = lambda mode: ["worker", mode]
        gui._append_log = lambda _line: None

        launched = []
        gui._launch_process = lambda command, mode: launched.append((command, mode))

        gui._send_hearts()

        self.assertEqual(launched, [(["worker", "--send-hearts"], "hearts")])
        command_text = " ".join(launched[0][0])
        for play_option in ("--fast-start", "--cookie-relay", "--boost-index", "--max-runs"):
            self.assertNotIn(play_option, command_text)

    def test_heart_logs_cannot_change_play_session_stats(self):
        gui = object.__new__(CookieRunBotGUI)
        gui.events = queue.Queue()
        gui.events.put(("log", "[STATS] attempts=9 completed=9 coins=999 exp=999 [HEARTS] sent=12\n"))
        gui.process_mode = "hearts"
        gui._heart_sent_count = None
        gui.root = mock.Mock()
        gui._append_log = mock.Mock()
        gui._update_session_stats = mock.Mock()

        gui._poll_events()

        gui._append_log.assert_called_once()
        gui._update_session_stats.assert_not_called()
        self.assertEqual(gui._heart_sent_count, 12)
        gui.root.after.assert_called_once_with(100, gui._poll_events)

    def test_heart_worker_exit_reports_success_error_and_user_stop(self):
        cases = (
            (0, False, 7, "ส่งหัวใจแล้ว 7 คน", "success"),
            (1, False, None, "ส่งหัวใจไม่สำเร็จ", "error"),
            (1, True, None, "หยุดส่งหัวใจแล้ว", "idle"),
        )
        for return_code, stop_requested, heart_count, expected_text, expected_kind in cases:
            with self.subTest(return_code=return_code, stop_requested=stop_requested):
                gui = object.__new__(CookieRunBotGUI)
                process = object()
                gui.events = queue.Queue()
                gui.events.put(("bot_exit", (process, return_code)))
                gui.process = process
                gui.process_mode = "hearts"
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


if __name__ == "__main__":
    unittest.main()
