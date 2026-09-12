"""Matched-action resource withdrawal with all original labels retained."""

from dataclasses import dataclass

import networkx as nx
import numpy as np

from swarmtrace.graph import SnapshotGraph


@dataclass
class StressResult:
    degree_order: np.ndarray
    degree_counts: np.ndarray
    random_orders: np.ndarray
    random_counts: np.ndarray
    tie_orders: np.ndarray
    tie_counts: np.ndarray


def largest_label_counts(snapshot: SnapshotGraph, order) -> np.ndarray:
    """Reverse-add resources using disjoint sets on the bipartite node set.

    Components carry a weight of one per original label and zero per resource.
    This counts labels, not total vertices. No label-label graph is constructed.
    """
    n, m = len(snapshot.labels), len(snapshot.resources)
    order = [int(i) for i in order]
    if sorted(order) != list(range(m)):
        raise ValueError("order must contain every resource exactly once")
    parent = list(range(n + m))
    weight = [1] * n + [0] * m
    size = [1] * (n + m)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    largest = int(n > 0)
    counts = np.empty(m + 1, dtype=np.int64)
    counts[m] = largest
    for k in range(m - 1, -1, -1):
        resource = order[k]
        for label in snapshot.writers[resource]:
            a, b = find(n + resource), find(label)
            if a != b:
                if size[a] < size[b]:
                    a, b = b, a
                parent[b] = a
                size[a] += size[b]
                weight[a] += weight[b]
                largest = max(largest, weight[a])
        counts[k] = largest
    return counts


def reference_counts(snapshot: SnapshotGraph, order) -> np.ndarray:
    """Slow independent forward removal, used for validation."""
    graph = snapshot.networkx()

    def count():
        return max(
            (sum(v[0] == "label" for v in c) for c in nx.connected_components(graph)), default=0
        )

    counts = [count()]
    for resource in order:
        graph.remove_node(("resource", int(resource)))
        counts.append(count())
    return np.array(counts)


def run_stress(
    snapshot: SnapshotGraph, horizon_hours: int, permutations: int = 500
) -> StressResult:
    if not snapshot.labels:
        raise ValueError("R is undefined for an empty eligible graph")
    if permutations < 1:
        raise ValueError("permutations must be positive")
    m = len(snapshot.resources)
    degree = np.array([len(w) for w in snapshot.writers])
    degree_order = np.array(sorted(range(m), key=lambda i: (-degree[i], snapshot.resources[i])))
    random_rng = np.random.Generator(np.random.PCG64(20260912 + horizon_hours))
    tie_rng = np.random.Generator(np.random.PCG64(20261912 + horizon_hours))
    random_orders = np.array([random_rng.permutation(m) for _ in range(permutations)])
    groups = [np.flatnonzero(degree == d) for d in sorted(set(degree), reverse=True)]
    tie_orders = np.array(
        [np.concatenate([tie_rng.permutation(g) for g in groups]) for _ in range(permutations)]
    )
    return StressResult(
        degree_order,
        largest_label_counts(snapshot, degree_order),
        random_orders,
        np.array([largest_label_counts(snapshot, o) for o in random_orders]),
        tie_orders,
        np.array([largest_label_counts(snapshot, o) for o in tie_orders]),
    )


def curve_rows(snapshot: SnapshotGraph, result: StressResult) -> list[dict]:
    n, m = len(snapshot.labels), len(snapshot.resources)
    r0 = result.degree_counts[0] / n
    random = np.quantile(result.random_counts / n, [0.05, 0.5, 0.95], axis=0, method="linear")
    ties = np.quantile(result.tie_counts / n, [0.05, 0.5, 0.95], axis=0, method="linear")
    rows = []
    for k in range(m + 1):
        rd = result.degree_counts[k] / n
        rows.append(
            {
                "k": k,
                "fraction_removed": k / m,
                "R0": r0,
                "R_degree": rd,
                "D_degree": r0 - rd,
                "Q_degree": rd / r0,
                "R_random_p05": random[0, k],
                "R_random_median": random[1, k],
                "R_random_p95": random[2, k],
                "Q_random_median": random[1, k] / r0,
                "G": random[1, k] - rd,
                "R_tie_p05": ties[0, k],
                "R_tie_median": ties[1, k],
                "R_tie_p95": ties[2, k],
                "random_fraction_at_least_as_disruptive": float(
                    np.mean(result.random_counts[:, k] <= result.degree_counts[k])
                ),
            }
        )
    return rows
