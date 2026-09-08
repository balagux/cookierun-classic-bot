import unittest
from unittest import mock

import cv2
import numpy as np

import actions
import bot


def _center(match):
    x, y, width, height = match
    return x + width // 2, y + height // 2


class _Mailbox:
    """State-machine double for the mailbox Lives-tab receive/send flow."""

    top_match = (150, 275, 53, 301)
    no_lives_match = (500, 300, 200, 60)
    all_done_match = (450, 280, 380, 50)
    confirm_match = (650, 405, 290, 101)

    def __init__(self, hearts=2, no_lives=False, stuck_confirm=False):
        self.hearts = hearts
        self.no_lives = no_lives
        self.stuck_confirm = stuck_confirm
        self.state = "leaderboard"
        self.receive_clicked = False
        self.confirm_hidden_until = -1
        self.all_visible_from = 10**9
        self.capture_index = 0
        self.taps = []
        self.bright_screen = np.full((720, 1280, 3), 225, dtype=np.uint8)
        self.dim_screen = np.full((720, 1280, 3), 70, dtype=np.uint8)

    def capture(self):
        self.capture_index += 1
        if self.state in ("leaderboard", "closed"):
            return self.bright_screen
        return self.dim_screen

    def detect(self, _screen, templates, _region):
        if templates == actions.FRIEND_TOP_LEADERBOARD_TEMPLATE:
            return [self.top_match] if self.state in ("leaderboard", "closed") else []
        if templates == actions.NO_LIVES_TO_RECEIVE_TEMPLATE:
            if self.no_lives and self.state == "mailbox":
                return [self.no_lives_match]
            return []
        if templates == actions.ALL_LIVES_RECEIVED_AND_SENT_TEMPLATE:
            if (
                self.receive_clicked
                and self.hearts == 0
                and self.capture_index >= self.all_visible_from
            ):
                return [self.all_done_match]
            return []
        if templates == actions.CONFIRM_SEND_LIFE_TEMPLATE:
            if self.stuck_confirm and self.receive_clicked:
                return [self.confirm_match]
            if (
                self.receive_clicked
                and self.hearts > 0
                and self.state == "mailbox"
                and self.capture_index > self.confirm_hidden_until
            ):
                return [self.confirm_match]
            return []
        return []

    def tap(self, x, y):
        point = (x, y)
        self.taps.append(point)
        if point == tuple(actions.MAIL_BOX_BUTTON):
            if self.no_lives or self.hearts == 0:
                self.state = "mailbox"
            else:
                self.state = "mailbox"
        elif point == tuple(actions.QUICK_RECEIVE_AND_SEND_LIVES_BUTTON):
            self.receive_clicked = True
            self.confirm_hidden_until = self.capture_index + 1
            if self.stuck_confirm:
                self.confirm_hidden_until = -1
        elif point == _center(self.confirm_match):
            self.hearts -= 1
            self.confirm_hidden_until = self.capture_index + 1
            if self.hearts == 0:
                self.all_visible_from = self.capture_index + 1
            if self.stuck_confirm:
                # The confirm never clears in the stuck scenario.
                self.hearts += 1
        elif point == _center(self.all_done_match):
            self.state = "mailbox"  # accept keeps us inside the mailbox
        elif point == tuple(actions.MAIL_BOX_CLOSE_BUTTON):
            self.state = "closed"


