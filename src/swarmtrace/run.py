"""Reproduce both frozen experiments and their audit evidence with one command."""

import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/swarmtrace-matplotlib")
os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

from swarmtrace.graph import SnapshotGraph, direct_snapshot
from swarmtrace.load import (
    build_validation_report,
    classify_revision,
    load_dse_revisions,
    load_successful_dse_deletes,
    parse_utc_timestamp,
    validate_report,
)
from swarmtrace.plots import REPORT_END, REPORT_START, plot_live_surface, write_hourly_csv
from swarmtrace.state import reconstruct_hourly, replay_records, snapshot_before
from swarmtrace.stress import curve_rows, reference_counts, run_stress

SNAPSHOT = datetime(2026, 6, 19, 14, 5, 2, tzinfo=UTC)
HASHES = {
    "pages.jsonl": "92b296170b496b836cdf5ef783bed9465d2d75db7e1a0becec1c36c8b7c42cfd",
    "revisions.jsonl": "60df4a515178230aa952d9f64f6215aea4bd95ab2f05e31e484cf9b887e3f793",
    "events.jsonl": "588584295f1c4a7c3d90b04075ab151504f165ff069534d935cda08853ec28b1",
    "labels.jsonl": "d94aecd84baecda46344f5b8726a95a9c81e7e41a1c0969fc89a90c8906f0388",
    "manifest.json": "b6d53e16b5d9a6a0a98d4577238835ee7a574d7d10a8f1312330b4e626c6ba2b",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=str, allow_nan=False) + "\n"
    )


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def audit_recreations(revisions, deletes, manifest):
    by_id = {r["event_id"]: r for r in deletes}
    evidence = []
    for r in revisions:
        if r.get("relation_type") != "first_recreation_of":
            continue
        related = r["related_event_id"]
        ids = related if isinstance(related, list) else [related]
        for event_id in ids:
            d = by_id.get(event_id)
            evidence.append(
                {
                    "rev_id": r["rev_id"],
                    "page_key": r["page_key"],
                    "time": r["time"],
                    "related_event_id": event_id,
                    "relation_type": r["relation_type"],
                    "delete_found": d is not None,
                    "same_page": d is not None and r["page_key"] == d["page_key"],
                    "seconds_after_delete": (
                        parse_utc_timestamp(r["time"]) - parse_utc_timestamp(d["time"])
                    ).total_seconds()
                    if d
                    else None,
                    "clock_note": r.get("clock_note"),
                }
            )
    return {
        "export_provenance": manifest["recreation_source"],
        "linked_revision_count": len({r["rev_id"] for r in evidence}),
        "linked_edges": len(evidence),
        "missing_event_links": sum(not r["delete_found"] for r in evidence),
        "page_mismatches": sum(not r["same_page"] for r in evidence),
    }, evidence


def clock_audit(revisions, deletes):
    by_page = defaultdict(list)
    for d in deletes:
        by_page[d["page_key"]].append(d)
    near = []
    for r in revisions:
        t = parse_utc_timestamp(r["time"])
        for d in by_page[r["page_key"]]:
            delta = (t - parse_utc_timestamp(d["time"])).total_seconds()
            if abs(delta) <= (r.get("uncertainty_seconds") or 0) + (
                d.get("uncertainty_seconds") or 0
            ):
                near.append(
                    {
                        "rev_id": r["rev_id"],
                        "event_id": d["event_id"],
                        "page_key": r["page_key"],
                        "revision_minus_delete_seconds": delta,
                    }
                )
    return {
        "revision_clock_grades": dict(Counter(r.get("time_grade") for r in revisions)),
        "revision_uncertainty_seconds": dict(
            Counter(r.get("uncertainty_seconds") for r in revisions)
        ),
        "delete_clock_grades": dict(Counter(d.get("time_grade") for d in deletes)),
        "delete_uncertainty_seconds": dict(Counter(d.get("uncertainty_seconds") for d in deletes)),
        "overlapping_revision_delete_uncertainty_intervals": near,
    }


