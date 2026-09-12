from datetime import UTC, datetime, timedelta
from itertools import permutations

import numpy as np
import pytest

from swarmtrace.graph import SnapshotGraph, direct_snapshot
from swarmtrace.state import LiveSurfaceState, snapshot_before
from swarmtrace.stress import largest_label_counts, reference_counts, run_stress


def revision(label, time, seq, page="p"):
    return {"page_key": page, "label": label, "time": time, "seq": seq, "ip16": "20.1"}


def test_snapshot_true_left_limit_and_no_future_leakage():
    t = datetime(2026, 6, 19, 14, 5, 2, tzinfo=UTC)
    h = timedelta(hours=6)
    rows = [
        revision("a", (t - h).isoformat(), 1),
        revision("b", (t - h + timedelta(seconds=1)).isoformat(), 2),
        revision("c", t.isoformat(), 3),
    ]
    deletes = [{"page_key": "p", "time": t.isoformat()}]
    # An exact-T collision is outside the snapshot and must not affect its construction.
    s = snapshot_before(rows, deletes, h, t)
    assert s.active_resources[("p", 1)] == {"a": t - h, "b": t - h + timedelta(seconds=1)}
    assert direct_snapshot(rows, deletes, h, t) == {"p": s.active_resources[("p", 1)]}
    s2 = snapshot_before(rows, [], h, t)
    assert s2.active_resources == s.active_resources
    after = snapshot_before(rows, [], h, t + timedelta(microseconds=1))
    assert set(after.active_resources[("p", 1)]) == {"b", "c"}


def test_lifecycle_survives_expiry_but_not_deletion():
    t = datetime(2026, 6, 19, tzinfo=UTC)
    s = LiveSurfaceState(timedelta(hours=1))
    s.apply_write("p", "a", t)
    s.expire(t + timedelta(hours=1))
    s.apply_delete("p", t + timedelta(hours=2))
    assert s.deletion_records[-1].episode == 1
    assert s.deletion_records[-1].live_writers == 0
    s.apply_delete("p", t + timedelta(hours=3))
    assert s.deletion_records[-1].episode is None
    s.apply_write("p", "b", t + timedelta(hours=4))
    s.apply_write("p", "c", t + timedelta(hours=4))
    assert set(s.active_resources) == {("p", 2)}
    assert set(s.active_resources[("p", 2)]) == {"b", "c"}


def test_same_page_source_collision_is_rejected():
    t = datetime(2026, 6, 19, tzinfo=UTC)
    with pytest.raises(ValueError, match="collision"):
        snapshot_before(
            [revision("a", t.isoformat(), 1)],
            [{"page_key": "p", "time": t.isoformat()}],
            timedelta(hours=1),
            t + timedelta(seconds=1),
        )


def test_largest_component_counts_labels_not_resources_and_keeps_isolates():
    # Three-label component with many duplicate resources vs one four-label resource.
    g = SnapshotGraph(
        tuple((str(i), 1) for i in range(5)),
        tuple("abcdefg"),
        ((0, 1), (0, 1), (1, 2), (0, 2), (3, 4, 5, 6)),
    )
    for order in permutations(range(5)):
        c = largest_label_counts(g, order)
        np.testing.assert_array_equal(c, reference_counts(g, order))
        assert c[0] == 4
        assert c[-1] == 1
        assert np.all(np.diff(c) <= 0)


def test_random_small_graphs_match_forward_bipartite_removal():
    rng = np.random.default_rng(17)
    for _ in range(40):
        n, m = int(rng.integers(2, 20)), int(rng.integers(1, 15))
        writers = tuple(
            tuple(sorted(rng.choice(n, size=int(rng.integers(2, n + 1)), replace=False)))
            for _ in range(m)
        )
        g = SnapshotGraph(tuple((str(i), 1) for i in range(m)), tuple(map(str, range(n))), writers)
        order = rng.permutation(m)
        np.testing.assert_array_equal(largest_label_counts(g, order), reference_counts(g, order))


