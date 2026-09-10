# Independent selection, statistics and interpretation review

2026-09-08. Scope: the statistical/diagnostic portion of `tools/analyze_results.py`, its shared selection/interval helpers, and completed `analysis/v2`. Input and runner validity are covered by the separate preparation/execution reviews. This reviewer did not edit the analysis implementation, run ANN, train a model, or create additional hypotheses/parameter sweeps.

**Verdict: PASS for analysis/v2 arithmetic and the specified 32-comparison family.** No unresolved blocking selection, tie, unsigned-arithmetic or confidence-interval implementation error was found. Use v2 for reported values; v1 is a preserved earlier analysis whose descriptive neighbor NDC subtraction and exact-C8 NDC handling were subsequently corrected.

## Independent numerical verification

The reviewer independently read the completed result matrices and reproduced all 32 primary per-query contrasts without importing the analysis script. Single-entry representatives were selected using a separate tuple comparison over eligible optimal IDs: maximum hitcount, then minimum source-query NDC, then minimum real base ID. The exact-C8 comparison used the top eight exact prototype ranks, not the approximate C8. All 32 mean Recall differences and declared sample counts match v2.

All 512 neighbor-transfer CSV rows across two datasets and two L values were independently checked. For both nearest and random fit sources, the selected real ID matches the source-only rule, target Recall matches that ID's target matrix cell, A0/A1 target means average every member of the source set, and the separately labeled target-best value is the target maximum over that source set. The corrected signed target-NDC differences match the raw matrix values. Exact-C8 oracle NDC equals the minimum NDC among the highest-recall entries within that exact shortlist.

The four fixed PCG64 streams were independently regenerated with a different chunk size of 250, versus 128 in the implementation. All draw-index SHA256 values match. All 128 saved interval endpoints—ordinary and Bonferroni-adjusted bounds for 32 comparisons—match the independently calculated percentile endpoints within `1e-14` Recall. All eight v2 completion-manifest artifact hashes and sizes match.

- Final analysis script SHA256: `738349120addbbe45df340a7cc2b6586599dcff08547f1f2b06b69e46821b356`.
- Final `analysis/v2/analysis.json` SHA256: `d4714a363e271ccc92f964b3f11e6c6418a903f15b92796c6d8f3fff6582dc16`.

## Selection and arithmetic review

`best_single` retains the maximum-recall eligibility set before applying source NDC and real-ID ties. It does not use the target query to select a nearest/random source representative. `best_variant` applies maximum hits and minimum actual NDC, then the fixed metadata-column order. Its supplied pair/triple column lists are in metadata order. These cost/ID tie rules choose reproducible representatives; they do not replace the separately reported set-valued recall optimum.

A0 contains all entries with maximum hitcount. A1 contains entries at most one GT10 hit below maximum and uses signed int16 arithmetic, including when the maximum is zero. The analysis retains the potentially negative `basin - Fast1` term and explicitly marks the decomposition as noncausal. The all-H, exact-C8, Fast-C8, pair and triple optima refer to different restricted action sets and remain separately labeled.

The true pair/triple masks and independent-single union masks refer to the same query's GT10 bit positions. Lost and new hits are counted separately and their signed difference is checked against the actual-minus-union hitcount difference. The independent-union and sum-single-hitcount selectors use observed singleton labels, so they are offline diagnostic selectors. They are not deployable feature-only alternatives, and independent searches do not have the same cost as one shared-beam joint search.

Cross-L transfer evaluates a source-L representative/set using the target-L result matrix. It reports source-set mean and target-best oracle separately, together with set intersections and a common-entry oracle regret. Changes in a unique tie-broken representative therefore need not imply that the query lacks a common good entry at both budgets.

The pilot-only density control uses already available pilot labels and is explicitly descriptive. It is additional post-hoc context, not a new primary test or a new independent evaluation set. GT-overlap strata also use labels for description; they must not be presented as observable query-only deployment features.

## Statistical contract

The exact primary family is two datasets × two L values × eight predefined Recall contrasts. Seven contrasts use 512 paired target queries; the nearest-minus-random contrast uses 128. Within each dataset, the 14 contrasts on 512 queries share resampled row indices across both budgets, and the two 128-query contrasts share their own row indices. The generator, dataset/group order, 10,000 resamples and draw-stream hashes are recorded. Differences are taken within each query before bootstrapping.

Ordinary endpoints use quantiles 0.025 and 0.975. The 32-family Bonferroni adjustment uses `0.05 / (2 * 32)` and its complement. Correlated contrasts do not invalidate the Bonferroni adjustment; separate 512/128 draw groups do not imply that these groups are independent experiments. NDC summaries, ranks, coverage, strata and action-level interaction statistics do not add unannounced significance tests.

The intervals are percentile-bootstrap approximations conditional on the fixed graph, fitted images, fit corpus and historical pilot design. They are not exact finite-sample coverage guarantees or uncertainty over independent graph/model builds. With 10,000 replicates and tail probability 0.00078125, each extreme Bonferroni endpoint is supported by roughly eight tail replicates; a bound extremely close to zero should not be treated as decisive evidence. No additional resampling was requested or performed beyond the fixed audit reproduction.

## Required interpretation boundaries

- A small mean exact-minus-approximate difference in these paired experiments supports a limited role for approximate retrieval here. A confidence interval spanning zero does not prove exact equivalence or that ANN can never matter.
- A large remaining all-H oracle gap after exact prototype ranking locates headroom beyond current approximate lookup. It does not alone identify whether representation, surrogate labels, finite-beam graph behavior or another downstream selector is the unique cause.
- The signed GT1-basin decomposition is an arithmetic comparison of alternative entries. Its terms are not two nonnegative error rates, and dividing them by total regret does not produce causal percentages.
- The nearest-source comparison tests local transfer from the fixed 20K corpus under the chosen query geometry. Weak transfer does not establish general unlearnability, an information-theoretic lower bound, or failure of every richer representation/model. Strong target-best set transfer is also optimistic because it uses target labels.
- The field `uniform_random_entry_hit_probability` is the probability that a uniformly drawn hub belongs to A0/A1. It is not expected Recall@10 or the probability of returning any GT10 neighbor. Zero-recall queries have all hubs in A0, so set membership needs the reported saturation strata.
- Report all 32 planned contrasts. A small positive adjusted bound in one cell must not be promoted into a cross-dataset method conclusion. Oracle gains, candidate disagreement, NDC savings and these instrumented wall times are not Recall–QPS or deployment improvements.

The numerical checks support using analysis/v2 for the final diagnosis, with these limits retained in the report and handoff documents.
