# SwarmTrace audit

Audit started September 12, 2026, from commit 207a1c3. The raw export, every source
module, existing tests, git history, validation output, prior figure and untracked
submission template were inspected. Initial tests: 28 passed. The raw files matched
all five frozen SHA-256 hashes. The original preanalysis file remains unchanged.

## Defects and repairs

- Same-second refresh protection conflicted with the frozen expiry-before-write rule.
  Removed it and corrected the test that had encoded the conflicting behavior.
  A comparison against archived pre-edit hourly outputs shows no changed endpoints
  or transition totals at W=1h, 6h or 24h. This was a semantic defect without an
  observed-data headline effect.
- Page existence had been represented only by live writers. Added episode identities
  and a deletion ledger independent of activity expiry. Inactive pages remain
  represented; deletion clears an episode and recreation starts a new one.
- The reusable validator did not enforce the actor/provenance counts checked by the
  loader CLI. Consolidated those checks so the analysis runner also enforces them.
- Snapshot construction was absent. Implemented the true left-limit boundary and
  excluded future records from snapshot validation. Same-page source collisions
  before a requested state are rejected rather than ordered arbitrarily.
- Experiment 2 was empty. Implemented bipartite resource withdrawal with original
  label nodes retained, explicit seeded policies, all budgets, tie sensitivity and
  complete simulation traces. Component size counts labels, not total vertices.
- Added independent direct-filter snapshots, forward NetworkX removal, conservation
  checks, raw-hash gates, source/output manifests and compact paper figures.

## Evidence audit

The 13,403 stored DSE revisions comprise 13,372 qualifying writes, 26 moderator-proxy
writes and five ambiguous-handle writes. None has a missing label. All 5,217 successful
deletes match the frozen moderator provenance. Save events are not counted again.
There are no same-page revision/delete timestamp collisions in the chosen clocks.

The export's one-second uncertainty intervals touch for one revision/delete pair,
on June 20. Explicitly evaluating both possible equal-time orders changes neither
the affected page's activation/exit totals nor the earlier frozen snapshot. This is
not a claim of complete robustness to missing or inaccurate timestamps.

All 64 exported recreation links refer to 63 stored revisions and point to an earlier
delete on the same page. The export's heuristic and fallback linkage provenance is
retained. Lifecycle replay uses observed revisions and successful deletions, not a
count of heuristic links.

Of all available deletion records, 3,960 match represented episodes and 1,257 do not.
All 1,248 `page_held=false` records are unmatched; nine `page_held=true` records also
lack a currently represented episode. This is consistent with the frozen rule:
`page_held` is validation/context, not an instruction to invent an episode. Incomplete
writes can explain a deletion of a page the reconstruction cannot currently represent.

## Original experiments

At 6h, the reporting week has 1,101 activations, 54 deletion exits and 1,047 expiry
exits. Its hourly peak is 331. Only 54 of 442 actions hit a currently multi-writer
resource under the operational definition. That fraction does not measure moderation
success or failure.

The frozen 6h graph contains 18 resources and 27 labels in seven components. Static
degree targeting shows no consistent advantage at the planned budgets. Exact
post-result enumeration removes Monte Carlo uncertainty from this small-graph
comparison: at nine removals, 35.1% of uniform subsets do at least as well as the
chosen degree ordering.

The 24h sensitivity graph is much larger. Its three largest hubs have no live 6h
writers, and 354 of 376 resources have none. The strong 24h targeting result therefore
must not be described as evidence that prioritizing resources would contain current
agents. Local cutoff and ambiguous-label sensitivities preserve this interpretation.

The original simulation arrays reproduced exactly in an isolated output directory.
The only initial table difference was the documented correction from linear sample
quantiles to inverse-CDF quantiles for the exact discrete distribution; the original
500-permutation quantile convention remains unchanged.

## Further research and provenance

The author then requested a bounded reassessment before finalizing the paper. See
`research-direction-review.md` and `temporal-audit-protocol.md`. The new work tests
snapshot representativeness and evaluates historical and recent rankings on the same
candidate pool and recent graph. It is explicitly exploratory and cannot replace the
frozen primary result. Its outputs and validation are kept separate.

Working checkpoints are committed only after the author authorized them. No existing
history has been rewritten, and the template, raw data and caches are excluded.

## Temporal extension results

At the 25% resource budget, degree targeting beats median uniform withdrawal in
138 of 151 nonempty 6h hourly graphs and 160 of 161 nonempty 24h graphs. The fixed
snapshot is therefore not typical. In the common 24h candidate pool with 6h evaluation,
older-degree ranking selects zero recent resources at frozen T with 18 actions,
and at 20 of 151 hourly snapshots with enough actions to select every recent resource.
Exact cutoff-tie bounds show all 20 misses persist under every valid degree tie order.
The older ranking still beats median uniform Q6 in 113 hours at this budget, which is
reported to avoid portraying it as generally ineffective. The final paper emphasizes
alignment of ranking and evaluation activity, not a universal failure of degree targeting.

The extension passed 336 full-incidence oracle comparisons and 27 forward NetworkX
trajectory checks. All original frozen seeded simulation arrays remain unchanged.
