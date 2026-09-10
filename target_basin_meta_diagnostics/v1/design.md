# Confidence-attentive target-basin views v1

The image's directly compatible idea is model-based memory/attention over metric prototypes, not
MAML/Reptile.  The two datasets are not enough to define a credible meta-task distribution.

Frozen diagnostic:

- Keep the current three-view target-basin candidate construction and seed-20260828 rank-0.
- For view `v`, compute confidence `m_v = score_v(top1) - score_v(top2)`.
- Rank the remaining union candidates by `score_v(q,e) + alpha * m_v`, merging duplicate IDs by max.
- Evaluate `alpha in {-2,-1,-0.5,0,0.5,1,2}` on the 10K `drl_train` split only. `alpha=0` must
  reproduce the current ensemble routes exactly.
- A nonzero alpha advances only if Recall and frozen utility are no worse than alpha=0 on WebVid and
  Yandex at both `L=64/128`, and at least 1% of route sets change.
- Validation is opened once for the train-selected alpha only. Held-out is forbidden.

This is described as a meta-learning-inspired attention diagnostic, not as a trained meta-learner.
