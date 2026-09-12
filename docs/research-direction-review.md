# Bounded research-direction review

2026-09-12, after the frozen snapshot experiments and initial paper draft.
The author requested a short assessment of a stronger contribution before settling
the final paper direction. The following options were considered using existing
infrastructure, before computing their new results.

1. More targeting algorithms: low value. The tiny primary graph and ambiguous
   endpoint interpretation dominate the problem; an algorithm contest would add
   complexity without resolving it.
2. Infer communication from text: potentially useful, but validating content and
   attribution would require substantial new labeling. It is a follow-up, not a
   reliable sprint pivot.
3. Extend lifecycle analysis to return after deletion: feasible, but the export's
   heuristic recreation links and incomplete writes complicate causal interpretation.
   The original investigation already discusses recreation.
4. Test snapshot representativeness and separate ranking horizon from evaluation
   horizon: highest value. The current three-horizon comparison changes both the
   candidate graph and the endpoint population. A strong 24h fragmentation result
   might coexist with little change in the recent 6h surface. Keeping candidates,
   action budgets and the evaluation graph fixed isolates this measurement issue.

Decision: retain both frozen experiments and add a bounded retrospective temporal
and crossed-horizon audit. This can strengthen or qualify the existing finding;
no outcome is presumed. It is not a new primary endpoint or a causal intervention
study. The protocol is in `docs/temporal-audit-protocol.md`.
