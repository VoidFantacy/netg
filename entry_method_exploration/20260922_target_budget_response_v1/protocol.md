# E120: Target-budget response and information study

User-authorized continuation of the next-stage plan, 2026-09-22. No default change, no revival of E119. This is a bounded response study, not a claim of a new algorithm or an end-to-end speedup.

## Question and Known Evidence

E119's complete all-H labels exist only at L128. E107 has eight fixed routing strategies at K1 L64/128/256/400/800 and K100 L128/256/400/800, on the same 4096 historically exposed E105 queries per dataset. E118 has six frozen strategies through L800 on a different exposed query set. E103 identifies default 90% Recall regions but cannot supply unmeasured action labels. No cross-dataset/query/kernel concatenation is allowed.

Hypothesis H-transfer: choosing a good action at L128 preserves at least 80% of the finite-family hindsight Recall gain at the intended budget. This is a testable supervision-transfer hypothesis, not an assumption of monotone beam outputs. Failure motivates budget-matched supervision, but does not prove that it is learnable or novel.

## Immutable Actions and Inputs

Reuse exactly E107's queries, GT100, raw-IP base, NSG, profiles, real IDs, entry order, and search kernel. Methods: NSGFixed1, UnitHub1/3, GT11/13, GT101/103, DefaultANN. The six exact strategies are unchanged diagnostic actions; their scoring cost must not be hidden in a future deployment claim. Eligible selection family in fixed tie priority is DefaultANN, UnitHub1, UnitHub3, GT11, GT13, GT101, GT103. NSGFixed1 is a control, not an action used to inflate the current-H oracle. Default wins utility ties.

All 4096 queries are previously exposed development. No new GT, new query payload, held-out access, profile fit, graph build, kernel/expansion/stopping changes. Every configuration uses a fixed L. New code is an isolated copy of E107, with only the evaluator's allowed upper L bound raised from 800 to 1250. Kernel sources remain byte-identical.

## Minimal Missing Measurements

Reuse all 144 E107 points after independently rescoring outputs. Add only:

- Web K1 L640; K100 L1120 and L1250.
- Yandex K1 L96; K100 L200.

All eight strategies at each missing point: 40 points. Main queries: 4096, full count/plain bit equality, 327680 NSG calls. Smoke: first16 queries, each missing point plus K1/K100 L128, count/plain/linked-E99 equality, 3456 NSG calls. Total planned NSG calls 331136; hard limit 335232, repair reserve 4096 only after diagnosing an identity/implementation error. No parameter tuning or extra outcome-selected points. The native program independently restores DefaultANN against E105 at every new point and L128 exact3 against E106. Route IDs must agree with E107 across all budgets.

CPU15; threads=1 including OMP/OpenBLAS/MKL/NumExpr; actual native process tasks and affinity monitored. Serial jobs, no concurrent training/performance jobs. Per-job 1800 seconds, total query jobs at most 3600 seconds; RSS40GiB, new artifacts <=1GiB, free disk >=6GiB. Failed job retains its reservation/output; no automatic retry. Performance QPS is not measured by this count/plain diagnostic. Main-search distance counts are work descriptors, not time or QPS.

## Fixed Response Analysis

For every old and new K/L point, independently score returned IDs against actual top-K GT, record all method recalls, target membership masks, per-query rescue/damage, distance counts, and entry identity. Retain the entire matrix, not just successful queries.

At each dataset/K target lower and upper endpoint, compare to L128:

1. Finite-family Recall oracle relative to DefaultANN, deterministic tied winner, and its domain limitation.
2. Recall of the L128 hindsight winner transferred to the target budget. Report achieved gain, oracle gap, gain-retention ratio (undefined if target oracle gain=0), and per-query gain/harm sign changes.
3. Tie-aware overlap between low and target optimal-action sets; raw winner agreement is insufficient.
4. Query bootstrap 5000 draws, seed20260922, paired differences, descriptive 95% intervals. Endpoint dependence and historical exposure are disclosed. No new bin or subgroup rules are selected.

Primary upper endpoints: Web K1 L800/K100 L1250; Y K1 L128/K100 L256. Also report the complete lower endpoints and old budget grid. A low-to-high regret bound and its synthetic counterexample are checked before interpretation.

## Conditional Cross-query Information Control

Run one fixed nonparametric information control only if every primary upper endpoint has finite-family oracle Recall gain >=0.0025 (0.25pp), and H-transfer fails at one or more *different-from-128* primary endpoints. The 0.25pp threshold is a declared allocation rule for this bounded quality-lever study, not a theorem or a global impossibility bound.

Use original raw queries normalized only for cosine neighbor lookup, not for NSG. Four deterministic query folds (seed20260922), fit3072/outer1024. Each outer query averages the action-minus-default Recall labels of its floor(sqrt(3072))=55 nearest fit queries. Float64 cosine; ties by original source-row ID. No learned embedding, bandwidth/neighbor-count search, tree or neural training. Labels of outer queries never affect neighbor choice or fit predictions. This is label-based prediction, not zero learning cost.

Four fixed rules: TargetKNN (labels at the primary target endpoint), LowKNN (L128 labels), TargetFixed (fit mean per action), ShuffleKNN (one seeded permutation of fit label rows, aligned across all actions and K). Choose the largest predicted delta with default first in ties. All four use the same action family, input information and folds; shuffled control is not a deployable candidate. Do not pool cross-fold model predictions for meta-training.

Information GO requires BOTH datasets: TargetKNN equal-K mean Recall gain positive with descriptive95% lower bound>0; each K mean gain >=0; TargetKNN exceeds TargetFixed and ShuffleKNN in equal-K mean with descriptive95% lower bound>0; and exceeds LowKNN in equal-K mean. Do not replace the nominated rule with a control. If this fails, stop this target-budget/local-geometry hypothesis with no tuning of k/features/seeds/pools. If it passes, this is only an information signal: before any advanced model or deployment, derive a cheap structural implementation and freeze a same-supervision control and complete-cost protocol in a separate version. No complete-wall or blind-test phase is automatically claimed complete.

## Preservation and Completion

Snapshot root documents; hash consumed old sources, input/query/GT/model/cache files and linked libraries. Revalidate base hashes against E105 manifests; preserve graph stat identity and check embedded base samples (no claim of a new complete graph hash). Freeze code/protocol/config before searches; old files are never written. Save costs, all jobs, numerical/identity audit, report, history record and synchronized root documents. Stop outcomes apply only to the tested action family, information and budget scope, not all high-Recall entry selection.
