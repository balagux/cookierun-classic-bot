import io
import unittest
from unittest import mock

import numpy as np

import bot
from bot import BoxSessionStats, _print_box_stats


class BoxSessionStatsTests(unittest.TestCase):
    def test_snapshot_starts_at_zero_for_all_types(self):
        stats = BoxSessionStats()

        self.assertEqual(
            stats.snapshot(),
            {
                "wood": 0,
                "silver": 0,
                "gold": 0,
                "rainbow": 0,
                "unknown": 0,
                "total": 0,
            },
        )

    def test_stale_or_incomplete_run_popup_is_not_counted(self):
        stats = BoxSessionStats()

        self.assertFalse(stats.record_popup(["gold"]))
        stats.begin_run()
        self.assertFalse(stats.record_popup(["rainbow"]))

        self.assertEqual(stats.snapshot()["total"], 0)

    def test_completed_run_counts_every_box_on_popup_once(self):
        stats = BoxSessionStats()
        stats.begin_run()
        self.assertTrue(stats.complete_run())

        self.assertTrue(
            stats.record_popup(
                ["wood", "silver", "wood", "gold", "rainbow"]
            )
        )
        self.assertFalse(stats.record_popup(["wood", "wood"]))

        self.assertEqual(
            stats.snapshot(),
            {
                "wood": 2,
                "silver": 1,
                "gold": 1,
                "rainbow": 1,
                "unknown": 0,
                "total": 5,
            },
        )

    def test_empty_result_is_not_changed_to_unknown_and_can_retry(self):
        stats = BoxSessionStats()
        stats.begin_run()
        stats.complete_run()

        self.assertFalse(stats.record_popup([]))
        self.assertFalse(stats.popup_recorded)
        self.assertTrue(stats.record_popup(["unknown"]))

        self.assertEqual(stats.snapshot()["unknown"], 1)
        self.assertEqual(stats.snapshot()["total"], 1)

    def test_unexpected_individual_label_is_preserved_as_unknown(self):
        stats = BoxSessionStats()
        stats.begin_run()
        stats.complete_run()

        self.assertTrue(stats.record_popup(["SILVER", "future-box", None]))

        self.assertEqual(stats.snapshot()["silver"], 1)
        self.assertEqual(stats.snapshot()["unknown"], 2)

    def test_cancel_and_close_block_late_popups_but_keep_session_totals(self):
        stats = BoxSessionStats()
        stats.begin_run()
        stats.complete_run()
        stats.record_popup(["gold"])

        stats.begin_run()
        stats.complete_run()
        stats.cancel_run()  # interruption, reset, or connection recovery
        self.assertFalse(stats.record_popup(["rainbow"]))

        stats.begin_run()
        stats.complete_run()
        stats.close_run()  # direct return to Main Menu
        self.assertFalse(stats.record_popup(["wood"]))

        self.assertEqual(stats.snapshot()["gold"], 1)
        self.assertEqual(stats.snapshot()["total"], 1)

    def test_new_completed_run_can_record_a_new_popup(self):
        stats = BoxSessionStats()
        stats.begin_run()
        stats.complete_run()
        stats.record_popup(["wood"])
        stats.close_run()

        stats.begin_run()
        stats.complete_run()
        self.assertTrue(stats.record_popup(["silver", "gold"]))

        self.assertEqual(stats.snapshot()["total"], 3)

    def test_protocol_line_has_stable_field_order(self):
        stats = BoxSessionStats()
        stats.begin_run()
        stats.complete_run()
        stats.record_popup(["wood", "silver", "gold", "rainbow", "unknown"])

        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            _print_box_stats(stats)

        self.assertEqual(
            output.getvalue(),
            "[BOX_STATS] wood=1 silver=1 gold=1 rainbow=1 unknown=1 total=5\n",
        )


class BoxStatsMainLifecycleTests(unittest.TestCase):
    def _options(self, max_runs=1):
        return {
            "use_fast_start": False,
            "use_cookie_relay": False,
            "use_desired_random_boost": False,
            "desired_boost_template": None,
            "desired_boost_name": None,
            "claim_relic_rewards": True,
            "max_runs": max_runs,
        }

    def test_duplicate_mystery_box_stage_counts_dialog_only_once(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        output = io.StringIO()
        stages = [
            "PURCHASE_ITEM",
            "GAME_COMPLETE",
            "MYSTERY_BOX",
            "MYSTERY_BOX",
            "MAINMENU",
        ]

        with (
            mock.patch.object(bot, "device_connect"),
            mock.patch.object(bot, "device_capture_screen", return_value=screen),
            mock.patch.object(bot, "load_templates"),
            mock.patch.object(bot, "detect_all_template_matches", return_value=[]),
            mock.patch.object(bot, "detect_stage", side_effect=stages),
            mock.patch.object(bot, "play_game"),
            mock.patch.object(bot, "complete_finish"),
            mock.patch.object(bot, "accept_mystery_box") as accept_box,
            mock.patch.object(
                bot,
                "detect_mystery_box_types",
                return_value=["wood", "silver", "gold", "rainbow"],
            ),
            mock.patch.object(
                bot,
                "_read_stable_result_rewards",
                return_value=(0, 0, {"coins": None, "exp": None}, screen, True),
            ),
            mock.patch.object(bot.time, "sleep"),
            mock.patch("sys.stdout", output),
        ):
            bot.main(self._options())

        self.assertEqual(accept_box.call_count, 2)
        self.assertEqual(
            output.getvalue().count(
                "[BOX_STATS] wood=1 silver=1 gold=1 rainbow=1 unknown=0 total=4"
            ),
            1,
        )

    def test_stale_popup_and_connection_reset_do_not_change_totals(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        output = io.StringIO()

        with (
            mock.patch.object(bot, "device_connect"),
            mock.patch.object(
                bot,
                "device_capture_screen",
                side_effect=[screen, screen, screen, KeyboardInterrupt()],
            ),
            mock.patch.object(bot, "load_templates"),
            mock.patch.object(bot, "detect_all_template_matches", return_value=[]),
            mock.patch.object(
                bot,
                "detect_stage",
                side_effect=["MYSTERY_BOX", "CONNECTION_LOST"],
            ),
            mock.patch.object(bot, "detect_mystery_box_types", return_value=["gold"]),
            mock.patch.object(bot, "accept_mystery_box") as accept_box,
            mock.patch.object(bot, "_reset_app_or_raise"),
            mock.patch.object(bot, "close_announcement_dialog"),
            mock.patch.object(bot.time, "sleep"),
            mock.patch("sys.stdout", output),
        ):
            bot.main(self._options(max_runs=0))

        accept_box.assert_called_once_with()
        self.assertIn(
            "[BOX_STATS] wood=0 silver=0 gold=0 rainbow=0 unknown=0 total=0",
            output.getvalue(),
        )
        self.assertNotIn("[BOX_STATS] wood=0 silver=0 gold=1", output.getvalue())
        self.assertIn("Ignored a Mystery Box popup", output.getvalue())


if __name__ == "__main__":
    unittest.main()
