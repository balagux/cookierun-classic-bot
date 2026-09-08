import io
import unittest
from unittest import mock

import numpy as np

import actions
import bot
import config


def _options():
    return {
        "use_fast_start": False,
        "use_cookie_relay": False,
        "use_desired_random_boost": False,
        "desired_boost_template": None,
        "desired_boost_name": None,
        "claim_relic_rewards": True,
        "max_runs": 0,
    }


class PopupBrightnessTests(unittest.TestCase):
    def test_main_menu_start_area_is_dark_when_overlay_is_dimmed(self):
        bright = np.full((720, 1280, 3), 225, dtype=np.uint8)
        dimmed = np.full((720, 1280, 3), 70, dtype=np.uint8)

        self.assertTrue(actions.main_menu_start_area_clear(bright))
        self.assertFalse(actions.main_menu_start_area_clear(dimmed))
        self.assertFalse(actions.main_menu_start_area_clear(None))

    def test_region_brightness_handles_partial_overlap(self):
        tiny = np.zeros((10, 10, 3), dtype=np.uint8)
        self.assertEqual(actions._region_mean_brightness(tiny, (-5, -5, 5, 5)), 0.0)


class CloseAnnouncementDialogTests(unittest.TestCase):
    def setUp(self):
        self.print_patcher = mock.patch("builtins.print")
        self.print_patcher.start()

    def tearDown(self):
        self.print_patcher.stop()

    def test_returns_true_when_first_x_candidate_closes_popup(self):
        bright_screen = np.full((720, 1280, 3), 225, dtype=np.uint8)
        with (
            mock.patch.object(actions, "safe_device_tap"),
            mock.patch.object(
                actions,
                "device_capture_screen",
                return_value=bright_screen,
            ),
            mock.patch.object(actions, "detect_stage", return_value=None) as detect,
            mock.patch.object(actions, "device_back") as back,
        ):
            closed = actions.close_announcement_dialog()

        self.assertTrue(closed)
        back.assert_not_called()
        self.assertGreaterEqual(detect.call_count, 1)

    def test_tries_every_candidate_then_back_when_popup_stays(self):
        dim_screen = np.full((720, 1280, 3), 70, dtype=np.uint8)
        with (
            mock.patch.object(actions, "safe_device_tap") as tap,
            mock.patch.object(
                actions,
                "device_capture_screen",
                return_value=dim_screen,
            ),
            mock.patch.object(
                actions,
                "detect_stage",
                return_value="ANNOUNCEMENT",
            ),
            mock.patch.object(actions, "device_back") as back,
            mock.patch.object(actions, "save_debug_screen") as save_debug,
        ):
            closed = actions.close_announcement_dialog()

        self.assertFalse(closed)
        expected_candidates = {
            *actions.POPUP_CLOSE_X_CANDIDATES,
            actions.CLOSE_ANNOUNCEMENT_DIALOG_BUTTON,
            actions.NEWS_CLOSE_BUTTON,
        }
        self.assertEqual(tap.call_count, len(expected_candidates))
        back.assert_called_once()
        save_debug.assert_called_once()


class CloseNewsDialogTests(unittest.TestCase):
    def setUp(self):
        self.print_patcher = mock.patch("builtins.print")
        self.print_patcher.start()

    def tearDown(self):
        self.print_patcher.stop()

    def test_news_popup_detected_taps_dedicated_close_button(self):
        bright_screen = np.full((720, 1280, 3), 225, dtype=np.uint8)
        with (
            mock.patch.object(actions, "safe_device_tap") as tap,
            mock.patch.object(
                actions,
                "device_capture_screen",
                return_value=bright_screen,
            ),
            mock.patch.object(
                actions,
                "detect_stage",
                side_effect=[
                    "NEWS",   # before close
                    None,     # after close (cleared with the first capture)
                ],
            ),
        ):
            closed = actions.close_news_dialog()

        self.assertTrue(closed)
        tap.assert_called_once_with(
            actions.DEVICE_IP,
            actions.DEVICE_PORT,
            actions.NEWS_CLOSE_BUTTON[0],
            actions.NEWS_CLOSE_BUTTON[1],
        )

    def test_news_popup_returns_true_when_not_detected(self):
        bright_screen = np.full((720, 1280, 3), 225, dtype=np.uint8)
        with (
            mock.patch.object(actions, "safe_device_tap") as tap,
            mock.patch.object(
                actions,
                "device_capture_screen",
                return_value=bright_screen,
            ),
            mock.patch.object(actions, "detect_stage", return_value=None),
        ):
            closed = actions.close_news_dialog()

        self.assertTrue(closed)
        tap.assert_not_called()

    def test_news_popup_falls_back_to_announcement_sweep_on_failure(self):
        dim_screen = np.full((720, 1280, 3), 70, dtype=np.uint8)
        with (
            mock.patch.object(actions, "safe_device_tap"),
            mock.patch.object(
                actions,
                "device_capture_screen",
                return_value=dim_screen,
            ),
            mock.patch.object(
                actions,
                "detect_stage",
                return_value="NEWS",  # stays detected after the X tap
            ),
            mock.patch.object(actions, "close_announcement_dialog") as fallback,
        ):
            fallback.return_value = False
            closed = actions.close_news_dialog()

        self.assertFalse(closed)
        fallback.assert_called_once()

    def test_news_stage_is_in_all_detection_groups(self):
        for group in ("PRE_GAME", "IN_GAME", "POST_GAME"):
            self.assertIn("NEWS", bot.get_detection_stage_names(group))
        self.assertIn("NEWS", config.DETECTION_ALWAYS_STAGES)


