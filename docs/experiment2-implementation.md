# Experiment 2 implementation decisions

Recorded 2026-09-12, before computing the first SwarmTrace snapshot or withdrawal result.
This supplements, and does not change, the frozen plan in `docs/preanalysis.md`
(commit `bf16642717ca69aff04e201158c5e7352dceb75b`). The existing Experiment 1
figure and its hourly peak were inspected before this note.

- Keep the frozen snapshot, actor classification, horizons, candidates and endpoint.
- Use 500 uniform random permutations per horizon, NumPy PCG64 seed 20260912 + W.
  Save complete orders and integer largest-label-component trajectories.
- Primary static-degree order: descending initial distinct-label degree, then
  lexicographic page key and episode index. Report this deterministic tie rule.
- Assess ties using 500 within-degree-group shuffles, seed 20261912 + W.
  Report their envelope separately from uniform withdrawal. Do not select a
  favorable tie ordering or replace the primary deterministic result afterwards.
- Evaluate every integer action count from zero to all candidates. Report the
  requested 10%, 25%, 50% budgets using ceiling(fraction * candidate count), with
  actual counts and fractions. Use NumPy linear quantiles for simulation envelopes.
- Preserve the original label denominator, including isolated nodes. The all-removed
  endpoint is 1 / label count, not zero. An empty eligible graph has undefined R.
- Verify an efficient reverse-addition connectivity implementation against explicit
  NetworkX bipartite resource removal, including disconnected graphs and isolates.
- Independently reconstruct snapshots directly from revisions after the last prior
  deletion, rather than relying only on the event replay. Audit hourly endpoints too.
- Audit clock uncertainty and export recreation provenance. If additional clock or
  identity sensitivity analyses are needed, label them as audit extensions. They do
  not replace the primary frozen operational definitions.
- Simulation envelopes describe random-policy variation on the observed fixed graph,
  not confidence intervals for the incident or evidence of causal containment.

Implementation correction already identified: expiry must precede same-second writes,
as required by the frozen plan. Remove the existing refresh protection. Preserve a
before/after comparison of historical outputs. Record deletion matches and episode
identities separately from whether any writer remains active.
