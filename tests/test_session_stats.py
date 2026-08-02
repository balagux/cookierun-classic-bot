import unittest
import tkinter as tk

from gui import CookieRunBotGUI


class SessionStatsTests(unittest.TestCase):
    def test_average_is_zero_before_any_completed_run(self):
        self.assertEqual(CookieRunBotGUI._format_session_average(500, 0), "0")

    def test_average_uses_completed_runs(self):
        self.assertEqual(CookieRunBotGUI._format_session_average(3600, 3), "1,200")
        self.assertEqual(CookieRunBotGUI._format_session_average(10, 4), "2.5")

    def test_summary_variables_include_totals_and_averages(self):
        interpreter = tk.Tcl()
        gui = CookieRunBotGUI.__new__(CookieRunBotGUI)
        gui.session_stats_var = tk.StringVar(interpreter)
        gui.session_runs_var = tk.StringVar(interpreter)
        gui.session_coins_total_var = tk.StringVar(interpreter)
        gui.session_coins_average_var = tk.StringVar(interpreter)
        gui.session_exp_total_var = tk.StringVar(interpreter)
        gui.session_exp_average_var = tk.StringVar(interpreter)

        gui._set_session_stats(4, 3, 269758, 9294)

        self.assertEqual(gui.session_runs_var.get(), "3 / 4")
        self.assertEqual(gui.session_coins_total_var.get(), "269,758")
        self.assertEqual(gui.session_coins_average_var.get(), "เฉลี่ย 89,919.3 / รอบ")
        self.assertEqual(gui.session_exp_total_var.get(), "9,294")
        self.assertEqual(gui.session_exp_average_var.get(), "เฉลี่ย 3,098 / รอบ")


if __name__ == "__main__":
    unittest.main()
