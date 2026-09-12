# Personal review before submission

The complete draft is `swarmtrace_draft.pdf`, with an editable Word version and
`manuscript.md` as their shared source. It has four main pages. Numerical claims have
computational checks, but this is still an AI-assisted draft, not your personal sign-off.

## Decisions and details you must verify

1. Confirm the name drawn from git metadata, Yazan Al-Dabain, and replace the affiliation
   placeholder. Do not infer an institutional affiliation from your MSc background.
2. Read and revise the paper in your own words, particularly the interpretation and
   limitations. The template explicitly encourages a final version primarily written
   by the team. Confirm the LLM Usage Statement describes both this audit and earlier
   assistance accurately. It must not imply independent human verification before you
   have performed it.
3. Check the original rationale for the frozen six-hour horizon and timestamp. The
   timestamp coincides with revision `dse~DataUSAConstructionWageSep18Live@16`, the
   cleanup warning cited by the original investigators. That factual correspondence
   is verified. The repo does not record why you chose this time or why six hours
   should be operationally appropriate. The draft does not invent those motivations.
4. Confirm the preparation disclosure and sprint eligibility. The frozen plan records
   schema inspection, dataset acquisition and methodological preparation on September
   10. Git records the first commit at September 10, 22:33 UTC. The implementation
   commits begin September 11. Keep that distinction visible.
5. Decide how to make the artifact available. There is no configured git remote. A
   reproducibility ZIP is prepared, but nothing has been published or uploaded. Working checkpoints are committed locally. Add the final artifact/repository URL in Code and Data, or provide it
   through an allowed attachment route. The local file path is not a public URL.
6. Check the event submission form and rubric. The official event page was retrieved;
   the rubric link embedded in the DOCX was not accessible through browsing. No claim
   is made that unseen form fields were checked. The event requires a PDF and a
   Limitations and Dual-Use Considerations appendix, both prepared here. The relevant
   track appears to be “What happened, and what breaks next”; confirm your selection.
7. After revision, rebuild the documents, rerun `verify_claims.py`, and review the PDF
   pagination. Remove the draft footer and replace pending-review language only after
   completing your review. Do not change the original frozen preanalysis document.

Deadline checked against the official event page: September 13 at 23:59 AoE,
equivalent to September 14 at 13:59 in Budapest. Aim to submit earlier.

## What you should be able to explain without the code

**What counts as live?** The latest qualifying write by a label to a still-existing
page episode falls within W. At an ordinary instant the interval is (t-W,t]. At the
frozen left-limit snapshot it is [T-W,T). No future event enters the snapshot.
Repeated writes refresh one incidence, not the number of writers.

**Why episodes?** Deletion clears the old writers. A later write can begin a new
episode under the same page name without importing the old episode's incidences.
An inactive page still exists in the reconstructed lifecycle. Missing initial
history means some deletion events cannot be matched to a represented episode.

**What does the graph mean?** Labels and resource episodes are separate node types.
An edge means recent writing, nothing stronger. Paths can join unrelated tasks via
a reused handle or hub. You have not measured reads or demonstrated information flow.

**What is the endpoint?** R is the fraction of the original labels in the largest
label component. It is not the fraction of all remaining nodes. Q normalizes to the
starting largest component. Original labels remain even when isolated. Removing all
resources gives R=1/|L| and Q=1/(initial largest label-component size), not zero.

**What is the primary finding?** The 6h graph has 18 resources and 27 labels; its
largest component starts with eight labels. At 2, 5 and 9 withdrawals, static degree
leaves eight, six and four labels, versus uniform medians of seven, six and five.
The slight gain at nine removals is unremarkable relative to the exact random
subsets: 35.1% perform at least as well. There is no consistent primary advantage.

**Why does the final emphasis differ from the first draft?** The later hourly survey
shows that the weak frozen result is unusual: at a 25% budget, degree targeting beats
median random withdrawal in 138 of 151 six-hour graphs. This survey was specified
after seeing the frozen result and is explicitly exploratory. Do not present it as
part of the original frozen plan or treat adjacent hours as independent experiments.

**What is the new comparison?** All policies select from the same 24-hour candidates
and receive the same number of actions, while the graph being evaluated is fixed at
six hours. A resource outside that recent graph consumes an action without changing
its endpoint. This does not make the action useless in reality. At frozen T, the top
18 older-degree resources include none of the 18 recent resources. Older-graph
connectivity falls from 782 to 545 labels, while recent connectivity remains eight.
The mismatch recurs at 20 hourly snapshots and is not a degree-tie artifact.

**Is recent-degree success tautological?** At the full recent-resource budget, yes:
that ordering necessarily selects every recent resource. It is a reference that
makes the budget opportunity explicit, not a newly discovered superior algorithm.
The empirical finding is the coverage of the older ranking and its variation across
time. Older-degree targeting still beats median uniform withdrawal on recent Q in
113 of 151 hours at that budget. We are not claiming that older rankings always fail.

**Why is 24h different?** It contains large older hubs that are absent at 6h. At 94
withdrawals, degree leaves 298 labels in the largest component, versus a median 700
under uniform withdrawal, from an initial 782. Q is 298/782=0.381 versus 700/782=0.895.
Neither ratio is a percentage of “agents contained”. The observation does not make
24h the correct horizon and must not replace the primary 6h conclusion.

**Do the 54 deletion exits mean deletion failed?** No. Of 442 recorded actions in the
reporting week, 54 hit a resource that was currently multi-writer under W=6h. Deletion
can have effects outside that narrow metric, including on single-writer resources,
older information or unobserved content. Expiry exits mean aging out of the measure,
not proof that information stopped being available.

**Why 500 simulations and exact enumeration?** The original plan fixed 500 uniform
permutations. A separate 500-run tie sensitivity covers nonunique degree rankings.
After seeing the small candidate set, the audit enumerated all subsets for 1h and 6h.
At a fixed k, uniformly permuted removal orders induce uniform k-subsets. The exact
calculation removes Monte Carlo uncertainty, not uncertainty about missing data.

## Suggested manual evidence check

Open `outputs/snapshot_incidences_w6.csv` and inspect a few referenced revisions in
the archived JSONL. Check their labels, latest-write times, page keys, and prior
deletions. Then open `outputs/simulations_w6.npz` and the saved snapshot to reproduce
one removal trajectory using `swarmtrace.stress.reference_counts`. Read the eight
labels in the starting largest component to understand why a page can have high
degree without controlling that component. This is a useful review exercise, not a
claim that it has already been done by you.
