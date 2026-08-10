import builtins
import importlib
import unittest
from unittest import mock

import actions
import bot
from config import RELIC_CLAIM_BUTTON, RELIC_CLOSE_BUTTON


_original_print = builtins.print
main = importlib.import_module("main")
builtins.print = _original_print


class RelicRewardTests(unittest.TestCase):
    def test_auto_claim_remains_enabled_by_default(self):
        self.assertTrue(bot.should_claim_relic_rewards({}))
        args = main.build_parser().parse_args(["--run-bot"])
        self.assertTrue(main._options_from_args(args)["claim_relic_rewards"])

    def test_keep_parts_cli_option_disables_claiming(self):
        args = main.build_parser().parse_args(
            ["--run-bot", "--keep-relic-parts"]
        )
        self.assertFalse(main._options_from_args(args)["claim_relic_rewards"])

    def test_keep_parts_ignores_get_button_but_can_close_open_claim_dialog(self):
        normal = bot.get_detection_stage_names(
            "PRE_GAME", claim_relic_rewards=True
        )
        keeping = bot.get_detection_stage_names(
            "PRE_GAME", claim_relic_rewards=False
        )
        recovery = bot.get_recovery_stage_names(claim_relic_rewards=False)

        self.assertIn("RELIC_COMPLETE", normal)
        self.assertNotIn("RELIC_COMPLETE", keeping)
        self.assertNotIn("RELIC_COMPLETE", recovery)
        self.assertIn("RELIC_CLAIM", keeping)
        self.assertIn("RELIC_CLAIM", recovery)

    def test_close_without_reward_never_taps_claim_button(self):
        with (
            mock.patch.object(actions, "safe_device_tap") as tap,
            mock.patch.object(actions.time, "sleep"),
        ):
            actions.close_relic_claim_without_reward()

        tapped_points = [(call.args[2], call.args[3]) for call in tap.call_args_list]
        self.assertEqual(tapped_points, [RELIC_CLOSE_BUTTON])
        self.assertNotIn(RELIC_CLAIM_BUTTON, tapped_points)


if __name__ == "__main__":
    unittest.main()
