"""Check manuscript headline values against reproducible outputs, and save their provenance."""

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
REPORT = ROOT / "report"


def verify():
    summary = json.loads((OUT / "summary.json").read_text())
    validation = json.loads((OUT / "validation.json").read_text())
    checks = pd.read_csv(OUT / "checkpoints.csv")
    exact = pd.read_csv(OUT / "exact_checkpoints.csv")
    hubs = pd.read_csv(OUT / "hub_recency.csv")
    claims = []

    def check(name, actual, expected, source):
        if isinstance(expected, (list, dict, str)):
            assert actual == expected, (name, actual, expected)
        else:
            assert math.isclose(float(actual), float(expected), rel_tol=0, abs_tol=1e-10), (
                name,
                actual,
                expected,
            )
        claims.append({"claim": name, "verified_value": actual, "source": source})

    for key, value in {
        "total": 13403,
        "suspicious": 13372,
        "moderator": 26,
        "ambiguous": 5,
        "missing": 0,
    }.items():
        check(
            "revision coverage: " + key,
            validation["revisions"]["actor_counts"][key],
            value,
            "outputs/validation.json: revisions.actor_counts." + key,
        )
    check(
        "all successful deletions",
        validation["deletes"]["total"],
        5217,
        "outputs/validation.json: deletes.total",
    )
    for w, expected in {
        "1": [112, 1186, 35, 1151, 0],
        "6": [331, 1101, 54, 1047, 0],
        "24": [379, 1066, 87, 904, 75],
    }.items():
        for key, value in zip(
            [
                "hourly_endpoint_peak",
                "activations",
                "deletion_exits",
                "inactivity_exits",
                "surface_end",
            ],
            expected,
            strict=True,
        ):
            check(
                f"history W={w}: {key}",
                summary[w]["history"][key],
                value,
                f"outputs/summary.json: {w}.history.{key}",
            )
        check(
            f"W={w} conservation",
            summary[w]["history"]["activations"]
            - summary[w]["history"]["deletion_exits"]
            - summary[w]["history"]["inactivity_exits"],
            expected[-1],
            f"outputs/summary.json: {w}.history",
        )
        check(
            f"W={w} deletion actions",
            summary[w]["history"]["delete_actions"],
            442,
            f"outputs/summary.json: {w}.history.delete_actions",
        )
    for key, value in {
        "matched_deletions": 345,
        "unmatched_deletions": 97,
        "matched_with_zero_live_writers": 230,
        "matched_with_one_live_writer": 61,
        "all_history_unmatched_deletions": 1257,
    }.items():
        check(
            "primary deletion ledger: " + key,
            summary["6"]["history"][key],
            value,
            "outputs/summary.json: 6.history." + key,
        )
    check(
        "deletion-action fraction with multi-writer exit, percent rounded",
        round(100 * 54 / 442, 1),
        12.2,
        "outputs/summary.json: 6.history.deletion_exits / delete_actions",
    )
    for w, vals in {"1": [3, 5, 7], "6": [18, 27, 40], "24": [376, 826, 2471]}.items():
        # Incidence count at 1h is taken from the output and not asserted in the paper.
        for key, value in zip(["resources", "labels"], vals[:2], strict=True):
            check(
                f"snapshot W={w}: {key}",
                summary[w]["snapshot"][key],
                value,
                f"outputs/summary.json: {w}.snapshot.{key}",
            )
    for w, value in [("6", 40), ("24", 2471)]:
        check(
            "snapshot incidences W=" + w,
            summary[w]["snapshot"]["incidences"],
            value,
            f"outputs/summary.json: {w}.snapshot.incidences",
        )
    check(
        "primary component labels",
        summary["6"]["snapshot"]["component_label_sizes"],
        [8, 6, 4, 3, 2, 2, 2],
        "outputs/summary.json: 6.snapshot.component_label_sizes",
    )
    check(
        "24h largest component",
        summary["24"]["snapshot"]["component_label_sizes"][0],
        782,
        "outputs/summary.json: 24.snapshot.component_label_sizes[0]",
    )
    check(
        "primary resource degree counts",
        summary["6"]["snapshot"]["degree_histogram"],
        {"2": 14, "3": 4},
        "outputs/summary.json: 6.snapshot.degree_histogram",
    )
    expected_rows = [
        (1, 1, 0.600, 0.800, 0.200),
        (6, 2, 1, 0.875, -0.037),
        (6, 5, 0.75, 0.75, 0),
        (6, 9, 0.5, 0.625, 0.037),
        (24, 38, 0.623, 0.964, 0.323),
        (24, 94, 0.381, 0.895, 0.487),
        (24, 188, 0.107, 0.701, 0.562),
    ]
    for w, k, qd, qr, g in expected_rows:
        row = checks[(checks.horizon_hours == w) & (checks.k == k)].iloc[0]
        for key, value in [("Q_degree", qd), ("Q_random_median", qr), ("G", g)]:
            check(
                f"Frozen checkpoint W={w}, k={k}: {key}",
                round(float(row[key]), 3),
                value,
                f"outputs/checkpoints.csv: horizon_hours={w}, k={k}, column={key}",
            )
    r = checks[(checks.horizon_hours == 24) & (checks.k == 94)].iloc[0]
    check(
        "24h 25% budget degree Q, percent",
        round(r.Q_degree * 100, 1),
        38.1,
        "outputs/checkpoints.csv: W=24,k=94,Q_degree times 100",
    )
    check(
        "24h 25% budget median random Q, percent",
        round(r.Q_random_median * 100, 1),
        89.5,
        "outputs/checkpoints.csv: W=24,k=94,Q_random_median times 100",
    )
    sims = np.load(OUT / "simulations_w24.npz")
    check(
        "24h 94 withdrawals degree component",
        int(sims["degree_counts"][94]),
        298,
        "outputs/simulations_w24.npz: degree_counts[94]",
    )
    check(
        "24h 94 withdrawals median random component",
        float(np.median(sims["random_counts"][:, 94])),
        700,
        "outputs/simulations_w24.npz: median(random_counts[:,94])",
    )
    check(
        "sampled random orders as disruptive as degree, W24 k94",
        int(np.sum(sims["random_counts"][:, 94] <= sims["degree_counts"][94])),
        0,
        "outputs/simulations_w24.npz: count(random_counts[:,94] <= degree_counts[94])",
    )
    for k, percent, total, median, d, tmin, tmax in [
        (2, 100, 153, 7, 8, 6, 8),
        (5, 61.9, 8568, 6, 6, 5, 6),
        (9, 35.1, 48620, 5, 4, 3, 6),
    ]:
        row = exact[(exact.horizon_hours == 6) & (exact.k == k)].iloc[0]
        for key, value in [
            ("uniform_subsets", total),
            ("uniform_component_median", median),
            ("degree_component_labels", d),
            ("tie_component_min", tmin),
            ("tie_component_max", tmax),
        ]:
            check(
                f"exact W6 k={k}: {key}",
                float(row[key]),
                value,
                f"outputs/exact_checkpoints.csv: W=6,k={k},{key}",
            )
        check(
            f"exact W6 k={k} probability percent rounded",
            round(100 * row.uniform_probability_at_least_as_disruptive, 1),
            percent,
            f"outputs/exact_checkpoints.csv: W=6,k={k},uniform_probability_at_least_as_disruptive",
        )
    for i, (degree, age) in enumerate([(323, 13.5), (156, 11.0), (106, 11.0)]):
        row = hubs.iloc[i]
        check(
            f"{row.page_key}: 24h degree",
            int(row.degree_24h),
            degree,
            f"outputs/hub_recency.csv: row={i}",
        )
        check(
            f"{row.page_key}: youngest write age rounded hours",
            round(row.latest_writer_age_hours, 1),
            age,
            f"outputs/hub_recency.csv: row={i},latest_writer_age_hours",
        )
        check(
            f"{row.page_key}: writers in 6h",
            int(row.writers_within_6h),
            0,
            f"outputs/hub_recency.csv: row={i}",
        )
    check(
        "24h resources with no writer in 6h",
        int((hubs.writers_within_6h == 0).sum()),
        354,
        "outputs/hub_recency.csv: count(writers_within_6h == 0)",
    )
    sensitivity = pd.read_csv(OUT / "snapshot_clock_sensitivity.csv")
    for w in [1, 6, 24]:
        base = sensitivity[
            (sensitivity.horizon_hours == w) & (sensitivity.snapshot_offset_seconds == 0)
        ]
        for offset in [-1, 1]:
            part = sensitivity[
                (sensitivity.horizon_hours == w) & (sensitivity.snapshot_offset_seconds == offset)
            ]
            for col in ["resources", "labels", "Q_degree", "Q_random_median", "G"]:
                assert np.array_equal(base[col].to_numpy(), part[col].to_numpy())
    claims.append(
        {
            "claim": "All local snapshot-offset checkpoints unchanged",
            "verified_value": True,
            "source": "outputs/snapshot_clock_sensitivity.csv: -1, 0, +1 second comparisons",
        }
    )
    exclusion = pd.read_csv(OUT / "ambiguous_label_sensitivity.csv")
    check(
        "24h labels when ambiguous revisions included",
        int(exclusion[exclusion.horizon_hours == 24].iloc[0].labels),
        827,
        "outputs/ambiguous_label_sensitivity.csv: W=24,labels",
    )
    for w in [1, 6]:
        part = exclusion[exclusion.horizon_hours == w]
        base = checks[checks.horizon_hours == w]
        for col in ["Q_degree", "Q_random_median", "G"]:
            np.testing.assert_array_equal(part[col].to_numpy(), base[col].to_numpy())
    clocks = pd.read_csv(OUT / "clock_order_sensitivity.csv")
    for w in [1, 6, 24]:
        for col in ["activation", "deletion_exit", "inactivity_exit"]:
            assert clocks[clocks.horizon_hours == w][col].nunique() == 1
    claims.append(
        {
            "claim": "Touching clock intervals preserve affected-page transition totals",
            "verified_value": True,
            "source": "outputs/clock_order_sensitivity.csv",
        }
    )
    recreation = json.loads((OUT / "recreation_audit.json").read_text())
    for key, value in [
        ("linked_edges", 64),
        ("linked_revision_count", 63),
        ("missing_event_links", 0),
        ("page_mismatches", 0),
    ]:
        check(
            "recreation provenance: " + key,
            recreation[key],
            value,
            "outputs/recreation_audit.json: " + key,
        )
    links = pd.read_csv(OUT / "recreation_evidence.csv")
    assert (links.seconds_after_delete > 0).all()
    checks2 = json.loads((OUT / "analysis_validation.json").read_text())
    check(
        "hourly independent checks",
        sum(r["hourly_oracle_checks"] for r in checks2.values()),
        504,
        "outputs/analysis_validation.json: sum(hourly_oracle_checks)",
    )
    check(
        "forward-removal trajectory checks",
        sum(r["forward_removal_trajectory_checks"] for r in checks2.values()),
        33,
        "outputs/analysis_validation.json: sum(forward_removal_trajectory_checks)",
    )
    temporal = pd.read_csv(OUT / "temporal_checkpoints.csv")
    for w, counts in [(6, (151, 138, 9, 4)), (24, (161, 160, 1, 0))]:
        part = temporal[(temporal.horizon_hours == w) & (temporal.requested_fraction == 0.25)]
        actual = [
            len(part),
            int((part.G > 1e-12).sum()),
            int((part.G.abs() <= 1e-12).sum()),
            int((part.G < -1e-12).sum()),
        ]
        check(
            f"Hourly W={w}, 25%: nonempty, positive, zero, negative gain",
            actual,
            list(counts),
            "outputs/temporal_checkpoints.csv: W, requested_fraction=0.25",
        )
    six = temporal[(temporal.horizon_hours == 6) & (temporal.requested_fraction == 0.25)]
    check(
        "Hourly W6 positive gain using degree-tie median",
        int((six.R_random_median - six.R_tie_median > 1e-12).sum()),
        139,
        "outputs/temporal_checkpoints.csv: W=6, fraction=0.25, R_random_median > R_tie_median",
    )
    crossed = pd.read_csv(OUT / "crossed_frozen_snapshot.csv")
    full = crossed[crossed.requested_fraction_of_recent_resources == 1].iloc[0]
    for key, value in [
        ("k", 18),
        ("older_candidates", 376),
        ("recent_resources", 18),
        ("recent_resources_selected_by_older_degree", 0),
        ("Q6_older_degree", 1),
        ("Q6_recent_degree", 0.125),
    ]:
        check(
            "Frozen common-pool comparison: " + key,
            float(full[key]),
            value,
            "outputs/crossed_frozen_snapshot.csv: requested_fraction=1, " + key,
        )
    check(
        "Older graph largest component after 18 older-degree withdrawals",
        int(sims["degree_counts"][18]),
        545,
        "outputs/simulations_w24.npz: degree_counts[18]",
    )
    hourly = pd.read_csv(OUT / "crossed_hourly.csv")
    full = hourly[hourly.requested_fraction_of_recent_resources == 1]
    check(
        "Hourly common-pool comparisons",
        len(full),
        151,
        "outputs/crossed_hourly.csv: count(requested_fraction=1)",
    )
    check(
        "Hourly complete misses of recent resources",
        int((full.recent_resource_coverage_older_degree == 0).sum()),
        20,
        "outputs/crossed_hourly.csv: full recent budget, count(older coverage=0)",
    )
    check(
        "Median older-degree coverage of recent resources, rounded percent",
        round(100 * full.recent_resource_coverage_older_degree.median(), 1),
        33.3,
        "outputs/crossed_hourly.csv: full recent budget, median(older coverage)",
    )
    check(
        "Older-degree Q6 better than median uniform at full recent budget",
        int((full.Q6_older_degree < full.Q6_uniform_median - 1e-12).sum()),
        113,
        "outputs/crossed_hourly.csv: full recent budget, Q6_older_degree < Q6_uniform_median",
    )
    bounds = pd.read_csv(OUT / "crossed_tie_bounds.csv")
    full_bounds = bounds[(bounds.source == "hourly") & (bounds.requested_fraction == 1)]
    check(
        "Hourly complete misses under every valid older-degree tie ordering",
        int((full_bounds.max_recent_resources_selected == 0).sum()),
        20,
        "outputs/crossed_tie_bounds.csv: hourly, requested_fraction=1, max_selected=0",
    )
    check(
        "Frozen zero recent coverage under every older-degree tie ordering",
        int(
            bounds[
                (bounds.source == "frozen") & (bounds.requested_fraction == 1)
            ].max_recent_resources_selected.iloc[0]
        ),
        0,
        "outputs/crossed_tie_bounds.csv: frozen, requested_fraction=1, max_selected",
    )
    val = json.loads((OUT / "temporal_validation.json").read_text())
    for key, value in [("full_incidence_oracle_checks", 336), ("forward_trajectory_checks", 27)]:
        check(
            "Temporal validation: " + key,
            val[key],
            value,
            "outputs/temporal_validation.json: " + key,
        )
    controls = pd.read_csv(OUT / "review_controls.csv")
    control_summary = pd.read_csv(OUT / "review_control_summary.csv")
    for w, nonempty, misses, all_ties, expected_misses, mean_coverage, uniform_coverage in [
        (1, 117, 64, 63, 74.6, 17.2, 10.4),
        (3, 147, 49, 49, 59.2, 25.7, 20.0),
        (6, 151, 20, 20, 29.0, 38.9, 33.4),
        (12, 157, 6, 6, 2.7, 58.3, 55.7),
    ]:
        row = control_summary[
            (control_summary.evaluation_hours == w) & (control_summary.requested_fraction == 1)
        ].iloc[0]
        for key, expected in [
            ("nonempty_hours", nonempty),
            ("empty_hours", 168 - nonempty),
            ("older_zero_coverage_hours", misses),
            ("zero_coverage_under_every_tie_order", all_ties),
        ]:
            check(
                f"Table 2 W={w}: {key}",
                int(row[key]),
                expected,
                f"outputs/review_control_summary.csv: W={w},fraction=1,{key}",
            )
        for key, scale, expected in [
            ("uniform_expected_zero_coverage_hours", 1, expected_misses),
            ("older_mean_coverage", 100, mean_coverage),
            ("uniform_mean_expected_coverage", 100, uniform_coverage),
        ]:
            check(
                f"Table 2 W={w}: {key}",
                round(float(row[key]) * scale, 1),
                expected,
                f"outputs/review_control_summary.csv: W={w},fraction=1,{key},scale={scale}",
            )
    for w, resources, pzero in [(1, 3, 97.6), (3, 11, 71.8), (6, 18, 40.5), (12, 30, 7.4)]:
        row = controls[
            (controls.source == "frozen")
            & (controls.evaluation_hours == w)
            & (controls.requested_fraction == 1)
        ].iloc[0]
        for key, expected in [
            ("recent_resources", resources),
            ("k", resources),
            ("tie_max_selected_recent", 0),
        ]:
            check(
                f"Frozen window control W={w}: {key}",
                int(row[key]),
                expected,
                f"outputs/review_controls.csv: frozen,W={w},fraction=1,{key}",
            )
        check(
            f"Frozen window control W={w}: uniform miss percent",
            round(100 * row.uniform_zero_coverage_probability, 1),
            pzero,
            f"outputs/review_controls.csv: frozen,W={w},fraction=1,uniform_zero_coverage_probability",
        )
    row = control_summary[
        (control_summary.evaluation_hours == 6) & (control_summary.requested_fraction == 1)
    ].iloc[0]
    for comparison, expected in [("above", 99), ("equal", 7), ("below", 45)]:
        key = f"coverage_{comparison}_uniform_expectation_hours"
        check(
            "6h coverage " + comparison + " uniform expectation",
            int(row[key]),
            expected,
            "outputs/review_control_summary.csv: W=6,fraction=1," + key,
        )
    review_validation = json.loads((OUT / "review_control_validation.json").read_text())
    for key, expected in [
        ("full_incidence_oracle_checks", 845),
        ("forward_trajectory_checks", 7),
        ("original_crossed_checkpoint_matches", 608),
    ]:
        check(
            "Final controls validation: " + key,
            review_validation[key],
            expected,
            "outputs/review_control_validation.json: " + key,
        )
    from swarmtrace.run import sha256

    check(
        "frozen methodology hash",
        sha256(ROOT / "docs/preanalysis.md"),
        "feb30cc6aa14a6915ccceb6507b2ace6a1fc529e65e1d8bbbbbbef29e1be931a",
        "docs/preanalysis.md",
    )
    (REPORT / "claims.json").write_text(
        json.dumps(
            {
                "verified_claims": len(claims),
                "manuscript_sha256": sha256(REPORT / "manuscript.md"),
                "verification_scope": "Explicit output-value assertions supporting this manuscript; prose interpretation and citations require separate review",
                "claims": claims,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"{len(claims)} numerical/provenance claims verified")


if __name__ == "__main__":
    verify()
