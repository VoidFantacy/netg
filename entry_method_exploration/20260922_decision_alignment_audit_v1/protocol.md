# Decision alignment audit v1

Authorized continuation, 2026-09-22. This is a retrospective research audit, not a new performance experiment. E119 remains frozen and STOP_CAPABILITY_PILOT. No new E-number is assigned.

## Known Before This Protocol

E119 aggregate OOF results, selected-score optimism, the binary normalized-rank counterexample, and E103's 90% Recall brackets have already been examined. These are NOT preregistered discoveries. The confidence-stratified diagnostics below have not been examined for this version. All queries are historically exposed development material; this protocol does not create a blind test.

## Scope and Objective

Keep the base, raw-IP metric, graph, kernel, candidate entries, original scores, query roles, and each evaluated configuration's fixed L unchanged. Existing labels are actual K1/K100 at L128, with search-only timing. No online GT, new search, new GT, graph construction, performance measurement, or base-model optimization is authorized by the diagnostic itself.

Future performance objective: minimize complete mean query time subject to Recall_K >= 0.90, separately for both datasets and K=1/100; 0.95 is a secondary reported target where reachable, not a substitute winner. The initial planning brackets come from E103. Comparing configurations at different fixed L is permitted for matched Recall; query-adaptive L, expansion, and stopping changes are not. New label budgets must cover the intended operating region. L128 success or failure is not a universal high-Recall gate.

## Fixed Analysis

Read all four E119 outer folds for GeomMSE, CapMSE, GeomRank, CapRank, GBDT, TabM, with original real-ID tie breaking. Reproduce every stored action and selected utility, recall delta and normalized search-time delta. Do not combine OOF rows to train a second-level model: another outer-fold predictor may have trained on the purported second-level test queries.

For each query and K, retain the highest-scoring nondefault entry even when its score is negative (forced candidate), and separately preserve the original score>0/default policy. Report:

1. Original selected prediction vs realized utility; all-pair bias and RMSE. Rank scores are not calibrated utilities.
2. Forced candidate's actual utility percentile among H entries (midrank), utility minus the row mean, and regret to max(0, best actual entry). These measure action ordering, not switch-vs-default discrimination or causality.
3. Forced-candidate score versus its realized utility: Spearman, positive-utility ROC-AUC, and five equal-count score bins within each fold and K. Bins use ascending score then source-row ID; np.array_split makes deterministic sizes. No selected bin is a deployable policy: its cutoffs use outer scores.
4. Primary contrast: highest quintile mean utility minus the remaining 80%, equally averaged over K. Also report the top-quintile utility and each K's mean recall delta. Bootstrap 5000 query draws within folds, paired across K, seed 20260922, percentile 95% intervals. Intervals are descriptive, conditional on already fitted overlapping models and exposed data, not confirmatory population inference.

## Conditional Minimal Control

GBDT is the sole nominated calibration candidate because its previously observed aggregate OOF utility was the least negative among the six new E119 scorers in both datasets. This is explicitly post-E119 model nomination, not unbiased model selection. Other diagnostics cannot promote a different model in this version.

Enter exactly one calibration control only if BOTH datasets have: top-quintile equal-K mean utility >0; top-minus-rest bootstrap lower bound >0; at least 3/4 positive fold contrasts; and each K's top-quintile recall mean >= -0.001. This is an allocation rule for a bounded calibration-only experiment, not a theorem that failed models have no information. No threshold, bin-count, model, seed, lambda, or feature search follows failure.

If eligible: freeze each existing GBDT, predict its original 256 monitor queries (not used by its fixed-iteration fit), fit one increasing isotonic regression of maximum nondefault score onto the forced candidate's realized U for each fold/K. Keep the candidate ID fixed. Switch only when calibrated U>0, otherwise GT10. Compare with original score>0 and the same-monitor constant mean rule. Isotonic uses all monitor values, squared loss, clip outside the monitor range; no hyperparameter or threshold search. Outer1024 is used only for this control's evaluation. This remains post-selection/exposed-development evidence. This contract permits at most 16 scalar isotonic fits and 16 scalar mean controls, no new base-model training. Do not claim new high-Recall or complete-cost gain from it.

If ineligible: stop this calibration-only reuse version, document the actual ordering/discrimination findings and the missing target-budget evidence. Do not infer that all information, models, or high-budget entry selection are impossible.

## Verification and Preservation

Numerically compare the original E119 rank objective (AST extraction of that function only, no old runner imports) with an independent scalar formula and derivative on the declared synthetic distribution. Reproduce E103 bracket/slope calculations from CSV. Independently audit cached action selection, bin partitions, aggregate identities and gate logic. Hash every consumed source/cache plus the E119 final seal before and after. Snapshot the root documents before updating them; do not update the old seal. Save analysis costs separately from online QPS.
