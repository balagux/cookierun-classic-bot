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
        gui.session_last_run_duration_var = MemoryVariable()
        gui.session_average_run_duration_var = MemoryVariable()
        gui.box_wood_total_var = MemoryVariable()
        gui.box_wood_average_var = MemoryVariable()
        gui.box_silver_total_var = MemoryVariable()
        gui.box_silver_average_var = MemoryVariable()
        gui.box_gold_total_var = MemoryVariable()
        gui.box_gold_average_var = MemoryVariable()
        gui.box_rainbow_total_var = MemoryVariable()
        gui.box_rainbow_average_var = MemoryVariable()
        gui.box_total_var = MemoryVariable()
        gui.box_total_average_var = MemoryVariable()
        gui.box_unknown_detail_var = MemoryVariable()
        gui._session_completed_runs = 0
        gui._box_stats_counts = gui._empty_box_stats()
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

    def test_duration_stats_line_updates_latest_and_average(self):
        gui = self._make_gui()

        gui._update_session_stats(
            "[STATS] attempts=4 completed=3 coins=269758 exp=9294 "
            "last_run_seconds=125.7 total_run_seconds=371.0 timed_runs=3"
        )

        self.assertEqual(gui.session_last_run_duration_var.get(), "02:06")
        self.assertEqual(
            gui.session_average_run_duration_var.get(),
            "เฉลี่ย 02:04 / รอบ",
        )

    def test_legacy_stats_line_remains_supported(self):
        gui = self._make_gui()
        gui._reset_run_duration_stats()

        gui._update_session_stats(
            "[STATS] attempts=1 completed=0 coins=0 exp=0"
        )

        self.assertEqual(gui.session_runs_var.get(), "0 / 1")
        self.assertEqual(gui.session_last_run_duration_var.get(), "--:--")
        self.assertEqual(
            gui.session_average_run_duration_var.get(),
            "เฉลี่ย --:-- / รอบ",
        )

    def test_duration_format_adds_hours_only_when_needed(self):
        self.assertEqual(CookieRunBotGUI._format_run_duration(59.4), "00:59")
        self.assertEqual(CookieRunBotGUI._format_run_duration(125.7), "02:06")
        self.assertEqual(CookieRunBotGUI._format_run_duration(3661), "01:01:01")

    def test_zero_timed_runs_show_placeholders(self):
        gui = self._make_gui()

        gui._set_run_duration_stats(0.0, 0.0, 0)

        self.assertEqual(gui.session_last_run_duration_var.get(), "--:--")
        self.assertEqual(
            gui.session_average_run_duration_var.get(),
            "เฉลี่ย --:-- / รอบ",
        )

    def test_box_stats_protocol_is_order_independent_and_includes_silver(self):
        gui = self._make_gui()
        gui._set_session_stats(4, 4, 0, 0)

        gui._update_box_stats(
            "[BOX_STATS] rainbow=2 total=15 wood=6 unknown=1 "
            "gold=3 silver=3"
        )

        self.assertEqual(gui.box_wood_total_var.get(), "6")
        self.assertEqual(gui.box_silver_total_var.get(), "3")
        self.assertEqual(gui.box_gold_total_var.get(), "3")
        self.assertEqual(gui.box_rainbow_total_var.get(), "2")
        self.assertEqual(gui.box_total_var.get(), "15")
        self.assertEqual(gui.box_total_average_var.get(), "เฉลี่ย 3.8 / รอบ")
        self.assertEqual(gui.box_wood_average_var.get(), "เฉลี่ย 1.5 / รอบ")
        self.assertIn("1 กล่อง", gui.box_unknown_detail_var.get())

    def test_incomplete_or_legacy_box_lines_do_not_mutate_stats(self):
        gui = self._make_gui()
        gui._set_box_stats(wood=2, silver=1, gold=0, rainbow=0, total=3)

        gui._update_box_stats("[BOX_STATS] wood=99 gold=99")
        gui._update_box_stats("collected a wooden mystery box")

        self.assertEqual(gui.box_wood_total_var.get(), "2")
        self.assertEqual(gui.box_silver_total_var.get(), "1")
        self.assertEqual(gui.box_total_var.get(), "3")

    def test_box_average_refreshes_when_completed_run_count_changes(self):
        gui = self._make_gui()
        gui._set_box_stats(wood=3, silver=2, gold=1, rainbow=0, total=6)

        gui._set_session_stats(2, 2, 0, 0)

        self.assertEqual(gui.box_total_average_var.get(), "เฉลี่ย 3 / รอบ")
        self.assertEqual(gui.box_silver_average_var.get(), "เฉลี่ย 1 / รอบ")

    def test_new_session_resets_rewards_and_stopped_session_keeps_elapsed_time(self):
        gui = self._make_gui()
        gui._set_session_stats(8, 7, 7000, 350)
        gui._set_box_stats(wood=9, silver=4, gold=2, rainbow=1, total=16)

        with mock.patch.object(gui_module.time, "monotonic", side_effect=(100.0, 4661.9)):
            gui._begin_bot_session()
            elapsed = gui._finish_bot_session()

        self.assertEqual(gui.session_runs_var.get(), "0 / 0")
        self.assertEqual(gui.session_coins_total_var.get(), "0")
        self.assertEqual(gui.session_coins_average_var.get(), "เฉลี่ย 0 / รอบ")
        self.assertEqual(gui.session_exp_total_var.get(), "0")
        self.assertEqual(gui.session_exp_average_var.get(), "เฉลี่ย 0 / รอบ")
        self.assertEqual(gui.session_last_run_duration_var.get(), "--:--")
        self.assertEqual(
            gui.session_average_run_duration_var.get(),
            "เฉลี่ย --:-- / รอบ",
        )
        self.assertEqual(gui.box_wood_total_var.get(), "0")
        self.assertEqual(gui.box_silver_total_var.get(), "0")
        self.assertEqual(gui.box_gold_total_var.get(), "0")
        self.assertEqual(gui.box_rainbow_total_var.get(), "0")
        self.assertEqual(gui.box_total_var.get(), "0")
        self.assertEqual(gui.box_total_average_var.get(), "เฉลี่ย 0 / รอบ")
        self.assertEqual(gui.box_unknown_detail_var.get(), "ยังไม่พบกล่องในรอบนี้")
        self.assertEqual(elapsed, "01:16:01")
        self.assertEqual(gui.session_elapsed_var.get(), "01:16:01")
        self.assertEqual(gui.session_elapsed_detail_var.get(), "เวลารวมหลังหยุด")


if __name__ == "__main__":
    unittest.main()
