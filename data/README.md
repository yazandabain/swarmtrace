# Data

SwarmTrace analyzes the public ProWiki incident export mirrored in:

JoshuaDavid/WikiAgentSwarmInvestigation
`agent-logs/prowiki/`

Downloaded: 2026-09-10

The export contains four wikis. SwarmTrace analyzes only records where:

`wiki == "dse"`

Raw files are stored outside this repository at:

`~/code/swarmtrace-data/`

## Verified source files

| File | SHA-256 |
|---|---|
| pages.jsonl | 92b296170b496b836cdf5ef783bed9465d2d75db7e1a0becec1c36c8b7c42cfd |
| revisions.jsonl | 60df4a515178230aa952d9f64f6215aea4bd95ab2f05e31e484cf9b887e3f793 |
| events.jsonl | 588584295f1c4a7c3d90b04075ab151504f165ff069534d935cda08853ec28b1 |
| labels.jsonl | d94aecd84baecda46344f5b8726a95a9c81e7e41a1c0969fc89a90c8906f0388 |
| manifest.json | b6d53e16b5d9a6a0a98d4577238835ee7a574d7d10a8f1312330b4e626c6ba2b |

Verification command:

`sha256sum -c SHA256SUMS`

All five checks passed on 2026-09-10.

## Important dataset facts

The export contains:

- 14,591 revisions overall
- 13,403 DSEWiki revisions
- 5,217 DSEWiki delete events
- 0 DSEWiki revisions with a blank/null label

Raw data is not committed to this repository.

## Source version

Mirror repository:

`JoshuaDavid/WikiAgentSwarmInvestigation`

Pinned source commit inspected for this analysis:

`9bc20957b9d3b40cce3f7ee7827e9001a6256a7f`

The published SHA-256 values at that commit match the locally downloaded files verified above.

The export's revision cut begins at `2026-05-01`.
