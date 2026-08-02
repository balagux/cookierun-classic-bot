import unittest

from modern_gui import ModernCookieRunBotGUI


class GuiLayoutTests(unittest.TestCase):
    def test_large_screen_keeps_full_desktop_layout(self):
        layout = ModernCookieRunBotGUI._layout_for_screen(1920, 1080)

        self.assertEqual((layout["width"], layout["height"]), (1380, 900))
        self.assertFalse(layout["compact"])
        self.assertEqual(layout["sidebar_width"], 238)
        self.assertFalse(layout["stack_settings"])
        self.assertEqual(layout["summary_columns"], 4)
        self.assertEqual(layout["profile_columns"], 2)

    def test_1024_by_768_uses_scrollable_compact_layout(self):
        layout = ModernCookieRunBotGUI._layout_for_screen(1024, 768)

        self.assertEqual((layout["width"], layout["height"]), (992, 656))
        self.assertEqual((layout["x"], layout["y"]), (16, 32))
        self.assertTrue(layout["compact"])
        self.assertEqual(layout["sidebar_width"], 218)
        self.assertTrue(layout["stack_settings"])
        self.assertEqual(layout["summary_columns"], 2)
        self.assertEqual(layout["profile_columns"], 1)
        self.assertEqual(layout["metric_columns"], 4)

    def test_800_by_600_keeps_everything_inside_the_display(self):
        layout = ModernCookieRunBotGUI._layout_for_screen(800, 600)

        self.assertLessEqual(layout["width"], 800)
        self.assertLessEqual(layout["height"], 600)
        self.assertTrue(layout["compact"])
        self.assertEqual(layout["sidebar_width"], 196)
        self.assertEqual(layout["summary_columns"], 2)
        self.assertEqual(layout["profile_columns"], 1)
        self.assertEqual(layout["metric_columns"], 2)

    def test_windows_scaling_is_applied_only_once(self):
        layout = ModernCookieRunBotGUI._layout_for_screen(1920, 1080, 1.5)

        self.assertEqual((layout["width"], layout["height"]), (1248, 608))
        self.assertEqual((layout["x"], layout["y"]), (24, 48))
        self.assertTrue(layout["compact"])
        self.assertLessEqual(round(layout["width"] * 1.5), 1920)
        self.assertLessEqual(round(layout["height"] * 1.5), 1080 - 100)


if __name__ == "__main__":
    unittest.main()
