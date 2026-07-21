#!/usr/bin/env python3
"""Event-level benchmark metrics for the pump-and-dump replication audit.

Implements the protocol v0.2 event-outcome specification:

- eligible events are ``pump_index`` groups with exactly one ``gt=1`` row;
  groups with no positive row are excluded from the event denominator and are
  not treated as negative events;
- ``t0`` is the ``date`` of the unique positive row and is only a benchmark
  reference onset-bin start, not verified economic truth;
- ``date`` is a bin label: with bin width ``delta_f`` the information in a row
  is earliest available at ``t_available = date + delta_f``, so onset-bin
  delays are interval-censored rather than exactly zero;
- alerts are emitted sequentially from the full event-window start with a
  fixed 30-minute cooldown taken from the original paper; crossings inside the
  cooldown are suppressed, so an early alert can legitimately suppress an
  onset-adjacent alert and that effect must not be bypassed;
- ``EDR_exact`` requires an emitted alert sourced from the ``gt=1`` row;
  ``EDR@H`` requires an emitted alert with ``t_available`` in ``(t0, t0+H]``;
  ``Lead@L`` counts only emitted alerts with ``t_available`` in ``[t0-L, t0]``
  and is reported separately from post-onset detection;
- delay is conditional on detection within the 120-second horizon and is
  always reported together with its denominators;
- emitted alerts sourced from ``gt=0`` rows are benchmark-negative alert
  episodes; uncertainty for event-level quantities uses an event-cluster
  bootstrap over ``pump_index``, never row resampling.

These are benchmark-faithful quantities on the event-centred public matrices.
They do not measure real-market false alarms, daily alert volume, deployment
specificity, or analyst workload.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


COOLDOWN_SECONDS = 30 * 60
DETECTION_HORIZONS_SECONDS = (30, 60, 120)
LEAD_HORIZONS_SECONDS = (30, 60, 120)
DELAY_HORIZON_SECONDS = 120
REPLICATION_ANCHOR_TAU = 0.5
FREQUENCY_BIN_SECONDS = {"25S": 25, "15S": 15, "5S": 5}


@dataclass
class EventClassification:
    """Partition of ``pump_index`` groups by positive-label count."""

    eligible: list[int]
    no_positive: list[int]
    multi_positive: list[int]

    @property
    def n_eligible(self) -> int:
        return len(self.eligible)


@dataclass
class EventOutcome:
    """Per-event detection outcome under one frozen threshold."""

    pump_index: int
    exact_hit: bool
    detection_hits: dict[int, bool]
    lead_hits: dict[int, bool]
    delay_seconds: float | None
    benchmark_negative_episodes: int
    n_emitted: int


@dataclass
class EventSummary:
    """Aggregate event-level metrics over all eligible events."""

    n_eligible: int
    edr_exact: float
    edr_at: dict[int, float]
    lead_at: dict[int, float]
    delay_median: float | None
    delay_q25: float | None
    delay_q75: float | None
    delay_p90: float | None
    n_detected_within_delay_horizon: int
    benchmark_negative_episodes_by_event: list[int] = field(repr=False)

    @property
    def benchmark_negative_mean(self) -> float:
        return float(np.mean(self.benchmark_negative_episodes_by_event))

    @property
    def benchmark_negative_median(self) -> float:
        return float(np.median(self.benchmark_negative_episodes_by_event))


def classify_events(frame: pd.DataFrame) -> EventClassification:
    """Partition event groups by their ``gt=1`` count.

    Only groups with exactly one positive row are eligible. Groups without a
    positive row stay out of the event denominator and are not negatives.
    """

    counts = frame.groupby("pump_index")["gt"].sum()
    return EventClassification(
        eligible=sorted(int(i) for i in counts.index[counts == 1]),
        no_positive=sorted(int(i) for i in counts.index[counts == 0]),
        multi_positive=sorted(int(i) for i in counts.index[counts > 1]),
    )


def benchmark_onset(group: pd.DataFrame) -> pd.Timestamp:
    """Return t0: the ``date`` of the unique ``gt=1`` row of an eligible event."""

    positives = group.loc[group["gt"] == 1, "date"]
    if len(positives) != 1:
        raise ValueError(
            f"Eligible event must have exactly one gt=1 row, found {len(positives)}"
        )
    return pd.Timestamp(positives.iloc[0])


def emit_alerts(
    group: pd.DataFrame,
    scores: np.ndarray,
    tau: float,
    cooldown_seconds: int = COOLDOWN_SECONDS,
) -> pd.DataFrame:
    """Sequentially emit alerts from the full window start with a cooldown.

    ``group`` must contain ``date`` and ``gt`` and is processed in strict
    ``date`` order from the first row of the event window. A candidate row has
    ``score >= tau``; it is emitted only when no alert was emitted within the
    preceding ``cooldown_seconds``. The cooldown clock runs from the window
    start, never from the onset bin.
    """

    if len(group) != len(scores):
        raise ValueError("scores must align with group rows")
    ordered = group.assign(score=np.asarray(scores, dtype=float)).sort_values(
        "date", kind="mergesort"
    )
    emitted_rows = []
    last_emitted: pd.Timestamp | None = None
    for row in ordered.itertuples(index=False):
        if row.score < tau:
            continue
        timestamp = pd.Timestamp(row.date)
        if (
            last_emitted is not None
            and (timestamp - last_emitted).total_seconds() < cooldown_seconds
        ):
            continue
        emitted_rows.append(row)
        last_emitted = timestamp
    if not emitted_rows:
        return ordered.iloc[0:0]
    return pd.DataFrame(emitted_rows)


def score_event(
    group: pd.DataFrame,
    scores: np.ndarray,
    tau: float,
    bin_seconds: int,
    cooldown_seconds: int = COOLDOWN_SECONDS,
) -> EventOutcome:
    """Compute the per-event outcome for one eligible event and one threshold."""

    t0 = benchmark_onset(group)
    emitted = emit_alerts(group, scores, tau, cooldown_seconds)
    pump_index = int(group["pump_index"].iloc[0])
    if emitted.empty:
        return EventOutcome(
            pump_index=pump_index,
            exact_hit=False,
            detection_hits={h: False for h in DETECTION_HORIZONS_SECONDS},
            lead_hits={h: False for h in LEAD_HORIZONS_SECONDS},
            delay_seconds=None,
            benchmark_negative_episodes=0,
            n_emitted=0,
        )

    available = pd.to_datetime(emitted["date"]) + pd.Timedelta(seconds=bin_seconds)
    offset = (available - t0).dt.total_seconds()

    exact_hit = bool((emitted["gt"] == 1).any())
    detection_hits = {
        h: bool(((offset > 0) & (offset <= h)).any())
        for h in DETECTION_HORIZONS_SECONDS
    }
    lead_hits = {
        h: bool(((offset >= -h) & (offset <= 0)).any())
        for h in LEAD_HORIZONS_SECONDS
    }
    qualifying = offset[(offset > 0) & (offset <= DELAY_HORIZON_SECONDS)]
    delay_seconds = float(qualifying.min()) if not qualifying.empty else None
    return EventOutcome(
        pump_index=pump_index,
        exact_hit=exact_hit,
        detection_hits=detection_hits,
        lead_hits=lead_hits,
        delay_seconds=delay_seconds,
        benchmark_negative_episodes=int((emitted["gt"] == 0).sum()),
        n_emitted=len(emitted),
    )


def summarize_events(outcomes: list[EventOutcome]) -> EventSummary:
    """Aggregate per-event outcomes; delay is reported with denominators."""

    if not outcomes:
        raise ValueError("No eligible events to summarize")
    n = len(outcomes)
    delays = [o.delay_seconds for o in outcomes if o.delay_seconds is not None]
    delay_array = np.asarray(delays, dtype=float)
    has_delay = delay_array.size > 0
    return EventSummary(
        n_eligible=n,
        edr_exact=sum(o.exact_hit for o in outcomes) / n,
        edr_at={
            h: sum(o.detection_hits[h] for o in outcomes) / n
            for h in DETECTION_HORIZONS_SECONDS
        },
        lead_at={
            h: sum(o.lead_hits[h] for o in outcomes) / n
            for h in LEAD_HORIZONS_SECONDS
        },
        delay_median=float(np.median(delay_array)) if has_delay else None,
        delay_q25=float(np.percentile(delay_array, 25)) if has_delay else None,
        delay_q75=float(np.percentile(delay_array, 75)) if has_delay else None,
        delay_p90=float(np.percentile(delay_array, 90)) if has_delay else None,
        n_detected_within_delay_horizon=len(delays),
        benchmark_negative_episodes_by_event=[
            o.benchmark_negative_episodes for o in outcomes
        ],
    )


def select_tau_star(
    y_true: np.ndarray, oof_scores: np.ndarray
) -> tuple[float, pd.DataFrame]:
    """Select the training-calibrated threshold from out-of-fold scores only.

    Candidates are the sorted unique out-of-fold probability values plus the
    replication anchor 0.5. The selected threshold maximizes chunk-level F1;
    ties resolve to the highest threshold so the benchmark emits fewer alerts.
    Outer-test data must never enter this function.
    """

    y = np.asarray(y_true, dtype=int)
    s = np.asarray(oof_scores, dtype=float)
    if y.shape != s.shape:
        raise ValueError("y_true and oof_scores must align")
    candidates = np.unique(np.concatenate([s, [REPLICATION_ANCHOR_TAU]]))
    rows = []
    for tau in candidates:
        predicted = s >= tau
        tp = int(np.sum(predicted & (y == 1)))
        fp = int(np.sum(predicted & (y == 0)))
        fn = int(np.sum(~predicted & (y == 1)))
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        rows.append({"tau": float(tau), "f1": f1, "tp": tp, "fp": fp, "fn": fn})
    table = pd.DataFrame(rows)
    best_f1 = table["f1"].max()
    tau_star = float(table.loc[table["f1"] == best_f1, "tau"].max())
    return tau_star, table


def cluster_bootstrap_interval(
    values_by_event: np.ndarray,
    n_boot: int = 2000,
    seed: int = 20260722,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Percentile bootstrap interval resampling whole events, never rows."""

    values = np.asarray(values_by_event, dtype=float)
    if values.size == 0:
        raise ValueError("No event-level values to bootstrap")
    rng = np.random.default_rng(seed)
    n = values.size
    means = np.empty(n_boot)
    for b in range(n_boot):
        sample = values[rng.integers(0, n, size=n)]
        means[b] = sample.mean()
    lower = float(np.percentile(means, 100 * (alpha / 2)))
    upper = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return lower, upper