def run(data_dir, output):
    project = Path(__file__).resolve().parents[2]
    actual_hashes = {name: sha256(data_dir / name) for name in HASHES}
    if actual_hashes != HASHES:
        raise ValueError("Raw data hashes differ from the frozen source")
    revisions = load_dse_revisions(data_dir / "revisions.jsonl")
    deletes = load_successful_dse_deletes(data_dir / "events.jsonl")
    validation = build_validation_report(revisions, deletes)
    validate_report(validation)
    write_json(output / "validation.json", validation)
    manifest = json.loads((data_dir / "manifest.json").read_text())
    recreation, evidence = audit_recreations(revisions, deletes, manifest)
    write_json(output / "recreation_audit.json", recreation)
    write_csv(output / "recreation_evidence.csv", evidence)
    write_json(output / "clock_audit.json", clock_audit(revisions, deletes))
    write_csv(
        output / "excluded_revisions.csv",
        [
            {k: r.get(k) for k in ("rev_id", "page_key", "label", "ip16", "time")}
            | {"classification": classify_revision(r)}
            for r in revisions
            if classify_revision(r) != "suspicious"
        ],
    )
    summary, checkpoints, audit = {}, [], {}
    for w in (1, 6, 24):
        print(f"W={w}h: reconstructing history", flush=True)
        horizon = timedelta(hours=w)
        rows = reconstruct_hourly(revisions, deletes, horizon, REPORT_START, REPORT_END)
        write_hourly_csv(rows, output / f"hourly_w{w}.csv")
        for row in rows:
            assert row.surface_end == (
                row.surface_start + row.activations - row.deletion_exits - row.inactivity_exits
            )
            direct = direct_snapshot(
                revisions, deletes, horizon, row.hour_start + timedelta(hours=1)
            )
            assert len(direct) == row.surface_end
            assert sum(map(len, direct.values())) == row.active_multiwriter_incidences
            assert (
                len(set().union(*(set(ws) for ws in direct.values())))
                == row.active_multiwriter_labels
            )
        historical = replay_records(revisions, deletes, horizon)
        ledger = [asdict(r) for r in historical.deletion_records]
        write_csv(output / f"deletions_w{w}.csv", ledger)
        write_csv(output / f"transitions_w{w}.csv", [asdict(r) for r in historical.transitions])
        interval_ledger = [r for r in ledger if REPORT_START <= r["timestamp"] < REPORT_END]
        peak = max(rows, key=lambda r: r.surface_end)
        history = {
            "hourly_endpoint_peak": peak.surface_end,
            "hourly_endpoint_peak_time": peak.hour_start + timedelta(hours=1),
            "surface_start": rows[0].surface_start,
            "surface_end": rows[-1].surface_end,
            "activations": sum(r.activations for r in rows),
            "deletion_exits": sum(r.deletion_exits for r in rows),
            "inactivity_exits": sum(r.inactivity_exits for r in rows),
            "delete_actions": sum(r.delete_actions for r in rows),
            "matched_deletions": sum(r["episode"] is not None for r in interval_ledger),
            "unmatched_deletions": sum(r["episode"] is None for r in interval_ledger),
            "matched_with_zero_live_writers": sum(
                r["episode"] is not None and r["live_writers"] == 0 for r in interval_ledger
            ),
            "matched_with_one_live_writer": sum(r["live_writers"] == 1 for r in interval_ledger),
            "all_history_matched_deletions": sum(r["episode"] is not None for r in ledger),
            "all_history_unmatched_deletions": sum(r["episode"] is None for r in ledger),
        }
        baseline_path = project / "docs" / "audit-baseline.json"
        before = json.loads(baseline_path.read_text())["horizons"][str(w)]
        history["audit_delta_vs_original_implementation"] = {
            key: sum(getattr(r, key) - b[key] for r, b in zip(rows, before, strict=True))
            for key in ("activations", "deletion_exits", "inactivity_exits")
        }
        history["changed_hourly_endpoints_vs_original"] = sum(
            r.surface_end != b["surface_end"] for r, b in zip(rows, before, strict=True)
        )
        state = snapshot_before(revisions, deletes, horizon, SNAPSHOT)
        assert {p: ws for (p, _), ws in state.active_resources.items()} == direct_snapshot(
            revisions, deletes, horizon, SNAPSHOT
        )
        graph = SnapshotGraph.from_state(state)
        write_json(
            output / f"snapshot_w{w}.json",
            {
                "timestamp": SNAPSHOT,
                "boundary": "T^-; [T-W,T)",
                "horizon_hours": w,
                "labels": graph.labels,
                "resources": [
                    {
                        "page_key": p,
                        "episode": ep,
                        "labels": [graph.labels[i] for i in graph.writers[j]],
                    }
                    for j, (p, ep) in enumerate(graph.resources)
                ],
            },
        )
        latest = {}
        for r in revisions:
            t = parse_utc_timestamp(r["time"])
            pair = r["page_key"], r["label"]
            if (
                t < SNAPSHOT
                and classify_revision(r) == "suspicious"
                and (
                    pair not in latest
                    or (r["time"], r["seq"]) > (latest[pair]["time"], latest[pair]["seq"])
                )
            ):
                latest[pair] = r
        write_csv(
            output / f"snapshot_incidences_w{w}.csv",
            [
                {
                    "page_key": p,
                    "episode": ep,
                    "label": label,
                    "latest_write": time,
                    "rev_id": latest[p, label]["rev_id"],
                    "ip16": latest[p, label]["ip16"],
                }
                for (p, ep), ws in sorted(state.active_resources.items())
                for label, time in sorted(ws.items())
            ],
        )
        print(
            f"W={w}h: {len(graph.resources)} resources, {len(graph.labels)} labels; simulating",
            flush=True,
        )
        result = run_stress(graph, w)
        for order, counts in [
            (result.degree_order, result.degree_counts),
            *zip(result.random_orders[:5], result.random_counts[:5], strict=True),
            *zip(result.tie_orders[:5], result.tie_counts[:5], strict=True),
        ]:
            np.testing.assert_array_equal(reference_counts(graph, order), counts)
        for counts in (result.random_counts, result.tie_counts):
            assert np.all(np.diff(counts, axis=1) <= 0)
            assert np.all(counts[:, -1] == 1)
            assert np.all(counts[:, 0] == result.degree_counts[0])
        np.savez_compressed(output / f"simulations_w{w}.npz", **asdict(result))
        curves = curve_rows(graph, result)
        write_csv(output / f"withdrawal_w{w}.csv", curves)
        write_csv(
            output / f"degree_ranking_w{w}.csv",
            [
                {
                    "rank": rank + 1,
                    "page_key": graph.resources[i][0],
                    "episode": graph.resources[i][1],
                    "distinct_label_degree": len(graph.writers[i]),
                }
                for rank, i in enumerate(result.degree_order)
            ],
        )
        for fraction in (0.1, 0.25, 0.5):
            k = math.ceil(fraction * len(graph.resources))
            checkpoints.append({"horizon_hours": w, "requested_fraction": fraction, **curves[k]})
        summary[str(w)] = {
            "history": history,
            "snapshot": {
                "resources": len(graph.resources),
                "labels": len(graph.labels),
                "incidences": sum(map(len, graph.writers)),
                "component_label_sizes": graph.component_label_sizes(),
                "degree_histogram": dict(Counter(map(len, graph.writers))),
                "R0": curves[0]["R0"],
                "random_permutations": 500,
                "tie_permutations": 500,
                "random_seed": 20260912 + w,
                "tie_seed": 20261912 + w,
            },
        }
        audit[str(w)] = {
            "hourly_oracle_checks": len(rows),
            "snapshot_exact_incidence_match": True,
            "forward_removal_trajectory_checks": 11,
            "conservation_checks": len(rows),
        }
        if w == 6:
            plot_live_surface(rows, output / "figures" / "figure1_live_surface.png")
    write_json(output / "summary.json", summary)
    write_csv(output / "checkpoints.csv", checkpoints)
    write_json(output / "analysis_validation.json", audit)
    print(json.dumps(summary, indent=2, default=str), flush=True)


