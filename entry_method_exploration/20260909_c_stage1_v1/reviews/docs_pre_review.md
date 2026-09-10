# C stage1 independent documentation pre-review

This is a pre-review while C2 raw collection is in progress. It establishes no quality, equal-cost, Pareto or QPS conclusion. The reviewer did not open GT, validation/held-out vectors, or run ANN.

## Read scope and supported contract

The reviewer read the current `AGENTS.md`, all four root documents, the complete C0/C1/C2 protocol, locked configuration, current state, C1 gate, independent kernel review and `state_machine.hpp`. Small source and raw C1 result identities were checked against the gate. Both real C1 result files have 32 records, the frozen first 16 sample positions at L64/L128; synthetic v2 reports 180 cases, 960 partial-row cases and PASS. These facts support an engineering acceptance statement for the frozen tested version, not a universal proof of parity.

The specification correctly describes the independent namespace, unchanged legacy API, L+1 pool, scheduler and partial-row state, separate visited/expanded membership, deep clone, query/DC binding, paid candidate distances, remaining cap, bounded history, original retset output, and separation of count/trace from branch wall. The shared-cap contract must remain explicit: actual NDC and wall can differ, natural termination does not spend the balance, and all 2,000 queries are included in the primary comparison.

One API description needs precision: `Engine::inject(force=true)` pays and inserts the candidate and starts the forced row; the subsequent `Engine::resume` scans that row. The specification should not imply that `inject` synchronously completes its adjacency scan. The environment sentence stating that no build was rerun should be limited to the historical comparison dependencies, because this stage builds independent C tools.

## Synchronization required at delivery

- `summary.md`: replace the statement that E20 remains the latest real experiment and all C work remains unimplemented. Lead with actual C1/C2 status, four unconditional results and corrected intervals, execution/split limitations, stopping decision, and evidence. Keep E20 as preceding evidence and C R0 as an unrun design version.
- `s-target.md`: replace `C0_LOCKED_C1_PENDING`, “C1 being implemented,” and “C has not measured same-state oracle” with the final stage state. Preserve C as this stage's first priority, but represent a failed gate as stopped. A passed headroom gate still waits for a new user decision before C3. C3/C4 and evaluation splits remain unrun and unauthorized.
- `s-experiment.md`: add E21 for C stage1 engineering/finite-action diagnosis, link the new detailed card, and update dates and the fixed nine-card description. The C R0 row remains design history; make clear that the independent stage1 successor is a distinct executed version.
- `experiment_history/10_*.md` and directory README: preserve C0 lock rules, C1 initial findings/fixes and v1/v2 evidence, smoke versus main raw runs, offline scoring, branch costs, final headroom gate and unrun stages. A successor link in historical card 09 must not rewrite R0 as executed.
- `spec.md`: retain only API/state/semantic and artifact contracts; keep measured quality tables in summary/history. The stage package README/report/state and four documents must use the same terminal decision.

Final review should compare each numeric statement to the authoritative analysis JSON and each command to the durable command records, without reproducing an ANN search. Verify four primary Bonferroni4 intervals over all queries, natural controls excluded from the primary force oracle, same-candidate force/natural pairing, and selection bias of winner-conditioned mechanism summaries. Full Recall–QPS, learner/state×reuse training, validation/held-out, A+B execution and interaction evidence must remain explicitly absent.

## Local checks

The old maintenance checker is tied to nine cards and E01–E20 and writes into its historical maintenance directory. Do not rerun it as the C-stage checker or replace its previous output. A new [check_documents.py](check_documents.py) reads bounded current documents, checks Markdown targets/fences and index coverage, verifies protected source snapshots and unchanged implementation/configuration identities, and checks C1 gate SHA256s. It only writes a new report path and rejects overwrites. Final mode expects ten cards and E01–E21.

Run from the project root:

```bash
python3 entry_method_exploration/20260909_c_stage1_v1/reviews/check_documents.py entry_method_exploration/20260909_c_stage1_v1/reviews/docs_checks_pre.json
python3 entry_method_exploration/20260909_c_stage1_v1/reviews/check_documents.py entry_method_exploration/20260909_c_stage1_v1/reviews/docs_checks_final.json --final
```

Target existence is not a semantic audit and does not validate Markdown anchors or large input contents. Independent final semantic review is still pending until C2 analysis and root-document synchronization finish.
