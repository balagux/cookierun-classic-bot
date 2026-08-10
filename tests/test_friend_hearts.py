import unittest
from unittest import mock
from pathlib import Path

import cv2
import numpy as np

import actions
import bot
import detection


class _FriendLeaderboard:
    main_match = (154, 150, 174, 59)
    top_match = (150, 275, 53, 301)
    first_heart = (610, 285, 111, 69)
    second_heart = (610, 390, 111, 69)
    confirm_match = (650, 405, 290, 101)
    acknowledgement_match = (500, 410, 290, 101)
    bottom_match = (270, 550, 340, 81)

    def __init__(self, success_popup=True):
        self.success_popup = success_popup
        self.state = "two_hearts"
        self.taps = []
        self.scrolls = []
        self.capture_count = 0
        self.bright_screen = np.full((720, 1280, 3), 225, dtype=np.uint8)
        self.dimmed_screen = np.full((720, 1280, 3), 70, dtype=np.uint8)
        self.success_screen = self.dimmed_screen.copy()
        acknowledgement_hsv = np.uint8([[[40, 210, 210]]])
        acknowledgement_bgr = cv2.cvtColor(
            acknowledgement_hsv,
            cv2.COLOR_HSV2BGR,
        )[0, 0]
        ack_x, ack_y, ack_width, ack_height = self.acknowledgement_match
        cv2.rectangle(
            self.success_screen,
            (ack_x, ack_y),
            (ack_x + ack_width - 1, ack_y + ack_height - 1),
            tuple(int(value) for value in acknowledgement_bgr),
            -1,
        )

    def capture(self):
        self.capture_count += 1
        if self.state.startswith("success_"):
            return self.success_screen
        if self.state.startswith(("confirm_", "stuck_confirm")):
            return self.dimmed_screen
        return self.bright_screen

    def detect(self, _screen, templates, _region):
        if templates == actions.STAGE_MAINMENU_TEMPLATE:
            return [self.main_match] if self.state not in {"confirm_first", "confirm_second", "stuck_confirm"} else []
        if templates == actions.FRIEND_TOP_LEADERBOARD_TEMPLATE:
            return [self.top_match] if self.state in {"two_hearts", "one_heart", "success_first"} else []
        if templates == actions.FRIEND_SEND_LIFE_TEMPLATE:
            if self.state == "two_hearts":
                return [self.first_heart, self.second_heart]
            if self.state == "one_heart":
                return [self.second_heart]
            if self.state == "success_first":
                # The grayscale template remains detectable behind the modal.
                return [self.second_heart]
            return []
        if templates == actions.CONFIRM_SEND_LIFE_TEMPLATE:
            return [self.confirm_match] if self.state.startswith("confirm_") else []
        if templates == actions.FRIEND_BOTTOM_LEADERBOARD_TEMPLATE:
            return [self.bottom_match] if self.state in {"bottom", "success_second"} else []
        return []

    @staticmethod
    def _center(match):
        x, y, width, height = match
        return x + width // 2, y + height // 2

    def tap(self, x, y):
        point = (x, y)
        self.taps.append(point)
        if self.state == "two_hearts" and point == self._center(self.first_heart):
            self.state = "confirm_first"
        elif self.state == "confirm_first" and point == self._center(self.confirm_match):
            self.state = "success_first" if self.success_popup else "one_heart"
        elif self.state == "success_first" and point == self._center(self.acknowledgement_match):
            self.state = "one_heart"
        elif self.state == "one_heart" and point == self._center(self.second_heart):
            self.state = "confirm_second"
        elif self.state == "confirm_second" and point == self._center(self.confirm_match):
            self.state = "success_second" if self.success_popup else "bottom"
        elif self.state == "success_second" and point == self._center(self.acknowledgement_match):
            self.state = "bottom"

    def scroll(self, x, y, direction, distance, duration):
        self.scrolls.append((x, y, direction, distance, duration))


