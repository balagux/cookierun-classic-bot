import io
import unittest
from unittest import mock

import numpy as np

import bot


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


class FriendsLeaderboardDetectorTests(unittest.TestCase):
    def test_detects_leaderboard_when_templates_match(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        with mock.patch.object(
            bot, "detect_all_template_matches", return_value=[(1, 2, 3, 4)]
        ):
            self.assertTrue(bot._is_friends_leaderboard_open(screen))

    def test_returns_false_when_no_templates_match(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        with mock.patch.object(bot, "detect_all_template_matches", return_value=[]):
            self.assertFalse(bot._is_friends_leaderboard_open(screen))

    def test_returns_false_for_none_screen(self):
        self.assertFalse(bot._is_friends_leaderboard_open(None))


class MainMenuGuardTests(unittest.TestCase):
    def test_starts_immediately_when_main_menu_is_detected(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        output = io.StringIO()
        # MAINMENU is detected, then the loop is stopped. Starting the game must
        # not press BACK or depend on a Friends leaderboard being open.
        with (
            mock.patch.object(bot, "device_connect"),
            mock.patch.object(bot, "device_capture_screen", return_value=screen),
            mock.patch.object(bot, "load_templates"),
            mock.patch.object(bot, "detect_all_template_matches", return_value=[]),
            mock.patch.object(bot, "detect_stage", side_effect=["MAINMENU", KeyboardInterrupt()]),
            mock.patch.object(bot, "device_back") as back,
            mock.patch.object(bot, "start_game") as start,
            mock.patch.object(bot.time, "sleep"),
            mock.patch("sys.stdout", output),
        ):
            bot.main(_options())

        self.assertEqual(back.call_count, 0)
        self.assertGreaterEqual(start.call_count, 1)

    def test_starts_normally_when_leaderboard_is_absent(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        output = io.StringIO()
        with (
            mock.patch.object(bot, "device_connect"),
            mock.patch.object(bot, "device_capture_screen", return_value=screen),
            mock.patch.object(bot, "load_templates"),
            mock.patch.object(bot, "detect_all_template_matches", return_value=[]),
            mock.patch.object(bot, "detect_stage", side_effect=["MAINMENU", KeyboardInterrupt()]),
            mock.patch.object(bot, "_is_friends_leaderboard_open", return_value=False),
            mock.patch.object(bot, "device_back") as back,
            mock.patch.object(bot, "start_game") as start,
            mock.patch.object(bot.time, "sleep"),
            mock.patch("sys.stdout", output),
        ):
            bot.main(_options())

        self.assertEqual(back.call_count, 0)
        self.assertGreaterEqual(start.call_count, 1)


if __name__ == "__main__":
    unittest.main()
