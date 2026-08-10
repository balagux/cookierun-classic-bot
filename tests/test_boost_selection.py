import unittest
from unittest import mock

import cv2
import numpy as np

import actions
from config import (
    MULTI_BUY_BUTTON,
    RANDOM_BOOST_DIALOG_CLOSE_BUTTON,
    RANDOM_BOOST_SELECTION_BUTTONS,
)


class _BoostDialog:
    def __init__(self, checked_names, ignore_taps=False):
        self.checked_names = set(checked_names)
        self.ignore_taps = ignore_taps
        self.taps = []

    def capture(self):
        screen = np.zeros((720, 1280, 3), dtype=np.uint8)
        for name in self.checked_names:
            x, y = RANDOM_BOOST_SELECTION_BUTTONS[name]
            cv2.circle(screen, (x, y), 12, (0, 255, 0), -1)
        return screen

    def tap(self, x, y):
        self.taps.append((x, y))
        if self.ignore_taps:
            return
        for name, button in RANDOM_BOOST_SELECTION_BUTTONS.items():
            if button == (x, y):
                if name in self.checked_names:
                    self.checked_names.remove(name)
                else:
                    self.checked_names.add(name)
                return


class BoostSelectionTests(unittest.TestCase):
    def test_single_existing_target_needs_no_tap(self):
        dialog = _BoostDialog({"Double Coins"})

        result = actions.sync_desired_boost_selection(
            "Double Coins",
            capture_func=dialog.capture,
            tap_func=dialog.tap,
            sleep_func=lambda _seconds: None,
        )

        self.assertTrue(result)
        self.assertEqual(dialog.checked_names, {"Double Coins"})
        self.assertEqual(dialog.taps, [])

    def test_unknown_boost_does_not_touch_the_dialog(self):
        dialog = _BoostDialog(set())

        result = actions.sync_desired_boost_selection(
            "Unknown Boost",
            capture_func=dialog.capture,
            tap_func=dialog.tap,
            sleep_func=lambda _seconds: None,
        )

        self.assertFalse(result)
        self.assertEqual(dialog.taps, [])

    def test_changing_gui_choice_unchecks_old_boost_then_checks_new_one(self):
        dialog = _BoostDialog({"Double Coins"})

        result = actions.sync_desired_boost_selection(
            "+15% Score Bonus",
            capture_func=dialog.capture,
            tap_func=dialog.tap,
            sleep_func=lambda _seconds: None,
        )

        self.assertTrue(result)
        self.assertEqual(dialog.checked_names, {"+15% Score Bonus"})
        self.assertEqual(
            dialog.taps,
            [
                RANDOM_BOOST_SELECTION_BUTTONS["Double Coins"],
                RANDOM_BOOST_SELECTION_BUTTONS["+15% Score Bonus"],
            ],
        )

    def test_existing_target_stays_checked_while_other_choices_are_removed(self):
        dialog = _BoostDialog({"Double Coins", "Magnetic Aura"})

        result = actions.sync_desired_boost_selection(
            "Double Coins",
            capture_func=dialog.capture,
            tap_func=dialog.tap,
            sleep_func=lambda _seconds: None,
        )

        self.assertTrue(result)
        self.assertEqual(dialog.checked_names, {"Double Coins"})
        self.assertEqual(
            dialog.taps,
            [RANDOM_BOOST_SELECTION_BUTTONS["Magnetic Aura"]],
        )

    def test_failed_uncheck_stops_before_selecting_or_spending(self):
        dialog = _BoostDialog({"Double Coins"}, ignore_taps=True)

        result = actions.sync_desired_boost_selection(
            "+15% Score Bonus",
            capture_func=dialog.capture,
            tap_func=dialog.tap,
            sleep_func=lambda _seconds: None,
        )

        self.assertFalse(result)
        self.assertEqual(
            dialog.taps,
            [RANDOM_BOOST_SELECTION_BUTTONS["Double Coins"]] * 3,
        )

    def test_final_verification_rejects_a_second_late_check_mark(self):
        dialog = _BoostDialog(set())
        capture_count = 0

        def capture_with_late_extra_selection():
            nonlocal capture_count
            capture_count += 1
            if capture_count >= 3:
                dialog.checked_names.add("Magnetic Aura")
            return dialog.capture()

        result = actions.sync_desired_boost_selection(
            "Double Coins",
            capture_func=capture_with_late_extra_selection,
            tap_func=dialog.tap,
            sleep_func=lambda _seconds: None,
        )

        self.assertFalse(result)
        self.assertEqual(
            dialog.checked_names,
            {"Double Coins", "Magnetic Aura"},
        )

    def test_purchase_closes_dialog_without_multi_buy_when_sync_fails(self):
        with (
            mock.patch.object(actions, "sync_desired_boost_selection", return_value=False),
            mock.patch.object(actions, "safe_device_tap") as safe_tap,
            mock.patch.object(actions.time, "sleep"),
        ):
            actions.purchase_desired_random_boost([], "Double Coins")

        tapped_points = [(call.args[2], call.args[3]) for call in safe_tap.call_args_list]
        self.assertIn(RANDOM_BOOST_DIALOG_CLOSE_BUTTON, tapped_points)
        self.assertNotIn(MULTI_BUY_BUTTON, tapped_points)


if __name__ == "__main__":
    unittest.main()
