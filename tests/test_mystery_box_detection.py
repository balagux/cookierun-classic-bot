import unittest
from collections import Counter
from pathlib import Path

import cv2

from mystery_box_detection import (
    REFERENCE_FILES,
    UNKNOWN_BOX_TYPE,
    classify_mystery_box,
    detect_mystery_box_types,
    detect_mystery_boxes,
)


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"


def _canonical_fixture(filename):
    screen = cv2.imread(str(FIXTURE_DIR / filename), cv2.IMREAD_COLOR)
    if screen is None:
        raise AssertionError(f"Could not load test fixture: {filename}")
    return cv2.resize(screen, (1280, 720), interpolation=cv2.INTER_CUBIC)


class MysteryBoxDetectionTests(unittest.TestCase):
    def test_three_box_screen_finds_two_rainbow_and_one_gold(self):
        screen = _canonical_fixture("mystery_box_three.png")

        detections = detect_mystery_boxes(screen)

        self.assertEqual(
            [item.box_type for item in detections],
            ["rainbow", "gold", "rainbow"],
        )
        self.assertEqual(
            Counter(item.box_type for item in detections),
            Counter({"rainbow": 2, "gold": 1}),
        )
        self.assertTrue(all(item.box_type != UNKNOWN_BOX_TYPE for item in detections))

    def test_five_box_screen_finds_every_tier_and_suppresses_duplicates(self):
        screen = _canonical_fixture("mystery_box_five.jpg")

        box_types = detect_mystery_box_types(screen)

        self.assertEqual(
            box_types,
            ["gold", "silver", "wood", "rainbow", "silver"],
        )
        self.assertEqual(
            Counter(box_types),
            Counter({"wood": 1, "silver": 2, "gold": 1, "rainbow": 1}),
        )
        self.assertEqual(len(box_types), 5)

    def test_each_reference_sprite_classifies_with_colour_preserved(self):
        for expected_type, filename in REFERENCE_FILES.items():
            with self.subTest(box_type=expected_type):
                crop = cv2.imread(str(TEMPLATE_DIR / filename), cv2.IMREAD_COLOR)
                self.assertIsNotNone(crop)
                self.assertEqual(classify_mystery_box(crop), expected_type)

    def test_ambiguous_colour_fails_closed_as_unknown(self):
        wood = cv2.imread(
            str(TEMPLATE_DIR / REFERENCE_FILES["wood"]),
            cv2.IMREAD_COLOR,
        )
        silver = cv2.imread(
            str(TEMPLATE_DIR / REFERENCE_FILES["silver"]),
            cv2.IMREAD_COLOR,
        )
        ambiguous = cv2.addWeighted(wood, 0.5, silver, 0.5, 0.0)

        self.assertEqual(classify_mystery_box(ambiguous), UNKNOWN_BOX_TYPE)

    def test_bad_input_never_raises_or_invents_a_box(self):
        self.assertEqual(detect_mystery_boxes(None), [])
        self.assertEqual(detect_mystery_box_types("not an image"), [])
        self.assertEqual(classify_mystery_box(None), UNKNOWN_BOX_TYPE)

    def test_grayscale_screen_fails_closed_instead_of_guessing_a_colour(self):
        screen = cv2.cvtColor(
            _canonical_fixture("mystery_box_five.jpg"),
            cv2.COLOR_BGR2GRAY,
        )

        self.assertEqual(detect_mystery_box_types(screen), [])


if __name__ == "__main__":
    unittest.main()