class MailboxHeartsActionTests(unittest.TestCase):
    def setUp(self):
        self.print_patcher = mock.patch("builtins.print")
        self.print_patcher.start()

    def tearDown(self):
        self.print_patcher.stop()

    def test_receives_and_confirms_each_heart_then_closes(self):
        mailbox = _Mailbox(hearts=2)

        processed = actions.handle_mailbox_receive_and_send_lives(
            capture_func=mailbox.capture,
            detect_func=mailbox.detect,
            tap_func=mailbox.tap,
            sleep_func=lambda _seconds: None,
        )

        self.assertEqual(processed, 2)
        self.assertIn(tuple(actions.MAIL_BOX_BUTTON), mailbox.taps)
        self.assertIn(tuple(actions.MAIL_BOX_LIVES_TAB_BUTTON), mailbox.taps)
        self.assertIn(tuple(actions.QUICK_RECEIVE_AND_SEND_LIVES_BUTTON), mailbox.taps)
        self.assertIn(_center(mailbox.confirm_match), mailbox.taps)
        self.assertIn(_center(mailbox.all_done_match), mailbox.taps)
        self.assertEqual(mailbox.taps[-1], tuple(actions.MAIL_BOX_CLOSE_BUTTON))

    def test_no_lives_closes_without_pressing_receive_all(self):
        mailbox = _Mailbox(hearts=0, no_lives=True)

        processed = actions.handle_mailbox_receive_and_send_lives(
            capture_func=mailbox.capture,
            detect_func=mailbox.detect,
            tap_func=mailbox.tap,
            sleep_func=lambda _seconds: None,
        )

        self.assertEqual(processed, 0)
        self.assertNotIn(
            tuple(actions.QUICK_RECEIVE_AND_SEND_LIVES_BUTTON),
            mailbox.taps,
        )
        self.assertEqual(mailbox.taps[-1], tuple(actions.MAIL_BOX_CLOSE_BUTTON))

    def test_rejects_when_friends_leaderboard_is_not_open(self):
        mailbox = _Mailbox(hearts=2)
        mailbox.state = "mailbox"  # no leaderboard visible before the first tap

        with self.assertRaisesRegex(RuntimeError, "Friends leaderboard"):
            actions.handle_mailbox_receive_and_send_lives(
                capture_func=mailbox.capture,
                detect_func=mailbox.detect,
                tap_func=mailbox.tap,
                sleep_func=lambda _seconds: None,
            )

        self.assertEqual(mailbox.taps, [])

    def test_stops_safely_when_mailbox_never_opens(self):
        mailbox = _Mailbox(hearts=2)
        mailbox.state = "leaderboard"

        def stuck_tap(x, y):
            mailbox.taps.append((x, y))

        with self.assertRaisesRegex(RuntimeError, "mailbox window did not open"):
            actions.handle_mailbox_receive_and_send_lives(
                capture_func=mailbox.capture,
                detect_func=mailbox.detect,
                tap_func=stuck_tap,
                sleep_func=lambda _seconds: None,
                max_open_attempts=2,
            )

        self.assertEqual(mailbox.state, "leaderboard")

    def test_stops_safely_when_confirm_never_clears(self):
        mailbox = _Mailbox(hearts=2, stuck_confirm=True)

        with self.assertRaisesRegex(RuntimeError, "did not clear"):
            actions.handle_mailbox_receive_and_send_lives(
                capture_func=mailbox.capture,
                detect_func=mailbox.detect,
                tap_func=mailbox.tap,
                sleep_func=lambda _seconds: None,
                confirm_poll_attempts=2,
            )


class MailboxHeartsBotEntryTests(unittest.TestCase):
    def setUp(self):
        self.print_patcher = mock.patch("builtins.print")
        self.print_patcher.start()

    def tearDown(self):
        self.print_patcher.stop()

    def test_one_shot_mailbox_worker_runs_on_main_screen(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        with (
            mock.patch.object(bot, "DEVICE_IP", "127.0.0.1"),
            mock.patch.object(bot, "DEVICE_PORT", 5555),
            mock.patch.object(actions, "DEVICE_IP", "127.0.0.1"),
            mock.patch.object(actions, "DEVICE_PORT", 5555),
            mock.patch.object(bot, "device_connect") as connect,
            mock.patch.object(bot, "device_capture_screen", return_value=screen),
            mock.patch.object(bot, "load_templates") as load_templates,
            mock.patch.object(bot, "detect_stage", return_value="MAINMENU") as detect_main,
            mock.patch.object(
                bot,
                "handle_mailbox_receive_and_send_lives",
                return_value=3,
            ) as receive,
        ):
            processed = bot.receive_and_send_mailbox_hearts("127.0.0.9", 5566)

        self.assertEqual(processed, 3)
        connect.assert_called_once_with("127.0.0.9", 5566)
        load_templates.assert_called_once_with()
        detect_main.assert_called_once_with(screen, ("MAINMENU",))
        receive.assert_called_once_with()

    def test_one_shot_mailbox_worker_rejects_non_main_screen(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        with (
            mock.patch.object(bot, "DEVICE_IP", "127.0.0.1"),
            mock.patch.object(bot, "DEVICE_PORT", 5555),
            mock.patch.object(actions, "DEVICE_IP", "127.0.0.1"),
            mock.patch.object(actions, "DEVICE_PORT", 5555),
            mock.patch.object(bot, "device_connect"),
            mock.patch.object(bot, "device_capture_screen", return_value=screen),
            mock.patch.object(bot, "load_templates"),
            mock.patch.object(bot, "detect_stage", return_value=None),
            mock.patch.object(bot, "handle_mailbox_receive_and_send_lives") as receive,
        ):
            with self.assertRaisesRegex(RuntimeError, "Main/Friends leaderboard"):
                bot.receive_and_send_mailbox_hearts("127.0.0.9", 5566)

        receive.assert_not_called()


class MailboxEntryBrightnessTests(unittest.TestCase):
    def test_dimmed_leaderboard_is_not_a_ready_mailbox_entry(self):
        match = (150, 275, 53, 301)
        bright = np.full((720, 1280, 3), 225, dtype=np.uint8)
        dimmed = np.full((720, 1280, 3), 70, dtype=np.uint8)
        detect = lambda _screen, _templates, _region: [match]

        self.assertTrue(actions._mailbox_entry_visible(bright, detect))
        self.assertFalse(actions._mailbox_entry_visible(dimmed, detect))
        self.assertFalse(actions._mailbox_entry_visible(None, detect))


if __name__ == "__main__":
    unittest.main()
