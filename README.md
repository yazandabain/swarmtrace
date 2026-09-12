# SwarmTrace

SwarmTrace reconstructs recent multi-writer activity in the DSEWiki incident and
stress-tests a frozen historical label-resource graph under resource withdrawal.
It measures observed write overlap, not communication, agent identity, information
loss or containment.

The frozen six-hour snapshot shows little targeting advantage, but an exploratory
hourly survey finds that degree targeting beats median uniform withdrawal in 138 of
151 nonempty six-hour graphs at the 25% budget. A separate comparison fixes candidates
and the six-hour evaluation graph: at the frozen time, the top 18 resources ranked by
24-hour degree include none of the 18 recent resources. This complete miss occurs at
20 of 151 hourly snapshots, under every valid older-degree tie ordering. Uniform
withdrawal would produce 29.0 such misses in expectation; complete misses alone do
not show that degree targeting is worse than random. Fragmenting historical overlap
need not reach the recently shared surface. Neither metric measures communication
loss or containment.

## Read the submission

- [Paper PDF](report/swarmtrace_paper.pdf): four main pages, references and three appendices.
- [Editable Word version](report/swarmtrace_paper.docx).
- [Manuscript source](report/manuscript.md): edit this to regenerate both documents.
- [Verified claim ledger](report/claims.json).
- [Compact source and evidence archive](report/swarmtrace_artifact.zip).
- [Audit findings](docs/audit.md), [frozen plan](docs/preanalysis.md), and
  [submission requirements](docs/submission-requirements.md).

The PDF uses the official template's embedded Old Standard TT fonts, Letter page
size, one-inch margins, title/abstract box and section order. The DOCX is generated
from the native template package. Word pagination can differ from the verified PDF.
The source template is supplied locally, remains unmodified and is not redistributed
in the artifact bundle.

## Reproduce

Python 3.12 and [uv](https://docs.astral.sh/uv/) are required. Dependencies are pinned
in `uv.lock`. The normal analysis does not require the optional document packages.

```bash
uv sync --locked
uv run python -m swarmtrace.run --data-dir ~/code/swarmtrace-data --with-temporal-audit
uv run pytest -q
uv run ruff check .
uv run python report/verify_claims.py
```

The raw directory must contain the five files listed in [data/README.md](data/README.md).
The runner checks their frozen SHA-256 hashes before doing any analysis. Obtain them
from the pinned [public export](https://github.com/JoshuaDavid/WikiAgentSwarmInvestigation/tree/9bc20957b9d3b40cce3f7ee7827e9001a6256a7f/agent-logs/prowiki).
No live wiki access is needed. Raw data are not included in this repository or bundle.

The command runs both frozen experiments at 1h, 6h and 24h, independent reconstruction
checks, 500 uniform permutations and 500 degree-tie permutations per horizon, exact
small-graph enumeration, clock/exclusion diagnostics and publication figures. With `--with-temporal-audit`, it
also runs every hourly 6h/24h snapshot, the common-candidate ranking comparison and
the final 1h/3h/6h/12h evaluation-window and exact candidate-pool controls. It uses
CPU only and no paid service. Use `--output-dir /tmp/swarmtrace-check` for an isolated
reproduction, or `--primary-only` to skip the initial post-result extensions and paper figures.
The full temporal run takes several minutes and produces about 115 MB of compressed
trace archives under `outputs/temporal/`. These are regenerated rather than committed
or included in the compact ZIP; the complete hourly tables and summary evidence are
included. Each archive uses lossless unsigned integers, saved seeds and graph mappings.

```bash
uv sync --locked --group report
uv run --group report python report/build_submission.py
```

Place `Copy of Apart Research hackathon submission template.docx` in the repository
root before rebuilding documents. The PDF renderer reads its embedded fonts and
formatting; it does not require LibreOffice. `report/preview/` contains page images,
and `report/render_validation.json` records pagination. Editing the Word document
alone will not update the Markdown source or PDF.

In a restricted environment, set `UV_CACHE_DIR` to a writable directory. Analysis
sets a temporary Matplotlib cache and uses the noninteractive Agg backend.

## Evidence files

| Output | Meaning |
| --- | --- |
| `outputs/summary.json` | Historical and snapshot totals by horizon |
| `outputs/hourly_w*.csv` | 168 hourly states and transition counts per horizon |
| `outputs/deletions_w*.csv` | Every deletion, episode match and live-writer count |
| `outputs/transitions_w*.csv` | Event-level activation, deletion and expiry transitions |
| `outputs/snapshot_w*.json` | Original labels and eligible resource episodes |
| `outputs/snapshot_incidences_w*.csv` | Each edge's latest qualifying revision ID and time |
| `outputs/degree_ranking_w*.csv` | Static rankings with explicit tie order |
| `outputs/withdrawal_w*.csv` | R, D, Q, G and pointwise simulation envelopes at every k |
| `outputs/simulations_w*.npz` | All resource orders and integer component-size trajectories |
| `outputs/checkpoints.csv` | Planned action fractions with actual rounded counts |
| `outputs/exact_distributions_w*.csv` | Exact uniform and degree-tie subset probabilities |
| `outputs/hub_recency.csv` | Why the 24h hubs disappear from shorter-horizon graphs |
| `outputs/*sensitivity.csv` | Clearly labeled post-result audit extensions |
| `outputs/temporal_checkpoints.csv` | All hourly graph-level withdrawal checkpoints |
| `outputs/crossed_hourly.csv` | Common-candidate comparisons evaluated on recent topology |
| `outputs/crossed_tie_bounds.csv` | Exact recent-resource coverage bounds over degree ties |
| `outputs/review_controls.csv` | Every final window/control checkpoint, including exact uniform baselines |
| `outputs/review_control_summary.csv` | All window/budget summaries, including empty-hour counts |
| `outputs/analysis_validation.json` | Independent oracle and forward-removal checks |
| `outputs/run_manifest.json` | Data, code, environment and output hashes |

`simulations_w*.npz` orders index the resources in `snapshot_w*.json`. Column k of
`*_counts` is the largest number of original labels in any connected component after
k withdrawals. Divide by the fixed original label count for R, or by column zero for Q.
All-removed R is 1/|L| because isolated labels are retained.

After an isolated full reproduction, compare every table, figure, graph mapping and
simulation array with `uv run python report/verify_reproduction.py /tmp/swarmtrace-check`.
The generated `report/reproduction_validation.json` records the comparisons. The
source-copy audit also uses `--require-no-git` to check archive portability.
Build the compact archive with `uv run python report/package_artifact.py`; it includes
a file-by-file SHA-256 manifest and excludes the large hourly trace archive.

Top-level derived tables, frozen simulations, validation and paper figures are
versioned. The large hourly trace archive remains on disk and can be regenerated
from the compact reproducibility ZIP. Working checkpoints are committed locally
after validation. Nothing has been published or submitted.
