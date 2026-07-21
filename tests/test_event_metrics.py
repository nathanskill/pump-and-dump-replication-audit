from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


MODULE_PATH = Path(__file__).parents[1] / "src" / "event_metrics.py"
SPEC = importlib.util.spec_from_file_location("event_metrics", MODULE_PATH)
EM = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["event_metrics"] = EM
SPEC.loader.exec_module(EM)


def make_event(pump_index, times, gts):
    return pd.DataFrame(
        {
            "pump_index": pump_index,
            "date": pd.to_datetime(times),
            "gt": gts,
        }
    )


class EligibilityTests(unittest.TestCase):
    def test_exactly_one_positive_defines_eligibility(self):
        frame = pd.concat(
            [
                make_event(1, ["2020-01-01 10:00:00", "2020-01-01 10:00:25"], [0, 1]),
                make_event(2, ["2020-01-01 11:00:00", "2020-01-01 11:00:25"], [0, 0]),
                make_event(3, ["2020-01-01 12:00:00", "2020-01-01 12:00:25"], [1, 1]),
            ]
        )
        cls = EM.classify_events(frame)
        self.assertEqual(cls.eligible, [1])
        self.assertEqual(cls.no_positive, [2])
        self.assertEqual(cls.multi_positive, [3])
        self.assertEqual(cls.n_eligible, 1)

    def test_onset_requires_unique_positive(self):
        group = make_event(3, ["2020-01-01 12:00:00", "2020-01-01 12:00:25"], [1, 1])
        with self.assertRaises(ValueError):
            EM.benchmark_onset(group)


class CooldownTests(unittest.TestCase):
    def test_crossings_inside_cooldown_are_suppressed(self):
        group = make_event(
            1,
            [
                "2020-01-01 10:00:00",
                "2020-01-01 10:10:00",
                "2020-01-01 10:29:59",
                "2020-01-01 10:30:00",
            ],
            [0, 0, 0, 0],
        )
        emitted = EM.emit_alerts(group, np.array([1.0, 1.0, 1.0, 1.0]), tau=0.5)
        self.assertEqual(
            list(pd.to_datetime(emitted["date"])),
            [pd.Timestamp("2020-01-01 10:00:00"), pd.Timestamp("2020-01-01 10:30:00")],
        )

    def test_cooldown_runs_from_window_start_and_can_suppress_onset_alert(self):
        # The documented trap: an early benign crossing suppresses the
        # onset-bin crossing; starting the clock at t0 would hide this.
        group = make_event(
            1,
            ["2020-01-01 09:50:00", "2020-01-01 10:00:00", "2020-01-01 10:40:00"],
            [0, 1, 0],
        )
        emitted = EM.emit_alerts(group, np.array([0.9, 0.9, 0.1]), tau=0.5)
        self.assertEqual(len(emitted), 1)
        self.assertEqual(int(emitted["gt"].iloc[0]), 0)
        outcome = EM.score_event(
            group, np.array([0.9, 0.9, 0.1]), tau=0.5, bin_seconds=25
        )
        self.assertFalse(outcome.exact_hit)

    def test_out_of_order_rows_are_processed_in_time_order(self):
        group = make_event(
            1,
            ["2020-01-01 10:30:00", "2020-01-01 10:00:00"],
            [0, 1],
        )
        emitted = EM.emit_alerts(group, np.array([1.0, 1.0]), tau=0.5)
        self.assertEqual(
            pd.Timestamp(emitted["date"].iloc[0]), pd.Timestamp("2020-01-01 10:00:00")
        )


class DetectionWindowTests(unittest.TestCase):
    def test_t_available_shifts_by_bin_width_and_bounds_are_half_open(self):
        # Onset bin at 10:00:00 with 25S bins: its own t_available is
        # 10:00:25, inside (t0, t0+30]. A row whose t_available equals t0
        # exactly (date = t0 - 25s) must not count as post-onset detection.
        at_t0 = make_event(
            1, ["2020-01-01 09:59:35", "2020-01-01 10:00:00"], [0, 1]
        )
        outcome = EM.score_event(
            at_t0, np.array([1.0, 0.0]), tau=0.5, bin_seconds=25
        )
        self.assertFalse(outcome.detection_hits[30])
        self.assertTrue(outcome.lead_hits[30])

        onset_row = EM.score_event(
            at_t0, np.array([0.0, 1.0]), tau=0.5, bin_seconds=25
        )
        self.assertTrue(onset_row.exact_hit)
        self.assertTrue(onset_row.detection_hits[30])

    def test_upper_bound_is_inclusive(self):
        # t_available - t0 == exactly 120s: date = t0 + 95s with 25S bins.
        group = make_event(
            1, ["2020-01-01 10:00:00", "2020-01-01 10:01:35"], [1, 0]
        )
        outcome = EM.score_event(
            group, np.array([0.0, 1.0]), tau=0.5, bin_seconds=25
        )
        self.assertFalse(outcome.detection_hits[60])
        self.assertTrue(outcome.detection_hits[120])
        self.assertEqual(outcome.delay_seconds, 120.0)

    def test_off_onset_hit_counts_for_horizon_but_not_exact(self):
        # A gt=0 row inside the tolerance horizon is simultaneously an
        # EDR@120s hit and a benchmark-negative alert episode.
        group = make_event(
            1, ["2020-01-01 10:00:00", "2020-01-01 10:00:50"], [1, 0]
        )
        outcome = EM.score_event(
            group, np.array([0.0, 1.0]), tau=0.5, bin_seconds=25
        )
        self.assertFalse(outcome.exact_hit)
        self.assertTrue(outcome.detection_hits[120])
        self.assertEqual(outcome.benchmark_negative_episodes, 1)

    def test_lead_alert_not_merged_into_detection(self):
        group = make_event(
            1, ["2020-01-01 09:59:00", "2020-01-01 10:00:00"], [0, 1]
        )
        outcome = EM.score_event(
            group, np.array([1.0, 0.0]), tau=0.5, bin_seconds=25
        )
        self.assertTrue(outcome.lead_hits[60])
        self.assertFalse(any(outcome.detection_hits.values()))
        self.assertIsNone(outcome.delay_seconds)


