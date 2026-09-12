# SwarmTrace: activity windows and resource targeting in DSEWiki

Author: Yazan Al-Dabain
Affiliation: [Affiliation to confirm]
With: Apart Research
Status: Draft for author review

## Abstract

Which shared resources should an incident responder prioritize when agents' writing activity changes over time? I reconstruct DSEWiki's observed multi-writer surface from stored revisions and successful deletion events, then test static degree targeting against uniform resource withdrawal. The locally frozen six-hour snapshot contains 18 resources and 27 labels and shows no consistent targeting advantage. An exploratory survey changes the interpretation: at a 25% budget, degree targeting beats median random withdrawal in 138 of 151 nonempty six-hour snapshots. I then hold the candidate pool and six-hour evaluation graph fixed while changing the ranking horizon. At the frozen time, the top 18 resources ranked by 24-hour degree include none of the 18 six-hour resources. Their removal reduces the older graph's largest-label component from 782 to 545 while leaving the recent graph unchanged. This complete miss occurs at 20 of 151 hourly snapshots and survives every valid degree-tie ordering. The result exposes a mismatch between historical connectivity and recent write overlap. It supports auditing ranking recency, not claims about communication loss, information lifetime or containment.

## 1. Introduction

The DSEWiki investigation documents agents sharing answers on public infrastructure and reacting to moderator cleanup [1]. This creates two measurement problems. A deletion may target a page with no recent writers; a page with many historical writers may be absent from the current multi-writer surface. Counting deletions or measuring fragmentation of an accumulated graph does not distinguish these cases.

SwarmTrace reconstructs resource lifecycles and recent co-writing, preserves a frozen historical withdrawal test, and adds an explicitly exploratory audit across time. Its main contribution is a controlled comparison of ranking horizons on the same candidate pool and recent evaluation graph. This tests whether a structural targeting result reaches the activity it is being used to describe. It does not infer communication or introduce a new attack algorithm.

## 2. Related Work

The original investigation [1] and ProWiki export [2] supply the incident evidence and provenance. Targeted versus random removal is an established network-robustness comparison [3]; here removals affect resource nodes and component size counts original labels. Temporal-network research explains why aggregation can alter connectivity and why static paths need not represent time-respecting information flow [4]. SwarmTrace applies these concerns to an incident-response measurement task, with explicit deletion and expiry accounting.

<!-- pagebreak -->

## 3. Methods

**Data and identity.** I use the pinned explorer-schema-2 export [2], verified against five SHA-256 hashes. DSEWiki supplies 13,403 revisions and 5,217 successful deletion events across the available history. The frozen actor rule excludes 26 revisions matching [Admin1] and IP /16 2.202, plus five ambiguous-handle revisions. No DSE revision lacks a label; 13,372 enter the qualifying-write stream. Labels are observable identifiers, not authenticated agents. Save-event pointers are not additional writes.

**Historical reconstruction.** The replay initializes from available prehistory and reports [June 16 00:00, June 23 00:00) UTC. A successful deletion clears a represented page episode; a subsequent write starts a new episode without inherited writers. Unmatched deletions remain in a separate ledger. An incidence is live when its latest qualifying write lies in (t-W,t], with expiry before same-second source events. At least two live labels make a resource multi-writer. I count entries, deletion exits and expiry exits. W=6h is primary; 1h and 24h were frozen sensitivities.

**Frozen withdrawal test.** The snapshot is immediately before June 19, 2026, 14:05:02 UTC. It excludes events at T and includes writes in [T-W,T). T coincides with the published cleanup-warning revision [1], which is excluded. The unweighted bipartite graph joins qualifying labels to eligible resource episodes. I rank resources once by distinct-label degree, breaking ties lexicographically by page key and episode. At each action count, I compare this ordering with 500 seeded uniform permutations and separately assess 500 degree-tie orderings.

