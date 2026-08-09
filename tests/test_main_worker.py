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


if __name__ == "__main__":
    unittest.main()