class SummaryTests(unittest.TestCase):
    def test_summary_reports_denominators_and_delay_stats(self):
        detected = make_event(
            1, ["2020-01-01 10:00:00", "2020-01-01 10:00:25"], [1, 0]
        )
        missed = make_event(
            2, ["2020-01-01 12:00:00", "2020-01-01 12:00:25"], [1, 0]
        )
        outcomes = [
            EM.score_event(detected, np.array([1.0, 0.0]), 0.5, bin_seconds=25),
            EM.score_event(missed, np.array([0.0, 0.0]), 0.5, bin_seconds=25),
        ]
        summary = EM.summarize_events(outcomes)
        self.assertEqual(summary.n_eligible, 2)
        self.assertEqual(summary.edr_exact, 0.5)
        self.assertEqual(summary.n_detected_within_delay_horizon, 1)
        self.assertEqual(summary.delay_median, 25.0)
        self.assertEqual(summary.benchmark_negative_episodes_by_event, [0, 0])

    def test_empty_outcomes_rejected(self):
        with self.assertRaises(ValueError):
            EM.summarize_events([])


class TauStarTests(unittest.TestCase):
    def test_selects_f1_maximizer_from_oof_scores_only(self):
        y = np.array([0, 0, 1, 1])
        scores = np.array([0.1, 0.4, 0.6, 0.9])
        tau_star, table = EM.select_tau_star(y, scores)
        self.assertEqual(tau_star, 0.6)
        self.assertEqual(table.loc[table["tau"] == 0.6, "f1"].iloc[0], 1.0)

    def test_tie_resolves_to_higher_threshold(self):
        # tau=0.5 and tau=0.8 produce identical predictions, hence equal F1;
        # the tie must resolve to the higher threshold.
        y = np.array([0, 1])
        scores = np.array([0.3, 0.8])
        tau_star, table = EM.select_tau_star(y, scores)
        f1_at = table.set_index("tau")["f1"]
        self.assertEqual(f1_at[0.5], f1_at[0.8])
        self.assertEqual(tau_star, 0.8)

    def test_replication_anchor_always_a_candidate(self):
        y = np.array([0, 1])
        scores = np.array([0.2, 0.8])
        _, table = EM.select_tau_star(y, scores)
        self.assertIn(0.5, set(table["tau"]))


class BootstrapTests(unittest.TestCase):
    def test_deterministic_under_seed_and_degenerate_when_constant(self):
        values = np.array([2.0, 2.0, 2.0])
        interval_a = EM.cluster_bootstrap_interval(values, n_boot=200, seed=7)
        interval_b = EM.cluster_bootstrap_interval(values, n_boot=200, seed=7)
        self.assertEqual(interval_a, interval_b)
        self.assertEqual(interval_a, (2.0, 2.0))

    def test_interval_covers_sample_mean(self):
        values = np.array([0.0, 1.0, 2.0, 3.0, 10.0])
        lower, upper = EM.cluster_bootstrap_interval(values, n_boot=500, seed=11)
        self.assertLessEqual(lower, values.mean())
        self.assertGreaterEqual(upper, values.mean())


UPSTREAM_DIR = Path(
    os.environ.get(
        "PUMP_AUDIT_UPSTREAM",
        Path(__file__).parents[2] / "tmp/repro_public_20260715/pump-and-dump-dataset",
    )
)


@unittest.skipUnless(
    (UPSTREAM_DIR / "labeled_features").is_dir(),
    "upstream matrices not available; set PUMP_AUDIT_UPSTREAM",
)
class UpstreamInvariantTests(unittest.TestCase):
    def test_eligible_event_invariants_hold_per_frequency(self):
        for frequency in ("25S", "15S", "5S"):
            frame = pd.read_csv(
                UPSTREAM_DIR / "labeled_features" / f"features_{frequency}.csv.gz",
                usecols=["date", "pump_index", "gt"],
            )
            cls = EM.classify_events(frame)
            with self.subTest(frequency=frequency):
                self.assertEqual(cls.n_eligible, 317)
                self.assertEqual(len(cls.no_positive), 10)
                self.assertEqual(cls.multi_positive, [])


if __name__ == "__main__":
    unittest.main()
