"""Deterministic figure generation for the manuscript, from frozen artifacts only.

Reads persisted prediction outputs and the forward summary; writes two figures
to paper/figures/. No model is trained, no threshold is re-selected; this is a
rendering of already-frozen results. Aggregate precision-recall pairs and
per-checkpoint EDR/tau* are summary statistics, consistent with the
repository's redistribution boundary (no upstream matrix or per-row prediction
is redistributed).

Run: .venv/bin/python src/make_figures.py
"""
from pathlib import Path
import gzip
import pandas as pd
import numpy as np
from sklearn.metrics import precision_recall_curve, average_precision_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / "artifacts"
OUT = ROOT / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

FREQS = ["25S", "15S", "5S"]
FREQ_LABEL = {"25S": "25 s", "15S": "15 s", "5S": "5 s"}


def load_cv(freq):
    return pd.read_csv(ART / f"formal_s1_s0_v1_20260722/{freq}/predictions_{freq}_cv.csv.gz")


def load_fwd(freq):
    return pd.read_csv(ART / f"formal_forward_v1_20260722/{freq}_80/predictions_{freq}_80.csv.gz")


def fig_pr_curves():
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
    for ax, freq in zip(axes, FREQS):
        cv = load_cv(freq)
        fwd = load_fwd(freq)
        for label, y, s, style in [
            ("S0 row-level", cv["gt"], cv["s0_oof"], dict(color="#444444", ls="-", lw=1.6)),
            ("S1 event-exclusive", cv["gt"], cv["s1_oof"], dict(color="#1f6feb", ls="-", lw=1.6)),
            ("S2 forward @80% (test subset)", fwd["gt"], fwd["score"], dict(color="#c0392b", ls="--", lw=1.6)),
        ]:
            p, r, _ = precision_recall_curve(y, s)
            ap = average_precision_score(y, s)
            ax.plot(r, p, label=f"{label} (AP {ap:.3f})", **style)
        ax.set_title(FREQ_LABEL[freq])
        ax.set_xlabel("Recall")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.grid(True, alpha=0.25, lw=0.5)
        ax.legend(loc="lower left", fontsize=6.5, frameon=False)
    axes[0].set_ylabel("Precision")
    fig.suptitle("Precision–recall by evaluation family and feature frequency", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUT / "fig1_pr_curves.pdf")
    fig.savefig(OUT / "fig1_pr_curves.png", dpi=200)
    plt.close(fig)


def fig_checkpoints():
    s = pd.read_csv(ART / "formal_forward_v1_20260722/summary.csv")
    s["cp"] = (s["fraction"].astype(float) * 100).round().astype(int)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.6))
    colors = {"25S": "#444444", "15S": "#1f6feb", "5S": "#c0392b"}
    for freq in FREQS:
        d = s[s["frequency"] == freq].sort_values("cp")
        a1.plot(d["cp"], d["edr_120_anchor"], marker="o", ms=4, color=colors[freq], label=FREQ_LABEL[freq])
        a2.plot(d["cp"], d["tau_star"], marker="s", ms=4, color=colors[freq], label=FREQ_LABEL[freq])
    a1.set_title("Event detection rate @120 s (anchor τ=0.5)")
    a1.set_xlabel("Forward checkpoint (% of calendar)")
    a1.set_ylabel("EDR@120")
    a1.set_ylim(0.5, 1.0)
    a2.set_title("Calibrated threshold τ* by checkpoint")
    a2.set_xlabel("Forward checkpoint (% of calendar)")
    a2.set_ylabel("τ*")
    a2.set_ylim(0, 0.8)
    for a in (a1, a2):
        a.set_xticks([40, 50, 60, 70, 80])
        a.grid(True, alpha=0.25, lw=0.5)
        a.legend(fontsize=7.5, frameon=False)
    fig.suptitle("Forward-time checkpoints: detection and threshold stability", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUT / "fig2_checkpoints.pdf")
    fig.savefig(OUT / "fig2_checkpoints.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    fig_pr_curves()
    fig_checkpoints()
    print("figures written to", OUT)
