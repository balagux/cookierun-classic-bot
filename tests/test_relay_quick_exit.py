import unittest
from unittest import mock

import cv2
import numpy as np

import actions
from bot import should_process_cookie_relay, should_quick_exit_after_relay


class RelayQuickExitTests(unittest.TestCase):
    def test_relay_is_ignored_before_a_game_run_starts(self):
        self.assertFalse(
            should_process_cookie_relay(
                {"use_cookie_relay": True},
                run_in_progress=False,
            )
        )
        self.assertTrue(
            should_process_cookie_relay(
                {"use_cookie_relay": True},
                run_in_progress=True,
            )
        )

    def test_enabled_only_when_cookie_relay_is_selected(self):
        self.assertTrue(
            should_quick_exit_after_relay(
                {"use_cookie_relay": True, "quick_exit_after_relay": True}
            )
        )
        self.assertFalse(
            should_quick_exit_after_relay({"use_cookie_relay": False})
        )

    def test_can_wait_for_the_second_cookie_to_die_naturally(self):
        self.assertFalse(
            should_quick_exit_after_relay(
                {
                    "use_cookie_relay": True,
                    "quick_exit_after_relay": False,
                }
            )
        )

    def test_missing_quick_exit_option_is_safe_by_default(self):
        self.assertTrue(
            should_quick_exit_after_relay(
                {"use_cookie_relay": True, "quick_exit_after_relay": True}
            )
        )
        self.assertFalse(should_quick_exit_after_relay({"use_cookie_relay": True}))

    def test_waits_for_relay_to_disappear_then_taps_pause_and_quit(self):
        with (
            mock.patch.object(actions.time, "monotonic", side_effect=(0.0, 1.0)),
            mock.patch.object(actions.time, "sleep") as sleep,
            mock.patch.object(
                actions,
                "device_capture_screen",
                return_value=np.zeros((720, 1280, 3), dtype=np.uint8),
            ),
            mock.patch.object(actions, "detect_templates", return_value=[]),
            mock.patch.object(actions, "_wait_for_quit_button", side_effect=(True, True)),
            mock.patch.object(actions, "device_tap") as tap,
            mock.patch("builtins.print"),
        ):
            succeeded = actions.quick_exit_after_cookie_relay()

        self.assertTrue(succeeded)
        self.assertEqual(
            [call.args[2:] for call in tap.call_args_list],
            [
                actions.PAUSE_GAME_BUTTON,
                actions.QUIT_GAME_BUTTON,
                actions.CONFIRM_QUIT_BUTTON,
            ],
        )
        sleep.assert_has_calls(
            [
                mock.call(actions.RELAY_QUICK_EXIT_MIN_WAIT),
                mock.call(actions.RELAY_QUICK_EXIT_RUNOUT_BUFFER),
                mock.call(0.12),
                mock.call(0.12),
                mock.call(0.5),
            ]
        )

    def test_start_banner_cancels_quick_exit_without_tapping_quit(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        x1, y1, x2, y2 = actions.STAGE_GAME_RELAY_REGION
        screen[y1:y2, x1:x2] = 220
        with (
            mock.patch.object(actions.time, "sleep"),
            mock.patch.object(actions, "device_capture_screen", return_value=screen),
            mock.patch.object(actions, "detect_templates", return_value=[]),
            mock.patch.object(actions, "device_tap") as tap,
            mock.patch("builtins.print"),
        ):
            succeeded = actions.quick_exit_after_cookie_relay()

        self.assertFalse(succeeded)
        tap.assert_not_called()

    def test_relay_click_can_skip_the_old_random_wait(self):
        with (
            mock.patch.object(actions, "safe_device_tap") as tap,
            mock.patch.object(actions.time, "sleep") as sleep,
            mock.patch("builtins.print"),
        ):
            actions.using_cookie_relay(wait_after=False)

        tap.assert_called_once()
        sleep.assert_not_called()

    def test_quit_readiness_requires_a_large_cyan_button(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        self.assertFalse(
            actions._is_cyan_quit_button_visible(
                screen,
                actions.PAUSE_QUIT_BUTTON_REGION,
            )
        )
        x1, y1, x2, y2 = actions.PAUSE_QUIT_BUTTON_REGION
        hsv_color = np.uint8([[[92, 220, 220]]])
        cyan = tuple(int(value) for value in cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0, 0])
        screen[y1:y2, x1:x2] = cyan
        self.assertTrue(
            actions._is_cyan_quit_button_visible(
                screen,
                actions.PAUSE_QUIT_BUTTON_REGION,
            )
        )


if __name__ == "__main__":
    unittest.main()
