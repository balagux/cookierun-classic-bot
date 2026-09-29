import unittest
from unittest import mock

from modern_gui import ModernCookieRunBotGUI


class _Value:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class ModernGuiHealthTests(unittest.TestCase):
    def _gui(self):
        gui = object.__new__(ModernCookieRunBotGUI)
        gui.status_var = _Value()
        gui.status_label = mock.Mock()
        gui.health_vars = {key: _Value() for key in ("ADB", "SCREEN", "DETECT", "STATE")}
        gui.health_labels = {key: mock.Mock() for key in gui.health_vars}
        return gui

    def test_connection_success_only_marks_proven_layers_healthy(self):
        gui = self._gui()

        gui._set_status("เชื่อมต่อสำเร็จ", "success")

        self.assertEqual(gui.health_vars["ADB"].get(), "● OK")
        self.assertEqual(gui.health_vars["SCREEN"].get(), "● OK")
        self.assertEqual(gui.health_vars["DETECT"].get(), "● IDLE")
        self.assertEqual(gui.health_vars["STATE"].get(), "● IDLE")

    def test_bot_running_marks_preflight_layers_healthy(self):
        gui = self._gui()

        gui._set_status("บอทกำลังทำงาน", "running")

        self.assertTrue(all(value.get() == "● OK" for value in gui.health_vars.values()))

    def test_health_state_updates_visual_color(self):
        gui = self._gui()

        gui._set_health("SCREEN", "error")

        self.assertEqual(gui.health_vars["SCREEN"].get(), "● ERROR")
        gui.health_labels["SCREEN"].configure.assert_called_once_with(text_color="#B02D4A")


if __name__ == "__main__":
    unittest.main()
