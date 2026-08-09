import unittest
from unittest import mock

import bot


class BotRestartFailureTests(unittest.TestCase):
    def test_failed_restart_is_propagated_to_worker(self):
        with (
            mock.patch.object(bot, "device_reset_app", return_value=False),
            mock.patch("builtins.print") as output,
        ):
            with self.assertRaisesRegex(RuntimeError, "could not be restarted"):
                bot._reset_app_or_raise("The game could not be restarted.")

        self.assertTrue(
            any("[BOT_STOPPED]" in str(call.args[0]) for call in output.call_args_list)
        )

    def test_successful_restart_returns_normally(self):
        with mock.patch.object(bot, "device_reset_app", return_value=True):
            self.assertIsNone(bot._reset_app_or_raise("unused"))


if __name__ == "__main__":
    unittest.main()
