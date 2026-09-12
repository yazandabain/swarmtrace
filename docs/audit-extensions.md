# Audit extensions after the first Experiment 2 results

Recorded 2026-09-12 after the first 500-permutation runs. These are supplemental,
result-informed diagnostics, not frozen primary analyses.

The primary snapshot has 18 resources, 27 labels and degrees only two or three.
The one-hour snapshot has three resources. The 24-hour graph has 376 resources,
including much higher-degree hubs. This motivates the following bounded checks:

1. Enumerate every withdrawal subset for the 1h and 6h graphs to obtain exact
   distributions of the frozen largest-label-component endpoint at every budget.
   Uniform permutations induce uniform k-subsets. Also enumerate allowed tie
   subsets at each k under static degree. Keep the 500-run outputs as primary.
2. Inspect each 24h resource's live writers at both 24h and 6h to quantify how
   recency changes high-degree hubs. This explains the sensitivity without making
   a claim that one horizon is the true operational lifetime.
3. Evaluate snapshots at T minus one second and T plus one second, using the
   export's stated one-second clock uncertainty as the scale. This checks local
   cutoff sensitivity, not all possible independent clock errors.
4. Audit any revision/deletion uncertainty intervals that overlap. If their
   possible order affects historical metrics, report both orderings explicitly.
5. Include the five ambiguous-handle revisions in a labeled sensitivity run by
   replacing only their excluded-label classification with distinct prefixed
   labels. This tests coverage of the frozen exclusion, not true actor identity.

No new snapshot will replace the frozen T. No alternative targeting policy,
optimality claim, causal effect or incident-wide significance test is introduced.

Exact-distribution quantiles use the inverse discrete CDF. The frozen Monte Carlo
outputs retain their specified linear sample quantiles. Exact probabilities, not
incident-wide p-values, are used to interpret the small graph.
