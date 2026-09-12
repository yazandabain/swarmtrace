"""Post-result controls for candidate-pool dilution and evaluation-window sensitivity."""

import argparse
import math
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from swarmtrace.graph import SnapshotGraph, direct_snapshot
from swarmtrace.load import load_dse_revisions, load_successful_dse_deletes
from swarmtrace.run import HASHES, REPORT_START, SNAPSHOT, sha256, write_csv, write_json
from swarmtrace.state import active_resources_before_times
from swarmtrace.stress import largest_label_counts, reference_counts
from swarmtrace.temporal import crossed_graph, tie_coverage_bounds


def uniform_coverage(candidate_count, recent_count, actions):
    """Exact expected coverage and miss probability for a uniform action subset."""
    if not 0 < recent_count <= candidate_count or not 0 <= actions <= candidate_count:
        raise ValueError("Require a nonempty recent set and a feasible action budget")
    probability = (
        math.comb(candidate_count - recent_count, actions) / math.comb(candidate_count, actions)
        if actions <= candidate_count - recent_count
        else 0.0
    )
    return actions / candidate_count, probability


def run(data_dir, output):
    if {name: sha256(data_dir / name) for name in HASHES} != HASHES:
        raise ValueError("Raw data hashes differ from the frozen source")
    revisions = load_dse_revisions(data_dir / "revisions.jsonl")
    deletes = load_successful_dse_deletes(data_dir / "events.jsonl")
    hours = {REPORT_START + timedelta(hours=i): i for i in range(1, 169)}
    times = sorted([*hours, SNAPSHOT])
    snapshots = {
        w: dict(active_resources_before_times(revisions, deletes, timedelta(hours=w), times))
        for w in [1, 3, 6, 12, 24]
    }
    validation = {"full_incidence_oracle_checks": 0, "forward_trajectory_checks": 0}
    rows, states = [], []
    for index, time in enumerate(times):
        graphs = {}
        for w, active in snapshots.items():
            assert {p: ws for (p, _), ws in active[time].items()} == direct_snapshot(
                revisions, deletes, timedelta(hours=w), time
            )
            validation["full_incidence_oracle_checks"] += 1
            graphs[w] = SnapshotGraph.from_resources(active[time])
        older = graphs[24]
        degree = np.array([len(ws) for ws in older.writers])
        order = sorted(range(len(degree)), key=lambda i: (-degree[i], older.resources[i]))
        older_counts = largest_label_counts(older, order)
        for w in [1, 3, 6, 12]:
            recent = graphs[w]
            m, M = len(recent.resources), len(older.resources)
            context = {
                "source": "hourly" if time in hours else "frozen",
                "hour_index": hours.get(time, 0),
                "time": time,
                "evaluation_hours": w,
                "ranking_hours": 24,
                "older_candidates": M,
                "recent_resources": m,
                "recent_labels": len(recent.labels),
            }
            states.append(context)
            if not m:
                continue
            fixed = crossed_graph(recent, older)
            counts = largest_label_counts(fixed, order)
            if context["hour_index"] in [0, 1, 84, 168]:
                np.testing.assert_array_equal(counts, reference_counts(fixed, order))
                validation["forward_trajectory_checks"] += 1
            present = np.array([bool(ws) for ws in fixed.writers])
            for fraction in [0.1, 0.25, 0.5, 1.0]:
                k = math.ceil(fraction * m)
                selected = int(present[order[:k]].sum())
                lo, hi = tie_coverage_bounds(degree, present, k)
                mean, pzero = uniform_coverage(M, m, k)
                rows.append(
                    context
                    | {
                        "requested_fraction": fraction,
                        "k": k,
                        "older_selected_recent": selected,
                        "older_coverage": selected / m,
                        "tie_min_selected_recent": lo,
                        "tie_max_selected_recent": hi,
                        "uniform_expected_coverage": mean,
                        "uniform_zero_coverage_probability": pzero,
                        "coverage_minus_uniform_expectation": selected / m - mean,
                        "recent_component_before": int(counts[0]),
                        "recent_component_after": int(counts[k]),
                        "Q_recent": counts[k] / counts[0],
                        "older_component_before": int(older_counts[0]),
                        "older_component_after": int(older_counts[k]),
                        "Q_older": older_counts[k] / older_counts[0],
                    }
                )
        if (index + 1) % 24 == 0:
            print(f"Review controls: {index + 1}/{len(times)} snapshots", flush=True)
    write_csv(output / "review_control_states.csv", states)
    write_csv(output / "review_controls.csv", rows)
    table = pd.DataFrame(rows)
    summary = []
    for w in [1, 3, 6, 12]:
        eligible = table[(table.source == "hourly") & (table.evaluation_hours == w)]
        for fraction in [0.1, 0.25, 0.5, 1.0]:
            part = eligible[eligible.requested_fraction == fraction]
            delta = part.coverage_minus_uniform_expectation
            summary.append(
                {
                    "evaluation_hours": w,
                    "requested_fraction": fraction,
                    "nonempty_hours": len(part),
                    "empty_hours": 168 - len(part),
                    "older_zero_coverage_hours": int((part.older_selected_recent == 0).sum()),
                    "zero_coverage_under_every_tie_order": int(
                        (part.tie_max_selected_recent == 0).sum()
                    ),
                    "uniform_expected_zero_coverage_hours": float(
                        part.uniform_zero_coverage_probability.sum()
                    ),
                    "older_mean_coverage": float(part.older_coverage.mean()),
                    "older_median_coverage": float(part.older_coverage.median()),
                    "uniform_mean_expected_coverage": float(part.uniform_expected_coverage.mean()),
                    "coverage_above_uniform_expectation_hours": int((delta > 1e-12).sum()),
                    "coverage_equal_uniform_expectation_hours": int((delta.abs() <= 1e-12).sum()),
                    "coverage_below_uniform_expectation_hours": int((delta < -1e-12).sum()),
                }
            )
    write_csv(output / "review_control_summary.csv", summary)
    # The expanded evaluation grid must reproduce the already saved 6h comparison.
    checked = 0
    for source, name in [
        ("hourly", "crossed_hourly.csv"),
        ("frozen", "crossed_frozen_snapshot.csv"),
    ]:
        original = pd.read_csv(output / name)
        new = table[(table.source == source) & (table.evaluation_hours == 6)]
        for record in original.to_dict("records"):
            match = new[
                (new.hour_index == record.get("hour_index", 0))
                & (new.requested_fraction == record["requested_fraction_of_recent_resources"])
            ].iloc[0]
            assert (
                match.older_selected_recent == record["recent_resources_selected_by_older_degree"]
            )
            assert math.isclose(match.Q_recent, record["Q6_older_degree"], abs_tol=1e-12)
            checked += 1
    validation["original_crossed_checkpoint_matches"] = checked
    write_json(output / "review_control_validation.json", validation)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path.home() / "code" / "swarmtrace-data")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    run(args.data_dir.expanduser(), args.output_dir)
