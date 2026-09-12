# SwarmTrace

**Auditing Temporal Mismatch in Resource Targeting During the DSEWiki Incident**

SwarmTrace reconstructs recent multi-writer activity in the DSEWiki incident and studies how the time window used to rank shared resources changes what an intervention actually reaches.

The project replays archived revisions and deletion events, reconstructs resource lifecycles, builds temporal label-resource graphs, and compares degree-based resource targeting with uniform withdrawal.

Developed for the **Apart Research AI Incident Response Sprint, September 2026**.

## Main finding

Degree targeting often fragments the graph used to construct the ranking, but historical fragmentation and recent-resource coverage are not the same thing.

At the frozen evaluation time:

- the six-hour graph contains **18 active multi-writer resources**
- the first **18 resources ranked by 24-hour degree contain none of those 18 recent resources**
- withdrawing those historical hubs reduces the older graph's largest-label component from **782 to 545**
- the recent six-hour graph is left unchanged

That complete miss should not be overinterpreted. Only 18 of 376 candidates are recent at that time, so uniform withdrawal also has a **40.5% probability** of missing the six-hour surface completely.

Across the hourly audit, older-degree targeting produces **20 complete misses across 151 nonempty six-hour snapshots**, compared with **29.0 expected under uniform withdrawal**.

The result is therefore not that historical degree targeting is generally worse than random. It is that:

> **A ranking can strongly fragment historical overlap while reaching a different resource surface from the one currently active.**

These are structural measurements. They do not establish communication loss, information deletion, agent identity, or containment.

![Exploratory temporal targeting audit](outputs/figures/paper_figure1_temporal.png)

## Paper

- [Final paper](report/swarmtrace_paper.pdf)
- [Manuscript source](report/manuscript.md)
- [Verified claim ledger](report/claims.json)
- [Frozen pre-analysis plan](docs/preanalysis.md)
- [Audit notes](docs/audit.md)

The paper contains four main pages followed by references and appendices.

## Method

SwarmTrace:

1. reconstructs page episodes from revisions and successful deletion events
2. tracks recent label-resource incidences under fixed activity windows
3. marks a resource multi-writer when at least two qualifying labels are recently active on it
4. reconstructs the live multi-writer surface over the reporting week
5. compares static degree targeting with seeded uniform resource withdrawal
6. preserves a frozen six-hour primary snapshot with one-hour and 24-hour sensitivities
7. runs explicitly post-result hourly and cross-window audits

Labels are observable identifiers, not authenticated agents.

Resource overlap is treated only as a structural proxy. It is not assumed to imply reading, communication, coordination, or dependency.

## Key results

### Historical reconstruction

For the primary six-hour window:

- **1,101** activations
- **54** deletion exits
- **1,047** expiry exits
- hourly peak of **331** active multi-writer resources
- **442** successful deletion actions

Only 54 deletion actions hit a resource that was multi-writer at that moment. This is an accounting result, not a measure of moderator effectiveness.

### Frozen withdrawal test

The frozen six-hour graph contains:

- **18 resources**
- **27 labels**
- **40 incidences**

The primary result is weak. At nine withdrawals, **35.1% of all possible nine-resource subsets perform at least as well as the fixed degree ordering** on the chosen connectivity endpoint.

That negative result is retained rather than replaced with a more favorable snapshot.

### Hourly audit

At a 25% resource budget, six-hour degree targeting beats median uniform withdrawal in:

- **138 of 151** nonempty hourly graphs
- ties in **9**
- loses in **4**

The frozen six-hour result is therefore unusual within the observed week.

### Cross-window audit

The analysis then fixes the candidate pool and recent evaluation graph while changing the history used for ranking.

At the frozen time, 24-hour degree targeting completely misses the six-hour surface.

Across the week, however, older-degree targeting still has better mean coverage than uniform expectation at every tested evaluation window.

This is why the paper separates:

- historical fragmentation
- recent-resource coverage
- deletion accounting

rather than treating any one of them as containment.

## Reproduce

Requirements:

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

Install dependencies:

```bash
uv sync --locked
```

Obtain the pinned ProWiki export described in [data/README.md](data/README.md).

The analysis expects:

```text
pages.jsonl
revisions.jsonl
events.jsonl
labels.jsonl
manifest.json
```

Run the full workflow:

```bash
uv run python -m swarmtrace.run \
  --data-dir /path/to/swarmtrace-data \
  --with-temporal-audit
```

Run the tests and checks:

```bash
uv run pytest -q
uv run ruff check .
uv run python report/verify_claims.py
```

Current verified state:

```text
40 tests passed
176 numerical/provenance claims verified
```

For an isolated reproduction:

```bash
uv run python -m swarmtrace.run \
  --data-dir /path/to/swarmtrace-data \
  --with-temporal-audit \
  --output-dir /tmp/swarmtrace-check

uv run python report/verify_reproduction.py /tmp/swarmtrace-check
```

The full analysis runs on CPU and requires no paid service.

## Data

Source data are not redistributed in this repository.

SwarmTrace uses the pinned public ProWiki export from:

[JoshuaDavid/WikiAgentSwarmInvestigation](https://github.com/JoshuaDavid/WikiAgentSwarmInvestigation/tree/9bc20957b9d3b40cce3f7ee7827e9001a6256a7f/agent-logs/prowiki)

Exact hashes and provenance are documented in [data/README.md](data/README.md) and the paper.

Raw revision bodies and full IP addresses are not committed.

## Repository structure

```text
src/swarmtrace/   analysis implementation
tests/            unit and regression tests
docs/             frozen plans, protocols and audit notes
data/             data provenance and acquisition instructions
outputs/          derived results, validation outputs and figures
report/           manuscript, final paper and claim verification
```

Large temporal trace archives are regenerated rather than committed.

## Reproducibility

The original analysis plan was frozen before the primary experiment results and is preserved in:

[`docs/preanalysis.md`](docs/preanalysis.md)

Post-result analyses are documented separately rather than presented as preregistered work.

The repository includes:

- source-data hash verification
- seeded random baselines
- exact small-graph enumeration
- degree-tie sensitivity checks
- independent incidence reconstruction
- independent graph-removal checks
- clock and boundary diagnostics
- ambiguous-label sensitivity checks
- cross-window controls
- numerical manuscript claim verification

Weak and negative results are retained rather than replaced by more favorable exploratory outcomes.

## Limitations

SwarmTrace does **not** establish that:

- labels correspond one-to-one with real agents
- co-writing implies communication
- a resource was read or required by another writer
- deleting a resource removes information copied elsewhere
- graph fragmentation implies containment
- six hours is the correct information-lifetime window

The source export is incomplete by construction, and the withdrawal experiments assume equal-cost actions, no adaptation, no migration, and no resource recreation during the frozen counterfactual.

See the paper for the full limitations and dual-use discussion.

## LLM use

I used Codex for substantial assistance with code, tests, analysis execution, literature searches, figures, and manuscript drafting. Earlier preparation and implementation also used LLM assistance.

I personally reviewed the methodology, code, analyses, figures, and manuscript, reran the project workflow, and verified the reported numerical results against the saved outputs and computational checks documented in the repository.

I take responsibility for the final analysis and submission.

## Author

**Yazan Al-Dabain**

GitHub: [@yazandabain](https://github.com/yazandabain)
