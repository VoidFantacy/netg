# P2 pilot analysis contract

`analyze_p2.py` reads existing results only. It does not invoke an evaluator, train a model, partition a graph, load query/GT/base vectors, or advance a stage. Actual P2 inputs were not available when the script was prepared; no P2 result is claimed by this implementation note.

## Inputs and invocation

Run with the existing CPU environment from `/data/netg/ACSG`. Use the root task controller for the actual analysis so it has a durable log, identity and timeout. `--input` is repeated exactly twice, with fields `DATASET COUNT_JSON TIMING_JSON MODEL_JSON FAST20K_MANIFEST`.

```bash
.venv_cpu/bin/python hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p2/analyze_p2.py \
  --protocol hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/protocol.json \
  --p1-gate hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/gates/P1.json \
  --input webvid2_5m_light_v1 WEBVID_COUNT.json WEBVID_TIMING.json WEBVID_MODEL.json \
    hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p1/paired_fast20k/webvid2_5m_light_v1/manifest.json \
  --input yandex_t2i_official10M_ip_v1 YANDEX_COUNT.json YANDEX_TIMING.json YANDEX_MODEL.json \
    hierarchical_target_search/20260907_v1/overnight_20260907T155400Z/p1/paired_fast20k/yandex_t2i_official10M_ip_v1/manifest.json \
  --output NEW_ANALYSIS_DIRECTORY
```

The uppercase JSON/output names are placeholders, not assertions that files exist. Use measured artifact paths when the complete P2 pilot is ready. Existing output directories are refused. Default `--bootstrap-chunk 64`; this can be lowered to reduce memory without changing the number of replicates or comparison definitions.

Required input scope is **complete pilot10K**, `[0,10000)` within `drl_train`, stage P2, K10, L64/128, threads matched between count/plain, warmup128, count one round, timing five rounds. The analyzer deliberately rejects smaller interim pilots rather than silently pooling or reporting them as complete P2 evidence. It accepts `geom_weighted`/`oracle_weighted` as metadata aliases of evaluator names `geom_probability`/`oracle_probability`.

## Integrity checks

- Both datasets and all six methods are required: paired Fast20K, geometric unified/uniform/probability, oracle unified/probability.
- P1 gate must be PASS. Evaluator output and `.parts/complete.json` must both be complete; an interrupted run does not become an algorithm failure.
- Query order is exactly0..9999. Result and full route hashes are recomputed from aligned count rows and plain round0 rows. Hashes and Recall means must match all five plain rounds; later timing rounds must reference the sole aligned round0 sample.
- Geometric queue controls share complete route fields and oracle controls share complete route fields. L changes cannot change routing. Actual seed count must equal the unique consumed IDs including the optional shared seed, and the paired Fast rank0 anchor must be present.
- Independent count means must reconstruct from per-query routing/graph/total NDC and MAC, with exact per-query additivity. Published plain QPS must equal `N / batch_wall_seconds`; count QPS must remain null. Oracle is never marked deployable.
- The actual saved timing schedule must alternate forward/reverse method order over five rounds. Timer contract flags exclude GT scoring, traces, hash, JSON, workspace and output allocations and include online routing/search/reset/result writes.
- Model and paired Fast both fit `[10000,30000)`. Fit-query, fit-GT and input-audit checksums must match; neither can use pilot labels. Model parameters and seed are fixed by protocol. Embedded evaluator model metadata must equal the supplied model file.
- Small model/Fast files are checked against their checksums. The multi-gigabyte frozen graph is not rescanned: its audited model checksum is retained as provenance, while evaluator index path/size and all other count/plain metadata must match. The parent P0/input audit remains authoritative for base/graph identity.

## Fixed comparisons and statistics

Every contrast below is reported for **both datasets and both L values**, with no favorable-point selection:

