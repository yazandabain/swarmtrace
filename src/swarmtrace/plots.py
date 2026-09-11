import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from swarmtrace.load import (
    load_dse_revisions,
    load_successful_dse_deletes,
)
from swarmtrace.state import HourlySurfaceRow, reconstruct_hourly

REPORT_START = datetime(2026, 6, 16, 0, 0, tzinfo=UTC)
REPORT_END = datetime(2026, 6, 23, 0, 0, tzinfo=UTC)
PRIMARY_HORIZON = timedelta(hours=6)


def write_hourly_csv(
    rows: list[HourlySurfaceRow],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "hour_start",
        "surface_start",
        "surface_end",
        "activations",
        "deletion_exits",
        "inactivity_exits",
        "delete_actions",
        "active_multiwriter_incidences",
        "active_multiwriter_labels",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    "hour_start": row.hour_start.isoformat(),
                    "surface_start": row.surface_start,
                    "surface_end": row.surface_end,
                    "activations": row.activations,
                    "deletion_exits": row.deletion_exits,
                    "inactivity_exits": row.inactivity_exits,
                    "delete_actions": row.delete_actions,
                    "active_multiwriter_incidences": (row.active_multiwriter_incidences),
                    "active_multiwriter_labels": (row.active_multiwriter_labels),
                }
            )


def plot_live_surface(
    rows: list[HourlySurfaceRow],
    output_path: Path,
) -> None:
    times = [row.hour_start + timedelta(hours=1) for row in rows]

    surface = [row.surface_end for row in rows]
    incidences = [row.active_multiwriter_incidences for row in rows]
    labels = [row.active_multiwriter_labels for row in rows]

    activations = [row.activations for row in rows]
    deletion_exits = [-row.deletion_exits for row in rows]
    inactivity_exits = [-row.inactivity_exits for row in rows]
    delete_actions = [row.delete_actions for row in rows]

    figure, axes = plt.subplots(
        3,
        1,
        figsize=(12, 9),
        sharex=True,
        constrained_layout=True,
    )

    surface_ax, context_ax, flow_ax = axes

    surface_ax.plot(
        times,
        surface,
        linewidth=2,
        label="Active multi-writer resources",
    )
    surface_ax.set_ylabel("Resources")
    surface_ax.set_title("DSEWiki live multi-writer surface, 6-hour activity horizon")
    surface_ax.legend()

    context_ax.plot(
        times,
        incidences,
        linewidth=1.8,
        label="Live label-resource incidences",
    )
    context_ax.plot(
        times,
        labels,
        linewidth=1.8,
        label="Participating labels",
    )
    context_ax.set_ylabel("Count")
    context_ax.legend()

    bar_width = 0.018

    flow_ax.bar(
        times,
        activations,
        width=bar_width,
        label="Activations",
    )

    flow_ax.bar(
        times,
        inactivity_exits,
        width=bar_width,
        label="Inactivity exits",
    )

    flow_ax.scatter(
        times,
        deletion_exits,
        s=18,
        marker="v",
        label="Deletion exits",
    )

    flow_ax.plot(
        times,
        delete_actions,
        linewidth=1.4,
        label="Moderator delete actions",
    )

    peak_index = max(
        range(len(surface)),
        key=surface.__getitem__,
    )

    peak_time = times[peak_index]
    peak_value = surface[peak_index]

    surface_ax.scatter(
        [peak_time],
        [peak_value],
        s=30,
        zorder=3,
    )

    surface_ax.annotate(
        f"Hourly endpoint peak: {peak_value}",
        xy=(peak_time, peak_value),
        xytext=(10, -25),
        textcoords="offset points",
        arrowprops={"arrowstyle": "->"},
    )

    flow_ax.axhline(0, linewidth=0.8)
    flow_ax.set_ylabel("Hourly events")
    flow_ax.set_xlabel("UTC")
    flow_ax.legend(ncol=2)

    locator = mdates.DayLocator()
    formatter = mdates.DateFormatter("%b %d")

    flow_ax.xaxis.set_major_locator(locator)
    flow_ax.xaxis.set_major_formatter(formatter)

    for axis in axes:
        axis.grid(axis="y", alpha=0.2)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    figure.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(figure)


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = Path.home() / "code" / "swarmtrace-data"

    revisions = load_dse_revisions(data_dir / "revisions.jsonl")
    deletes = load_successful_dse_deletes(data_dir / "events.jsonl")

    rows = reconstruct_hourly(
        revisions=revisions,
        deletes=deletes,
        horizon=PRIMARY_HORIZON,
        start=REPORT_START,
        end=REPORT_END,
    )

    output_path = project_root / "outputs" / "hourly_w6.csv"
    write_hourly_csv(rows, output_path)

    figure_path = project_root / "outputs" / "figures" / "figure1_live_surface.png"

    plot_live_surface(
        rows=rows,
        output_path=figure_path,
    )

    print(f"Wrote {len(rows):,} hourly rows to {output_path}")
    print(f"Wrote Figure 1 to {figure_path}")


if __name__ == "__main__":
    main()
