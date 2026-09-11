import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from itertools import pairwise
from pathlib import Path

EXPECTED_DSE_REVISIONS = 13_403
EXPECTED_MODERATOR_REVISIONS = 26
EXPECTED_AMBIGUOUS_REVISIONS = 5
EXPECTED_MISSING_LABELS = 0
EXPECTED_SUSPICIOUS_REVISIONS = 13_372

EXPECTED_SUCCESSFUL_DSE_DELETES = 5_217
EXPECTED_DELETE_PAGE_HELD_TRUE = 3_969
EXPECTED_DELETE_PAGE_HELD_FALSE = 1_248
EXPECTED_UNEXPECTED_DELETE_ACTORS = 0

MODERATOR_LABEL = "[Admin1]"
MODERATOR_IP16 = "2.202"

AMBIGUOUS_LABELS = {"[Admin2]", "[Person22]"}


def classify_revision(record: dict) -> str:
    label = record.get("label")
    ip16 = record.get("ip16")

    if label == MODERATOR_LABEL and ip16 == MODERATOR_IP16:
        return "moderator"

    if label in AMBIGUOUS_LABELS:
        return "ambiguous"

    if label is None or not str(label).strip():
        return "missing"

    return "suspicious"


def load_dse_revisions(revisions_path: Path) -> list[dict]:
    records = []

    with revisions_path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)

            if record.get("wiki") == "dse":
                records.append(record)

    return records


def load_successful_dse_deletes(events_path: Path) -> list[dict]:
    records = []

    with events_path.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            record = json.loads(line)

            if not (
                record.get("wiki") == "dse"
                and record.get("event_type") == "delete"
                and record.get("success_observed") is True
            ):
                continue

            records.append(record)

    return records


def summarize_dse_revisions(revisions: list[dict]) -> dict[str, int]:
    counts = {
        "total": 0,
        "moderator": 0,
        "ambiguous": 0,
        "missing": 0,
        "suspicious": 0,
    }

    for record in revisions:
        counts["total"] += 1

        category = classify_revision(record)
        counts[category] += 1

    return counts


def summarize_dse_deletes(deletes: list[dict]) -> dict[str, int]:
    counts = {
        "successful": 0,
        "page_held_true": 0,
        "page_held_false": 0,
        "page_held_missing": 0,
        "unexpected_actor": 0,
    }

    for record in deletes:
        counts["successful"] += 1

        page_held = record.get("page_held")

        if page_held is True:
            counts["page_held_true"] += 1
        elif page_held is False:
            counts["page_held_false"] += 1
        else:
            counts["page_held_missing"] += 1

        if record.get("actor_label") != MODERATOR_LABEL or record.get("ip16") != MODERATOR_IP16:
            counts["unexpected_actor"] += 1

    return counts


def parse_utc_timestamp(value: str) -> datetime:
    timestamp = datetime.fromisoformat(value)

    if timestamp.utcoffset() != timedelta(0):
        raise ValueError(f"Timestamp is not UTC: {value}")

    return timestamp.astimezone(UTC)


def format_utc_timestamp(timestamp: datetime) -> str:
    return timestamp.isoformat().replace("+00:00", "Z")


def build_validation_report(revisions: list[dict], deletes: list[dict]) -> dict:
    revision_ids = [record.get("rev_id") for record in revisions]
    delete_ids = [record.get("event_id") for record in deletes]

    revision_times = [record.get("time") for record in revisions]
    delete_times = [record.get("time") for record in deletes]

    revision_id_counts = Counter(revision_ids)
    delete_id_counts = Counter(delete_ids)

    page_seq_counts = Counter((record.get("page_key"), record.get("seq")) for record in revisions)

    revision_time_counts = Counter(revision_times)
    delete_time_counts = Counter(delete_times)

    revision_page_time_counts = Counter(
        (record.get("time"), record.get("page_key")) for record in revisions
    )

    parsed_revision_times = []
    parsed_delete_times = []
    bad_revision_timestamps = 0
    bad_delete_timestamps = 0

    for record in revisions:
        try:
            parsed_revision_times.append(parse_utc_timestamp(record["time"]))
        except (KeyError, TypeError, ValueError):
            bad_revision_timestamps += 1

    for record in deletes:
        try:
            parsed_delete_times.append(parse_utc_timestamp(record["time"]))
        except (KeyError, TypeError, ValueError):
            bad_delete_timestamps += 1

    revisions_by_page = defaultdict(list)

    for record in revisions:
        if record.get("seq") is None:
            continue

        try:
            timestamp = parse_utc_timestamp(record["time"])
        except (KeyError, TypeError, ValueError):
            continue

        revisions_by_page[record["page_key"]].append((record["seq"], timestamp))

    seq_time_reversals = 0

    for rows in revisions_by_page.values():
        rows.sort(key=lambda item: item[0])

        for previous, current in pairwise(rows):
            if previous[1] > current[1]:
                seq_time_reversals += 1

    revision_timestamp_set = set(revision_times)
    delete_timestamp_set = set(delete_times)

    revision_page_time_set = {(record.get("time"), record.get("page_key")) for record in revisions}
    delete_page_time_set = {(record.get("time"), record.get("page_key")) for record in deletes}

    return {
        "revisions": {
            "total": len(revisions),
            "pages": len({record.get("page_key") for record in revisions}),
            "actor_counts": summarize_dse_revisions(revisions),
            "missing_rev_id": sum(revision_id is None for revision_id in revision_ids),
            "duplicate_rev_id_groups": sum(count > 1 for count in revision_id_counts.values()),
            "missing_seq": sum(record.get("seq") is None for record in revisions),
            "duplicate_page_seq_groups": sum(count > 1 for count in page_seq_counts.values()),
            "shared_timestamp_groups": sum(count > 1 for count in revision_time_counts.values()),
            "same_page_same_timestamp_groups": sum(
                count > 1 for count in revision_page_time_counts.values()
            ),
            "seq_time_reversals": seq_time_reversals,
            "bad_timestamps": bad_revision_timestamps,
            "time_min": format_utc_timestamp(min(parsed_revision_times)),
            "time_max": format_utc_timestamp(max(parsed_revision_times)),
        },
        "deletes": {
            "total": len(deletes),
            "summary": summarize_dse_deletes(deletes),
            "missing_event_id": sum(event_id is None for event_id in delete_ids),
            "duplicate_event_id_groups": sum(count > 1 for count in delete_id_counts.values()),
            "shared_timestamp_groups": sum(count > 1 for count in delete_time_counts.values()),
            "bad_timestamps": bad_delete_timestamps,
            "time_min": format_utc_timestamp(min(parsed_delete_times)),
            "time_max": format_utc_timestamp(max(parsed_delete_times)),
        },
        "cross_stream": {
            "shared_timestamps": len(revision_timestamp_set & delete_timestamp_set),
            "same_page_same_timestamp_collisions": len(
                revision_page_time_set & delete_page_time_set
            ),
        },
    }


