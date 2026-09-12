# Literature positioning checked September 12, 2026

This review used the original incident account, the pinned source export, and primary
research papers. It is targeted positioning work, not a systematic literature review.

| Source | Relevant result | Consequence for SwarmTrace |
| --- | --- | --- |
| [Albert, Jeong and Barabasi (2000)](https://doi.org/10.1038/35019019) | Contrasts network response to random failures and targeted removal. | Static degree withdrawal is an established baseline, not a new method. |
| [Holme and Saramaki (2012)](https://doi.org/10.1016/j.physrep.2012.03.001), [author manuscript](https://arxiv.org/abs/1108.1780) | Reviews temporal-network structure and the limitations of static connectivity for dynamic processes. | Recent write overlap is not a time-respecting communication graph. |
| [Lee, Rocha, Liljeros and Holme (2012)](https://doi.org/10.1371/journal.pone.0036439) | Uses recent or frequent contacts to select immunization targets; evaluates on subsequent contacts and simulated spreading. Results depend on the dataset and protocol. | Recency-sensitive targeting predates this project. SwarmTrace does not evaluate future transmission or introduce an immunization algorithm. |
| [Williams and Musolesi (2016)](https://doi.org/10.1098/rsos.160196), [author manuscript](https://arxiv.org/html/1506.00627v2) | Separates topological, temporal and spatial disruption under node failure across empirical networks. | A structural robustness endpoint can differ from functional disruption; this is established prior work. |

Lee et al. was read for its protocol definitions, retrospective/predictive split and
limitations, including the different behavior of its email dataset. Williams and
Musolesi was read for its path model, robustness definitions, and comparison of
topological versus temporal/spatial responses. Neither supplies an empirical claim
about agent communication in DSEWiki.

[Scholtes, Wider and Garas (2016)](https://doi.org/10.1140/epjb/e2016-60663-0)
was also checked through its [author manuscript](https://arxiv.org/abs/1508.06467).
It models path-based temporal centralities with higher-order aggregate networks.
It is relevant background but is not added to the paper: SwarmTrace does not estimate
those paths, and the existing temporal-network references support its narrower claims.

The incident account is [Von Arx et al. (2026)](https://collusion.wiki/), with data
from the pinned [ProWiki export](https://github.com/JoshuaDavid/WikiAgentSwarmInvestigation/tree/9bc20957b9d3b40cce3f7ee7827e9001a6256a7f/agent-logs/prowiki).
The paper distinguishes those investigators' behavioral claims from SwarmTrace's
measured co-writing proxy. Its contribution is a reproducible incident-specific
audit: explicit resource episodes and expiry accounting, preserved frozen results,
and separation of ranking window, action pool and evaluated write overlap.
