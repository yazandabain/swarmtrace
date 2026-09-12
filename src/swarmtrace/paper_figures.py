"""Compact publication figures from saved, auditable output tables."""

import argparse
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/swarmtrace-matplotlib")
os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate(output):
    plt.rcParams.update(
        {
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "legend.fontsize": 8,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )
    folder = output / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    h = pd.read_csv(output / "hourly_w6.csv", parse_dates=["hour_start"])
    time = h.hour_start + pd.Timedelta(hours=1)
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(6.5, 3.2),
        sharex=True,
        layout="constrained",
        gridspec_kw={"height_ratios": [1, 1]},
    )
    ax = axes[0]
    ax.plot(time, h.surface_end, color="#21658c", linewidth=1.4)
    ax.axvline(pd.Timestamp("2026-06-19T14:05:02Z"), color="#a23e2d", linestyle=":", linewidth=1)
    ax.set_ylabel("Active resources")
    i = h.surface_end.idxmax()
    ax.annotate(
        "331 at hourly endpoint",
        xy=(time[i], h.surface_end[i]),
        xytext=(-20, -25),
        textcoords="offset points",
        fontsize=8,
        ha="right",
        arrowprops={"arrowstyle": "->", "linewidth": 0.6},
    )
    ax.text(0.60, 0.79, "Frozen snapshot", color="#a23e2d", transform=ax.transAxes, fontsize=8)
    ax = axes[1]
    # Positive counts in distinct series avoid conflating zero markers with observations.
    ax.plot(time, h.delete_actions, label="Deletion actions", color="#666666", linewidth=1)
    ax.plot(time, h.inactivity_exits, label="Expiry exits", color="#cd8e25", linewidth=1.2)
    ax.plot(time, h.deletion_exits, label="Deletion exits", color="#a23e2d", linewidth=1.2)
    ax.set_ylabel("Events per hour")
    ax.set_xlabel("June 2026 (UTC)")
    ax.legend(loc="upper right", frameon=False, ncol=3)
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d"))
    for ax in axes:
        ax.grid(axis="y", alpha=0.18)
        ax.spines[["top", "right"]].set_visible(False)
    for ext in ["png", "pdf", "svg"]:
        fig.savefig(folder / f"paper_figure1.{ext}", dpi=300)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(6.5, 2.7), sharey=True, layout="constrained")
    for ax, w in zip(axes, [1, 6, 24], strict=True):
        df = pd.read_csv(output / f"withdrawal_w{w}.csv")
        r0 = df.R0.iloc[0]
        x = df.fraction_removed
        ax.fill_between(
            x,
            df.R_random_p05 / r0,
            df.R_random_p95 / r0,
            color="#21658c",
            alpha=0.18,
            step="post",
            label="Random 5-95%",
        )
        ax.step(
            x,
            df.Q_random_median,
            where="post",
            color="#21658c",
            linewidth=1.3,
            label="Random median",
        )
        ax.fill_between(
            x,
            df.R_tie_p05 / r0,
            df.R_tie_p95 / r0,
            color="#a23e2d",
            alpha=0.18,
            step="post",
            label="Degree ties 5-95%",
        )
        ax.step(x, df.Q_degree, where="post", color="#a23e2d", linewidth=1.3, label="Static degree")
        ax.set_title(f"{w}h" + (" (primary)" if w == 6 else " (sensitivity)"))
        ax.set_xlabel("Fraction removed")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.05)
        ax.set_xticks([0, 0.5, 1])
        ax.grid(alpha=0.18)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Largest-label component\n/ baseline (Q)")
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=2, frameon=False)
    for ext in ["png", "pdf", "svg"]:
        fig.savefig(folder / f"paper_figure2.{ext}", dpi=300)
    plt.close(fig)

    # Appendix: distribution of the exact primary endpoint at the planned budgets.
    df = pd.read_csv(output / "exact_distributions_w6.csv")
    fig, axes = plt.subplots(1, 3, figsize=(6.5, 2.4), sharey=True, layout="constrained")
    for ax, k in zip(axes, [2, 5, 9], strict=True):
        for policy, offset, color, label in [
            ("uniform", -0.17, "#21658c", "Uniform withdrawal"),
            ("degree_ties", 0.17, "#a23e2d", "Degree tie orderings"),
        ]:
            part = df[(df.k == k) & (df.policy == policy)]
            ax.bar(
                part.largest_label_component + offset,
                part.probability,
                width=0.32,
                color=color,
                label=label,
            )
        ax.set_title(f"{k} of 18 resources removed")
        ax.set_xlabel("Labels in largest component")
        ax.set_xticks(np.arange(1, 9, 2))
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Exact probability")
    fig.legend(
        *axes[0].get_legend_handles_labels(), loc="outside lower center", ncol=2, frameon=False
    )
    for ext in ["png", "pdf", "svg"]:
        fig.savefig(folder / f"paper_figure3_exact.{ext}", dpi=300)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, default=Path("outputs"))
    generate(p.parse_args().output_dir)


if __name__ == "__main__":
    main()
