# E119 Waiting Handoff

Completion update, 2026-09-22: training, analysis, independent numerical audit
and report have finished. Outcome: `STOP_CAPABILITY_PILOT`; no conditional
native/fresh-data stage was triggered. See [decision.md](decision.md) and
[report.md](report.md). The snapshot and resume commands below are retained
as history, not instructions to rerun completed work.

Snapshot: 2026-09-22 10:41 Asia/Shanghai. The user explicitly requested that
the conversation may close while the experiment runs; they will report when
it finishes. The research goal is NOT complete. No active polling is required.

## Running Experiment

- Working directory: `/data/netg/ACSG`.
- PID at handoff: `7591`; exec session: `65042`; no controlling terminal.
- Command: `.venv_cpu/bin/python -u entry_method_exploration/20260922_service_capability_v1/src/run.py`.
- Output: `training.log`, `progress.json`, `state.json` in this directory.
- WebVid: all four folds completed. Yandex: fold 0 completed, fold 1 TabM
  running (epoch 9 at this snapshot), folds 2 and 3 remain. Fold indices are
  zero-based. This snapshot will become stale; inspect the files on return.
- The controller has a 12-hour cap and resource guards. It exits after
  training and does NOT automatically analyze results, launch fresh data,
  run native performance tests, or change the default.
- Successful completion creates `reviews/training_complete.json` with
  `status=COMPLETE` and sets `state.json` to `TRAINED_PENDING_ANALYSIS`.
- Do not rerun `src/run.py`, refit, overwrite artifacts, or alter frozen
  training code/configuration. A stopped process without a completion marker
  needs a failure audit, not an assumed successful finish.

## Resume After Notification

First inspect the log, process identity and completion marker. Then execute
these commands sequentially from `/data/netg/ACSG`, checking each exit status:

```bash
.venv_cpu/bin/python entry_method_exploration/20260922_service_capability_v1/src/analyze.py
.venv_cpu/bin/python entry_method_exploration/20260922_service_capability_v1/src/audit.py
.venv_cpu/bin/python entry_method_exploration/20260922_service_capability_v1/src/report.py
```

Analysis is not idempotent: preserve a failed attempt before any corrected
rerun. Postprocessing code is not part of the pretraining freeze. Audit
failures must be investigated and recorded without changing selected models.
Inspect `figures/oof_utility.png`, all gates, both K metrics, rescue/harm,
fit/monitor/OOF gaps and costs. The independent audit is a separate numerical
implementation in the same session, not another human or agent review.

Completed prerequisites: preflight, full base identity audit, cached K100
return/mask audit. Training sources and 920 inherited files were frozen.
Fresh-source work checked only metadata: no new test payload, GT, or search.
`theory_bounds.md`, `inference_cost.md` and `prior_work_addendum.md` clarify
limits and prior-work overlap without modifying the frozen experiment.

## Conditional Boundary

- Primary gate pass: freeze exactly one candidate; complete untouched-source
  audit and power-based sample lock BEFORE fresh query payload or labels,
  then native parity and serial CPU15/actual-one-thread complete-wall curves.
- Only strong controls pass: compression research opportunity, not deployment.
- All fail: audit first, then stop this version; no seed/depth/threshold/lambda
  expansion, new labels, or fresh test access to rescue it.
- Cached timing covers main search only, not scorer/router or QPS. Historical
  query-out folds are development evidence, not a blind generalization test.
- Default WebVid GT10-soft-t1 / Yandex GT10-hard and production E99 stay fixed.

After the appropriate branch completes, write detailed history card 122,
update `experiment_history/README.md`, `s-experiment.md`, `summary.md`,
`spec.md`, and `s-target.md` by their roles, seal provenance and completed
state, then close the goal. No final result or completion is claimed now.
