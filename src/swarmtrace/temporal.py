"""Exploratory hourly and crossed-horizon audit, separately specified after primary results."""

import argparse
import json
import math
from dataclasses import asdict
from datetime import timedelta
from pathlib import Path

import numpy as np

from swarmtrace.graph import SnapshotGraph, direct_snapshot
from swarmtrace.load import load_dse_revisions, load_successful_dse_deletes
from swarmtrace.run import REPORT_END, REPORT_START, SNAPSHOT, write_csv, write_json
from swarmtrace.state import active_resources_before_times, snapshot_before
from swarmtrace.stress import curve_rows, largest_label_counts, reference_counts, run_stress


def crossed_graph(recent: SnapshotGraph, older: SnapshotGraph) -> SnapshotGraph:
    """Same older action pool, but exactly the recent labels and incidences."""
    if not set(recent.resources) <= set(older.resources):
        raise ValueError("Recent resources must be a subset of older candidates")
    by_resource = dict(zip(recent.resources, recent.writers, strict=True))
    return SnapshotGraph(
        older.resources, recent.labels, tuple(by_resource.get(r, ()) for r in older.resources)
    )


def tie_coverage_bounds(degrees, present, k):
    """Exact coverage bounds when only the cutoff degree group's order is free."""
    degrees = np.asarray(degrees)
    present = np.asarray(present, dtype=bool)
    if not 0 <= k <= len(degrees):
        raise ValueError("k must lie within the candidate count")
    if k == 0:
        return 0, 0
    cutoff = sorted(degrees, reverse=True)[k - 1]
    strict = degrees > cutoff
    ties = degrees == cutoff
    slots = k - int(strict.sum())
    fixed_hits = int((strict & present).sum())
    minimum = fixed_hits + max(0, slots - int((ties & ~present).sum()))
    maximum = fixed_hits + min(slots, int((ties & present).sum()))
    return minimum, maximum


def audit_tie_bounds(output):
    import pandas as pd

    rows = []
    for source, filename in [
        ("hourly", "crossed_hourly.csv"),
        ("frozen", "crossed_frozen_snapshot.csv"),
    ]:
        df = pd.read_csv(output / filename)
        for record in df.to_dict("records"):
            index = int(record.get("hour_index", 0))
            name = f"hour_{index:03d}_graphs.json" if index else "frozen_graphs.json"
            evidence = json.loads((output / "temporal" / name).read_text())
            recent = {(r["page_key"], r["episode"]) for r in evidence["graphs"]["6"]["resources"]}
            older = evidence["graphs"]["24"]["resources"]
            lo, hi = tie_coverage_bounds(
                [len(r["writer_indices"]) for r in older],
                [(r["page_key"], r["episode"]) in recent for r in older],
                int(record["k"]),
            )
            rows.append(
                {
                    "source": source,
                    "hour_index": index,
                    "time": evidence["time"],
                    "k": int(record["k"]),
                    "requested_fraction": record["requested_fraction_of_recent_resources"],
                    "recent_resources": len(recent),
                    "min_recent_resources_selected": lo,
                    "max_recent_resources_selected": hi,
                }
            )
    write_csv(output / "crossed_tie_bounds.csv", rows)
    hourly = [r for r in rows if r["source"] == "hourly" and r["requested_fraction"] == 1]
    write_json(
        output / "crossed_tie_summary.json",
        {
            "hourly_snapshots": len(hourly),
            "zero_coverage_under_every_degree_tie_order": sum(
                r["max_recent_resources_selected"] == 0 for r in hourly
            ),
            "zero_coverage_under_some_degree_tie_order": sum(
                r["min_recent_resources_selected"] == 0 for r in hourly
            ),
        },
    )


def compact_save(path, arrays):
    """Lossless compact integers for the full trace archives, including action orders."""
    compact = {}
    for name, array in arrays.items():
        maximum = int(np.max(array, initial=0))
        assert np.all(array >= 0)
        dtype = np.uint16 if maximum <= 65535 else np.uint32
        compact[name] = array.astype(dtype)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **compact)


def graph_record(active, graph):
    return {
        "labels": graph.labels,
        "resources": [
            {
                "page_key": p,
                "episode": ep,
                "writer_indices": graph.writers[i],
                "latest_writes": {label: time for label, time in sorted(active[p, ep].items())},
            }
            for i, (p, ep) in enumerate(graph.resources)
        ],
    }


