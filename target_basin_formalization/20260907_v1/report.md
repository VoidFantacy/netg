# Multi-view Target-Basin formalization

Execution status: **COMPLETE**. Decision: **NO_GO_ROUTING_COST**.

- E0: `PASS` (16 engineering checks).
- E1 dense: `FAIL`; routing NDC alone made both L64 targets infeasible.
- E1b fixed HNSW-all: `FAIL`; all four equal-total-NDC Recall comparisons are below Fast.
- E2, E3, E4: `NOT_RUN` by the frozen stopping rule.
- Held-out accessed: `false`.

The fixed backend is efficient enough to make the comparison feasible, but not efficient enough to preserve the same graph-search budget: matched Recall deltas are WebVid `-14.697/-4.960 pp` and Yandex `-4.103/-1.463 pp` for the Fast L64/L128 targets.

The project therefore returns to Fast v1. Detailed evidence is in `pilot/hnsw/report.md`; the machine-readable decision is `gate.json`. Tail/stability, attribution, offline break-even, and held-out evaluation are not applicable after this early gate failure.
