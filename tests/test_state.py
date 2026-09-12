from datetime import UTC, datetime, timedelta

from swarmtrace.state import LiveSurfaceState, reconstruct_hourly, replay_records


def test_two_labels_make_one_active_multiwriter_resource() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start,
    )

    assert state.active_multiwriter_count == 0

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentB",
        timestamp=start + timedelta(minutes=1),
    )

    assert state.active_multiwriter_count == 1


def test_repeated_writes_by_same_label_still_count_as_one_writer() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start,
    )

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start + timedelta(minutes=1),
    )

    assert state.active_multiwriter_count == 0


def test_writer_expires_at_horizon_boundary() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start,
    )

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentB",
        timestamp=start + timedelta(minutes=1),
    )

    assert state.active_multiwriter_count == 1

    state.expire(start + timedelta(hours=6))

    assert state.active_multiwriter_count == 0


def test_newer_write_refreshes_writer_activity() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start,
    )

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentB",
        timestamp=start + timedelta(minutes=1),
    )

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start + timedelta(hours=5),
    )

    state.expire(start + timedelta(hours=6))

    assert state.active_multiwriter_count == 1


def test_delete_clears_all_live_writers_for_page() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start,
    )

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentB",
        timestamp=start + timedelta(minutes=1),
    )

    assert state.active_multiwriter_count == 1

    state.apply_delete(
        page_key="dse~ExamplePage",
        timestamp=start + timedelta(minutes=2),
    )

    assert state.active_multiwriter_count == 0


def test_recreated_page_does_not_inherit_old_writers() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start,
    )

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentB",
        timestamp=start + timedelta(minutes=1),
    )

    assert state.active_multiwriter_count == 1

    state.apply_delete(
        page_key="dse~ExamplePage",
        timestamp=start + timedelta(minutes=2),
    )

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentC",
        timestamp=start + timedelta(minutes=3),
    )

    assert state.active_multiwriter_count == 0


def test_unmatched_delete_does_not_change_active_surface() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write(
        page_key="dse~ActivePage",
        label="AgentA",
        timestamp=start,
    )

    state.apply_write(
        page_key="dse~ActivePage",
        label="AgentB",
        timestamp=start + timedelta(minutes=1),
    )

    assert state.active_multiwriter_count == 1

    state.apply_delete(
        page_key="dse~NeverSeenPage",
        timestamp=start + timedelta(minutes=2),
    )

    assert state.active_multiwriter_count == 1


def test_writer_is_still_live_just_before_horizon_boundary() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start,
    )

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentB",
        timestamp=start + timedelta(seconds=1),
    )

    state.expire(start + timedelta(hours=5, minutes=59, seconds=59))

    assert state.active_multiwriter_count == 1


def test_moderator_revision_does_not_enter_live_surface() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_revision(
        {
            "page_key": "dse~ExamplePage",
            "label": "AgentA",
            "ip16": "20.57",
            "time": start,
        }
    )

    state.apply_revision(
        {
            "page_key": "dse~ExamplePage",
            "label": "[Admin1]",
            "ip16": "2.202",
            "time": start + timedelta(minutes=1),
        }
    )

    assert state.active_multiwriter_count == 0


def test_ambiguous_revision_does_not_enter_live_surface() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_revision(
        {
            "page_key": "dse~ExamplePage",
            "label": "AgentA",
            "ip16": "20.57",
            "time": start,
        }
    )

    state.apply_revision(
        {
            "page_key": "dse~ExamplePage",
            "label": "[Admin2]",
            "ip16": "20.168",
            "time": start + timedelta(minutes=1),
        }
    )

    assert state.active_multiwriter_count == 0


def test_second_writer_records_activation() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start,
    )

    assert state.transitions == []

    second_write = start + timedelta(minutes=1)

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentB",
        timestamp=second_write,
    )

    assert len(state.transitions) == 1

    transition = state.transitions[0]

    assert transition.kind == "activation"
    assert transition.page_key == "dse~ExamplePage"
    assert transition.timestamp == second_write


def test_delete_records_deletion_exit_for_active_multiwriter_page() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start,
    )

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentB",
        timestamp=start + timedelta(minutes=1),
    )

    delete_time = start + timedelta(minutes=2)

    state.apply_delete(
        page_key="dse~ExamplePage",
        timestamp=delete_time,
    )

    assert len(state.transitions) == 2

    transition = state.transitions[-1]

    assert transition.kind == "deletion_exit"
    assert transition.page_key == "dse~ExamplePage"
    assert transition.timestamp == delete_time


def test_expiry_records_inactivity_exit() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentA",
        timestamp=start,
    )

    state.apply_write(
        page_key="dse~ExamplePage",
        label="AgentB",
        timestamp=start + timedelta(minutes=1),
    )

    expire_time = start + timedelta(hours=6)

    state.expire(expire_time)

    assert len(state.transitions) == 2

    transition = state.transitions[-1]

    assert transition.kind == "inactivity_exit"
    assert transition.page_key == "dse~ExamplePage"
    assert transition.timestamp == expire_time


