# Response-defined entry capability: research contract

2026-09-22. User-authorized successor to E118. This is a testable research
hypothesis, not a proven improvement or a claim of paper novelty.

## Problem and Bridge to Search

Freeze the original graph, raw-IP metric, main search, L=128, and real entry IDs.
An action is one of all H single entries, or the ORIGINAL query-dependent GT10
three-entry action. It is not a sum of single-entry outcomes. For K in {1,100},
use the measured response

    u_K(q,a) = R_K(q,a)-R_K(q,GT10)
               -0.1*(t_K(q,a)-t_K(q,GT10))/T_K.

T_K is the mean baseline time on the fold's support queries. These cached times
exclude a new scorer and are labels, not deployment QPS. Let I(q) be available
pre-search information. The full-information supervised decision is
argmax_a E[u(q,a)|I(q)], including default value zero. No propensity correction
or sequential RL is needed: every candidate action has measured feedback.

There are four separate obligations: useful oracle opportunity; observable
capability representation; query-out generalization; and paid online cost.
None implies the next. Under uniform conditional-score error epsilon, the
plug-in decision loses at most 2*epsilon against the information-constrained
Bayes action. Proof: add and subtract the two predicted scores and use their
argmax ordering. This elementary bound is NOT novelty. The oracle gap includes
irreducible information loss, not just model error. MSE averaged across H can
miss the extreme errors that determine the selected action.

If the new scorer costs c(q), its measured gain in this scalar objective loses
0.1*E[c]/T. At matched Recall, 5% QPS improvement requires new total mean time
at most old time/1.05. Fixed-L utility cannot establish that frontier claim.
Any quality-speed exchange therefore requires the complete budget curves.

## Papers and What Transfers

- [UniRoute, 2025](https://arxiv.org/abs/2502.08773): represent a service by its
  measured responses on representative inputs. We use per-cluster response
  differences on disjoint support queries. This borrows the representation
  principle, not its dynamic-LLM theorem: our pool is fixed and time depends on
  the query. A new entry would need support labels; no zero-label claim.
- [Decision-focused learning through learning to rank, ICML 2022](https://proceedings.mlr.press/v162/mandi22a.html):
  distinguish response fitting from choosing an action. Compare regression
  against gap-weighted pairwise logistic loss with the same scorer and labels.
  Ranking is a control, not an assumed universal improvement.
- [DCNv2, WWW 2021](https://arxiv.org/abs/2008.13535): explicit feature products
  motivate a small shared gated interaction. Our model below is NOT a DCNv2
  reproduction. Fixed query ReLUs with separate entry coefficients, as in
  E118, do not provide entry-dependent activation boundaries.
- [TabM, ICLR 2025](https://github.com/yandex-research/tabm): an independently
  implemented efficient neural ensemble is a capacity control. Use the author
  package, not an unverified reimplementation. GBDT is the other strong control.
- [RouteLLM](https://arxiv.org/abs/2406.18665) already uses preference-trained
  routing. A linear two-tower scorer reduces to affine entry profiles; changing
  the model name is not a new method.

## Historical Differences and Limits

E07 used sparse Fast-top32 real-response listwise learning with diagonal
query/profile interactions. E23 used measured joint triples and gap-weighted
pairwise loss but exported static W. E16 transferred partial top8 utilities by
64-neighbor averaging; it did not test every possible neural distillation.
E36 already used a query/action MLP with real reward. E104 transformed queries
against a fixed profile bank and known triple teachers. E118 used all-H real
K1/K100 labels but independent entry outputs of fixed additive ReLU64 features.
The new hypothesis is specifically response-defined entry sharing, disjoint
support construction, and entry-dependent shared interactions. Full-H cached
actions remove the old unlabelled-candidate problem ONLY for single entries.
These distinctions do not by themselves establish publication novelty.

## Two Falsifiable Hypotheses

H1: support-response capability descriptors improve query-out selected utility
over geometry plus global entry response means, at identical model size/loss.
Prediction: the capability-minus-geometry contrast is positive across both
datasets and at least three of four outer folds per dataset for one fixed loss.

H2: the shared nonlinear interaction can convert label information into better
query-out decisions than the matched additive E118 control. Strong GBDT/TabM
controls distinguish limited cheap-scorer capacity from absent observed signal.
Training improvement alone does not pass either hypothesis.

Counterexamples: IID random action payoffs have an oracle but no observable
gain; response clusters that mix opposing entry preferences cancel information;
entry-dependent gains can be too rare for the available support; useful scores
can cost more than the saved search; changes in query distribution can break
the conditional response law. No arbitrary-OOD guarantee is claimed.

## Interpretation Before Running

Cheap capability model works: freeze a candidate and pay for native evaluation.
Only strong scorer works: record a compression opportunity, not a deployed win.
Only fit works: stop this representation/data-support version, not all models.
Neither fits adequately: report an optimization/capacity-limited diagnostic,
not proof that the response signal does not exist. All valid controls fail
query-out: stop this hypothesis version without seed/depth/threshold search.
