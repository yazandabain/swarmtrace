# Final review: scope and controls

Recorded September 12, 2026, after commit 27dc1cc and before the additional
window-sensitivity results. About 43 hours remain before the stated AoE deadline.
The frozen plan and original results remain unchanged.

The skeptical review identified three issues worth addressing:

1. A complete miss can result from the small fraction of recent candidates. A first
   calculation from existing tables gives a 40.4888% uniform probability of selecting
   no recent resource at frozen T (18 actions, 18 recent resources, 376 candidates).
   Across the 151 eligible hours the sum of these probabilities is 29.0234, compared
   with 20 observed older-degree misses. This is an expectation, not a significance
   test; linearity of expectation does not require independent hours. Report this
   qualification in the main paper and provide exact baselines at all saved budgets.
2. The crossed comparison only evaluates the chosen six-hour definition. Extend the
   descriptive coverage check to evaluation horizons 1, 3, 6 and 12 hours, always
   using the same 24-hour candidate pool and ranking at each instant. Evaluate all
   168 hourly snapshots plus frozen T. Retain empty graphs separately. Use the same
   ceil(10%, 25%, 50%, 100% of recent resources) budgets. Do not choose a preferred
   window from these results. Report exact tie bounds, older-degree Q for each
   evaluation graph, exact uniform expected coverage and complete-miss probability.
   No extra targeting algorithms or simulation sweeps are needed for these controls.
3. Recency-sensitive targeting and aggregation-dependent robustness are established
   topics. Add directly relevant literature and distinguish the case-specific
   contribution: deletion-aware resource reconstruction and a fixed-candidate,
   fixed-evaluation audit of the DSEWiki overlap proxy. Do not claim a new temporal
   centrality, a demonstrated intervention benefit, or a validated information lifetime.

For M older candidates, m recent resources and k actions, uniform selection has
expected recent coverage k/M and complete-miss probability C(M-m,k)/C(M,k), with
probability zero when k>M-m. Check this against exhaustive small synthetic sets and
the existing saved simulations. Audit every new graph against the direct-filter
oracle and selected withdrawal trajectories against forward NetworkX removal.

After these bounded controls, focus on final writing, source attribution, template
rendering, author-specific details and reproducibility. Additional methods, behavioral
inference or an unrelated pivot would not address the current evidential limits.
