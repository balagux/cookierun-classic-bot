import builtins
import importlib
import unittest
from unittest import mock


class MainWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original_print = builtins.print
        cls.main_module = importlib.import_module("main")
        # main.py timestamps worker output by replacing builtins.print. Tests
        # restore it immediately so importing this module cannot affect others.
        builtins.print = original_print

    def test_run_bot_exception_returns_error_instead_of_escaping(self):
        with (
            mock.patch.object(
                self.main_module,
                "run_bot",
                side_effect=RuntimeError("app failed to start"),
            ),
            mock.patch("builtins.print") as output,
        ):
            exit_code = self.main_module.main(["--run-bot"])

        self.assertEqual(exit_code, 1)
        self.assertTrue(
            any(
                "Bot stopped safely" in str(call.args[0])
                and "app failed to start" in str(call.args[0])
                for call in output.call_args_list
            )
        )

    def test_wait_relay_death_disables_only_the_quick_exit(self):
        args = self.main_module.build_parser().parse_args(
            ["--run-bot", "--cookie-relay", "--wait-relay-death"]
        )

        options = self.main_module._options_from_args(args)

        self.assertTrue(options["use_cookie_relay"])
        self.assertFalse(options["quick_exit_after_relay"])

    def test_relay_quick_exit_is_disabled_without_an_explicit_setting(self):
        args = self.main_module.build_parser().parse_args(
            ["--run-bot", "--cookie-relay"]
        )

        options = self.main_module._options_from_args(args)

        self.assertTrue(options["use_cookie_relay"])
        self.assertFalse(options["quick_exit_after_relay"])

    def test_relay_quick_exit_can_be_enabled_explicitly(self):
        args = self.main_module.build_parser().parse_args(
            ["--run-bot", "--cookie-relay", "--quick-exit-after-relay"]
        )

        options = self.main_module._options_from_args(args)

        self.assertTrue(options["quick_exit_after_relay"])

    def test_send_hearts_mode_calls_one_shot_worker(self):
        with mock.patch.object(
            self.main_module,
            "send_friend_hearts",
            return_value=4,
        ) as send_hearts:
            exit_code = self.main_module.main(
                [
                    "--send-hearts",
                    "--device-ip",
                    "127.0.0.9",
                    "--device-port",
                    "5566",
                ]
            )

        self.assertEqual(exit_code, 0)
        send_hearts.assert_called_once_with(
            device_ip="127.0.0.9",
            device_port=5566,
        )

    def test_send_hearts_exception_returns_error_instead_of_escaping(self):
        with (
            mock.patch.object(
                self.main_module,
                "send_friend_hearts",
                side_effect=RuntimeError("open the leaderboard"),
            ),
            mock.patch("builtins.print") as output,
        ):
            exit_code = self.main_module.main(["--send-hearts"])

        self.assertEqual(exit_code, 1)
        self.assertTrue(
            any(
                "Sending hearts stopped safely" in str(call.args[0])
                and "open the leaderboard" in str(call.args[0])
                for call in output.call_args_list
            )
        )


if __name__ == "__main__":
    unittest.main()
