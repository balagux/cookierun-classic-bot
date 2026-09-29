import unittest
from unittest import mock

import adb


class AdbResetTests(unittest.TestCase):
    def test_adb_run_has_a_bounded_default_timeout(self):
        completed = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(adb.subprocess, "run", return_value=completed) as run:
            adb.adb_run(["adb", "devices"])

            self.assertEqual(run.call_args.kwargs["timeout"], adb.ADB_COMMAND_TIMEOUT)
            self.assertEqual(run.call_args.kwargs["creationflags"], adb.ADB_SUBPROCESS_FLAGS)

            run.reset_mock()
            adb.adb_run(["adb", "devices"], timeout=1.25)

            self.assertEqual(run.call_args.kwargs["timeout"], 1.25)

    def test_find_adb_falls_back_to_ldplayer_install(self):
        ldplayer = r"D:\LDPlayer\LDPlayer14\adb.exe"

        def exists(candidate):
            return str(candidate) == ldplayer

        with (
            mock.patch.object(adb.Path, "exists", autospec=True, side_effect=exists),
            mock.patch.object(adb.shutil, "which", return_value=None),
        ):
            self.assertEqual(adb._find_adb_executable(), ldplayer)

    def test_remote_host_does_not_resolve_to_local_emulator(self):
        with (
            mock.patch.dict(adb._DEVICE_TARGET_CACHE, {}, clear=True),
            mock.patch.object(adb, "adb_run") as adb_command,
        ):
            target = adb._resolve_device_target("192.168.1.20", 5556)

        self.assertEqual(target, "192.168.1.20:5556")
        adb_command.assert_not_called()

    def test_tap_failures_are_reported(self):
        failed = mock.Mock(returncode=1, stdout="", stderr="device offline")
        with (
            mock.patch.object(adb, "_resolve_device_target", return_value="emulator-5556"),
            mock.patch.object(adb, "adb_run", return_value=failed),
        ):
            with self.assertRaisesRegex(RuntimeError, "device offline"):
                adb.device_tap("127.0.0.1", 5556, 100, 200)
            with self.assertRaisesRegex(RuntimeError, "device offline"):
                adb.safe_device_tap("127.0.0.1", 5556, 100, 200)
            with self.assertRaisesRegex(RuntimeError, "device offline"):
                adb.device_back("127.0.0.1", 5556)

    def test_deterministic_scroll_uses_exact_requested_coordinates(self):
        completed = mock.Mock(returncode=0, stdout="", stderr="")
        with (
            mock.patch.object(adb, "_resolve_device_target", return_value="emulator-5556"),
            mock.patch.object(adb, "adb_run", return_value=completed) as adb_command,
        ):
            adb.device_scroll(
                "127.0.0.1",
                5556,
                435,
                447,
                direction="up",
                distance=150,
                duration=150,
            )

        command = adb_command.call_args.args[0]
        self.assertEqual(
            command[-6:],
            ["swipe", "435", "597", "435", "297", "150"],
        )

    def test_deterministic_scroll_propagates_an_adb_failure(self):
        failed = mock.Mock(returncode=1, stdout="", stderr="device offline")
        with (
            mock.patch.object(adb, "_resolve_device_target", return_value="emulator-5556"),
            mock.patch.object(adb, "adb_run", return_value=failed),
            self.assertRaisesRegex(RuntimeError, "device offline"),
        ):
            adb.device_scroll(
                "127.0.0.1",
                5556,
                435,
                447,
                direction="up",
                distance=90,
                duration=400,
            )

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
