import os
import unittest

import cv2
import numpy as np

import actions
import config


class StageConfigTests(unittest.TestCase):
    def test_every_template_fits_its_detection_region(self):
        for stage, filenames in config.STAGE_TEMPLATES.items():
            self.assertIn(stage, config.STAGE_REGIONS)
            x1, y1, x2, y2 = config.STAGE_REGIONS[stage]
            region_width = x2 - x1
            region_height = y2 - y1
            for filename in filenames:
                image = cv2.imread(os.path.join(config.TEMPLATE_DIR, filename))
                self.assertIsNotNone(image, filename)
                height, width = image.shape[:2]
                self.assertLessEqual(width, region_width, (stage, filename))
                self.assertLessEqual(height, region_height, (stage, filename))

    def test_every_stage_is_in_a_detection_group(self):
        grouped = set(config.DETECTION_ALWAYS_STAGES)
        for stages in config.DETECTION_GROUPS.values():
            grouped.update(stages)
        self.assertEqual(set(config.STAGE_TEMPLATES), grouped)

    def test_post_game_checks_result_and_party_run_without_recovery_delay(self):
        self.assertIn("GAME_COMPLETE", config.DETECTION_GROUP_POST_GAME)
        self.assertIn("PARTY_RUN", config.DETECTION_GROUP_POST_GAME)

    def test_cookie_relay_stock_uses_quantity_badge_not_price(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        x1, y1, _, _ = config.COOKIE_RELAY_STOCK_REGION
        cv2.rectangle(screen, (x1 + 8, y1 + 8), (x1 + 17, y1 + 27), (255, 255, 255), -1)
        self.assertTrue(actions.cookie_relay_has_stock(screen))

        screen[:] = 0
        cv2.circle(screen, (x1 + 16, y1 + 18), 11, (145, 145, 145), 3)
        self.assertFalse(actions.cookie_relay_has_stock(screen))


if __name__ == "__main__":
    unittest.main()
