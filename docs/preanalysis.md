# SwarmTrace Pre-analysis Plan

Frozen before primary analysis results are computed.

Date frozen: 2026-09-10

## Research question

How did DSEWiki's observed active multi-writer surface evolve during moderator deletion, and at a fixed historical snapshot, how much additional structural disruption did static contemporaneous distinct-label-degree prioritization achieve over random resource withdrawal at matched action counts?

## Scope

- Analyze only DSEWiki (`wiki == "dse"`).
- Process all available DSEWiki history in the export to initialize state.
- Primary reporting interval:
  - start: 2026-06-16 00:00:00 UTC
  - end:   2026-06-23 00:00:00 UTC
  - interval is [start, end)
- Primary activity horizon W = 6 hours.
- Mandatory sensitivity horizons: 1 hour and 24 hours.
- Reporting bins for historical plots: 1 hour.

## Actor interpretation

A revision `label` is treated as an observed actor-label proxy, not proof of a unique underlying agent or process.

Moderator/system activity does not contribute to suspicious writer counts or graph nodes.

Moderator deletions are identified from explicit successful `delete` event records and their provenance, not from username string matching alone.

Raw actor identifiers are preserved.

Rows without a usable suspicious label are excluded from identity-dependent topology and their coverage must be reported.

## Resource lifecycle

A resource is represented by a page episode.

A successful deletion ends the current episode and removes all live incidences on that episode.

A recreation begins a new episode with no inherited writers.

Where recreation linkage is supplied by the export, its provenance and heuristic nature must be preserved and reported.

## Live incidence

For ordinary state at time t, a label-resource incidence is live when the label's latest qualifying write to that resource episode lies in:

(t - W, t]

Exactly W-old writes are expired.

Repeated writes refresh the incidence expiry.

Stale scheduled expirations must not remove a more recently refreshed incidence.

## Active multi-writer resource

An existing resource episode is active multi-writer when at least two distinct suspicious observed-label proxies have live incidences on it.

This is write overlap only.

It does not establish communication, information transfer, or true distinct-agent identity.

## Historical metric

S(t) = number of active multi-writer resource episodes at time t.

Changes in S are categorized as:

- entry/reactivation into active multi-writer state
- exit caused by observed deletion
- exit caused by activity-window expiry

Also report:

- live label-resource incidences on active multi-writer resources
- distinct labels participating in the active multi-writer surface

## Snapshot experiment

Primary snapshot:

2026-06-19 14:05:02 UTC

Use the state immediately BEFORE this timestamp (T^-).

Source events with timestamps >= T do not enter the snapshot.

The graph is an unweighted bipartite graph:

observed suspicious labels <-> active multi-writer resource episodes

No label-label projection is used.

Snapshot label set L_T contains only labels with at least one live incidence on an eligible active multi-writer resource at T^-.

Every label in L_T remains a graph node during resource-removal simulations, including isolated labels.

## Intervention policies

Candidate resources are all active multi-writer resource nodes at T^-.

### Random

Uniformly random resource orderings.

Primary experiment: 500 seeded permutations.

Report median and 5th-95th percentile simulation envelope.

### Static degree

For each resource at T^-:

degree = number of distinct suspicious labels with a live incidence on that resource.

Rank resources once at T^- by descending degree.

Do not use future information and do not re-rank after removals.

Material degree ties may be randomized within degree groups using seeded permutations.

## Primary structural endpoint

For connected components C after k resource removals:

R(k) = max_C |C intersect L_T| / |L_T|

The largest component is selected by number of original label nodes, not by total bipartite nodes.

Because the baseline graph may already be disconnected, also use:

D(k) = R(0) - R(k)

and/or

Q(k) = R(k) / R(0)

## Degree-prioritization gain

G(k) = median(R_random(k)) - R_degree(k)

G > 0 means static degree prioritization produces more disruption of this endpoint than random withdrawal.

G = 0 means similar performance.

G < 0 means degree prioritization performs worse.

This comparison evaluates only the simple static degree heuristic.

## Cross-horizon sensitivity

Changing W changes the eligible graph.

Compare W = 1h, 6h, 24h using fractions of each horizon's eligible resource set, such as:

- 10%
- 25%
- 50%

Prefer baseline-normalized Q for cross-horizon comparison.

## Interpretation limits

The analysis does not establish:

- communication from write overlap alone
- true distinct-agent identities
- information erased by deletion
- unreadability after deletion
- overall containment of the agent system
- adaptation after simulated withdrawal
- optimal targeting
- universal incident-response thresholds

The structural experiment is a frozen historical stress test of dependence on the observable DSEWiki write-overlap topology.

## Frozen data-input rules

Writes are taken only from `revisions.jsonl`.

`events.jsonl` `save` rows are not counted as additional writes because they point back to revisions already represented in `revisions.jsonl`.

Successful DSEWiki `delete` events from `events.jsonl` are processed as lifecycle events. A deletion ends a modeled page episode only when an episode is currently represented in reconstructed state; otherwise it is recorded as an unmatched deletion and does not create a modeled multi-writer exit.

`page_held` is used for validation/context, not as the sole rule for whether a deletion is processed.

## Frozen moderator-provenance rule

The export's `is_human_handle` field is label-level metadata and is not sufficient by itself to authenticate an individual write.

For the primary analysis, a stored revision is classified as verified moderator activity only when:

- `label == "[Admin1]"`
- `ip16 == "2.202"`

This proxy was frozen during schema/provenance inspection because all 5,217 observed successful DSEWiki deletion events use that same label and IP /16, and all 26 stored `[Admin1]` revisions use that same IP /16.

Writes carrying `[Admin2]` or `[Person22]` are classified as ambiguous rather than automatically moderator or suspicious activity. They are excluded from primary identity-dependent topology and their exclusion count is reported.

This operational classification does not prove underlying human identity.

## Available-history boundary

"All available prehistory" means all usable DSEWiki history present in this released export.

The export applies a revision cut of:

`revision.write_date >= 2026-05-01`

That available prehistory is processed to initialize state before the primary reporting interval.

## Equal-time handling

Activity-window expirations at timestamp t are applied before new source events at t, consistent with the ordinary live interval `(t-W, t]`.

For source events sharing an identical timestamp, an authoritative source sequence is used only when the export provides one that is valid for those events.

If unresolved equal-time ordering could change a scientific state transition or snapshot classification, the affected case is treated as ambiguous rather than being decided by arbitrary file order.

## Preparation disclosure

Work completed on 2026-09-10 before primary sprint analysis:

- selected and refined the research question
- obtained the public dataset through a GitHub mirror
- verified source-file SHA-256 hashes
- inspected the released schema and event semantics
- checked actor/moderator provenance
- created the repository scaffold
- drafted and froze the pre-analysis methodology

No primary SwarmTrace time-series metrics, figures, snapshot graph, random-withdrawal experiment, degree-prioritization result, or headline empirical result was computed during that preparation.

## Snapshot boundary clarification

The primary snapshot is a true pre-event state immediately before `T`.

Although ordinary state evaluated at an event timestamp `t` uses the live-write interval `(t-W, t]`, the `T^-` snapshot excludes source events occurring at exactly `T`.

Accordingly, for the pre-event snapshot, qualifying write timestamps lie in:

`[T-W, T)`

A qualifying write occurring exactly at `T-W` remains live immediately before `T`; a source event occurring exactly at `T` is excluded.

This special boundary rule applies only to the `T^-` snapshot.

The `T^-` snapshot is the explicit exception described above: it represents the left-limit immediately before `T`, rather than ordinary state evaluated at `T`.
