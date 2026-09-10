# Finite-Beam Reachability v1: train-only diagnostic conclusion

## Terminal status

`NO_GO_TRACE_NOT_INCREMENTAL` under the pre-registered operational gate. No validation or
held-out data was read, and the no-online-probe compression stage was not started.

This is **not** evidence that finite-beam trace is uninformative. It is evidence that, under the
frozen top-8/single-entry routing budget and the required `<= +0.5%` graph-NDC condition, the
trace-informed selector does not meet the project criterion on both workloads.

## Protocol

- frozen Fast seed `20260828`, geometry top-8 candidates, one entry per search;
- WebVid and official Yandex/IP prototype-train `drl_train` rows `[0,2000)` only;
- `Recall@10`, `L=64/128`, trace from the unchanged frozen `ACSG::search_new` loop;
- fit rows `[0,1600)`, evaluate rows `[1600,2000)`; ridge alpha `1`, utility lambda `0.05`;
- query-level 10,000-round bootstrap; all configuration was frozen in `trace_design.md` before
  the pilot completed.

Both smoke runs compared traced and ordinary search on 20 queries × top-3 × two budgets:
240 total cases, zero ID/distance/NDC parity failures. Both 2K pilots satisfy
`distance_evaluations == graph_ndc` and
`accepted_insertion_count + rejected_by_pool_bound_count <= evaluated_neighbor_count` for every
row.

## Trace-informed selector versus geometry rank-0

| Dataset | L | Utility delta | 95% CI lower | Recall@10 delta | Graph NDC delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| WebVid | 64 | +0.023416 | +0.009254 | +2.525 pp | **+0.924%** |
| WebVid | 128 | +0.011848 | +0.002204 | +1.200 pp | -0.193% |
| Yandex | 64 | +0.016991 | +0.003632 | +1.900 pp | **+1.988%** |
| Yandex | 128 | +0.007268 | +0.000501 | +0.875 pp | **+1.030%** |

The trace features do explain residual search utility: all four utility deltas are positive and
their bootstrap lower bounds exceed zero. However, three of four points exceed the frozen
`+0.5%` graph-NDC limit. A selector that needs these traces would additionally require online
search to observe them, which is outside the lightweight entry-layer budget.

## Decision

Do not proceed to Stage E, validation 10K, held-out, top-m sweeps, all-hub probes, graph edits,
or an online-probe/resumable-search workaround. The valid finding is narrower:

> Actual finite-beam path statistics contain signal beyond geometric prototype routing, but this
> v1 trace-conditioned route choice does not satisfy the project's cost-aligned cross-workload
> gate and is not a lightweight deployable mechanism.

The next research choice must be made outside this task. A future direction may only reuse these
artifacts after a new formulation explains how to predict or compress the signal without online
probe and with an explicitly revised cost constraint; it cannot continue this v1 by threshold or
feature sweeps.

## Reproduction

See `trace_design.md`, `report.json`, the two smoke logs, and the two train-2K logs. The
analysis command is:

```bash
.venv_cpu/bin/python benches/run/analyze_finite_beam_trace.py \
  --webvid finite_beam_reachability_diagnostics/v1/traces/webvid_train2k_top8_l64_128.json \
  --yandex finite_beam_reachability_diagnostics/v1/traces/yandex_train2k_top8_l64_128.json \
  --output finite_beam_reachability_diagnostics/v1/report.json
```