| Contrast | Candidate minus reference | Interpretation |
|---|---|---|
| `uniform_protection` | geometric uniform − geometric unified | Primary fixed-route queue comparison |
| `probability_protection` | geometric probability − geometric unified | Primary fixed-route queue comparison |
| `oracle_protection` | oracle probability − oracle unified | Primary fixed-oracle-route queue comparison |
| `oracle_selection_unified` | oracle unified − geometric unified | Diagnostic region selection plus selected-portal gap |
| `oracle_selection_protected` | oracle probability − geometric probability | Diagnostic selection gap with protection |
| `geometric_bundle_vs_fast` | geometric unified − paired Fast20K | Diagnostic routing/portal/entry-count/shared-seed bundle |
| `oracle_bundle_vs_fast` | oracle unified − paired Fast20K | Oracle diagnostic bundle, never deployment evidence |

Recall uncertainty uses 10,000 percentile bootstrap replicates with NumPy `default_rng(2026090711)`, ordered WebVid then Yandex, L64 then L128. Each replicate samples aligned query IDs with replacement; every fixed contrast within a dataset/L shares that same sample. The statistic is the mean of the candidate-minus-reference per-query Recall differences. One model build supplies one deterministic aligned Recall vector per method; timing rounds do not multiply its sample size.

The 95% intervals are **pointwise, exploratory and unadjusted**. There are twelve primary dataset×L×queue contrasts plus sixteen explicitly diagnostic contrasts. No claim of familywise significance, chosen-best confidence, or P5/P6/P7 acceptance is made. An interval crossing zero does not prove equivalence. Exact zero observed paired differences are described as such without extrapolating beyond the sampled pilot.

Each QPS comparison stores all five matched round pairs and ratios, mean and median paired ratio, min/max ratio, faster-round count, and ratio of mean QPS. These are different statistics and are named separately. Per-method summaries preserve mean QPS, median QPS, all five rounds, and the pooled `5N/sum(wall)` value. No QPS confidence interval is fabricated from five rounds. Routing-only wall remains separately labeled explanatory evidence.

Bootstrap Recall draws are stored in compressed NPZ artifacts. With chunk64 and10K queries, the index buffer is about2.56MB and a single float64 gather about5.12MB; artifact JSON parsing generally dominates memory. Only one dataset's raw count/plain JSON remains in the main analysis state at a time.

## Gate and claim boundaries

The output always leaves the algorithm gate as `REQUIRES_MECHANISM_REVIEW`; passing integrity checks is not P2 GO. The first three comparisons address candidate protection with the real route held fixed. Positive oracle-selection differences address potential lost by real routing/selected portals, not an isolated portal-quality or graph-connectivity cause. Positive oracle-vs-Fast Recall may result from different entries and shared-default seeding. It cannot alone justify a larger model or auxiliary graph.

All measured points use the same fixed L within each contrast. They are not matched Recall or matched QPS comparisons. The descriptive real-method pilot frontier excludes oracle and supplies no formal performance confidence. P5/P6/P7 retain the preregistered measured-point matching and selection inside bootstrap, Bonferroni-corrected family, two adjacent anchors, independent builds, and later frozen testing. None is replaced by the exploratory95% intervals here.

The root P2 review must combine these tables with prespecified competition traces, consider both budgets on both datasets, identify a localized prediction/portal bottleneck when relying on oracle-only potential, and follow the registered failure action. Neither a nominal positive interval nor an implementation PASS automatically authorizes P3/P4.

## Outputs and preparation checks

Outputs: `analysis.json`, `report.md`, `measurements.csv`, `comparisons.csv`, two dataset summaries, two bootstrap NPZ files, `invocation.json` with all input/script/protocol/gate hashes, and `complete.json`. Incomplete or invalid analysis retains `failure.json` and already-completed dataset artifacts. Nothing overwrites existing output.

Preparation verification in `analysis_implementation_checks.json`: Python compilation/help passed; C++ hash reconstruction passed on both existing P1 real-data count artifacts; the bootstrap's paired-difference behavior and seeded repeatability passed a tiny analytic check; cross-zero classification does not claim equivalence. These are implementation checks only, **not generated P2 experimental results**.
