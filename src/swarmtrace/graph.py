"""Frozen, unweighted bipartite snapshots. Actor labels remain opaque strings."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

import networkx as nx

from swarmtrace.load import classify_revision, parse_utc_timestamp
from swarmtrace.state import LiveSurfaceState

Resource = tuple[str, int]


@dataclass(frozen=True)
class SnapshotGraph:
    resources: tuple[Resource, ...]
    labels: tuple[str, ...]
    writers: tuple[tuple[int, ...], ...]

    @classmethod
    def from_state(cls, state: LiveSurfaceState) -> "SnapshotGraph":
        return cls.from_resources(state.active_resources)

    @classmethod
    def from_resources(cls, active: dict[Resource, dict[str, datetime]]) -> "SnapshotGraph":
        resources = tuple(sorted(active))
        labels = tuple(sorted({label for writers in active.values() for label in writers}))
        index = {label: i for i, label in enumerate(labels)}
        writers = tuple(tuple(sorted(index[label] for label in active[r])) for r in resources)
        return cls(resources, labels, writers)

    def networkx(self) -> nx.Graph:
        graph = nx.Graph()
        graph.add_nodes_from((("label", i) for i in range(len(self.labels))), bipartite=0)
        for j, writers in enumerate(self.writers):
            resource = ("resource", j)
            graph.add_node(resource, bipartite=1)
            graph.add_edges_from((resource, ("label", i)) for i in writers)
        return graph

    def component_label_sizes(self) -> list[int]:
        return sorted(
            (sum(n[0] == "label" for n in c) for c in nx.connected_components(self.networkx())),
            reverse=True,
        )


def direct_snapshot(
    revisions: list[dict], deletes: list[dict], horizon: timedelta, timestamp: datetime
) -> dict[str, dict[str, datetime]]:
    """Independent left-limit oracle: filter against each page's last prior deletion.

    This deliberately does not call the replay, expiry scheduler or episode tracker.
    A same-page equal-time source collision is undefined and rejected by the loader/replay.
    """
    last_delete = {}
    for record in deletes:
        time = parse_utc_timestamp(record["time"])
        page = record["page_key"]
        if time < timestamp and (page not in last_delete or time > last_delete[page]):
            last_delete[page] = time
    writers = defaultdict(dict)
    for record in revisions:
        time = parse_utc_timestamp(record["time"])
        page = record["page_key"]
        if not timestamp - horizon <= time < timestamp:
            continue
        if page in last_delete and time <= last_delete[page]:
            continue
        if classify_revision(record) != "suspicious":
            continue
        label = record["label"]
        if label not in writers[page] or time > writers[page][label]:
            writers[page][label] = time
    return {p: dict(ws) for p, ws in writers.items() if len(ws) >= 2}
