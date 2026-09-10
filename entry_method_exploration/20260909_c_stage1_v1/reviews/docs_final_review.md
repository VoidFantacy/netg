# C stage1 independent final documentation review

**`DOCUMENTATION_FINAL_REVIEW_PASS`**. The current documents consistently report C0/C1 engineering acceptance, completed C2 diagnosis and `NO_GO_UNCONDITIONAL_HEADROOM_STOP_C`. The frozen configuration stops because both Yandex means fail the registered +0.5 pp material threshold. WebVid passes, and all four corrected intervals are positive. No document under final review promotes the oracle into a deployable learner, equal-cost gain, Recall–QPS result or A+B synergy.

This review read the complete current root `summary.md`, `spec.md`, `s-target.md`, `s-experiment.md`, history README/cards 09 and 10, and the stage README/report/commands/state. It checked their claims against the locked protocol/configuration, [C1 gate](../results/c1_gate.json), [kernel final review](kernel_final_review.md), authoritative [C2 JSON](../results/analysis_v1/report.json), [independent statistical final review](c2_statistics_final_review.md), completion markers and durable command records. It did not open GT, validation/held-out vectors, or execute an ANN/model call.

## Numerical and decision agreement

| Point | Continue / oracle R@10 | Unconditional gain | Bonferroni4 family95 interval | Extra hits / required | Gate |
|---|---|---|---|---|---|
| WebVid L64 | 65.595% / 66.575% | +0.980 pp | [+0.620, +1.410] pp | 196 / 100 | PASS |
| WebVid L128 | 74.800% / 75.435% | +0.635 pp | [+0.365, +0.975] pp | 127 / 100 | PASS |
| Official Yandex-IP L64 | 83.150% / 83.380% | +0.230 pp | [+0.040, +0.495] pp | 46 / 100 | FAIL |
| Official Yandex-IP L128 | 89.440% / 89.580% | +0.140 pp | [+0.005, +0.360] pp | 28 / 100 | FAIL |

The Yandex L64 upper endpoint is 0.49503125 pp before display rounding; the three-decimal documents correctly show 0.495. All four points retain N=2000. Coverage, action proportions, same-candidate natural controls, graph-NDC summaries and ratio-of-means changes, clone and serialization/deserialization means agree with the authoritative report. The separate statistical reviewer independently reconstructed the raw evidence; this documentation review verifies that the prose and tables represent those results faithfully.

The comparison baseline is **capped native continuation from the paired Fast3 prefix**. Its cap-stop counts are 2/43/25/356, so the 17.8% Yandex L128 truncation is material to interpretation. The summary, stage report and historical card explicitly prevent labeling that baseline as uncapped full Fast. All common-cap branches preserve actual work separately; no equal-work claim is made. Main oracle choices exclude natural controls, Recall ties prefer continue, and all no-eligible/no-op rows remain in the denominator. Winner-conditioned force-versus-natural observations retain their GT-selection limitation.

## Contract, commands and evidence boundaries

The API documentation now correctly says that `inject(force=true)` starts the forced row and subsequent `resume` scans it. It preserves ordered pool and pending flags, separate visited/expanded, cursor/rewind and partial-row state, query and immutable input identity, paid candidate distance, deep branch isolation and bounded history. C1 remains an engineering result over the stated fixtures and real samples, not an exhaustive proof. The historical dependency-build sentence is now explicitly scoped and no longer conflicts with the new independent C builds.

All 18 labeled child commands currently listed in [commands.md](../commands.md) exactly match the tokenized argv in their individual durable command JSONs, with exit code zero and no recorded resource stop. This includes the final protection audit. C2 smoke and main use the accepted `c2_v2` build; main counts are 2000 per dataset. Initial preparation/build commands are explicitly disclosed as predating the durable launcher, with missing per-process resource timing rather than fabricated measurements. Controller and launcher descriptions are consistent with their source and saved reservations.

Main raw completion markers record 38.728218445 and 58.824170738 seconds, 74596 and 79604 physical prefix/branch executions, and no GT access. These raw-worker times differ from their outer launcher elapsed times, and the documentation labels them accurately. Both main commands finish before offline scoring starts. Diagnostic branch wall, clone, routing and state persistence costs are itemized without conversion into formal method QPS. The statistical review records the conservative total 172261 <= 200000 calls; the final protection audit reports the unchanged input/source/scientific lock and bounded artifact footprint.

## Document roles and final checks

`spec.md` owns the implemented API/semantics, `summary.md` the latest measured result, `s-target.md` the stopped stage and unrun gates, and history/E21 the detailed process and evidence. C R0 and v5 original files remain unrun design versions with explicit links to their executed successor. Two final historical tense ambiguities were reported and corrected before acceptance. No review required an additional experiment or alteration of the scientific lock.

C3 learner/state-by-reuse, C4 full Recall–QPS, validation/held-out, all-H online action scans, multiple checkpoints, multi-step RL and A+B execution remain unrun. Future A+B labels must be regenerated on its deployed induced state, and the policy-specific factorial and positive-interaction requirement are retained as future conditions only.

The version-local [check_documents.py](check_documents.py) final run validates ten historical cards, E01–E21, local Markdown target existence, balanced fences, frozen source snapshots, permitted document changes and C1 hashes. Its output is `docs_checks_final.json`; this semantic review's machine result and reviewed root-document SHA256s are in `docs_final_review.json`. No old maintenance output or pre-review was overwritten.

This audit checks documentation and existing evidence. It does not independently reproduce large input hashes, raw GT memberships or ANN trajectories; those claims are bounded by the separately linked protection/statistics/kernel audits. Initial preparation timing remains unmeasured, and historical development-pool/single-build inference limits remain explicit. No unresolved documentation finding remains.