class DismissOverlayOverMainMenuTests(unittest.TestCase):
    def setUp(self):
        self.print_patcher = mock.patch("builtins.print")
        self.print_patcher.start()

    def tearDown(self):
        self.print_patcher.stop()

    def test_returns_true_immediately_when_start_area_is_clear(self):
        bright_screen = np.full((720, 1280, 3), 225, dtype=np.uint8)
        with (
            mock.patch.object(
                actions,
                "device_capture_screen",
                return_value=bright_screen,
            ),
            mock.patch.object(actions, "safe_device_tap") as tap,
            mock.patch.object(actions, "device_back") as back,
        ):
            cleared = actions.dismiss_overlay_over_main_menu()

        self.assertTrue(cleared)
        tap.assert_not_called()
        back.assert_not_called()

    def test_x_candidates_restore_bright_start_area(self):
        dim_screen = np.full((720, 1280, 3), 70, dtype=np.uint8)
        bright_screen = np.full((720, 1280, 3), 225, dtype=np.uint8)
        captures = iter([dim_screen, bright_screen])

        with (
            mock.patch.object(
                actions,
                "device_capture_screen",
                side_effect=lambda *_args: next(captures),
            ),
            mock.patch.object(actions, "safe_device_tap") as tap,
            mock.patch.object(actions, "device_back") as back,
        ):
            cleared = actions.dismiss_overlay_over_main_menu()

        self.assertTrue(cleared)
        self.assertEqual(tap.call_count, 1)
        back.assert_not_called()

    def test_returns_false_and_saves_screenshot_when_still_dim(self):
        dim_screen = np.full((720, 1280, 3), 70, dtype=np.uint8)
        with (
            mock.patch.object(
                actions,
                "device_capture_screen",
                return_value=dim_screen,
            ),
            mock.patch.object(actions, "safe_device_tap"),
            mock.patch.object(actions, "device_back"),
            mock.patch.object(actions, "save_debug_screen") as save_debug,
        ):
            cleared = actions.dismiss_overlay_over_main_menu()

        self.assertFalse(cleared)
        save_debug.assert_called_once()


class MainMenuStartStallGuardTests(unittest.TestCase):
    def test_main_loop_resets_app_after_repeated_start_stalls(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        output = io.StringIO()
        with (
            mock.patch.object(bot, "device_connect"),
            mock.patch.object(bot, "device_capture_screen", return_value=screen),
            mock.patch.object(bot, "load_templates"),
            mock.patch.object(bot, "detect_all_template_matches", return_value=[]),
            # MAINMENU keeps coming back after start_game() was pressed.
            mock.patch.object(
                bot,
                "detect_stage",
                side_effect=[
                    "MAINMENU",
                    "MAINMENU",
                    "MAINMENU",
                    KeyboardInterrupt(),
                ],
            ),
            mock.patch.object(bot, "start_game"),
            mock.patch.object(
                bot.actions_module,
                "dismiss_overlay_over_main_menu",
                return_value=False,
            ) as dismiss,
            mock.patch.object(bot, "device_reset_app", return_value=True) as reset,
            mock.patch.object(bot, "close_announcement_dialog"),
            mock.patch.object(bot, "save_debug_screen"),
            mock.patch.object(bot.time, "sleep"),
            mock.patch("sys.stdout", output),
        ):
            bot.main(_options())

        dismiss.assert_called()
        reset.assert_called()

    def test_clean_main_menu_starts_without_overlay_dismissal(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        with (
            mock.patch.object(bot, "device_connect"),
            mock.patch.object(bot, "device_capture_screen", return_value=screen),
            mock.patch.object(bot, "load_templates"),
            mock.patch.object(bot, "detect_all_template_matches", return_value=[]),
            mock.patch.object(
                bot,
                "detect_stage",
                side_effect=["MAINMENU", KeyboardInterrupt()],
            ),
            mock.patch.object(bot, "start_game") as start,
            mock.patch.object(
                bot.actions_module,
                "dismiss_overlay_over_main_menu",
            ) as dismiss,
            mock.patch.object(bot, "device_back"),
            mock.patch.object(bot.time, "sleep"),
            mock.patch("sys.stdout", io.StringIO()),
        ):
            bot.main(_options())

        start.assert_called()
        dismiss.assert_not_called()

    def test_announcement_popup_that_cannot_close_resets_app(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        output = io.StringIO()
        with (
            mock.patch.object(bot, "device_connect"),
            mock.patch.object(bot, "device_capture_screen", return_value=screen),
            mock.patch.object(bot, "load_templates"),
            mock.patch.object(bot, "detect_all_template_matches", return_value=[]),
            mock.patch.object(
                bot,
                "detect_stage",
                side_effect=[
                    "ANNOUNCEMENT",
                    "ANNOUNCEMENT",
                    "ANNOUNCEMENT",
                    KeyboardInterrupt(),
                ],
            ),
            mock.patch.object(
                bot,
                "close_announcement_dialog",
                return_value=False,
            ),
            mock.patch.object(bot, "device_reset_app", return_value=True) as reset,
            mock.patch.object(bot, "save_debug_screen"),
            mock.patch.object(bot.time, "sleep"),
            mock.patch("sys.stdout", output),
        ):
            bot.main(_options())

        reset.assert_called()


if __name__ == "__main__":
    unittest.main()
