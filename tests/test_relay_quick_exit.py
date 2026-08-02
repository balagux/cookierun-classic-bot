import unittest
from unittest import mock

import actions
from bot import should_quick_exit_after_relay


class RelayQuickExitTests(unittest.TestCase):
    def test_enabled_for_bot_but_not_profile_recording(self):
        self.assertTrue(
            should_quick_exit_after_relay(
                {"use_cookie_relay": True, "record_profile": None}
            )
        )
        self.assertFalse(
            should_quick_exit_after_relay(
                {"use_cookie_relay": True, "record_profile": "run.json"}
            )
        )
        self.assertFalse(
            should_quick_exit_after_relay(
                {"use_cookie_relay": False, "record_profile": None}
            )
        )

    def test_waits_for_relay_to_disappear_then_taps_pause_and_quit(self):
        with (
            mock.patch.object(actions.time, "monotonic", side_effect=(0.0, 1.0)),
            mock.patch.object(actions.time, "sleep") as sleep,
            mock.patch.object(actions, "device_capture_screen", return_value=object()),
            mock.patch.object(actions, "detect_templates", return_value=[]),
            mock.patch.object(actions, "device_tap") as tap,
            mock.patch("builtins.print"),
        ):
            actions.quick_exit_after_cookie_relay()

        self.assertEqual(
            [call.args[2:] for call in tap.call_args_list],
            [actions.PAUSE_GAME_BUTTON, actions.QUIT_GAME_BUTTON],
        )
        sleep.assert_has_calls(
            [
                mock.call(actions.RELAY_QUICK_EXIT_MIN_WAIT),
                mock.call(actions.RELAY_QUICK_EXIT_RUNOUT_BUFFER),
                mock.call(0.22),
                mock.call(0.35),
            ]
        )

    def test_relay_click_can_skip_the_old_random_wait(self):
        with (
            mock.patch.object(actions, "safe_device_tap") as tap,
            mock.patch.object(actions.time, "sleep") as sleep,
            mock.patch("builtins.print"),
        ):
            actions.using_cookie_relay(wait_after=False)

        tap.assert_called_once()
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
