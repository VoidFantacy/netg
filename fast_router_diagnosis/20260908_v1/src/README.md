# Isolated Fast diagnosis runner

This directory contains a standalone diagnostic executable linked against the existing ACSG, MRNN-Descent and Faiss static libraries. It does not rebuild or modify those libraries, the frozen index or method sources. The runner calls `IndexACSGFlat::loadACPG` and the original `ACSG::search_new(mode=2)` shared-beam kernel.

Build and inspect:

```bash
bash fast_router_diagnosis/20260908_v1/src/build.sh
fast_router_diagnosis/20260908_v1/bin/fast_router_diagnosis --help
fast_router_diagnosis/20260908_v1/bin/fast_router_diagnosis --self-test
```

Real runs are scheduled by the root coordinator. Use the frozen `inputs/prepared_v2/<dataset>/runner_config.json`, and distinct new output directories for acceptance and diagnosis:

```text
fast_router_diagnosis --config CONFIG --output NEW_PARITY_DIRECTORY --parity-queries 8 --parity-only
fast_router_diagnosis --config CONFIG --output NEW_RESULT_DIRECTORY --parity-queries 0
```

Acceptance uses rows `[pilot_count,pilot_count+parity_queries)` only. For every L it checks every single hub and each multi-entry variant against a plain distance computer and a repeated counted search. Returned IDs and distances must match exactly; repeated NDC must match exactly. The counted distance computer also verifies that the first distance evaluations are exactly all requested real base entry IDs, in the requested order. Routing checks plain/count and repeat identity plus direct top1/2/3 identity with top8 prefixes. `parity.json` records three search calls per graph check; those calls belong in the global budget.

## Input contract

JSON required keys: `dim`, `index_path`, `queries_file`, `gt_file`, `row_ids`, `hub_ids`, `raw_hubs`, `prototypes`. These path keys refer to headerless little-endian C-order arrays:

| Key | dtype | Shape |
| --- | --- | --- |
| queries_file | float32 | N × dim |
| gt_file | int64 | N × gt_k |
| row_ids | int64 | N |
| hub_ids | int32 | H |
| raw_hubs | float32 | H × dim |
| prototypes | float32 | H × dim |
| basin_label_local (optional) | int32 | N |

Optional scalar keys: `num_queries`, `hub_count`, `gt_k=100`, `pilot_count=512`, `L=[64,128]`, `K=10`, `threads=16`, `seed100_search=true`. K is fixed at 10; threads must be 1–16. Omitted counts are inferred and checked against byte lengths. All IDs are validated, row/hub IDs must be unique, matrices must contain finite values. Prepared basin labels are preferred. If omitted, the runner reconstructs GT1 and computes its nearest normalized raw hub; this is explicitly a GT oracle diagnostic, outside search and routing.

Both HNSW and exhaustive prototype ranking consume unchanged raw query vectors. HNSW uses M16, efConstruction200, efSearch10, primary seed20260828 and seed100 control. Labels inserted into HNSW are real base IDs. Exact ranking calls the identical `hnswlib::InnerProductSpace` function on the same raw query and prototype bytes; smaller distance is better, and exact ties use smaller real base ID. Approximate results preserve the legacy reversed-heap order. `1 - distance` recovers the stored inner-product score convention; do not treat a tie-only ID disagreement as search-quality loss.

## Output contract

The output root must not exist. `metadata.json` contains all shapes, variants and contracts. Every binary is C-order, headerless little-endian. Root arrays:

| File | dtype | Shape |
| --- | --- | --- |
| row_ids.i64 | int64 | N |
| hub_ids.i32 | int32 | H |
| exact.rank_local.i32 | int32 | N × H |
| exact.rank_distance.f32 | float32 | N × H |
| fast.top8_local.i32 / seed100.top8_local.i32 | int32 | N × 8 |
| fast.top8_distance.f32 / seed100.top8_distance.f32 | float32 | N × 8 |
| fast.route_ndc.u32 / seed100.route_ndc.u32 | uint32 | N |
| basin_label_local.i32 | int32 | N |
| pilot.entry_local.i32 | int32 | P × V × 3 |

`local` means hub row ordinal: `base_id = hub_ids[local]`. Unused entry slots are -1. P is pilot_count. Default V=91. `metadata.variants` is an array of `{column,name,route,route_ranks,entry_count}`. Columns 0–5 are `fast_top1`, `fast_top2`, `fast_top3`, `exact_top1`, `exact_top2`, `exact_top3`. Next come all 28 `c8_pair_i_j` in ascending i<j loop order, then all 56 `c8_triple_i_j_k` in ascending i<j<k loop order. The final column is `seed100_top3`. Every combination preserves the query's actual C8 rank order. Read actual local IDs from `pilot.entry_local.i32`; `route_ranks` describes positions, not IDs.

Each `L64/` or `L128/` directory contains:

| Prefix + suffix | dtype | Shape |
| --- | --- | --- |
| all_single.hitcount.u8 | uint8 | N × H |
| all_single.hitmask.u16 | uint16 | N × H |
| all_single.ndc.u32 | uint32 | N × H |
| all_single.ids.i32 | int32 | N × H × 10 |
| pilot.hitcount.u8 | uint8 | P × V |
| pilot.hitmask.u16 | uint16 | P × V |
| pilot.ndc.u32 | uint32 | P × V |
| pilot.ids.i32 | int32 | P × V × 10 |

Returned IDs are real base IDs, with -1 padding. Hitmask bit g indicates whether exact-GT rank g, for g in [0,10), was returned. Hitcount is its popcount; Recall@10 is hitcount/10. Single-entry variants reuse all_single. Identical ordered entry sets reuse their results, including Fast top2/top3 and their C8 pair/triple. Actual graph call counts account for this reuse.

Search outputs flush every 16 query rows. `progress.jsonl` flushes after each block and `L*/progress.json` records committed row counts. Only `L*/complete.json` certifies the full L matrix. `metadata.status=COMPLETE` certifies the complete run. Do not interpret a partially written file as a full matrix. No old output is overwritten.

## Timing and validation limits

All timings are instrumented offline diagnostics, never publishable QPS. L completion files separately record all-single search wall, pilot joint search wall and scoring/binary-I/O wall. Search calls are GT-free; hitmask scoring happens afterwards. Count instrumentation, entry audits, buffer/result handling and variant-cache work are still present. Overall wall includes loading, routing, acceptance and output work. CPU/RSS/disk/wall/search-call hard limits are enforced by the root scheduler and frozen protocol, not this runner.

`synthetic_fixture.cpp` builds only a tiny generated 192-node index and exercises the full serialization/runner path. Its accepted fixture is in `bin/synthetic_e2e_v1/`; it does not read any real dataset. From this version directory, build with `bash src/build.sh src/synthetic_fixture.cpp bin/synthetic_fixture`. The runner's own `--self-test` checks 144 synthetic graph parity cases and 48 router parity cases. The fixture additionally checked 3,464 serialized mask/count/NDC records, all 91 variants, cached single identity, unique/padded entries and refusal to overwrite an existing output root. These checks establish implementation consistency, not method effectiveness.
