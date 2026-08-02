import unittest
from unittest import mock

import numpy as np

import actions
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
)
from detection import _is_anti_bot_screen, detect_anti_bot_odd_cards, detect_stage


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

    def test_handler_recaptures_after_each_tap_and_stops_when_page_closes(self):
        with (
            mock.patch.object(actions, "detect_anti_bot_odd_cards", return_value=[2, 4]),
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


if __name__ == "__main__":
    unittest.main()
