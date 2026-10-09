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
        self.final_acknowledged = False
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
                and not self.final_acknowledged
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
        elif point == _center(self.all_done_match) or point == tuple(
            actions.ACCEPT_ALL_LIVES_RECEIVED_AND_SENT_BUTTON
        ):
            self.final_acknowledged = True
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
        self.assertIn(tuple(actions.ACCEPT_ALL_LIVES_RECEIVED_AND_SENT_BUTTON), mailbox.taps)
        self.assertEqual(mailbox.taps[-1], tuple(actions.MAIL_BOX_CLOSE_BUTTON))

    def test_final_all_done_dialog_must_actually_close_before_mailbox_exit(self):
        """Regression: the live final Confirm button is around y=460, not y=520."""
        mailbox = _Mailbox(hearts=1)
        final_confirm = (500, 410, 280, 96)
        final_confirm_center = _center(final_confirm)
        final_acknowledged = False
        original_tap = mailbox.tap

        def tap_with_real_final_modal(x, y):
            nonlocal final_acknowledged
            point = (x, y)
            mailbox.taps.append(point)

            final_modal_visible = (
                mailbox.receive_clicked
                and mailbox.hearts == 0
                and mailbox.capture_index >= mailbox.all_visible_from
                and not final_acknowledged
            )
            if final_modal_visible:
                if point == final_confirm_center:
                    final_acknowledged = True
                # While the modal is visible, taps behind it (including the
                # mailbox X) do nothing in the real game.
                return

            mailbox.taps.pop()
            original_tap(x, y)

        green_hsv = np.uint8([[[40, 210, 210]]])
        green_bgr = cv2.cvtColor(green_hsv, cv2.COLOR_HSV2BGR)[0, 0]

        def capture_with_final_button():
            screen = mailbox.capture().copy()
            final_modal_visible = (
                mailbox.receive_clicked
                and mailbox.hearts == 0
                and mailbox.capture_index >= mailbox.all_visible_from
                and not final_acknowledged
            )
            if final_modal_visible:
                x, y, width, height = final_confirm
                cv2.rectangle(
                    screen,
                    (x, y),
                    (x + width - 1, y + height - 1),
                    tuple(int(value) for value in green_bgr),
                    -1,
                )
            return screen

        def detect_with_final_button(screen, templates, region):
            if templates == actions.ALL_LIVES_RECEIVED_AND_SENT_TEMPLATE:
                if final_acknowledged:
                    return []
                return mailbox.detect(screen, templates, region)
            return mailbox.detect(screen, templates, region)

        processed = actions.handle_mailbox_receive_and_send_lives(
            capture_func=capture_with_final_button,
            detect_func=detect_with_final_button,
            tap_func=tap_with_real_final_modal,
            sleep_func=lambda _seconds: None,
        )

        self.assertEqual(processed, 1)
        self.assertTrue(final_acknowledged)
        self.assertIn(final_confirm_center, mailbox.taps)
        self.assertEqual(mailbox.state, "closed")

    def test_transient_dark_mailbox_frame_is_retried_not_reported_complete(self):
        mailbox = _Mailbox(hearts=1)
        dark_once = {"used": False}

        def capture_with_one_dark_transition():
            if mailbox.receive_clicked and not dark_once["used"]:
                dark_once["used"] = True
                mailbox.capture_index += 1
                return np.zeros((720, 1280, 3), dtype=np.uint8)
            return mailbox.capture()

        def detect_with_dark_guard(screen, templates, region):
            if float(screen.mean()) < 1.0:
                return []
            return mailbox.detect(screen, templates, region)

        processed = actions.handle_mailbox_receive_and_send_lives(
            capture_func=capture_with_one_dark_transition,
            detect_func=detect_with_dark_guard,
            tap_func=mailbox.tap,
            sleep_func=lambda _seconds: None,
            panel_recovery_attempts=3,
        )

        self.assertTrue(dark_once["used"])
        self.assertEqual(processed, 1)
        self.assertEqual(mailbox.taps[-1], tuple(actions.MAIL_BOX_CLOSE_BUTTON))

    def test_slow_mailbox_transition_survives_more_than_four_dark_frames(self):
        mailbox = _Mailbox(hearts=2)
        dark_frames_remaining = 0
        original_tap = mailbox.tap

        def tap_with_slow_transition(x, y):
            nonlocal dark_frames_remaining
            original_tap(x, y)
            if (x, y) == _center(mailbox.confirm_match):
                dark_frames_remaining = 6

        def capture_with_slow_transition():
            nonlocal dark_frames_remaining
            if dark_frames_remaining > 0:
                dark_frames_remaining -= 1
                mailbox.capture_index += 1
                return np.zeros((720, 1280, 3), dtype=np.uint8)
            return mailbox.capture()

        def detect_with_dark_guard(screen, templates, region):
            if float(screen.mean()) < 1.0:
                return []
            return mailbox.detect(screen, templates, region)

        processed = actions.handle_mailbox_receive_and_send_lives(
            capture_func=capture_with_slow_transition,
            detect_func=detect_with_dark_guard,
            tap_func=tap_with_slow_transition,
            sleep_func=lambda _seconds: None,
        )

        self.assertEqual(processed, 2)
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

    def test_fails_loudly_when_confirm_never_advances(self):
        mailbox = _Mailbox(hearts=2, stuck_confirm=True)

        with self.assertRaisesRegex(RuntimeError, "Confirm did not advance"):
            actions.handle_mailbox_receive_and_send_lives(
                capture_func=mailbox.capture,
                detect_func=mailbox.detect,
                tap_func=mailbox.tap,
                sleep_func=lambda _seconds: None,
                confirm_poll_attempts=2,
                confirm_tap_attempts=3,
            )

        self.assertNotEqual(mailbox.taps[-1], tuple(actions.MAIL_BOX_CLOSE_BUTTON))

    def test_back_to_back_confirm_visual_change_counts_as_progress(self):
        before = np.full((720, 1280, 3), 70, dtype=np.uint8)
        after = before.copy()
        after[250:340, 430:780] = 150

        self.assertTrue(actions._mailbox_dialog_has_progressed(before, after))
        self.assertFalse(actions._mailbox_dialog_has_progressed(before, before.copy()))


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
