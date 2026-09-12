"""Post-result audit extensions. Primary results stay in swarmtrace.run outputs."""

import argparse
from collections import Counter
from datetime import timedelta
from pathlib import Path

import numpy as np

from swarmtrace.graph import SnapshotGraph
from swarmtrace.load import (
    classify_revision,
    load_dse_revisions,
    load_successful_dse_deletes,
    parse_utc_timestamp,
)
from swarmtrace.run import REPORT_END, REPORT_START, SNAPSHOT, write_csv, write_json
from swarmtrace.state import LiveSurfaceState, snapshot_before
from swarmtrace.stress import curve_rows, largest_label_counts, run_stress


def exact_distributions(graph):
    """Enumerate uniform withdrawn subsets, including every admissible degree-tie subset."""
    m, n = len(graph.resources), len(graph.labels)
    if m > 20:
        raise ValueError("Exact enumeration is restricted to at most 20 resources")
    random_hist = np.zeros((m + 1, n + 1), dtype=np.int64)
    tie_hist = np.zeros_like(random_hist)
    degrees = [len(ws) for ws in graph.writers]
    for mask in range(1 << m):
        removed = [i for i in range(m) if mask & (1 << i)]
        retained = [i for i in range(m) if not mask & (1 << i)]
        k = len(removed)
        count = largest_label_counts(graph, removed + retained)[k]
        random_hist[k, count] += 1
        if (
            not removed
            or not retained
            or min(degrees[i] for i in removed) >= max(degrees[i] for i in retained)
        ):
            tie_hist[k, count] += 1
    rows = []
    for k in range(m + 1):
        for policy, hist in [("uniform", random_hist), ("degree_ties", tie_hist)]:
            for size in np.flatnonzero(hist[k]):
                rows.append(
                    {
                        "k": k,
                        "policy": policy,
                        "largest_label_component": int(size),
                        "R": size / n,
                        "subsets": int(hist[k, size]),
                        "total_subsets": int(hist[k].sum()),
                        "probability": hist[k, size] / hist[k].sum(),
                    }
                )
    return rows, random_hist, tie_hist


def local_clock_order(revisions, deletes, w, order):
    """Replay the one affected page at the touching uncertainty intervals.

    Both relevant clocks are set to their common possible time. Ordering at that
    time is explicit here, unlike primary replay which rejects ambiguous collisions.
    """
    page = "dse~OECDEducationEquitySequence"
    target_revision = "dse~OECDEducationEquitySequence@13"
    target_delete = "delete:dse:rclog:146261"
    events = []
    horizon = timedelta(hours=w)
    common = parse_utc_timestamp("2026-06-20T00:01:23Z")
    times = set()
    for r in revisions:
        if r["page_key"] != page:
            continue
        time = (
            common
            if order != "observed" and r["rev_id"] == target_revision
            else parse_utc_timestamp(r["time"])
        )
        events.append((time, 1 if order == "delete_then_write" else 0, r["seq"], "write", r))
        times.add(time)
        if classify_revision(r) == "suspicious":
            times.add(time + horizon)
    for d in deletes:
        if d["page_key"] != page:
            continue
        time = (
            common
            if order != "observed" and d["event_id"] == target_delete
            else parse_utc_timestamp(d["time"])
        )
        events.append((time, 0 if order == "delete_then_write" else 1, 0, "delete", d))
        times.add(time)
    events.sort(key=lambda e: e[:3])
    i = 0
    state = LiveSurfaceState(horizon)
    for time in sorted(times):
        state.expire(time)
        while i < len(events) and events[i][0] == time:
            _, _, _, kind, record = events[i]
            if kind == "write":
                state.apply_revision({**record, "time": time})
            else:
                state.apply_delete(page, time)
            i += 1
    counts = Counter(t.kind for t in state.transitions if REPORT_START <= t.timestamp < REPORT_END)
    return {
        "horizon_hours": w,
        "ordering": order,
        **{kind: counts[kind] for kind in ["activation", "deletion_exit", "inactivity_exit"]},
    }


