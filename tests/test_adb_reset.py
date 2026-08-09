import unittest
from unittest import mock

import adb


class AdbResetTests(unittest.TestCase):
    def test_reset_uses_short_health_check_instead_of_old_ninety_second_wait(self):
        completed = mock.Mock(returncode=0, stdout="", stderr="")
        with (
            mock.patch.object(adb, "_resolve_device_target", return_value="emulator-5556"),
            mock.patch.object(adb, "adb_run", return_value=completed) as adb_command,
            mock.patch.object(adb, "device_is_app_running", side_effect=(True, True)),
            mock.patch.object(adb.time, "sleep") as sleep,
            mock.patch("builtins.print"),
        ):
            result = adb.device_reset_app("127.0.0.1", 5556, max_retries=1)

        self.assertTrue(result)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1.0, 1.0])
        commands = [call.args[0] for call in adb_command.call_args_list]
        self.assertFalse(any("resolve-activity" in command for command in commands))

    def test_reset_returns_false_instead_of_crashing_gui_when_launch_fails(self):
        completed = mock.Mock(returncode=0, stdout="", stderr="")
        with (
            mock.patch.object(adb, "_resolve_device_target", return_value="emulator-5556"),
            mock.patch.object(adb, "adb_run", return_value=completed),
            mock.patch.object(adb, "device_is_app_running", return_value=False),
            mock.patch.object(adb.time, "sleep"),
            mock.patch("builtins.print") as output,
        ):
            result = adb.device_reset_app(
                "127.0.0.1",
                5556,
                max_retries=2,
                launch_timeout=0,
                retry_delay=0,
            )

        self.assertFalse(result)
        lines = [str(call.args[0]) for call in output.call_args_list]
        self.assertTrue(any("[APP_START_FAILED]" in line for line in lines))
        self.assertTrue(any("window will remain open" in line for line in lines))

    def test_reset_can_still_raise_when_fatal_behavior_is_requested(self):
        completed = mock.Mock(returncode=0, stdout="", stderr="")
        with (
            mock.patch.object(adb, "_resolve_device_target", return_value="emulator-5556"),
            mock.patch.object(adb, "adb_run", return_value=completed),
            mock.patch.object(adb, "device_is_app_running", return_value=False),
            mock.patch.object(adb.time, "sleep"),
            mock.patch("builtins.print"),
        ):
            with self.assertRaises(adb.DeviceAppStartError):
                adb.device_reset_app(
                    "127.0.0.1",
                    5556,
                    max_retries=1,
                    launch_timeout=0,
                    retry_delay=0,
                    raise_on_failure=True,
                )

    def test_reset_uses_resolved_launcher_activity_as_fallback(self):
        def fake_adb_run(command, **_kwargs):
            if "resolve-activity" in command:
                return mock.Mock(
                    returncode=0,
                    stdout="com.devsisters.crg/.CookieRunActivity\n",
                    stderr="",
                )
            return mock.Mock(returncode=0, stdout="", stderr="")

        with (
            mock.patch.object(adb, "_resolve_device_target", return_value="emulator-5556"),
            mock.patch.object(adb, "adb_run", side_effect=fake_adb_run) as adb_command,
            mock.patch.object(adb, "device_is_app_running", side_effect=(False, True, True)),
            mock.patch.object(adb.time, "sleep"),
            mock.patch("builtins.print"),
        ):
            result = adb.device_reset_app(
                "127.0.0.1",
                5556,
                max_retries=1,
                launch_timeout=0,
            )

        self.assertTrue(result)
        commands = [call.args[0] for call in adb_command.call_args_list]
        self.assertTrue(
            any(
                command[-4:] == [
                    "am",
                    "start",
                    "-n",
                    "com.devsisters.crg/.CookieRunActivity",
                ]
                for command in commands
            )
        )


if __name__ == "__main__":
    unittest.main()