def write_validation_report(report: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, sort_keys=True)
        file.write("\n")


def validate_report(report: dict) -> None:
    checks = {
        "DSE page count": (
            report["revisions"]["pages"],
            3_908,
        ),
        "missing revision IDs": (
            report["revisions"]["missing_rev_id"],
            0,
        ),
        "duplicate revision ID groups": (
            report["revisions"]["duplicate_rev_id_groups"],
            0,
        ),
        "missing revision seq": (
            report["revisions"]["missing_seq"],
            0,
        ),
        "duplicate (page_key, seq) groups": (
            report["revisions"]["duplicate_page_seq_groups"],
            0,
        ),
        "seq/time reversals": (
            report["revisions"]["seq_time_reversals"],
            0,
        ),
        "bad revision timestamps": (
            report["revisions"]["bad_timestamps"],
            0,
        ),
        "missing delete event IDs": (
            report["deletes"]["missing_event_id"],
            0,
        ),
        "duplicate delete event ID groups": (
            report["deletes"]["duplicate_event_id_groups"],
            0,
        ),
        "bad delete timestamps": (
            report["deletes"]["bad_timestamps"],
            0,
        ),
        "same-page revision/delete timestamp collisions": (
            report["cross_stream"]["same_page_same_timestamp_collisions"],
            0,
        ),
    }

    for name, (actual, expected) in checks.items():
        if actual != expected:
            raise SystemExit(
                f"Validation failed for {name}: expected {expected:,}, found {actual:,}"
            )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m swarmtrace.load DATA_DIR")

    data_dir = Path(sys.argv[1]).expanduser()
    revisions_path = data_dir / "revisions.jsonl"
    events_path = data_dir / "events.jsonl"

    if not revisions_path.is_file():
        raise SystemExit(f"Missing file: {revisions_path}")

    if not events_path.is_file():
        raise SystemExit(f"Missing file: {events_path}")

    revisions = load_dse_revisions(revisions_path)
    deletes = load_successful_dse_deletes(events_path)

    counts = summarize_dse_revisions(revisions)

    print(f"DSE revisions: {counts['total']:,}")
    print(f"  moderator:   {counts['moderator']:,}")
    print(f"  ambiguous:   {counts['ambiguous']:,}")
    print(f"  missing:     {counts['missing']:,}")
    print(f"  suspicious:  {counts['suspicious']:,}")

    expected = {
        "total": EXPECTED_DSE_REVISIONS,
        "moderator": EXPECTED_MODERATOR_REVISIONS,
        "ambiguous": EXPECTED_AMBIGUOUS_REVISIONS,
        "missing": EXPECTED_MISSING_LABELS,
        "suspicious": EXPECTED_SUSPICIOUS_REVISIONS,
    }

    for category, expected_count in expected.items():
        actual_count = counts[category]

        if actual_count != expected_count:
            raise SystemExit(
                f"Expected {expected_count:,} {category} revisions, found {actual_count:,}"
            )

    delete_counts = summarize_dse_deletes(deletes)

    print()
    print(f"Successful DSE deletes: {delete_counts['successful']:,}")
    print(f"  page_held true:       {delete_counts['page_held_true']:,}")
    print(f"  page_held false:      {delete_counts['page_held_false']:,}")
    print(f"  page_held missing:    {delete_counts['page_held_missing']:,}")
    print(f"  unexpected actor/IP:  {delete_counts['unexpected_actor']:,}")

    expected_deletes = {
        "successful": EXPECTED_SUCCESSFUL_DSE_DELETES,
        "page_held_true": EXPECTED_DELETE_PAGE_HELD_TRUE,
        "page_held_false": EXPECTED_DELETE_PAGE_HELD_FALSE,
        "page_held_missing": 0,
        "unexpected_actor": EXPECTED_UNEXPECTED_DELETE_ACTORS,
    }

    for category, expected_count in expected_deletes.items():
        actual_count = delete_counts[category]

        if actual_count != expected_count:
            raise SystemExit(
                f"Expected {expected_count:,} for delete metric {category}, found {actual_count:,}"
            )

    report = build_validation_report(revisions, deletes)
    validate_report(report)

    project_root = Path(__file__).resolve().parents[2]
    output_path = project_root / "outputs" / "validation.json"

    write_validation_report(report, output_path)

    print()
    print(f"Validation report: {output_path}")


if __name__ == "__main__":
    main()
