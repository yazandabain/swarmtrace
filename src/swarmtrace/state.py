from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from swarmtrace.load import classify_revision, parse_utc_timestamp


@dataclass(frozen=True)
class SurfaceTransition:
    kind: str
    page_key: str
    timestamp: datetime


class LiveSurfaceState:
    def __init__(self, horizon: timedelta) -> None:
        self.horizon = horizon
        self._writers_by_page: dict[str, dict[str, datetime]] = {}
        self.transitions: list[SurfaceTransition] = []

    def apply_write(
        self,
        page_key: str,
        label: str,
        timestamp: datetime,
    ) -> None:
        writers = self._writers_by_page.setdefault(page_key, {})

        was_multiwriter = len(writers) >= 2

        writers[label] = timestamp

        is_multiwriter = len(writers) >= 2

        if not was_multiwriter and is_multiwriter:
            self.transitions.append(
                SurfaceTransition(
                    kind="activation",
                    page_key=page_key,
                    timestamp=timestamp,
                )
            )

    def expire(
        self,
        timestamp: datetime,
        protected_pairs: set[tuple[str, str]] | None = None,
    ) -> None:
        cutoff = timestamp - self.horizon
        protected_pairs = protected_pairs or set()

        for page_key, writers in list(self._writers_by_page.items()):
            was_multiwriter = len(writers) >= 2

            expired_labels = [
                label
                for label, last_write in writers.items()
                if last_write <= cutoff and (page_key, label) not in protected_pairs
            ]

            for label in expired_labels:
                del writers[label]

            is_multiwriter = len(writers) >= 2

            if was_multiwriter and not is_multiwriter:
                self.transitions.append(
                    SurfaceTransition(
                        kind="inactivity_exit",
                        page_key=page_key,
                        timestamp=timestamp,
                    )
                )

            if not writers:
                del self._writers_by_page[page_key]

    @property
    def active_multiwriter_count(self) -> int:
        return sum(len(writers) >= 2 for writers in self._writers_by_page.values())

    def apply_delete(
        self,
        page_key: str,
        timestamp: datetime,
    ) -> None:
        writers = self._writers_by_page.get(page_key)

        if writers is not None and len(writers) >= 2:
            self.transitions.append(
                SurfaceTransition(
                    kind="deletion_exit",
                    page_key=page_key,
                    timestamp=timestamp,
                )
            )

        self._writers_by_page.pop(page_key, None)

    def apply_revision(self, record: dict) -> None:
        if classify_revision(record) != "suspicious":
            return

        self.apply_write(
            page_key=record["page_key"],
            label=record["label"],
            timestamp=record["time"],
        )


def replay_records(
    revisions: list[dict],
    deletes: list[dict],
    horizon: timedelta,
) -> LiveSurfaceState:
    state = LiveSurfaceState(horizon=horizon)

    revisions_by_time: dict[datetime, list[dict]] = defaultdict(list)
    deletes_by_time: dict[datetime, list[dict]] = defaultdict(list)
    expiry_times: set[datetime] = set()

    revision_page_times = set()
    delete_page_times = set()

    for record in revisions:
        timestamp = parse_utc_timestamp(record["time"])
        revisions_by_time[timestamp].append(record)
        revision_page_times.add((timestamp, record["page_key"]))

        if classify_revision(record) == "suspicious":
            expiry_times.add(timestamp + horizon)

    for record in deletes:
        timestamp = parse_utc_timestamp(record["time"])
        deletes_by_time[timestamp].append(record)
        delete_page_times.add((timestamp, record["page_key"]))

    ambiguous_collisions = revision_page_times & delete_page_times

    if ambiguous_collisions:
        raise ValueError("Revision/delete collision on same page and timestamp")

    event_times = set(revisions_by_time) | set(deletes_by_time) | expiry_times

    for timestamp in sorted(event_times):
        revisions_at_time = sorted(
            revisions_by_time.get(timestamp, []),
            key=lambda record: (record["page_key"], record["seq"]),
        )

        protected_pairs = {
            (record["page_key"], record["label"])
            for record in revisions_at_time
            if classify_revision(record) == "suspicious"
        }

        state.expire(
            timestamp,
            protected_pairs=protected_pairs,
        )

        for record in revisions_at_time:
            normalized = dict(record)
            normalized["time"] = timestamp
            state.apply_revision(normalized)

        for record in deletes_by_time.get(timestamp, []):
            state.apply_delete(
                page_key=record["page_key"],
                timestamp=timestamp,
            )

    return state
