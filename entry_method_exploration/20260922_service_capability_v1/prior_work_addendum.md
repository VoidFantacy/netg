# Algorithm Selection Is an Important Prior

Added during the locked E119 run. This changes attribution and interpretation,
not any model, feature, data role, objective, or acceptance gate.

- [ALORS, Artificial Intelligence 2017](https://www.sciencedirect.com/science/article/pii/S0004370216301436):
  collaborative filtering represents algorithms and instances through their
  performance matrix; a nonlinear map from observable instance features handles
  new instances. Therefore, performance-defined capability plus a learned query
  map is not itself a new framework. The publisher abstract was accessible via
  search; direct full-text fetching returned HTTP 403. No full-paper theorem
  claim is based on that abstract.
- [Bi-linear Learning to Rank for Algorithm Selection, published online 2020](https://link.springer.com/article/10.1007/s41060-020-00229-x):
  directly learns a bilinear instance/algorithm performance scorer using a
  ranking loss, and explicitly considers selector inference time. Ranking,
  latent candidate factors, and charging scorer cost are also established ideas.
  Its TOPK portfolio evaluation does not establish finite-graph joint-entry
  utility or allow us to assume additive gains from composing new entry sets.

## ACSG Research Gap, Not a Novelty Claim

The concrete unresolved question is whether cheap observable query/entry
information predicts *relative to the existing dynamic GT10 policy* a useful
finite-search decision, across unseen queries and after all online costs.
E119 tests one support-derived descriptor and a bounded scorer family against
same-supervision controls. It neither reproduces ALORS/BLR nor demonstrates a
new algorithm-selection paradigm. A paper contribution still requires an
ANN-specific mechanism or result beyond applying those established ideas.

Together with UniRoute, decision-focused ranking, DCNv2 and TabM in
[research.md](research.md), these sources motivate three distinct questions:
what information describes response, which loss preserves valuable decisions,
and what scorer can be executed cheaply. A stronger scorer answers none of
the other questions automatically.