def run(data_dir, output):
    revisions = load_dse_revisions(data_dir / "revisions.jsonl")
    deletes = load_successful_dse_deletes(data_dir / "events.jsonl")
    boundary_rows = []
    exclusion_rows = []
    exact_checks = []
    clock_rows = []
    for w in [1, 6, 24]:
        state = snapshot_before(revisions, deletes, timedelta(hours=w), SNAPSHOT)
        graph = SnapshotGraph.from_state(state)
        if w <= 6:
            print(f"Enumerating all {2 ** len(graph.resources):,} subsets for W={w}", flush=True)
            rows, rh, th = exact_distributions(graph)
            write_csv(output / f"exact_distributions_w{w}.csv", rows)
            primary = run_stress(graph, w)
            import math

            for frac in [0.1, 0.25, 0.5]:
                k = math.ceil(frac * len(graph.resources))
                cut = primary.degree_counts[k]
                random = np.repeat(np.arange(len(graph.labels) + 1), rh[k])
                ties = np.repeat(np.arange(len(graph.labels) + 1), th[k])
                exact_checks.append(
                    {
                        "horizon_hours": w,
                        "requested_fraction": frac,
                        "k": k,
                        "degree_component_labels": int(cut),
                        "uniform_component_p05": float(
                            np.quantile(random, 0.05, method="inverted_cdf")
                        ),
                        "uniform_component_median": float(np.median(random)),
                        "uniform_component_p95": float(
                            np.quantile(random, 0.95, method="inverted_cdf")
                        ),
                        "uniform_probability_at_least_as_disruptive": float(np.mean(random <= cut)),
                        "tie_component_min": int(ties.min()),
                        "tie_component_median": float(np.median(ties)),
                        "tie_component_max": int(ties.max()),
                        "uniform_subsets": int(rh[k].sum()),
                        "degree_tie_subsets": int(th[k].sum()),
                    }
                )
        for offset in [-1, 0, 1]:
            other = SnapshotGraph.from_state(
                snapshot_before(
                    revisions, deletes, timedelta(hours=w), SNAPSHOT + timedelta(seconds=offset)
                )
            )
            sim = run_stress(other, w)
            curves = curve_rows(other, sim)
            import math

            for frac in [0.1, 0.25, 0.5]:
                row = curves[math.ceil(frac * len(other.resources))]
                boundary_rows.append(
                    {
                        "horizon_hours": w,
                        "snapshot_offset_seconds": offset,
                        "resources": len(other.resources),
                        "labels": len(other.labels),
                        "requested_fraction": frac,
                        **row,
                    }
                )
        included = [
            {**r, "label": "INCLUDED_AMBIGUOUS:" + r["label"]}
            if classify_revision(r) == "ambiguous"
            else r
            for r in revisions
        ]
        other = SnapshotGraph.from_state(
            snapshot_before(included, deletes, timedelta(hours=w), SNAPSHOT)
        )
        sim = run_stress(other, w)
        curves = curve_rows(other, sim)
        for frac in [0.1, 0.25, 0.5]:
            row = curves[math.ceil(frac * len(other.resources))]
            exclusion_rows.append(
                {
                    "horizon_hours": w,
                    "resources": len(other.resources),
                    "labels": len(other.labels),
                    "requested_fraction": frac,
                    **row,
                }
            )
        for order in ["observed", "write_then_delete", "delete_then_write"]:
            clock_rows.append(local_clock_order(revisions, deletes, w, order))
        if w == 24:
            hub_rows = []
            for (page, episode), writers in state.active_resources.items():
                ages = [(SNAPSHOT - time).total_seconds() / 3600 for time in writers.values()]
                hub_rows.append(
                    {
                        "page_key": page,
                        "episode": episode,
                        "degree_24h": len(writers),
                        "writers_within_6h": sum(age <= 6 for age in ages),
                        "latest_writer_age_hours": min(ages),
                        "median_latest_write_age_hours": float(np.median(ages)),
                        "oldest_writer_age_hours": max(ages),
                    }
                )
            write_csv(
                output / "hub_recency.csv",
                sorted(hub_rows, key=lambda r: (-r["degree_24h"], r["page_key"])),
            )
    write_csv(output / "exact_checkpoints.csv", exact_checks)
    write_csv(output / "snapshot_clock_sensitivity.csv", boundary_rows)
    write_csv(output / "ambiguous_label_sensitivity.csv", exclusion_rows)
    write_csv(output / "clock_order_sensitivity.csv", clock_rows)
    write_json(
        output / "diagnostics_validation.json",
        {
            "exact_subset_totals": {"1": 8, "6": 262144},
            "scope": "Post-result diagnostics; do not replace primary results",
        },
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=Path.home() / "code" / "swarmtrace-data")
    p.add_argument("--output-dir", type=Path, default=Path("outputs"))
    a = p.parse_args()
    run(a.data_dir, a.output_dir)


if __name__ == "__main__":
    main()