def finalize_manifest(data_dir, output):
    project = Path(__file__).resolve().parents[2]
    actual_hashes = {name: sha256(data_dir / name) for name in HASHES}
    source_files = [
        *sorted((project / "src").rglob("*.py")),
        *sorted((project / "tests").glob("*.py")),
        project / "pyproject.toml",
        project / "uv.lock",
        *sorted((project / "docs").glob("*.md")),
        *sorted((project / "docs").glob("*.json")),
    ]
    # A source ZIP is reproducible without requiring a .git directory.
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=project, capture_output=True, text=True, check=False
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=project, capture_output=True, text=True, check=False
    )
    write_json(
        output / "run_manifest.json",
        {
            "data_sha256": actual_hashes,
            "source_sha256": {str(p.relative_to(project)): sha256(p) for p in source_files},
            "python": platform.python_version(),
            "packages": {
                p: importlib.metadata.version(p)
                for p in ["numpy", "networkx", "pandas", "matplotlib"]
            },
            "git_head": head.stdout.strip() if head.returncode == 0 else None,
            "worktree_has_uncommitted_changes": (
                bool(status.stdout) if status.returncode == 0 else None
            ),
            "report_interval": "[2026-06-16T00:00:00Z, 2026-06-23T00:00:00Z)",
            "snapshot": SNAPSHOT,
            "quantiles": "NumPy linear; pointwise simulation envelope",
            "output_sha256": {
                str(p.relative_to(output)): sha256(p)
                for p in sorted(output.rglob("*"))
                if p.is_file() and p.name != "run_manifest.json"
            },
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path.home() / "code" / "swarmtrace-data")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument(
        "--primary-only",
        action="store_true",
        help="Skip post-result exact and sensitivity diagnostics and paper figures",
    )
    parser.add_argument(
        "--with-temporal-audit",
        action="store_true",
        help="Also run the exploratory hourly and crossed-horizon audit (several minutes)",
    )
    args = parser.parse_args()
    run(args.data_dir.expanduser(), args.output_dir)
    if not args.primary_only:
        from swarmtrace.diagnostics import run as run_diagnostics
        from swarmtrace.paper_figures import generate

        run_diagnostics(args.data_dir.expanduser(), args.output_dir)
        generate(args.output_dir)
    if args.with_temporal_audit:
        from swarmtrace.temporal import run as run_temporal

        run_temporal(args.data_dir.expanduser(), args.output_dir)
        from swarmtrace.review_controls import run as run_review_controls

        run_review_controls(args.data_dir.expanduser(), args.output_dir)
        from swarmtrace.paper_figures import generate_temporal

        generate_temporal(args.output_dir)
    finalize_manifest(args.data_dir.expanduser(), args.output_dir)


if __name__ == "__main__":
    main()
