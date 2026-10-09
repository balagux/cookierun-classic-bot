import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

import actions
import bot
from config import (
    ANTI_BOT_CARD_HEIGHT,
    ANTI_BOT_CARD_POS_1,
    ANTI_BOT_CARD_POS_2,
    ANTI_BOT_CARD_POS_3,
    ANTI_BOT_CARD_POS_4,
    ANTI_BOT_CARD_POS_5,
    ANTI_BOT_CARD_POS_6,
    ANTI_BOT_CARD_WIDTH,
    DETECTION_ALWAYS_STAGES,
    STAGE_ANTI_BOT_REGION,
    STAGE_NEWS_REGION,
    TEMPLATE_DIR,
)
from detection import (
    _is_anti_bot_screen,
    detect_anti_bot_card_candidates,
    detect_anti_bot_instruction,
    detect_anti_bot_odd_cards,
    detect_stage,
)


class AntiBotTests(unittest.TestCase):
    def test_anti_bot_is_checked_in_every_detection_group(self):
        self.assertIn("ANTI_BOT", DETECTION_ALWAYS_STAGES)

    def test_wide_low_sliding_poses_rank_above_running_poses(self):
        screen = np.full((720, 1280, 3), 220, dtype=np.uint8)
        positions = (
            ANTI_BOT_CARD_POS_1,
            ANTI_BOT_CARD_POS_2,
            ANTI_BOT_CARD_POS_3,
            ANTI_BOT_CARD_POS_4,
            ANTI_BOT_CARD_POS_5,
            ANTI_BOT_CARD_POS_6,
        )
        sliding = {1, 4}
        for index, (x, y) in enumerate(positions):
            if index in sliding:
                screen[y + 110:y + 165, x + 20:x + ANTI_BOT_CARD_WIDTH - 20] = (0, 0, 255)
            else:
                screen[y + 55:y + ANTI_BOT_CARD_HEIGHT - 35, x + 65:x + 105] = (0, 0, 255)

        ranked = detect_anti_bot_odd_cards(screen)

        self.assertEqual(set(ranked), sliding)

    def test_layout_detector_accepts_sliding_wording_without_old_text_template(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        screen[10:112, 108:1172] = (220, 160, 20)
        positions = (
            ANTI_BOT_CARD_POS_1,
            ANTI_BOT_CARD_POS_2,
            ANTI_BOT_CARD_POS_3,
            ANTI_BOT_CARD_POS_4,
            ANTI_BOT_CARD_POS_5,
            ANTI_BOT_CARD_POS_6,
        )
        for x, y in positions:
            screen[
                y + 10:y + ANTI_BOT_CARD_HEIGHT - 10,
                x + 10:x + ANTI_BOT_CARD_WIDTH - 10,
            ] = (220, 220, 220)

        self.assertTrue(_is_anti_bot_screen(screen))
        self.assertEqual(detect_stage(screen, ("ANTI_BOT",)), "ANTI_BOT")

    def test_daily_checkin_fixture_is_not_misclassified_as_anti_bot(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "daily_checkin_antibot_false_positive.png"
        screen = cv2.imread(str(fixture))
        self.assertIsNotNone(screen)
        self.assertEqual(detect_stage(screen, ("DAILY_CHECKIN",)), "DAILY_CHECKIN")
        self.assertIsNone(detect_stage(screen, ("ANTI_BOT",)))
        self.assertFalse(_is_anti_bot_screen(screen))

    def test_news_template_overrides_broad_anti_bot_layout_heuristic(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        screen[10:112, 108:1172] = (220, 160, 20)
        positions = (
            ANTI_BOT_CARD_POS_1,
            ANTI_BOT_CARD_POS_2,
            ANTI_BOT_CARD_POS_3,
            ANTI_BOT_CARD_POS_4,
            ANTI_BOT_CARD_POS_5,
            ANTI_BOT_CARD_POS_6,
        )
        for x, y in positions:
            screen[
                y + 10:y + ANTI_BOT_CARD_HEIGHT - 10,
                x + 10:x + ANTI_BOT_CARD_WIDTH - 10,
            ] = (220, 220, 220)

        news = cv2.imread(str(Path(TEMPLATE_DIR) / "NEWS_TITLE_1.png"))
        self.assertIsNotNone(news)
        x1, y1, _, _ = STAGE_NEWS_REGION
        height, width = news.shape[:2]
        screen[y1:y1 + height, x1:x1 + width] = news

        self.assertFalse(_is_anti_bot_screen(screen))
        self.assertEqual(detect_stage(screen, ("ANTI_BOT", "NEWS")), "NEWS")

    def _anti_bot_layout_with_known_header(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        screen[10:112, 108:1172] = (220, 160, 20)
        header = cv2.imread(str(Path(TEMPLATE_DIR) / "ANTI_BOT_1.png"))
        self.assertIsNotNone(header)
        x1, y1, _, _ = STAGE_ANTI_BOT_REGION
        height, width = header.shape[:2]
        screen[y1:y1 + height, x1:x1 + width] = header
        positions = (
            ANTI_BOT_CARD_POS_1, ANTI_BOT_CARD_POS_2, ANTI_BOT_CARD_POS_3,
            ANTI_BOT_CARD_POS_4, ANTI_BOT_CARD_POS_5, ANTI_BOT_CARD_POS_6,
        )
        for x, y in positions:
            screen[
                y + 10:y + ANTI_BOT_CARD_HEIGHT - 10,
                x + 10:x + ANTI_BOT_CARD_WIDTH - 10,
            ] = (220, 220, 220)
        return screen

    def test_known_header_is_classified_as_jumping_instruction(self):
        screen = self._anti_bot_layout_with_known_header()
        self.assertEqual(detect_anti_bot_instruction(screen), "jumping")

    def test_changed_instruction_word_falls_back_to_sliding(self):
        screen = self._anti_bot_layout_with_known_header()
        x1, y1, _, _ = STAGE_ANTI_BOT_REGION
        screen[y1 + 15:y1 + 75, x1 + 410:x1 + 545] = (220, 160, 20)
        self.assertEqual(detect_anti_bot_instruction(screen), "sliding")

    def test_jumping_candidates_reverse_sliding_ranking(self):
        screen = np.full((720, 1280, 3), 220, dtype=np.uint8)
        positions = (
            ANTI_BOT_CARD_POS_1, ANTI_BOT_CARD_POS_2, ANTI_BOT_CARD_POS_3,
            ANTI_BOT_CARD_POS_4, ANTI_BOT_CARD_POS_5, ANTI_BOT_CARD_POS_6,
        )
        sliding = {1, 4}
        for index, (x, y) in enumerate(positions):
            if index in sliding:
                screen[y + 110:y + 165, x + 20:x + ANTI_BOT_CARD_WIDTH - 20] = (0, 0, 255)
            else:
                screen[y + 55:y + ANTI_BOT_CARD_HEIGHT - 35, x + 65:x + 105] = (0, 0, 255)

        sliding_order = detect_anti_bot_card_candidates(screen, "sliding")
        jumping_order = detect_anti_bot_card_candidates(screen, "jumping")

        self.assertEqual(set(sliding_order[:2]), sliding)
        self.assertTrue(all(index not in sliding for index in jumping_order[:4]))

    def test_bot_stops_after_bounded_anti_bot_handler_failure_and_saves_evidence(self):
        screen = object()
        with (
            mock.patch.object(bot, "handle_anti_bot", return_value=False),
            mock.patch.object(bot, "save_debug_screen") as save_debug,
            mock.patch("builtins.print"),
        ):
            with self.assertRaisesRegex(RuntimeError, "manual intervention"):
                bot._handle_anti_bot_or_raise(screen)
        save_debug.assert_called_once_with(screen)

    def test_handler_recaptures_after_each_tap_and_stops_when_page_closes(self):
        with (
            mock.patch.object(actions, "detect_anti_bot_instruction", return_value="jumping"),
            mock.patch.object(actions, "detect_anti_bot_card_candidates", return_value=[2, 4, 1]),
            mock.patch.object(actions, "device_tap") as tap,
            mock.patch.object(actions, "device_capture_screen", return_value=object()) as capture,
            mock.patch.object(actions, "detect_stage", return_value=None),
            mock.patch.object(actions.time, "sleep") as sleep,
            mock.patch("builtins.print"),
        ):
            solved = actions.handle_anti_bot(object())

        self.assertTrue(solved)
        tap.assert_called_once()
        capture.assert_called_once()
        sleep.assert_called_once_with(0.35)

    def test_handler_tries_distinct_ranked_candidates_before_failing(self):
        with (
            mock.patch.object(actions, "detect_anti_bot_instruction", return_value="jumping"),
            mock.patch.object(actions, "detect_anti_bot_card_candidates", return_value=[2, 4, 1, 0, 3, 5]),
            mock.patch.object(actions, "device_tap") as tap,
            mock.patch.object(actions, "device_capture_screen", return_value=object()),
            mock.patch.object(actions, "detect_stage", side_effect=["ANTI_BOT", "ANTI_BOT", None]),
            mock.patch.object(actions.time, "sleep"),
            mock.patch("builtins.print"),
        ):
            solved = actions.handle_anti_bot(object())

        self.assertTrue(solved)
        self.assertEqual(tap.call_count, 3)
        tapped = [call.args[2:4] for call in tap.call_args_list]
        expected = []
        for index in (2, 4, 1):
            x, y = (
                ANTI_BOT_CARD_POS_1, ANTI_BOT_CARD_POS_2, ANTI_BOT_CARD_POS_3,
                ANTI_BOT_CARD_POS_4, ANTI_BOT_CARD_POS_5, ANTI_BOT_CARD_POS_6,
            )[index]
            expected.append((x + ANTI_BOT_CARD_WIDTH // 2, y + ANTI_BOT_CARD_HEIGHT // 2))
        self.assertEqual(tapped, expected)


if __name__ == "__main__":
    unittest.main()
