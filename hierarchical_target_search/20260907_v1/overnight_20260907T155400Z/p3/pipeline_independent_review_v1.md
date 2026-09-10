# P3 pipeline independent review v1

Source review found one required input-binding fix in `run_p3_evaluation.py`; the portal finalizer passed source review and its existing synthetic self-test. No dataset vectors or GT were read and no ANN calls or new experiments were run by this review.

The finalizer supplies every schema2 field required by the evaluator, keeps geometry fields absent, validates all 256 complete leaf caches and their GT10 order/target-leaf masks, independently rebuilds greedy unions with Python sets, and matches the final 768 portal IDs. Both fixed portal rules are written; empty-query fallback and negative proxy differences remain visible. The existing controller self-test passed with no real data or ANN calls.

The evaluation runner matches the preregistered four-model order, three methods, pilot10K, L64/128, K10, Fast m3, 16 threads, count1/timing5, and warmup128. It requires the accepted evaluator/protocol gate, checks model/fit/graph inputs, retains incomplete logs, and marks between-model wall comparisons descriptive. Its terminal status describes completed measurements only.

Required fix R1: lines65–71 and113–118 trust the paired Fast manifest without checking the actual `hubs_file`/`ids_file` SHA256 values. Shape-valid substitution of these files could change the matched baseline without changing the manifest. No such substitution was observed. Before real P3 performance, verify `fast.input_audit_sha256` against the supplied audit, verify the two actual Fast raw hashes, record those bindings, and recheck the small files plus Fast manifest before every count/timing cell. This fix needs source verification, no extra ANN run.

Full10K count/plain alignment and all fixed contrasts remain obligations of the later result analyzer. This source review does not establish P3 performance or gate passage.

Source hashes:

- finalizer: `d1945203dc99e7027ebdc9a414a6b1303df5da0988b491dcc15ac1b30f537a7e`
- evaluation runner: `84a3567f23304d8399faad1f2f5dd4485b86299febd5157105691b545cca746e`
- evaluator: `cf40032dc469c08840e409af23bd503e1ad6571184351a2694776247e21d1316`
- prober: `9137ae4ebc3b4a3c437fb171b0ffc1b5857d5ea1b610a674a59bf46c8af78385`
- protocol: `fea64bc3c6a8046378849f55508198dcfd9a00df880a74e9d93cf22d051a418f`

Exact paths, the self-test log hash, findings, and scope are recorded in `pipeline_independent_review_v1.json`.