def cross_evaluate(recent, older, older_result, hour_index):
    fixed = crossed_graph(recent, older)
    # The random ordering is identical to the older-graph run because candidate
    # order and seed are identical. Only the evaluation edges and labels change.
    result = run_stress(
        fixed, 24, random_seed=20260936 + 1000 * hour_index, tie_seed=20261936 + 1000 * hour_index
    )
    np.testing.assert_array_equal(result.random_orders, older_result.random_orders)
    older_counts = largest_label_counts(fixed, older_result.degree_order)
    older_tie_counts = np.array([largest_label_counts(fixed, o) for o in older_result.tie_orders])
    present = np.array([bool(w) for w in fixed.writers])
    m, n = len(recent.resources), len(recent.labels)
    l0 = int(result.degree_counts[0])
    rows = []
    for fraction in [0.1, 0.25, 0.5, 1.0]:
        k = math.ceil(fraction * m)
        old_selected = int(present[older_result.degree_order[:k]].sum())
        recent_selected = int(present[result.degree_order[:k]].sum())
        random_selected = present[result.random_orders[:, :k]].sum(axis=1)
        old_tie_selected = present[older_result.tie_orders[:, :k]].sum(axis=1)
        row = {
            "requested_fraction_of_recent_resources": fraction,
            "k": k,
            "older_candidates": len(older.resources),
            "recent_resources": m,
            "recent_labels": n,
            "R6_0": l0 / n,
            "Q6_recent_degree": result.degree_counts[k] / l0,
            "Q6_older_degree": older_counts[k] / l0,
            "Q6_uniform_median": float(np.median(result.random_counts[:, k]) / l0),
            "Q6_uniform_p05": float(np.quantile(result.random_counts[:, k], 0.05) / l0),
            "Q6_uniform_p95": float(np.quantile(result.random_counts[:, k], 0.95) / l0),
            "Q6_older_ties_p05": float(np.quantile(older_tie_counts[:, k], 0.05) / l0),
            "Q6_older_ties_median": float(np.median(older_tie_counts[:, k]) / l0),
            "Q6_older_ties_p95": float(np.quantile(older_tie_counts[:, k], 0.95) / l0),
            "Q6_recent_ties_p05": float(np.quantile(result.tie_counts[:, k], 0.05) / l0),
            "Q6_recent_ties_p95": float(np.quantile(result.tie_counts[:, k], 0.95) / l0),
            "recent_resources_selected_by_older_degree": old_selected,
            "recent_resource_coverage_older_degree": old_selected / m,
            "recent_resource_coverage_recent_degree": recent_selected / m,
            "recent_resource_coverage_uniform_median": float(np.median(random_selected) / m),
            "recent_resource_coverage_older_ties_p05": float(
                np.quantile(old_tie_selected, 0.05) / m
            ),
            "recent_resource_coverage_older_ties_p95": float(
                np.quantile(old_tie_selected, 0.95) / m
            ),
            "fraction_older_degree_actions_outside_recent": 1 - old_selected / k,
        }
        rows.append(row)
    arrays = {"recent_" + key: value for key, value in asdict(result).items()}
    arrays.update(
        {
            "older_degree_order": older_result.degree_order,
            "older_degree_counts": older_counts,
            "older_tie_orders": older_result.tie_orders,
            "older_tie_counts": older_tie_counts,
        }
    )
    return rows, arrays, fixed