class FriendHeartTests(unittest.TestCase):
    def setUp(self):
        self.print_patcher = mock.patch("builtins.print")
        self.print_patcher.start()

    def tearDown(self):
        self.print_patcher.stop()

    def test_recaptures_each_heart_and_closes_dimmed_success_popup(self):
        leaderboard = _FriendLeaderboard()

        sent_count = actions.handle_send_friend_life(
            capture_func=leaderboard.capture,
            detect_func=leaderboard.detect,
            tap_func=leaderboard.tap,
            scroll_func=leaderboard.scroll,
            sleep_func=lambda _seconds: None,
            active_button_func=lambda _screen, _match: True,
        )

        self.assertEqual(sent_count, 2)
        self.assertEqual(
            leaderboard.taps,
            [
                leaderboard._center(leaderboard.first_heart),
                leaderboard._center(leaderboard.confirm_match),
                leaderboard._center(leaderboard.acknowledgement_match),
                leaderboard._center(leaderboard.second_heart),
                leaderboard._center(leaderboard.confirm_match),
                leaderboard._center(leaderboard.acknowledgement_match),
            ],
        )
        self.assertGreaterEqual(leaderboard.capture_count, 7)
        self.assertEqual(leaderboard.scrolls, [])

    def test_does_not_blind_tap_close_when_list_returns_without_popup(self):
        leaderboard = _FriendLeaderboard(success_popup=False)

        sent_count = actions.handle_send_friend_life(
            capture_func=leaderboard.capture,
            detect_func=leaderboard.detect,
            tap_func=leaderboard.tap,
            scroll_func=leaderboard.scroll,
            sleep_func=lambda _seconds: None,
            active_button_func=lambda _screen, _match: True,
        )

        self.assertEqual(sent_count, 2)
        self.assertNotIn(
            leaderboard._center(leaderboard.acknowledgement_match),
            leaderboard.taps,
        )

    def test_wrong_screen_fails_without_tapping_or_scrolling(self):
        taps = []
        scrolls = []

        with self.assertRaisesRegex(RuntimeError, "leaderboard not detected"):
            actions.handle_send_friend_life(
                capture_func=lambda: np.zeros((720, 1280, 3), dtype=np.uint8),
                detect_func=lambda _screen, _templates, _region: [],
                tap_func=lambda x, y: taps.append((x, y)),
                scroll_func=lambda *args: scrolls.append(args),
                sleep_func=lambda _seconds: None,
                active_button_func=lambda _screen, _match: True,
            )

        self.assertEqual(taps, [])
        self.assertEqual(scrolls, [])

    def test_top_search_is_bounded_before_any_heart_is_tapped(self):
        leaderboard = _FriendLeaderboard()

        def never_find_top(_screen, templates, _region):
            if templates == actions.STAGE_MAINMENU_TEMPLATE:
                return [leaderboard.main_match]
            if templates == actions.FRIEND_SEND_LIFE_TEMPLATE:
                return [leaderboard.first_heart]
            return []

        with self.assertRaisesRegex(RuntimeError, "after 3 scrolls"):
            actions.handle_send_friend_life(
                capture_func=leaderboard.capture,
                detect_func=never_find_top,
                tap_func=leaderboard.tap,
                scroll_func=leaderboard.scroll,
                sleep_func=lambda _seconds: None,
                active_button_func=lambda _screen, _match: True,
                max_top_scrolls=3,
            )

        self.assertEqual(leaderboard.taps, [])
        self.assertEqual(len(leaderboard.scrolls), 3)
        for _x, y, _direction, distance, _duration in leaderboard.scrolls:
            # safe_device_scroll may add up to 15px of jitter before applying
            # y +/- distance; both endpoints must remain inside the row list.
            self.assertGreaterEqual(y - 15 - distance, 270)
            self.assertLessEqual(y + 15 + distance, 630)

    def test_rank_107_reaches_top_with_safe_long_swipes(self):
        screen = np.full((720, 1280, 3), 225, dtype=np.uint8)
        rank = 107
        scrolls = []

        def detect_rank(_screen, templates, _region):
            if templates == actions.STAGE_MAINMENU_TEMPLATE:
                return [_FriendLeaderboard.main_match]
            if templates == actions.FRIEND_TOP_LEADERBOARD_TEMPLATE and rank == 1:
                return [_FriendLeaderboard.top_match]
            if templates == actions.FRIEND_BOTTOM_LEADERBOARD_TEMPLATE and rank == 1:
                return [_FriendLeaderboard.bottom_match]
            return []

        def scroll_to_top(x, y, direction, distance, duration):
            nonlocal rank
            scrolls.append((x, y, direction, distance, duration))
            self.assertEqual(direction, "down")
            rank = max(1, rank - 3)

        sent_count = actions.handle_send_friend_life(
            capture_func=lambda: screen,
            detect_func=detect_rank,
            tap_func=lambda _x, _y: self.fail("no tap expected"),
            scroll_func=scroll_to_top,
            sleep_func=lambda _seconds: None,
        )

        self.assertEqual(sent_count, 0)
        self.assertEqual(rank, 1)
        self.assertEqual(len(scrolls), 36)
        for _x, y, _direction, distance, _duration in scrolls:
            self.assertEqual((y, distance), (447, 150))
            self.assertGreaterEqual(y - 15 - distance, 270)
            self.assertLessEqual(y + 15 + distance, 630)

    def test_default_list_bound_reaches_friend_202(self):
        screen = np.full((720, 1280, 3), 225, dtype=np.uint8)
        rank = 1
        scrolls = []

        def detect_rank(_screen, templates, _region):
            if templates == actions.STAGE_MAINMENU_TEMPLATE:
                return [_FriendLeaderboard.main_match]
            if templates == actions.FRIEND_TOP_LEADERBOARD_TEMPLATE and rank == 1:
                return [_FriendLeaderboard.top_match]
            if templates == actions.FRIEND_BOTTOM_LEADERBOARD_TEMPLATE and rank >= 199:
                return [_FriendLeaderboard.bottom_match]
            return []

        def scroll_to_bottom(x, y, direction, distance, duration):
            nonlocal rank
            scrolls.append((x, y, direction, distance, duration))
            self.assertEqual(direction, "up")
            rank = min(202, rank + 3)

        sent_count = actions.handle_send_friend_life(
            capture_func=lambda: screen,
            detect_func=detect_rank,
            tap_func=lambda _x, _y: self.fail("no tap expected"),
            scroll_func=scroll_to_bottom,
            sleep_func=lambda _seconds: None,
        )

        self.assertEqual(sent_count, 0)
        self.assertGreaterEqual(rank, 199)
        self.assertLessEqual(len(scrolls), 160)
        self.assertTrue(
            all(y == 447 and distance == 150 for _x, y, _d, distance, _t in scrolls)
        )

    def test_dim_overlay_after_scroll_fails_before_another_action(self):
        bright = np.full((720, 1280, 3), 225, dtype=np.uint8)
        dim = np.full((720, 1280, 3), 70, dtype=np.uint8)
        overlay_visible = False
        scrolls = []

        def capture():
            return dim if overlay_visible else bright

        def detect_list(_screen, templates, _region):
            if templates == actions.STAGE_MAINMENU_TEMPLATE:
                return [_FriendLeaderboard.main_match]
            if templates == actions.FRIEND_TOP_LEADERBOARD_TEMPLATE:
                return [_FriendLeaderboard.top_match]
            return []

        def show_overlay(*args):
            nonlocal overlay_visible
            scrolls.append(args)
            overlay_visible = True

        with self.assertRaisesRegex(RuntimeError, "covered or no longer ready"):
            actions.handle_send_friend_life(
                capture_func=capture,
                detect_func=detect_list,
                tap_func=lambda _x, _y: self.fail("no tap expected"),
                scroll_func=show_overlay,
                sleep_func=lambda _seconds: None,
                max_list_scrolls=3,
            )

        self.assertEqual(len(scrolls), 1)

    def test_missing_confirmation_never_blind_taps_confirm(self):
        leaderboard = _FriendLeaderboard()

        def confirmation_never_appears(_screen, templates, _region):
            if templates == actions.STAGE_MAINMENU_TEMPLATE:
                return [leaderboard.main_match]
            if templates == actions.FRIEND_TOP_LEADERBOARD_TEMPLATE:
                return [leaderboard.top_match]
            if templates == actions.FRIEND_SEND_LIFE_TEMPLATE:
                return [leaderboard.first_heart]
            return []

        with self.assertRaisesRegex(RuntimeError, "confirmation did not appear"):
            actions.handle_send_friend_life(
                capture_func=leaderboard.capture,
                detect_func=confirmation_never_appears,
                tap_func=lambda x, y: leaderboard.taps.append((x, y)),
                scroll_func=leaderboard.scroll,
                sleep_func=lambda _seconds: None,
                active_button_func=lambda _screen, _match: True,
                heart_tap_attempts=2,
                confirm_poll_attempts=2,
            )

        self.assertEqual(
            leaderboard.taps,
            [leaderboard._center(leaderboard.first_heart)] * 2,
        )
        self.assertNotIn(leaderboard._center(leaderboard.confirm_match), leaderboard.taps)

    def test_stuck_confirmation_is_bounded_and_never_taps_close(self):
        leaderboard = _FriendLeaderboard()

        def detect_stuck_confirmation(_screen, templates, _region):
            if templates == actions.STAGE_MAINMENU_TEMPLATE:
                return [leaderboard.main_match] if leaderboard.state == "two_hearts" else []
            if templates == actions.FRIEND_TOP_LEADERBOARD_TEMPLATE:
                return [leaderboard.top_match] if leaderboard.state == "two_hearts" else []
            if templates == actions.FRIEND_SEND_LIFE_TEMPLATE:
                return [leaderboard.first_heart] if leaderboard.state == "two_hearts" else []
            if templates == actions.CONFIRM_SEND_LIFE_TEMPLATE:
                return [leaderboard.confirm_match] if leaderboard.state == "stuck_confirm" else []
            return []

        def tap_without_closing_confirmation(x, y):
            point = (x, y)
            leaderboard.taps.append(point)
            if point == leaderboard._center(leaderboard.first_heart):
                leaderboard.state = "stuck_confirm"

        with self.assertRaisesRegex(RuntimeError, "confirmation did not close"):
            actions.handle_send_friend_life(
                capture_func=leaderboard.capture,
                detect_func=detect_stuck_confirmation,
                tap_func=tap_without_closing_confirmation,
                scroll_func=leaderboard.scroll,
                sleep_func=lambda _seconds: None,
                active_button_func=lambda _screen, _match: True,
                confirm_poll_attempts=2,
                confirm_tap_attempts=2,
            )

        self.assertEqual(
            leaderboard.taps,
            [
                leaderboard._center(leaderboard.first_heart),
                leaderboard._center(leaderboard.confirm_match),
                leaderboard._center(leaderboard.confirm_match),
            ],
        )
        self.assertNotIn(
            leaderboard._center(leaderboard.acknowledgement_match),
            leaderboard.taps,
        )

    def test_last_visible_heart_is_sent_before_bottom_marker_stops_scan(self):
        leaderboard = _FriendLeaderboard(success_popup=False)
        leaderboard.state = "last_heart"

        def detect_last_row(_screen, templates, _region):
            if templates == actions.STAGE_MAINMENU_TEMPLATE:
                return [leaderboard.main_match] if leaderboard.state != "confirm_last" else []
            if templates == actions.FRIEND_TOP_LEADERBOARD_TEMPLATE:
                return [leaderboard.top_match] if leaderboard.state == "last_heart" else []
            if templates == actions.FRIEND_SEND_LIFE_TEMPLATE:
                return [leaderboard.first_heart] if leaderboard.state == "last_heart" else []
            if templates == actions.FRIEND_BOTTOM_LEADERBOARD_TEMPLATE:
                return [leaderboard.bottom_match] if leaderboard.state in {"last_heart", "bottom"} else []
            if templates == actions.CONFIRM_SEND_LIFE_TEMPLATE:
                return [leaderboard.confirm_match] if leaderboard.state == "confirm_last" else []
            return []

        def tap_last_row(x, y):
            point = (x, y)
            leaderboard.taps.append(point)
            if leaderboard.state == "last_heart" and point == leaderboard._center(leaderboard.first_heart):
                leaderboard.state = "confirm_last"
            elif leaderboard.state == "confirm_last" and point == leaderboard._center(leaderboard.confirm_match):
                leaderboard.state = "bottom"

        sent_count = actions.handle_send_friend_life(
            capture_func=leaderboard.capture,
            detect_func=detect_last_row,
            tap_func=tap_last_row,
            scroll_func=leaderboard.scroll,
            sleep_func=lambda _seconds: None,
            active_button_func=lambda _screen, _match: True,
        )

        self.assertEqual(sent_count, 1)
        self.assertEqual(
            leaderboard.taps,
            [
                leaderboard._center(leaderboard.first_heart),
                leaderboard._center(leaderboard.confirm_match),
            ],
        )

    def test_reappearing_same_icon_stops_before_a_duplicate_send(self):
        leaderboard = _FriendLeaderboard(success_popup=False)
        leaderboard.state = "initial"
        post_confirm_capture_count = 0

        def capture():
            nonlocal post_confirm_capture_count
            if leaderboard.state == "post_confirm":
                post_confirm_capture_count += 1
                if post_confirm_capture_count >= 2:
                    leaderboard.state = "repeated"
            if leaderboard.state == "confirm":
                return leaderboard.dimmed_screen
            return leaderboard.bright_screen

        def detect_repeated(_screen, templates, _region):
            if templates == actions.STAGE_MAINMENU_TEMPLATE:
                return [leaderboard.main_match] if leaderboard.state != "confirm" else []
            if templates == actions.FRIEND_TOP_LEADERBOARD_TEMPLATE:
                return [leaderboard.top_match] if leaderboard.state != "confirm" else []
            if templates == actions.FRIEND_SEND_LIFE_TEMPLATE:
                return [leaderboard.first_heart] if leaderboard.state in {"initial", "repeated"} else []
            if templates == actions.CONFIRM_SEND_LIFE_TEMPLATE:
                return [leaderboard.confirm_match] if leaderboard.state == "confirm" else []
            return []

        def tap(x, y):
            point = (x, y)
            leaderboard.taps.append(point)
            if leaderboard.state == "initial" and point == leaderboard._center(leaderboard.first_heart):
                leaderboard.state = "confirm"
            elif leaderboard.state == "confirm" and point == leaderboard._center(leaderboard.confirm_match):
                leaderboard.state = "post_confirm"

        with self.assertRaisesRegex(RuntimeError, "previously sent heart button reappeared"):
            actions.handle_send_friend_life(
                capture_func=capture,
                detect_func=detect_repeated,
                tap_func=tap,
                scroll_func=leaderboard.scroll,
                sleep_func=lambda _seconds: None,
                active_button_func=lambda _screen, _match: True,
            )

        self.assertEqual(
            leaderboard.taps,
            [
                leaderboard._center(leaderboard.first_heart),
                leaderboard._center(leaderboard.confirm_match),
            ],
        )

    def test_zero_send_limit_stops_before_first_heart_tap(self):
        leaderboard = _FriendLeaderboard(success_popup=False)

        with self.assertRaisesRegex(RuntimeError, "maximum heart-send safety limit"):
            actions.handle_send_friend_life(
                capture_func=leaderboard.capture,
                detect_func=leaderboard.detect,
                tap_func=leaderboard.tap,
                scroll_func=leaderboard.scroll,
                sleep_func=lambda _seconds: None,
                active_button_func=lambda _screen, _match: True,
                max_heart_sends=0,
            )

        self.assertEqual(leaderboard.taps, [])

    def test_total_iteration_guard_bounds_a_nonprogressing_list(self):
        leaderboard = _FriendLeaderboard(success_popup=False)

        def detect_no_progress(_screen, templates, _region):
            if templates == actions.STAGE_MAINMENU_TEMPLATE:
                return [leaderboard.main_match]
            if templates == actions.FRIEND_TOP_LEADERBOARD_TEMPLATE:
                return [leaderboard.top_match]
            return []

        with self.assertRaisesRegex(RuntimeError, "safety limit was reached"):
            actions.handle_send_friend_life(
                capture_func=leaderboard.capture,
                detect_func=detect_no_progress,
                tap_func=leaderboard.tap,
                scroll_func=leaderboard.scroll,
                sleep_func=lambda _seconds: None,
                max_total_iterations=1,
            )

        self.assertEqual(leaderboard.taps, [])
        self.assertEqual(len(leaderboard.scrolls), 1)

    def test_green_gate_rejects_a_grey_disabled_envelope(self):
        active_screen = np.zeros((100, 160, 3), dtype=np.uint8)
        disabled_screen = np.zeros_like(active_screen)
        match = (20, 20, 111, 69)
        active_hsv = np.uint8([[[40, 210, 210]]])
        active_bgr = cv2.cvtColor(active_hsv, cv2.COLOR_HSV2BGR)[0, 0]
        x, y, width, height = match
        active_screen[y:y + height, x:x + width] = active_bgr
        disabled_screen[y:y + height, x:x + width] = (135, 135, 135)

        self.assertTrue(actions._is_active_friend_life_button(active_screen, match))
        self.assertFalse(actions._is_active_friend_life_button(disabled_screen, match))

    def test_real_rank_107_screenshot_detects_active_rows_not_acknowledgement(self):
        screenshot_path = (
            Path(actions.__file__).resolve().parent
            / "debug_screens"
            / "after_quick_result_ok.png"
        )
        screen = cv2.imread(str(screenshot_path))
        self.assertIsNotNone(screen)
        self.assertEqual(detection.detect_stage(screen, ("MAINMENU",)), "MAINMENU")

        matches = detection.detect_all_template_matches(
            screen,
            actions.FRIEND_SEND_LIFE_TEMPLATE,
            actions.FRIEND_SEND_LIFE_REGION,
        )
        active_matches = [
            match
            for match in matches
            if actions._is_active_friend_life_button(screen, match)
        ]

        self.assertEqual(
            [(x, y) for x, y, _width, _height in active_matches],
            [(609, 314), (609, 521)],
        )
        # The small green row crossing the old fixed point around (645, 463)
        # is normal leaderboard UI, not a large acknowledgement button.
        self.assertIsNone(actions._detect_friend_acknowledgement_button(screen))

    def test_large_green_acknowledgement_is_detected_by_shape(self):
        leaderboard = _FriendLeaderboard()

        detected = actions._detect_friend_acknowledgement_button(
            leaderboard.success_screen
        )

        self.assertEqual(detected, leaderboard.acknowledgement_match)

    def test_dim_transition_without_large_acknowledgement_never_stray_taps(self):
        leaderboard = _FriendLeaderboard()
        leaderboard.success_screen = leaderboard.dimmed_screen

        with self.assertRaisesRegex(RuntimeError, "no large heart-sent acknowledgement"):
            actions.handle_send_friend_life(
                capture_func=leaderboard.capture,
                detect_func=leaderboard.detect,
                tap_func=leaderboard.tap,
                scroll_func=leaderboard.scroll,
                sleep_func=lambda _seconds: None,
                active_button_func=lambda _screen, _match: True,
                list_return_poll_attempts=2,
                acknowledgement_poll_attempts=2,
            )

        self.assertEqual(
            leaderboard.taps,
            [
                leaderboard._center(leaderboard.first_heart),
                leaderboard._center(leaderboard.confirm_match),
            ],
        )

    def test_one_shot_worker_connects_without_resetting_the_game(self):
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
            mock.patch.object(bot, "handle_send_friend_life", return_value=6) as send,
            mock.patch.object(bot, "device_reset_app") as reset_app,
        ):
            sent_count = bot.send_friend_hearts("127.0.0.9", 5566)

        self.assertEqual(sent_count, 6)
        connect.assert_called_once_with("127.0.0.9", 5566)
        load_templates.assert_called_once_with()
        detect_main.assert_called_once_with(screen, ("MAINMENU",))
        send.assert_called_once_with()
        reset_app.assert_not_called()

    def test_one_shot_worker_rejects_non_main_screen_before_any_tap(self):
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
            mock.patch.object(bot, "handle_send_friend_life") as send,
        ):
            with self.assertRaisesRegex(RuntimeError, "Main/Friends leaderboard"):
                bot.send_friend_hearts("127.0.0.9", 5566)

        send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
