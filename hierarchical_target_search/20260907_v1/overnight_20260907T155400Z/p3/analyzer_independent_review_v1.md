# P3 analyzer independent review

The final analyzer source `a840b060a61061df6e60ae6166cd9a090570ef6ec0002a3ec7c7deea14e4e03e` passes source review and17 small synthetic checks. No actual dataset values or ANN calls were used. Evidence: `analyzer_independent_checks_v2/report.json`.

The parser requires the complete two-dataset, four-model, three-method, L64/128 family with10000 aligned pilot query IDs per cell. Full count/plain results and routes are checked, all five timing rounds retain the count identity, and Fast results/routes/Recall/NDC/MAC must remain stable across all four models. The new runner's frozen Fast manifest/hubs/IDs bindings are accepted and verified.

The eight fixed comparisons use candidate minus reference. Independent RNG-index resampling matched the bootstrap output exactly; all eight contrasts share each dataset/L's resampling indices. The main comparison remains protected λ1_greedy3 minus protected λ0_greedy3 at both L values in both datasets. Ordinary pointwise95% intervals are explicitly exploratory and unadjusted. No automatic gate or deployment claim is produced.

Cross-model timing remains descriptive, with no paired-ratio or confidence-interval inference. The fixed measurement-key parser bug reported by root is corrected in this source and the full eight-invocation fixture passes. The earlier reviewer fixture's bitwise expectation for algebraically equal floating-point differences was replaced by a1e-15 tolerance; direct identical-input bootstrap checks remain bitwise exact. Both intermediate and final checks are retained.

No source fixes remain in this bounded review. Actual-data analysis and the separate structure/search gate are still required.
