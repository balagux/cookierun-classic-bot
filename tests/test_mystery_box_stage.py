import os
import unittest
from pathlib import Path

import cv2
import numpy as np

import config
from detection import detect_stage


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


def _canonical_fixture(filename):
    screen = cv2.imread(str(FIXTURE_DIR / filename), cv2.IMREAD_COLOR)
    if screen is None:
        raise AssertionError(f"Could not load test fixture: {filename}")
    return cv2.resize(screen, (1280, 720), interpolation=cv2.INTER_CUBIC)


class MysteryBoxStageTests(unittest.TestCase):
    def test_open_a_mystery_box_header_is_detected_in_both_real_screens(self):
        for filename in ("mystery_box_three.png", "mystery_box_five.jpg"):
            with self.subTest(filename=filename):
                screen = _canonical_fixture(filename)
                self.assertEqual(
                    detect_stage(screen, ("MYSTERY_BOX",)),
                    "MYSTERY_BOX",
                )

    def test_legacy_mystery_box_header_remains_compatible(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        legacy = cv2.imread(
            os.path.join(config.TEMPLATE_DIR, "MYSTERY_BOX_1.png"),
            cv2.IMREAD_COLOR,
        )
        self.assertIsNotNone(legacy)
        height, width = legacy.shape[:2]
        x, y = 503, 46
        screen[y:y + height, x:x + width] = legacy

        self.assertEqual(
            detect_stage(screen, ("MYSTERY_BOX",)),
            "MYSTERY_BOX",
        )

    def test_other_real_stage_header_does_not_trigger_mystery_box(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        level_up = cv2.imread(
            os.path.join(config.TEMPLATE_DIR, "LEVEL_UP_1.png"),
            cv2.IMREAD_COLOR,
        )
        self.assertIsNotNone(level_up)
        height, width = level_up.shape[:2]
        x, y = 481, 34
        screen[y:y + height, x:x + width] = level_up

        self.assertIsNone(detect_stage(screen, ("MYSTERY_BOX",)))


if __name__ == "__main__":
    unittest.main()