def test_seeded_policies_are_reproducible_and_degree_ties_preserve_ranking():
    g = SnapshotGraph((("p", 1), ("q", 1), ("r", 1)), tuple("abcd"), ((0, 1), (1, 2, 3), (2, 3)))
    a, b = run_stress(g, 6, 20), run_stress(g, 6, 20)
    np.testing.assert_array_equal(a.random_orders, b.random_orders)
    np.testing.assert_array_equal(a.tie_orders, b.tie_orders)
    assert list(a.degree_order) == [1, 0, 2]
    assert set(a.tie_orders[:, 0]) == {1}
    assert len({tuple(o) for o in a.tie_orders}) == 2
    with pytest.raises(ValueError):
        largest_label_counts(g, [0, 0, 1])


def test_exact_subset_distributions_match_all_uniform_permutations():
    from collections import Counter
    from math import comb, factorial

    from swarmtrace.diagnostics import exact_distributions

    g = SnapshotGraph((("p", 1), ("q", 1), ("r", 1)), tuple("abcde"), ((0, 1, 2), (2, 3), (3, 4)))
    _, histogram, tie_histogram = exact_distributions(g)
    orders = list(permutations(range(3)))
    for k in range(4):
        reference = Counter(reference_counts(g, order)[k] for order in orders)
        assert histogram[k].sum() == comb(3, k)
        for size, count in reference.items():
            assert histogram[k, size] * factorial(k) * factorial(3 - k) == count
    assert tie_histogram[1, 3] == 1
    assert tie_histogram[2].sum() == 2


def test_crossed_graph_changes_action_pool_without_importing_historical_labels():
    from swarmtrace.temporal import crossed_graph

    recent = SnapshotGraph((("p", 1),), ("a", "b"), ((0, 1),))
    older = SnapshotGraph((("p", 1), ("q", 1)), ("a", "b", "c", "d", "e"), ((0, 1), (2, 3, 4)))
    fixed = crossed_graph(recent, older)
    assert fixed.labels == ("a", "b")
    assert fixed.writers == ((0, 1), ())
    # Removing the older hub consumes a step without changing recent connectivity.
    assert list(largest_label_counts(fixed, [1, 0])) == [2, 2, 1]
    assert list(largest_label_counts(fixed, [0, 1])) == [2, 1, 1]
    np.testing.assert_array_equal(reference_counts(fixed, [1, 0]), [2, 2, 1])


def test_multi_snapshot_iterator_preserves_boundaries_and_detaches_results():
    from swarmtrace.state import active_resources_before_times

    t = datetime(2026, 6, 19, tzinfo=UTC)
    h = timedelta(hours=1)
    rows = [
        revision("a", t.isoformat(), 1),
        revision("b", t.isoformat(), 2),
        revision("c", (t + h).isoformat(), 3),
    ]
    times = [t, t + h, t + h + timedelta(microseconds=1)]
    values = list(active_resources_before_times(rows, [], h, times))
    assert values[0][1] == {}
    assert set(values[1][1][("p", 1)]) == {"a", "b"}
    assert values[2][1] == {}
    for time, active in values:
        assert active == snapshot_before(rows, [], h, time).active_resources
    with pytest.raises(ValueError, match="strictly increasing"):
        list(active_resources_before_times(rows, [], h, [t, t]))


def test_exact_tie_coverage_bounds_match_all_admissible_orders():
    from swarmtrace.temporal import tie_coverage_bounds

    degrees = [4, 3, 3, 2]
    present = np.array([False, True, False, True])
    orders = [
        o
        for o in permutations(range(4))
        if [degrees[i] for i in o] == sorted(degrees, reverse=True)
    ]
    for k in range(5):
        hits = [int(present[list(o[:k])].sum()) for o in orders]
        assert tie_coverage_bounds(degrees, present, k) == (min(hits), max(hits))