For original snapshot labels L, R(k)=max_C |C intersect L|/|L|. Labels remain nodes after withdrawal, including isolates. I report Q(k)=R(k)/R(0) and G(k)=median(R_random(k))-R_degree(k). Positive G favors degree targeting. Budgets round upward to whole resources. Pointwise 5th-95th percentile envelopes describe policy variation on a fixed graph, not uncertainty about the incident.

**Exploratory temporal audit.** After inspecting the frozen results, I specified a survey of all 168 hourly left-limit snapshots, using 6h and 24h graphs and the same 500-permutation comparisons. Empty graphs are reported separately. At each nonempty six-hour snapshot, I also fix the action pool to all 24h-eligible episodes and evaluate only the six-hour graph with its original labels. These candidates contain every six-hour resource. I compare 24h degree, 6h eligible-resource degree and uniform withdrawal at identical action counts. Actions outside the six-hour graph consume budget but do not alter its endpoint.

The main coverage diagnostic uses k equal to the number of six-hour resources: enough actions to remove that surface if selected. Recent-degree coverage is then one by construction; it is a reference, not an algorithmic discovery. I compute exact coverage bounds over valid older-degree ties and retain the sampled tie trajectories. Adjacent hourly observations are dependent. These analyses are descriptive extensions, not replacements for the frozen test. Protocols, validation and full traces are documented in Appendix A.

<!-- pagebreak -->

## 4. Results

**Reconstruction and frozen test.** At 6h, 1,101 activations balance 54 deletion exits and 1,047 expiry exits over the reporting week. Of 442 deletion actions, 345 match represented episodes: 54 have at least two live writers, 61 have one and 230 have none; 97 are unmatched. The hourly peak is 331 resources. The frozen graph has 18 resources, 27 labels and 40 incidences, split into components of 8, 6, 4, 3, 2, 2 and 2 labels. At 2, 5 and 9 removals, G is -0.037, 0 and +0.037. Exact enumeration shows that 35.1% of all nine-resource subsets do at least as well as the fixed degree order. The weak primary result is retained (Appendix B).

**Across time.** At the 25% budget, six-hour degree targeting beats median uniform withdrawal in 138 of 151 nonempty hourly graphs; nine tie and four favor uniform withdrawal. Using the median degree-tie result gives 139 positive hours. At 24h, the corresponding fixed-order count is 160 of 161. The frozen six-hour result is therefore not typical of the reporting week (Figure 1, upper panel).

![Figure 1](../outputs/figures/paper_figure1_temporal.png)

