# Independent execution and result-integrity audit

2026-09-08. Reviewed the complete frozen 469-line `src/fast_router_diagnosis.cpp`, complete `tools/run_diagnosis.py`, the original linked kernel's entry initialization/result extraction, and completed `results/run_v1` artifacts. This reviewer launched no ANN search, graph replay, new model, or large graph process. Prepared input provenance is covered separately by `protocol_input_preparation_review.md`.

**Execution/data-integrity verdict: PASS for the completed run_v1.** No blocking implementation or result-layout defect was found in the fixed configuration. This is an audit of execution validity and reported arrays, not a conclusion that Fast's recall loss has one identified cause.

## Completed jobs and acceptance

| Dataset | Auxiliary parity query count | Configurations checked | Count/plain/repeat graph calls | Main graph calls, both L |
|---|---:|---:|---:|---:|
| WebVid | 8 | 14,464 | 43,392 | 1,336,510 |
| Yandex | 8 | 14,560 | 43,680 | 1,347,188 |

All four jobs exited with code zero and the expected terminal metadata status. Their time intervals do not overlap. Total graph calls are exactly 2,770,770, matching the four job records and the controller completion manifest. Controller instrumented wall time is 150.676378459 seconds. The largest observed child RSS was 10,746,122,240 bytes, below 80 GiB. At audit time this version occupied 204,579,894 bytes and `/data` had 17,649,594,368 bytes free, within the 2 GiB artifact and 10 GiB reserve limits.

Both formal parity files under `results/run_v1/parity/<dataset>/parity.json` report PASS. They cover only local rows `[512,520)`, hence only auxiliary fit rows. For each query and both L values they check all H singleton entries and all 89 multi-entry variant columns. Counted/plain IDs and distances match exactly; a counted repeat additionally matches NDC. Fast route counted/plain/repeat results match, and direct top1/2/3 results agree with the same route's top8 prefix on these acceptance rows. `main/<dataset>/parity.json` is intentionally NOT_RUN because the controller checks the completed dedicated parity job before launching main; it is not evidence of failed or missing acceptance.

The counted distance wrapper also checks on every counted search that the first distance evaluations visit all supplied actual base IDs in their supplied order. This confirms the effective one/two/three-entry contract for these valid, distinct hub IDs. It does not imply that entry ordering is irrelevant in all kernels or that count/plain parity was replayed independently on all 512 pilot rows.

## Source and controller checks

- Queries are passed unchanged to approximate prototype routing, exact prototype distances and the original `ACSG::search_new(mode=2)` graph kernel. GT is absent from `Work::run`; hit scoring occurs after search. Precomputed basin labels are diagnostic output and never choose entries for Fast/exact/combination searches.
- Approximate and exact prototype distances use the same `hnswlib::InnerProductSpace` function. Exact ranking uses increasing distance, then increasing real base ID. Local IDs in arrays are hub-row ordinals, mapped through the saved real hub IDs.
- All C8 pairs and triples are enumerated once as rank combinations: 28 pairs and 56 triples, with no forced anchor. The pilot has 91 named columns including Fast/exact top1/2/3 and the seed100 top3 control. Variant entries are generated from each query's corresponding route, not from GT or another query's route.
- Each OpenMP thread owns its distance computer, visited table and return buffer. The graph is shared for read-only search; L is changed outside each parallel region. The cache only reuses identical ordered entry arrays, with `-1` padding distinguishing different cardinalities. Single-entry variant values are taken from that query's exhaustive singleton matrix.
- The controller runs one child job at a time with 16 OpenMP threads and one BLAS thread. It monitors RSS, remaining disk, total version-directory bytes and elapsed time. Stops target the owned process group after matching PID/PGID/start ticks. It verifies a frozen identity set before each child and requires the correct parity and terminal statuses.
- The 3,000,000-call check is applied after each completed job, rather than as a per-call runtime counter limit. For this run the fixed source/configuration and completed totals remain under budget. Do not interpret this wrapper as a general hard per-call limiter for arbitrary future configurations.

## Independent array verification

The audit rehashed all 33 execution-freeze paths, all 14 build-manifest files and all 94 protected prior files; every current hash and recorded size matched. The runner source SHA256 is `968796a903bd562a2b4231a1b92a90bb35528f5dc932de37c1361f7f9f8c9c28`; executable SHA256 is `c2948518b715aa66d28cede1aec126fef197b513dc555d0f42ff6e14d826287f`. No large base/graph full hash was repeated.

For every query in both completed datasets, exact rank local IDs form a full permutation of H hubs, distances are finite and sorted, and exact floating-point ties follow increasing real base ID. Both Fast and seed100 top8 routes contain eight valid distinct local IDs in increasing distance order. Every saved approximate distance equals the saved exact-distance value for that same query and local hub. Saved row IDs and real hub IDs match prepared_v2/source bytes.

All 512 pilot rows' entry-local matrices were independently rebuilt from the saved route ranks and each variant's declared cardinality. All match, including unused `-1` padding, the complete pair/triple sets and the seed100 source.

For each completed L matrix, every hitmask uses only its low ten bits and every hitcount equals its mask's popcount. All NDCs are positive. For all pilot rows, Fast1/exact1 outputs exactly match the corresponding exhaustive-singleton column, and Fast2/Fast3 exactly match their declared C8 pair/triple duplicate columns in IDs, masks, counts and NDC. These cache correspondences verify output indexing; they are not extra independent search replications.

Returned IDs were independently rescored against the selected query's prepared GT10 for deterministic local query rows `0,15,16,31,32,127,128,255,256,495,496,511,512,527,528,n-1`. Every H singleton column and, where applicable, every pilot column was checked. This reconstructs 14,132 search-result masks per L for WebVid and 14,228 per L for Yandex, including batch boundaries, the pilot/auxiliary boundary and the final row. All sampled IDs are in range, all ten returned IDs are distinct, and all reconstructed masks match exactly.

A further 236 returned top10 lists per dataset, spanning both L values, fixed singleton columns and Fast/exact/combination controls, were checked against raw base-vector/query inner products using small indexed base reads. No float64 IP inversion was observed. This confirms the sampled result ordering without loading a graph or replaying a search.

## Interpretation limits and reporting requirements

The execution confirms the correctness of the audited input, routing-score bookkeeping and original-kernel evaluation for the frozen run. A count/plain implementation match does not show that a cosine GT1 basin is an optimal finite-L Recall@10 target. Approximate-versus-exact candidate disagreement is not itself recall regret; the paired actual-search outputs must determine that. All-H single-entry and C8 combination optima remain restricted offline oracles; their headroom is not deployable routing accuracy or a Recall–QPS gain.

Only 512 historical pilot queries per dataset are primary statistical units, and nearest/random transfer comparisons use their first 128 paired queries. The 2.77 million graph calls, exhaustive hub columns, pair/triple columns and repeated acceptance searches are not additional independent observations. Set-valued ties and the source-only versus target-oracle distinction must be retained in the analysis.

Timing coverage is narrower than the protocol requested: the runner emits a `route` progress event before HNSW construction and route/exact-score computation, but does not independently time those components. Report them as a combined instrumented stage or mark the unavailable subcomponents explicitly. Never fill unavailable HNSW-build/routing or historical exact-GT/QGT/graph-build times with zero. Main search/scoring/I/O times and controller elapsed time are diagnostic costs, not pure query latency or QPS.

Analysis-script selection, tie and confidence-interval review is complete for final `analysis/v2`; see `independent_analysis_review.md`. No empirical cause ranking is asserted by this execution-integrity verdict alone.
