import unittest
from unittest import mock

import gui as gui_module
from gui import CookieRunBotGUI


class MemoryVariable:
    def __init__(self):
        self.value = ""

    def set(self, value):
        self.value = str(value)

    def get(self):
        return self.value


class SessionStatsTests(unittest.TestCase):
    @staticmethod
    def _make_gui():
        gui = CookieRunBotGUI.__new__(CookieRunBotGUI)
        gui.session_stats_var = MemoryVariable()
        gui.session_runs_var = MemoryVariable()
        gui.session_coins_total_var = MemoryVariable()
        gui.session_coins_average_var = MemoryVariable()
        gui.session_exp_total_var = MemoryVariable()
        gui.session_exp_average_var = MemoryVariable()
        gui.session_elapsed_var = MemoryVariable()
        gui.session_elapsed_detail_var = MemoryVariable()
        gui._session_started_at = None
        gui._session_last_elapsed_second = None
        return gui

    def test_average_is_zero_before_any_completed_run(self):
        self.assertEqual(CookieRunBotGUI._format_session_average(500, 0), "0")

    def test_average_uses_completed_runs(self):
        self.assertEqual(CookieRunBotGUI._format_session_average(3600, 3), "1,200")
        self.assertEqual(CookieRunBotGUI._format_session_average(10, 4), "2.5")

    def test_summary_variables_include_totals_and_averages(self):
        gui = self._make_gui()

        gui._set_session_stats(4, 3, 269758, 9294)

        self.assertEqual(gui.session_runs_var.get(), "3 / 4")
        self.assertEqual(gui.session_coins_total_var.get(), "269,758")
        self.assertEqual(gui.session_coins_average_var.get(), "เฉลี่ย 89,919.3 / รอบ")
        self.assertEqual(gui.session_exp_total_var.get(), "9,294")
        self.assertEqual(gui.session_exp_average_var.get(), "เฉลี่ย 3,098 / รอบ")

    def test_new_session_resets_rewards_and_stopped_session_keeps_elapsed_time(self):
        gui = self._make_gui()
        gui._set_session_stats(8, 7, 7000, 350)

        with mock.patch.object(gui_module.time, "monotonic", side_effect=(100.0, 4661.9)):
            gui._begin_bot_session()
            elapsed = gui._finish_bot_session()

        self.assertEqual(gui.session_runs_var.get(), "0 / 0")
        self.assertEqual(gui.session_coins_total_var.get(), "0")
        self.assertEqual(gui.session_coins_average_var.get(), "เฉลี่ย 0 / รอบ")
        self.assertEqual(gui.session_exp_total_var.get(), "0")
        self.assertEqual(gui.session_exp_average_var.get(), "เฉลี่ย 0 / รอบ")
        self.assertEqual(elapsed, "01:16:01")
        self.assertEqual(gui.session_elapsed_var.get(), "01:16:01")
        self.assertEqual(gui.session_elapsed_detail_var.get(), "เวลารวมหลังหยุด")


if __name__ == "__main__":
    unittest.main()
