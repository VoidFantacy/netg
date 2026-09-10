# v1 Trace Design (frozen before smoke)

## Scope

This diagnostic instruments the existing `ACSG::search_new` finite-beam loop for a **single
custom entry**. It does not alter the graph, entry initialization, candidate-pool insertion rule,
or result ordering. The trace is collected only when the new explicit traced entry point is used;
all existing callers retain their original code path.

## Exact event definitions

All distance values use the active `DistanceComputer` ordering: smaller is better for both
configured IP and L2 search implementations.

| Field | Event / definition |
| --- | --- |
| `distance_evaluations` | Every invocation of `dis(id)`, including initial entry evaluation. Must equal external counted NDC. |
| `expanded_count` | A retained candidate with `flag=true` is popped and its adjacency row is scanned. |
| `evaluated_neighbor_count` | Valid, not-previously-visited neighbor whose distance is evaluated; excludes the initial entry. |
| `accepted_insertion_count` | A newly evaluated neighbor with `insert_into_pool` return value `< L`. |
| `rejected_by_pool_bound_count` | After the pool is full, a newly evaluated neighbor has `dist >= retset[L-1].distance`. |
| `rewind_count` | At the end of an expansion, `updated_pos <= current_k`; the subsequent cursor visits an earlier pool location. |
| `rewind_span_sum/max` | `current_k - updated_pos` for each rewind. |
| `best_distance_improvement_count/sum` | Strict decreases of `retset[0].distance` caused by an accepted insertion; sum is the positive decrease. |
| `pool_bound_improvement_count/sum` | Strict decreases of the full-pool worst retained distance caused by an accepted insertion. |
| `max/mean_stagnation_expansions` | Consecutive expanded nodes without a strict decrease in current best distance; mean is over completed runs of stagnation. |
| `final_frontier_gap` | `retset[1].distance - retset[0].distance` if at least two retained nodes; otherwise `null`. |
| `final_pool_gap` | `retset[last_retained].distance - retset[0].distance`; `last_retained=min(num_ids,L)-1`. |
| `first_topk_gt_evaluation_ndc/expansion` | First distance-evaluation matching one of the supplied top-K GT IDs. Supervision-only: never an online feature. |

`accepted_insertion_count + rejected_by_pool_bound_count <= evaluated_neighbor_count` is an
invariant. Candidates rejected because they do not beat the pool bound are counted separately;
duplicates are excluded before distance evaluation by the existing visited table.

## Parity contract

For every smoke `(query, entry, L)`, traced and ordinary `search_new` must have identical top-10
IDs, distances within `1e-6`, and equal NDC. The tracer is in the shared core search function so
it preserves the production insertion and rewind semantics exactly; `trace == nullptr` executes
the original branch with only null checks.

## Pilot protocol frozen here

- `dataset`: WebVid and Yandex official-IP only.
- `query_type`: `drl_train` (the independent prototype-train split).
- query rows: `[0, 2000)`.
- candidate set: current Fast seed-20260828 geometry top-8, evaluated one entry per search.
- `search_L`: 64 and 128; `top_k`: 10.
- held-out access: false; validation is not used before the train-only gate.

The analysis will treat prototype distance, raw-entry distance, geometry rank and an entry prior as
the geometry baseline. GT-derived fields are saved only for labels/diagnostics and are prohibited
from route scoring.
