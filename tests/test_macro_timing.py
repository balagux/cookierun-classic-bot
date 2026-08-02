import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import actions
import macro


class _FinishedProcess:
    def wait(self):
        return 0


class ReplayTimingTests(unittest.TestCase):
    def test_play_game_returns_tap_dispatch_midpoint(self):
        with (
            mock.patch.object(actions.time, "monotonic", side_effect=(10.0, 10.1)),
            mock.patch.object(actions, "safe_device_tap") as tap,
            mock.patch.object(actions.time, "sleep") as sleep,
            mock.patch("builtins.print"),
        ):
            started_at = actions.play_game()

        self.assertAlmostEqual(started_at, 10.05, places=6)
        tap.assert_called_once()
        sleep.assert_called_once_with(0.15)

    def test_replay_uses_shared_play_timeline(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / "run.json"
            profile.write_text(
                json.dumps(
                    {
                        "version": 4,
                        "timeline_origin": "play_tap",
                        "actions": [
                            {
                                "type": "control",
                                "control": "jump",
                                "at": 1.25,
                                "duration": 0.05,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            deadlines = []

            def capture_deadline(deadline, _stop_event):
                deadlines.append(deadline)
                return True

            with (
                mock.patch.object(macro, "_resolve_device_target", return_value="emulator-5556"),
                mock.patch.object(macro, "_wait_until", side_effect=capture_deadline),
                mock.patch.object(macro, "_launch_action", return_value=_FinishedProcess()),
                mock.patch.object(macro.time, "monotonic", return_value=101.211),
            ):
                count = macro.replay_profile(
                    "127.0.0.1",
                    5556,
                    profile,
                    timeline_started_at=100.0,
                )

        self.assertEqual(count, 1)
        self.assertEqual(len(deadlines), 1)
        self.assertAlmostEqual(
            deadlines[0],
            100.0 + 1.25 - macro.REPLAY_INPUT_LEAD_TIME,
            places=6,
        )

    def test_legacy_profile_uses_stable_compatibility_offset(self):
        started_at, legacy = macro._resolve_replay_start({"version": 3}, 100.0)
        self.assertTrue(legacy)
        self.assertAlmostEqual(
            started_at,
            100.0 + macro.LEGACY_REPLAY_START_DELAY,
            places=6,
        )


if __name__ == "__main__":
    unittest.main()
