import unittest

from gui import CookieRunBotGUI


class _Value:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


class _Combo:
    def __init__(self, index):
        self.index = index

    def current(self):
        return self.index


class GuiStartCommandTests(unittest.TestCase):
    def test_start_keeps_item_options_without_any_recorder_arguments(self):
        gui = object.__new__(CookieRunBotGUI)
        gui.process = None
        gui.fast_start_var = _Value(True)
        gui.cookie_relay_var = _Value(True)
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
        gui.use_boost_var = _Value(False)
        gui.claim_relic_rewards_var = _Value(True)
        gui.boost_combo = _Combo(0)
        command = []

        gui._append_play_options(command)

        self.assertNotIn("--keep-relic-parts", command)


if __name__ == "__main__":
    unittest.main()
