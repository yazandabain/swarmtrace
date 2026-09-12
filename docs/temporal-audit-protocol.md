# Temporal and ranking-horizon audit protocol

Recorded 2026-09-12, after the original snapshot results and before running this
extension. This is explicitly exploratory. The unchanged frozen results remain
primary, including the negative or weak 6h degree comparison.

## A. Is the frozen snapshot representative?

Evaluate every existing hourly endpoint in the frozen reporting interval (June 16
01:00 through June 23 00:00 UTC), using the same true left-limit state. Include all
nonempty graphs; report empty-hour counts. Use W=6h and W=24h. At each snapshot,
use the existing static degree rule, 500 uniform permutations and 500 degree-tie
orders. Record the same 10%, 25% and 50% resource budgets and Q, R and G endpoints.

Summarize the distributions and signs across hours descriptively. Adjacent hours
are dependent and one incident is not a population sample; do not treat snapshots
as independent trials or report incident-wide p-values. Report the frozen T and
its relation to the hourly survey without replacing it with a favorable time.
Use seed 20260912 + W + 1000 * hour_index for uniform orders and
20261912 + W + 1000 * hour_index for tie orders (hour_index 1..168).

## B. Does older-hub targeting reach the current multi-writer surface?

At the frozen T and every hourly endpoint with nonempty 6h topology:

- Candidate actions: all 24h-eligible resource episodes, a superset of 6h-eligible
  episodes at the same instant. Assert the subset relation.
- Fixed evaluation: the 6h bipartite graph and its original labels. Removing a
  candidate outside this graph consumes one action but leaves this endpoint unchanged.
- Compare static ranking by 24h degree, static ranking by 6h eligible-resource degree,
  and uniform resource withdrawal from the same 24h candidate pool. The recent
  ranking puts its 6h-eligible resources first, with lexicographic degree ties.
- Budgets: ceil(10%, 25%, 50%, 100% of the 6h eligible resource count), capped only
  by the common candidate set. Report actual actions and resource counts. The 100%
  budget means enough actions to withdraw every recently shared resource if chosen.
- For each ranking, report R6 and Q6, the fraction of the 6h resource set selected,
  and the fraction of selected actions outside the 6h evaluation graph. Do not call
  these actions useless: older information and single-writer resources can matter.
- Save 500 uniform and 500 older-degree-tie trajectories per snapshot, with seeds
  as in A; add 500 recent-degree-tie trajectories. At frozen T use the original
  horizon seeds. Export graph/label mappings and all orders for traceability.
- Display time-resolved coverage at the 100% recent-resource budget. Report the
  full distribution across eligible hours, not only an illustrative favorable hour.
- The 6h endpoint deliberately operationalizes recency. Better performance under
  that endpoint cannot establish a true information lifetime or operational benefit.

Implementation: reuse verified weighted bipartite connectivity. Add dormant
candidate resource nodes with zero edges to the fixed 6h evaluation graph; never
remove labels or import additional historical labels. Check selected trajectories
against explicit NetworkX removal and hourly snapshots against the independent
filter oracle. Retain all original snapshot outputs unchanged.

## Additional tie diagnostic after the first hourly results

The chosen older-degree order selects zero recent resources at 20 hourly snapshots
at the full recent-resource budget. To check whether this finding is a tie artifact,
compute exact minimum and maximum recent-resource coverage over valid degree-tie
choices, from the degree group at the cutoff. This is an analytic coverage bound,
not an optimization of the connectivity endpoint. Keep the original 500 tie runs.
