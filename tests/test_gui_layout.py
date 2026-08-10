import unittest

from modern_gui import ModernCookieRunBotGUI


class GuiLayoutTests(unittest.TestCase):
    def test_large_screen_uses_small_companion_window(self):
        layout = ModernCookieRunBotGUI._layout_for_screen(1920, 1080)

        self.assertEqual((layout["width"], layout["height"]), (720, 500))
        self.assertEqual((layout["x"], layout["y"]), (600, 290))
        self.assertTrue(layout["compact"])
        self.assertEqual(layout["sidebar_width"], 180)
        self.assertTrue(layout["stack_settings"])
        self.assertFalse(layout["narrow_controls"])
        self.assertEqual(layout["relic_switch_row"], 1)
        self.assertEqual(layout["boost_combo_row"], 2)
        self.assertEqual(layout["summary_columns"], 2)

    def test_1024_by_768_keeps_the_same_compact_controller(self):
        layout = ModernCookieRunBotGUI._layout_for_screen(1024, 768)

        self.assertEqual((layout["width"], layout["height"]), (720, 500))
        self.assertEqual((layout["x"], layout["y"]), (152, 134))
        self.assertTrue(layout["compact"])
        self.assertEqual(layout["sidebar_width"], 180)
        self.assertTrue(layout["stack_settings"])
        self.assertFalse(layout["narrow_controls"])
        self.assertEqual(layout["relic_switch_row"], 1)
        self.assertEqual(layout["boost_combo_row"], 2)
        self.assertEqual(layout["summary_columns"], 2)

    def test_800_by_600_keeps_everything_inside_the_display(self):
        layout = ModernCookieRunBotGUI._layout_for_screen(800, 600)

        self.assertEqual((layout["width"], layout["height"]), (720, 500))
        self.assertEqual((layout["x"], layout["y"]), (40, 20))
        self.assertTrue(layout["compact"])
        self.assertEqual(layout["sidebar_width"], 180)
        self.assertEqual(layout["summary_columns"], 2)
        self.assertFalse(layout["narrow_controls"])
        self.assertEqual(layout["relic_switch_row"], 1)
        self.assertEqual(layout["boost_combo_row"], 2)

    def test_windows_scaling_is_applied_only_once(self):
        layout = ModernCookieRunBotGUI._layout_for_screen(1920, 1080, 1.5)

        self.assertEqual((layout["width"], layout["height"]), (720, 500))
        self.assertEqual((layout["x"], layout["y"]), (420, 165))
        self.assertTrue(layout["compact"])
        self.assertLessEqual(round(layout["width"] * 1.5), 1920)
        self.assertLessEqual(round(layout["height"] * 1.5), 1080 - 100)
        self.assertFalse(layout["narrow_controls"])
        self.assertEqual(layout["relic_switch_row"], 1)
        self.assertEqual(layout["boost_combo_row"], 2)

    def test_small_hidpi_screen_stacks_wide_controls(self):
        layout = ModernCookieRunBotGUI._layout_for_screen(800, 600, 1.5)

        self.assertEqual((layout["width"], layout["height"]), (533, 400))
        self.assertEqual((layout["x"], layout["y"]), (0, 0))
        self.assertTrue(layout["narrow_controls"])
        self.assertEqual(layout["relic_switch_row"], 3)
        self.assertEqual(layout["boost_combo_row"], 4)
        self.assertLess(layout["content_width"], 500)


if __name__ == "__main__":
    unittest.main()
