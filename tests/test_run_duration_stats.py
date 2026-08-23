import io
import unittest
from unittest import mock

from bot import RunDurationStats, _print_session_stats


class FakeClock:
    def __init__(self, now=0.0):
        self.now = float(now)

    def __call__(self):
        return self.now


class RunDurationStatsTests(unittest.TestCase):
    def test_complete_records_latest_total_and_timed_run_count(self):
        clock = FakeClock(100.0)
        durations = RunDurationStats(clock)

        durations.start()
        clock.now = 225.25
        self.assertAlmostEqual(durations.complete(), 125.25)

        clock.now = 300.0
        durations.start()
        clock.now = 390.5
        self.assertAlmostEqual(durations.complete(), 90.5)
        self.assertAlmostEqual(durations.latest_seconds, 90.5)
        self.assertAlmostEqual(durations.total_seconds, 215.75)
        self.assertEqual(durations.timed_runs, 2)
        self.assertFalse(durations.in_progress)

    def test_complete_is_idempotent(self):
        clock = FakeClock(5.0)
        durations = RunDurationStats(clock)
        durations.start()
        clock.now = 15.0

        self.assertEqual(durations.complete(), 10.0)
        self.assertIsNone(durations.complete())
        self.assertEqual(durations.latest_seconds, 10.0)
        self.assertEqual(durations.total_seconds, 10.0)
        self.assertEqual(durations.timed_runs, 1)

    def test_capture_waits_for_confirmation_before_aggregation(self):
        clock = FakeClock(10.0)
        durations = RunDurationStats(clock)
        durations.start()
        clock.now = 35.5

        self.assertEqual(durations.capture(), 25.5)
        self.assertIsNone(durations.latest_seconds)
        self.assertEqual(durations.total_seconds, 0.0)
        self.assertEqual(durations.timed_runs, 0)

        self.assertEqual(durations.commit(), 25.5)
        self.assertEqual(durations.latest_seconds, 25.5)
        self.assertEqual(durations.total_seconds, 25.5)
        self.assertEqual(durations.timed_runs, 1)
        self.assertIsNone(durations.commit())

    def test_cancel_discards_interrupted_run(self):
        clock = FakeClock(10.0)
        durations = RunDurationStats(clock)

        durations.start()
        clock.now = 999.0
        durations.cancel()

        self.assertIsNone(durations.complete())
        self.assertIsNone(durations.latest_seconds)
        self.assertEqual(durations.total_seconds, 0.0)
        self.assertEqual(durations.timed_runs, 0)

    def test_cancel_also_discards_a_captured_unconfirmed_run(self):
        clock = FakeClock(10.0)
        durations = RunDurationStats(clock)
        durations.start()
        clock.now = 25.0
        durations.capture()
        durations.cancel()

        self.assertIsNone(durations.commit())
        self.assertEqual(durations.total_seconds, 0.0)
        self.assertEqual(durations.timed_runs, 0)

    def test_monotonic_clock_regression_cannot_create_negative_duration(self):
        clock = FakeClock(20.0)
        durations = RunDurationStats(clock)
        durations.start()
        clock.now = 19.0

        self.assertEqual(durations.complete(), 0.0)
        self.assertEqual(durations.total_seconds, 0.0)
        self.assertEqual(durations.timed_runs, 1)

    def test_stats_line_keeps_old_fields_and_adds_duration_fields(self):
        clock = FakeClock(40.0)
        durations = RunDurationStats(clock)
        durations.start()
        clock.now = 165.67
        durations.complete()

        output = io.StringIO()
        with mock.patch("sys.stdout", output):
            _print_session_stats(3, 2, 12345, 678, durations)

        self.assertEqual(
            output.getvalue(),
            "[STATS] attempts=3 completed=2 coins=12345 exp=678 "
            "last_run_seconds=125.7 total_run_seconds=125.7 timed_runs=1\n",
        )


if __name__ == "__main__":
    unittest.main()