def test_replay_records_processes_unsorted_events_chronologically() -> None:
    revisions = [
        {
            "page_key": "dse~ExamplePage",
            "label": "AgentB",
            "ip16": "20.57",
            "time": "2026-06-18T12:01:00Z",
            "seq": 2,
        },
        {
            "page_key": "dse~ExamplePage",
            "label": "AgentA",
            "ip16": "20.58",
            "time": "2026-06-18T12:00:00Z",
            "seq": 1,
        },
    ]

    deletes = [
        {
            "page_key": "dse~ExamplePage",
            "event_id": "delete:test:1",
            "time": "2026-06-18T12:02:00Z",
        }
    ]

    state = replay_records(
        revisions=revisions,
        deletes=deletes,
        horizon=timedelta(hours=6),
    )

    assert state.active_multiwriter_count == 0

    assert [transition.kind for transition in state.transitions] == [
        "activation",
        "deletion_exit",
    ]

    assert state.transitions[0].timestamp == datetime(2026, 6, 18, 12, 1, tzinfo=UTC)

    assert state.transitions[1].timestamp == datetime(2026, 6, 18, 12, 2, tzinfo=UTC)


def test_replay_records_inactivity_exit_at_exact_expiry_time() -> None:
    revisions = [
        {
            "page_key": "dse~ExamplePage",
            "label": "AgentA",
            "ip16": "20.57",
            "time": "2026-06-18T12:00:00Z",
            "seq": 1,
        },
        {
            "page_key": "dse~ExamplePage",
            "label": "AgentB",
            "ip16": "20.58",
            "time": "2026-06-18T12:01:00Z",
            "seq": 2,
        },
    ]

    state = replay_records(
        revisions=revisions,
        deletes=[],
        horizon=timedelta(hours=6),
    )

    assert [transition.kind for transition in state.transitions] == [
        "activation",
        "inactivity_exit",
    ]

    assert state.transitions[-1].timestamp == datetime(2026, 6, 18, 18, 0, tzinfo=UTC)


def test_refresh_at_exact_expiry_expires_before_new_write() -> None:
    revisions = [
        {
            "page_key": "dse~ExamplePage",
            "label": "AgentA",
            "ip16": "20.57",
            "time": "2026-06-18T12:00:00Z",
            "seq": 1,
        },
        {
            "page_key": "dse~ExamplePage",
            "label": "AgentB",
            "ip16": "20.58",
            "time": "2026-06-18T12:01:00Z",
            "seq": 2,
        },
        {
            "page_key": "dse~ExamplePage",
            "label": "AgentA",
            "ip16": "20.57",
            "time": "2026-06-18T18:00:00Z",
            "seq": 3,
        },
    ]

    state = replay_records(
        revisions=revisions,
        deletes=[],
        horizon=timedelta(hours=6),
    )

    assert [transition.kind for transition in state.transitions] == [
        "activation",
        "inactivity_exit",
        "activation",
        "inactivity_exit",
    ]

    assert state.transitions[0].timestamp == datetime(2026, 6, 18, 12, 1, tzinfo=UTC)

    assert state.transitions[1].timestamp == datetime(2026, 6, 18, 18, 0, tzinfo=UTC)


def test_active_multiwriter_context_counts() -> None:
    state = LiveSurfaceState(horizon=timedelta(hours=6))

    start = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)

    state.apply_write("dse~PageA", "AgentA", start)
    state.apply_write("dse~PageA", "AgentB", start)

    state.apply_write("dse~PageB", "AgentB", start)
    state.apply_write("dse~PageB", "AgentC", start)
    state.apply_write("dse~PageB", "AgentD", start)

    state.apply_write("dse~SingleWriterPage", "AgentE", start)

    assert state.active_multiwriter_count == 2
    assert state.active_multiwriter_incidence_count == 5
    assert state.active_multiwriter_label_count == 4


def test_reconstruct_hourly_tracks_surface_and_context() -> None:
    revisions = [
        {
            "page_key": "dse~ExamplePage",
            "label": "AgentA",
            "ip16": "20.57",
            "time": "2026-06-18T12:10:00Z",
            "seq": 1,
        },
        {
            "page_key": "dse~ExamplePage",
            "label": "AgentB",
            "ip16": "20.58",
            "time": "2026-06-18T12:20:00Z",
            "seq": 2,
        },
    ]

    deletes = [
        {
            "page_key": "dse~UnrelatedPage",
            "event_id": "delete:test:1",
            "time": "2026-06-18T12:30:00Z",
        }
    ]

    rows = reconstruct_hourly(
        revisions=revisions,
        deletes=deletes,
        horizon=timedelta(hours=6),
        start=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
        end=datetime(2026, 6, 18, 14, 0, tzinfo=UTC),
    )

    assert len(rows) == 2

    first = rows[0]

    assert first.hour_start == datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    assert first.surface_start == 0
    assert first.surface_end == 1

    assert first.activations == 1
    assert first.deletion_exits == 0
    assert first.inactivity_exits == 0

    assert first.delete_actions == 1

    assert first.active_multiwriter_incidences == 2
    assert first.active_multiwriter_labels == 2

    second = rows[1]

    assert second.surface_start == 1
    assert second.surface_end == 1

    assert second.activations == 0
    assert second.deletion_exits == 0
    assert second.inactivity_exits == 0
    assert second.delete_actions == 0

    assert second.active_multiwriter_incidences == 2
    assert second.active_multiwriter_labels == 2