def run(data_dir, output):
    revisions = load_dse_revisions(data_dir / "revisions.jsonl")
    deletes = load_successful_dse_deletes(data_dir / "events.jsonl")
    times = [REPORT_START + timedelta(hours=i) for i in range(1, 169)]
    assert times[-1] == REPORT_END
    snapshots = {
        w: dict(active_resources_before_times(revisions, deletes, timedelta(hours=w), times))
        for w in [6, 24]
    }
    hourly_rows = []
    crossed_rows = []
    validation = {
        "full_incidence_oracle_checks": 0,
        "forward_trajectory_checks": 0,
        "hourly_snapshots": 168,
    }
    for hour_index, time in enumerate(times, 1):
        graphs = {w: SnapshotGraph.from_resources(snapshots[w][time]) for w in [6, 24]}
        results = {}
        evidence = {"time": time, "hour_index": hour_index, "graphs": {}}
        for w in [6, 24]:
            active = snapshots[w][time]
            graph = graphs[w]
            assert {p: ws for (p, _), ws in active.items()} == direct_snapshot(
                revisions, deletes, timedelta(hours=w), time
            )
            validation["full_incidence_oracle_checks"] += 1
            evidence["graphs"][str(w)] = graph_record(active, graph)
            if not graph.labels:
                continue
            result = run_stress(
                graph,
                w,
                random_seed=20260912 + w + 1000 * hour_index,
                tie_seed=20261912 + w + 1000 * hour_index,
            )
            results[w] = result
            curves = curve_rows(graph, result)
            compact_save(output / "temporal" / f"hour_{hour_index:03d}_w{w}.npz", asdict(result))
            for fraction in [0.1, 0.25, 0.5]:
                k = math.ceil(fraction * len(graph.resources))
                hourly_rows.append(
                    {
                        "hour_index": hour_index,
                        "time": time,
                        "horizon_hours": w,
                        "resources": len(graph.resources),
                        "labels": len(graph.labels),
                        "largest_resource_degree": max(map(len, graph.writers)),
                        "requested_fraction": fraction,
                        **curves[k],
                    }
                )
            if hour_index % 24 == 0:
                np.testing.assert_array_equal(
                    reference_counts(graph, result.degree_order), result.degree_counts
                )
                validation["forward_trajectory_checks"] += 1
        write_json(output / "temporal" / f"hour_{hour_index:03d}_graphs.json", evidence)
        if graphs[6].labels:
            rows, arrays, fixed = cross_evaluate(graphs[6], graphs[24], results[24], hour_index)
            crossed_rows.extend({"hour_index": hour_index, "time": time, **row} for row in rows)
            compact_save(output / "temporal" / f"hour_{hour_index:03d}_crossed.npz", arrays)
            if hour_index % 24 == 0:
                for policy in ["older_degree", "recent_degree"]:
                    np.testing.assert_array_equal(
                        reference_counts(fixed, arrays[policy + "_order"]),
                        arrays[policy + "_counts"],
                    )
                    validation["forward_trajectory_checks"] += 1
        if hour_index % 24 == 0:
            print(f"Temporal audit: {hour_index}/168 hourly snapshots", flush=True)
    # Crossed-horizon comparison at the original T has its own explicit provenance.
    active = {
        w: snapshot_before(revisions, deletes, timedelta(hours=w), SNAPSHOT).active_resources
        for w in [6, 24]
    }
    graphs = {w: SnapshotGraph.from_resources(active[w]) for w in [6, 24]}
    older = run_stress(graphs[24], 24)
    rows, arrays, fixed = cross_evaluate(graphs[6], graphs[24], older, 0)
    write_csv(output / "crossed_frozen_snapshot.csv", rows)
    compact_save(output / "temporal" / "frozen_crossed.npz", arrays)
    write_json(
        output / "temporal" / "frozen_graphs.json",
        {"time": SNAPSHOT, "graphs": {str(w): graph_record(active[w], graphs[w]) for w in [6, 24]}},
    )
    for policy in ["older_degree", "recent_degree"]:
        np.testing.assert_array_equal(
            reference_counts(fixed, arrays[policy + "_order"]), arrays[policy + "_counts"]
        )
        validation["forward_trajectory_checks"] += 1
    write_csv(output / "temporal_checkpoints.csv", hourly_rows)
    write_csv(output / "crossed_hourly.csv", crossed_rows)
    # Every hour is represented in the graph archive, including empty graphs.
    import pandas as pd

    df = pd.DataFrame(hourly_rows)
    cross = pd.DataFrame(crossed_rows)
    summary = {}
    for w in [6, 24]:
        summary[str(w)] = {}
        for frac in [0.1, 0.25, 0.5]:
            part = df[(df.horizon_hours == w) & (df.requested_fraction == frac)]
            summary[str(w)][str(frac)] = {
                "nonempty_hours": len(part),
                "empty_hours": 168 - len(part),
                "positive_gain_hours": int((part.G > 1e-12).sum()),
                "zero_gain_hours": int((part.G.abs() <= 1e-12).sum()),
                "negative_gain_hours": int((part.G < -1e-12).sum()),
                "median_G": float(part.G.median()),
                "median_Q_gain": float((part.Q_random_median - part.Q_degree).median()),
                "degree_below_random_p05_hours": int(
                    (part.R_degree < part.R_random_p05 - 1e-12).sum()
                ),
                "resources_min": int(part.resources.min()),
                "resources_median": float(part.resources.median()),
                "resources_max": int(part.resources.max()),
            }
    part = cross[cross.requested_fraction_of_recent_resources == 1.0]
    summary["crossed_at_full_recent_budget"] = {
        "nonempty_recent_hours": len(part),
        "older_degree_zero_recent_coverage_hours": int(
            (part.recent_resource_coverage_older_degree == 0).sum()
        ),
        "older_degree_unchanged_Q6_hours": int((part.Q6_older_degree == 1).sum()),
        "coverage_quantiles": {
            str(q): float(part.recent_resource_coverage_older_degree.quantile(q))
            for q in [0, 0.25, 0.5, 0.75, 1]
        },
        "Q6_older_degree_quantiles": {
            str(q): float(part.Q6_older_degree.quantile(q)) for q in [0, 0.25, 0.5, 0.75, 1]
        },
        "all_recent_degree_coverage_one": bool(
            (part.recent_resource_coverage_recent_degree == 1).all()
        ),
        "older_degree_below_uniform_coverage_hours": int(
            (
                part.recent_resource_coverage_older_degree
                < part.recent_resource_coverage_uniform_median
            ).sum()
        ),
    }
    write_json(output / "temporal_summary.json", summary)
    write_json(output / "temporal_validation.json", validation)
    audit_tie_bounds(output)
    print(summary, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=Path.home() / "code" / "swarmtrace-data")
    p.add_argument("--output-dir", type=Path, default=Path("outputs"))
    a = p.parse_args()
    run(a.data_dir, a.output_dir)


if __name__ == "__main__":
    main()
