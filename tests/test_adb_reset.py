import unittest
from unittest import mock

import adb


class AdbResetTests(unittest.TestCase):
    def test_reset_uses_short_health_check_instead_of_old_ninety_second_wait(self):
        with (
            mock.patch.object(adb, "_resolve_device_target", return_value="emulator-5556"),
            mock.patch.object(adb, "adb_run"),
            mock.patch.object(adb, "device_is_app_running", side_effect=(True, True)),
            mock.patch.object(adb.time, "sleep") as sleep,
            mock.patch("builtins.print"),
        ):
            adb.device_reset_app("127.0.0.1", 5556, max_retries=1)

        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1.0, 3.0])


if __name__ == "__main__":
    unittest.main()
