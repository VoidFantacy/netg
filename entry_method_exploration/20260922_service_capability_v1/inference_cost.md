# Online work is not free

This is static operation accounting, not a measurement or an implemented native
optimization. The training diagnostic does not produce online QPS.

## Shared Interaction Scorer

Entry encoding B(entry), the response descriptors, PCA-projected entry vectors,
and normalization constants can be computed offline for the frozen H bank.
Every query still needs normalization, a D-by-32 query projection, H-by-32
entry-dependent gated activations and a scalar head, plus the two geometric
cosines over all H raw unit hub/profile vectors. Default fallback then invokes
the original GT10 router; a selected single does not need that router.

The current Python feature path's two full geometric products require 2*H*D
multiply-accumulates per query: WebVid 834560, Yandex 328400. Query projection
adds 32*D; the shared interaction has O(32*H) elementwise/head work. This is not
the sublinear original micro-HNSW route, and input/scoring cost is paid even
when every query falls back to GT10.

Because each K head has two constant geometry coefficients, a future exact
native implementation could precombine those two vector banks per K. That
would reduce two geometric products to one without changing the mathematical
score, subject to floating-point parity validation. It has NOT been implemented
or benchmarked. No estimate here is charged as a measured speed improvement.

## Strong Controls

GBDT evaluates an entry for every H candidate; its trees are diagnostic capacity,
not an assumed cheap route. TabM scores H candidates with 16 ensemble members
and two128-wide blocks. Neither has been compressed, indexed, or measured
inside the original search loop. An advantage exclusive to these controls
would motivate a separate frozen compression study, not direct deployment.

## Break-Even Condition

For the scalar diagnostic, paid scorer cost c reduces the search-only expected
gain by 0.1*E[c]/T, with fallback-routing differences accounted for separately.
For a 5% QPS improvement at matched Recall, total new time must be <= old/1.05.
Cached main-search savings must first exceed the new routing/scoring overhead.
Fixed-L Recall changes and cached microtiming cannot establish this inequality
on a matched-Recall frontier. Conditional evaluation must keep every budget
point and include the entire online action path.
