# E119 cached capability pilot: frozen protocol

Lock before fitting. Original E118 data and default remain immutable.

## Roles and Representation

- Reuse ONLY the two E118 fit4096 full-H K1/K100/L128 label matrices, raw queries,
  source IDs, real hub vectors and original GT10 profiles. Old direction and
  accept payloads are not new validation data. No new search/GT/graph/K10.
- Seed 20260922. Four outer query folds, 1024 rows each. In each outer training
  set, a deterministic permutation assigns 1024 support, 1792 fit, 256 monitor.
  These four sets are byte- and row-disjoint. Every outer query is scored once
  per method. All rows are historically exposed: OOF is development evidence.
- PCA32 is fitted on support+fit queries only. KMeans16 is fitted on support
  queries only, n_init=1, max_iter=50, fixed seed. For each entry, capability is
  the 16 cluster means of four deltas (R1,R100,T1,T100), shrunk by 16 support
  pseudo-observations toward that entry's support-global mean. Empty clusters
  use that mean. Center capability at that mean. No target-query responses.
- Geometry: PCA32 projections of unit real hub and unit GT10 profile, plus
  four support-global response means. Capability adds the 64 centered cluster
  means; geometry-only replaces those coordinates with zeros. Both have the
  same parameter count and identical scalar global-response supervision.
- Query input: unit raw query, standardized on support+fit only. Pair geometry
  adds exact cosines to the real hub and the GT10 profile. Standardization of
  entry descriptors uses the support-derived H bank, not outer responses.

## Fixed Models and Training

Four primary arms: GeomMSE, CapMSE, GeomRank, CapRank. Shared scorer has 32
interaction coordinates: u=Aq, v=B(entry); z=ReLU(u+v+u*v). Two linear heads
predict utility residuals above support-global utility, plus two cosine terms.
Entry encoding is offline. Geometry masks capability, with matched dimensions.
Default score is exactly zero. Highest strictly positive single wins; equal
scores choose lower real base ID. No top-C screening or learned threshold.

MSE: all H utility targets, equal query and K weight. Rank: per query/K use the
true best action including default; compare with all H+1 alternatives using
true nonnegative utility gaps times softplus(-(s_best-s_other)/0.1), normalized
by total gap. Add 0.1*MSE to anchor scale/default. This is a deliberate composite
loss, not a claim of identical pure-MSE calibration or universal consistency.

AdamW lr0.002, weight_decay0.0003, batch64 queries, at most64 epochs, seed fixed.
Monitor every4 epochs; select max mean actual selected utility over the two K,
ties prefer earlier epoch. Stop after4 nonimproving monitor checkpoints.
Save all fit/monitor learning curves. No outer-fold checkpoint selection.

Controls: GT10 zero, support+fit best fixed action; nearest support cluster's
response mean (UniRoute-style nonlearned control); E118 ReLU64 ridge alpha10
refitted on the SAME fit rows, with no outer labels in its normalization.
The inherited direction dictionary is historically exposed and labelled as an
E118 diagnostic reference, not a clean newly learned fold representation.

Two stronger fixed controls use capability and the SAME query/pair information:
sklearn HistGradientBoostingRegressor (one per K, 200 iterations, 31 leaves,
learning_rate0.05, l2_regularization1, min_samples_leaf100, early_stopping=False);
author TabM, k16, two128-unit blocks, dropout0.1, no numeric embeddings,
AdamW defaults above, batch2048 pairs, max16 epochs, monitor each epoch with
patience3. Fit uses all query-entry pairs with uniform query/action weighting.
TabM trains each ensemble member independently and averages predictions for
decisions. Monitor is whole-query; sklearn does not randomly split pair rows.
These are bounded controls, not exhaustive tuned estimates of each family.

## Checks, Costs, and Gates

Before training: validate all shapes/ranges/finite positive times; independently
score saved top1 IDs against GT1 and popcount masks against K100 counts;
verify old source identities, real IDs, source rows and query-byte disjointness.
Synthetic tests cover default/ties, reward accounting, scalar/batched forward,
loss gradients and support-only representation invariance to outer labels.

Report per query: action, actual two-K Recall deltas, rescue/harm, normalized
time deltas, selected utility, oracle regret, fit/monitor/OOF gaps. Bootstrap
whole queries, never pairs or timing repeats. OOF bootstrap intervals are
descriptive conditional intervals because training folds overlap and these
queries are historically exposed; they are not final significance evidence.
Report all folds and both datasets, all six configurations, and MSE secondarily.

Proceed to a frozen native candidate only if the same primary configuration
has positive mean utility on both datasets, descriptive95% lower bounds above
zero on equal-K query-average utility, and no K's mean Recall loss exceeds
0.1 percentage point. H1 additionally needs the prespecified paired contrast;
H2 additionally needs superiority over the matched additive reference. A
strong-control-only pass opens a compression research result, not deployment.
Do not require every fixed-L Recall CI to be positive. Do not pick a dataset
or K after results. No post-OOF tuning, candidate/depth/seed/lambda expansion.

Conditional next stage: freeze exactly one primary configuration by equal
dataset/equal-K OOF utility (ties lower model name). Audit fresh source rows and
query-byte duplicates against registered and historical use; estimate sample
size from paired development variance BEFORE new labels. Native scorer parity
and CPU15/threads1 complete online wall must include representation/scoring,
fallback GT10 routing, original search and output. Use true K1/K100 and the
E118 five-budget contract, all methods serial and no concurrent training.
Target >=5% QPS at prespecified common Recall regions with uncertainty; one
threshold jump is insufficient. No clean source means no blind generalization
claim. Stage-two exact sample/budget lock must precede any new test payload.

Resource cap: offline single process, <=8 numerical threads, 12h total, 40GiB
RSS, <=2GiB new disk, >=6GiB free. No concurrent performance jobs. Package code
installed only into this version's vendor directory; old environment untouched.
Failure/timeout artifacts retained. Inspect implementation/optimization before
attributing a negative result to the hypothesis. Default changes: forbidden.