Figure 1. Exploratory hourly audit. Upper: median random Q minus fixed degree Q at ceil(25% of each graph's resources); positive values favor degree targeting. Lower: coverage of six-hour resources after k withdrawals from the common 24h candidate pool, where k equals the six-hour resource count. Recent-degree coverage is one by construction. Gaps are empty graphs. The dotted vertical line marks frozen T. These are dependent snapshots of one incident.

**Ranking horizon versus evaluation horizon.** At T, 24h degree's first 18 actions select zero six-hour resources, regardless of degree ties. They reduce the 24h largest-label component from 782 to 545, but leave the six-hour component at eight. Recent-degree withdrawal leaves isolated labels at the same budget. Across the 151 hourly comparisons, older-degree coverage has median 33.3%; it is zero at 20 snapshots under every valid tie ordering. Older-degree Q6 still beats median uniform Q6 in 113 hours. Thus older ranking often helps, but its historical fragmentation result does not establish coverage of the recent surface.

<!-- pagebreak -->

## 5. Discussion and Limitations

The frozen experiment alone would support an incomplete account. It finds little advantage at six hours and a large advantage at 24 hours, but both the eligible graph and its label population change. The hourly survey shows that degree prioritization usually performs better than median uniform withdrawal on the graph that supplies its ranking. The common-pool comparison asks a different question: whether older-degree targeting reaches the recently shared resources, at the same action budget and with the evaluation graph held fixed.

The mismatch at T is concrete. WillkommenImWiki, StartSeite and TestSeite have 24h degrees of 323, 156 and 106; their latest qualifying writes are approximately 13.5, 11.0 and 11.0 hours old. They are absent from the six-hour graph. In total, 354 of 376 older candidates have no qualifying writer within six hours. This explains how substantial fragmentation of older overlap can coexist with no change in the recent graph. It does not establish that these older pages were useless or unreadable.

For incident analysis, the practical output is a check: state which activity a ranking describes, then evaluate its selected actions against that same activity definition. SwarmTrace exposes disagreement between those choices and preserves the underlying revisions and deletion matches for review. The reference recent-degree policy optimizes a recency-defined proxy. Its complete coverage at the full recent-resource budget is guaranteed by construction and cannot validate six hours as the correct information lifetime.

### Limitations

The export omits some activity, including unrecovered short writes. Labels can be reused, changed or impersonated. Co-writing does not demonstrate reading, communication or independent agents, and a static path is not necessarily a time-respecting information path. Deletion ends a modeled resource episode, not knowledge copied elsewhere.

Withdrawal uses equal action costs and assumes no adaptation. R tracks only the largest label component and can hide changes elsewhere. The frozen timestamp is not a representative sample; the later hourly survey is explicitly exploratory and its observations are dependent. Local clock, tie and ambiguous-label checks preserve the main interpretation, but do not resolve missing-data or identity uncertainty. Appendix C details these assumptions and dual-use limits.

### Future Work

The useful next step is to test which observed overlaps correspond to addressing, reads or other evidence of information use. That would help evaluate recency windows against behavior rather than choosing one from the graph result.

## 6. Conclusion

Degree targeting often fragments observed co-writing more than uniform withdrawal. Its apparent success can nevertheless describe older overlap while missing the recent surface. SwarmTrace measures that mismatch without treating graph fragmentation as containment.

## Code and Data

The SwarmTrace reproducibility bundle contains code and derived evidence; a public code URL is pending author publication. Source data are the pinned ProWiki export [2]. Appendix A gives reproduction commands. Raw revision bodies and the supplied template are not included in the bundle.

<!-- pagebreak -->

## References

[1] Sydney Von Arx, Cormac Slade Byrd, Spencer Kitts, and Thomas Larsen. 2026. Discovery of a new OpenAI agent message board. Nightingale Collective and collaborators, September 4. https://collusion.wiki/

[2] WikiAgentSwarmInvestigation contributors. 2026. ProWiki explorer-schema-2 export and schema documentation. GitHub repository JoshuaDavid/WikiAgentSwarmInvestigation, commit 9bc20957b9d3b40cce3f7ee7827e9001a6256a7f. https://github.com/JoshuaDavid/WikiAgentSwarmInvestigation/tree/9bc20957b9d3b40cce3f7ee7827e9001a6256a7f/agent-logs/prowiki

[3] Reka Albert, Hawoong Jeong, and Albert-Laszlo Barabasi. 2000. Error and attack tolerance of complex networks. Nature 406, 378-382. https://doi.org/10.1038/35019019

[4] Petter Holme and Jari Saramaki. 2012. Temporal networks. Physics Reports 519, 97-125. https://doi.org/10.1016/j.physrep.2012.03.001

<!-- pagebreak -->

## Appendix A. Reproduction and audit trail

The original plan is docs/preanalysis.md, frozen in commit bf16642717ca69aff04e201158c5e7352dceb75b before analysis implementation. Its SHA-256 is feb30cc6aa14a6915ccceb6507b2ace6a1fc529e65e1d8bbbbbbef29e1be931a. It remains unchanged. The preparation disclosure covers dataset acquisition, schema/provenance inspection, repository setup and methodological planning before the sprint. It does not claim that this preparation occurred during the sprint.

Implementation details not fixed originally were recorded before the first snapshot results in docs/experiment2-implementation.md. The random seed is 20260912+W; the degree-tie seed is 20261912+W, with NumPy PCG64. Simulation quantiles use NumPy's linear method. Exact subset quantiles use the inverse discrete CDF. Post-result diagnostics and their motivations are recorded separately in docs/audit-extensions.md.

With Python 3.12 and uv, install using `uv sync --locked --group report`. Run `uv run python -m swarmtrace.run --data-dir /path/to/swarmtrace-data --with-temporal-audit`. The raw directory needs pages.jsonl, revisions.jsonl, events.jsonl, labels.jsonl and manifest.json from [2]; the runner verifies their frozen hashes. Run `uv run pytest -q` for tests. `uv run --group report python report/build_submission.py` rebuilds the PDF and editable DOCX using the supplied local template and report/manuscript.md.

The analysis saves hourly tables, every deletion match and transition, snapshot label-resource incidences with source revision IDs, degree rankings, all 500 random and 500 tie orderings per horizon, integer component trajectories and checkpoint tables. The run manifest identifies source hashes, dependency versions, the current commit and working-tree status. The temporal protocol was specified after the original results in docs/temporal-audit-protocol.md. Full hourly graph mappings and traces remain in outputs/temporal; the compact bundle provides the summary tables and code to regenerate that archive. report/claims.json maps manuscript numbers to output cells; report/author-review.md gives the remaining personal checks.

An independent direct-filter reconstruction agrees with all 504 hourly endpoints and all three full snapshot incidence sets. A forward NetworkX bipartite-removal implementation agrees with 33 sampled full trajectories across the three horizons. Synthetic tests cover exact expiry, refreshes, recreation, pre-event boundaries, same-page source collisions, label-based component size, isolates and exact subset enumeration. The temporal extension adds 336 exact incidence-set checks and 27 forward-removal trajectory checks. These are computational checks within the same project, not an external replication.

The audit found that the prior implementation protected an incidence refreshed at its exact expiry time, contrary to the frozen expiry-first rule. Removing that protection changed no hourly endpoints or transition totals in the observed data at any horizon. Page existence is now tracked independently of recent writers, so an expired page is not mistaken for a deleted one.

<!-- pagebreak -->

## Appendix B. Frozen results and supplemental checks

![Figure 2](../outputs/figures/paper_figure2_history.png)

Figure 2. Six-hour reconstruction during June 16-22. The upper panel shows active multi-writer resources immediately before hourly endpoints; the lower panel counts events in the preceding hour. The 331-resource hourly peak is June 18 at 22:00 UTC. The dotted line marks frozen T. Deletion actions and deletion exits have different denominators.

![Figure 3](../outputs/figures/paper_figure3_withdrawal.png)

Figure 3. Frozen withdrawal curves. Lower Q means a smaller largest-label component relative to baseline. Blue shows median uniform withdrawal and its pointwise 5th-95th percentile envelope over 500 permutations. Red shows the fixed degree order and the envelope over 500 degree-tie orders. Each horizon defines a different graph. Original labels remain when isolated.

At 24h, the frozen graph has 376 resources, 826 labels and 2,471 incidences. At 94 removals (25%), degree targeting leaves 298 labels in the largest component, versus a median 700 under uniform withdrawal, from a baseline of 782. Q is 0.381 versus 0.895, or 38.1% versus 89.5% of baseline. No sampled uniform order does as well at this budget. This is a fixed-graph sensitivity result, not evidence of containment.

<!-- pagebreak -->

### Historical counts and exact small-graph distributions

| W | Hourly peak | Activations | Deletion exits | Expiry exits | End surface |
| --- | --- | --- | --- | --- | --- |
| 1h | 112 | 1186 | 35 | 1151 | 0 |
| 6h | 331 | 1101 | 54 | 1047 | 0 |
| 24h | 379 | 1066 | 87 | 904 | 75 |

Table 1. Historical counts during the frozen reporting interval. All horizons start at zero and observe the same 442 deletion actions. Activations minus deletion and expiry exits equal the ending surface. These are state transitions and can count a resource more than once. Hourly peaks are sampled maxima, not claims about the continuous-time maximum.

![Figure 4](../outputs/figures/paper_figure4_exact.png)

Figure 4. Exact primary-snapshot distributions after 2, 5 and 9 withdrawals. Uniform subsets are equiprobable at each k. Red includes every subset allowed by descending degree with arbitrary ties. These distributions enumerate all 262,144 resource subsets across budgets, without Monte Carlo error. They describe the fixed observed graph only.

At five removals, 61.9% of all 8,568 uniform subsets do at least as well as the primary degree ordering. At nine, the proportion is 35.1% of 48,620 subsets. The median uniform largest-label-component sizes are seven, six and five at 2, 5 and 9 removals, versus eight, six and four for the fixed degree order. Exact degree-tie ranges are 6-8, 5-6 and 3-6 labels. The 1h graph admits only eight total subsets and six permutations; its coarse action fractions should not be treated as directly equivalent to a 10% budget on the larger graphs.

Moving the snapshot cutoff by one second in either direction leaves graph counts and checkpoint results unchanged at all horizons. Including the five ambiguous-handle revisions leaves the 1h and 6h graphs unchanged and adds one label at 24h. Its 25% degree Q becomes 0.381 after rounding, while median random Q remains 0.895. This is an exclusion sensitivity, not an identity validation.

One revision/deletion pair has touching one-second uncertainty intervals, on June 20, after the snapshot. Evaluating both possible equal-time orderings preserves the affected page's activation and exit totals at all horizons. The 64 exported recreation links attach 63 stored revisions; all point to an earlier deletion on the same page. Their export provenance is retained, including fallback linkage. They are not counted as additional writes, and they do not substitute for lifecycle replay.

<!-- pagebreak -->

## Appendix C. Limitations and Dual-Use Considerations

**Observation and retention.** The available export is filtered by revision.write_date >= May 1, 2026. The first stored DSE revision in it is May 24. Historical state therefore reflects available records, not guaranteed complete prehistory. Missing short writes or missing pages can add unseen resources and incidences; missing deletion evidence can instead preserve an episode too long. Neither error direction is estimated here. In the full available history, 1,257 of 5,217 deletions are unmatched to a represented episode. A missing match does not imply that the original page never existed.

**Identity and semantics.** A label is a proxy. Splitting or merging underlying identities could change degree and component structure. The frozen moderator proxy relies on matching both label and network /16; it is not authentication. The five ambiguous revisions are too narrow a sensitivity to settle this issue. Resource overlap is a dependency proxy only in the structural sense used by the stress test. It is not evidence that a given agent needed that page, read another writer's content or relied on a path through the graph.

**Timing and action model.** W determines whether old writes remain represented. It does not measure how long information stays useful, whether a page remains readable or whether an agent is still active. The graph has no read chronology or transmission delays. Withdrawal deletes whole resource nodes at equal unit cost. It does not model alternative copies, caches, operator workload, page value, access controls, agent migration or later recreation. Re-ranking and behavioral adaptation are outside the experiment.

**External validity and uncertainty.** One retrospectively selected, locally frozen snapshot cannot establish a general containment rule. The 24h result is a sensitivity finding and must not be substituted for the primary 6h result. Policy envelopes condition on the recorded graph and its operational definitions. Exact enumeration removes sampling error from the small-graph comparison, not uncertainty about the incident. Source hashes establish which data were analyzed; they do not establish completeness or authenticity of all source content.

**Dual use and handling.** The artifact is an offline reconstruction and graph-withdrawal analysis. It contains no exploit, live intervention or adaptation policy. Resource rankings could still be repurposed to disrupt shared infrastructure, and public labels should not be treated as authenticated people or agents. The reproducibility bundle excludes raw page bodies and full IP addresses, retains already-public identifiers needed to audit the analysis, and does not contact the affected wiki. Readers should obtain source data through the published archive. The results do not justify automatic deletion or attribution decisions.

## LLM Usage Statement

Codex provided substantial assistance with repository inspection, methodological auditing, code and tests, execution of the analyses, interpretation checks, figures and this report draft. Earlier preparation and implementation also involved AI assistance, as described in the project history and author review notes. Numerical claims have been checked against saved outputs and independent computational implementations within this workflow. This is not a claim of independent human verification. The author must personally review the analysis, revise the prose and confirm this disclosure before submitting the final version.
