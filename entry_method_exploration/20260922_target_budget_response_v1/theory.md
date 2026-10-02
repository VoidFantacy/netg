# Budget-conditioned decision information

## Response, context and decision

For one fixed K, let r_L(q,a) be the Recall returned by the unchanged finite-beam search with routing action a, and define d_L(q,a)=r_L(q,a)-r_L(q,0). The baseline action 0 is original GT10. Candidate pool size, action IDs and search semantics are part of this response definition. Changing L changes the response function, even though the online routing features and underlying graph do not change.

The relevant object for a feature-only decision is m_L(x,a)=E[d_L(q,a)|x], not the outcome of the best action after seeing GT. This distinction separates three possibilities: there is little action-family headroom; useful actions differ across budgets; or there is headroom but available query information does not predict it. Changing an optimizer cannot resolve all three.

## A simple transfer bound and its limits

For any fixed action family, write epsilon(q)=max_a |d_H(q,a)-d_l(q,a)|. If a_l is optimal at the lower budget l, then

    max_a d_H(q,a)-d_H(q,a_l) <= 2 epsilon(q).

Insert d_l for both actions and use d_l(q,a_l)>=d_l(q,a_H). If a learned lower-budget action has regret eta_l, the right side becomes eta_l+2epsilon. The identical argument holds for conditional means. This is an elementary bound, not a novelty claim. It is useful only if the response drift is small on relevant actions, which must be checked. A large bound does not prove large actual regret.

Even componentwise nondecreasing Recall across budgets does not preserve action preference: for [default,alternative], lower Recall [.2,.4] and higher Recall [.9,.8] reverse the preferred action. These numbers form an abstract response-table counterexample, not a constructed NSG trace. Real finite-beam outputs need not themselves be nested; all empirical reversals are measured rather than inferred from this example.

## Why the information control is consistent with its stated target

The fixed nearest-query estimator takes a local arithmetic mean of actual action-minus-default Recall. For a fixed neighborhood and random query drawn from that neighborhood, it estimates the same conditional mean used by the Recall decision rule. It does not normalize away query-specific benefit magnitude. This alone provides neither a finite-sample guarantee nor nonparametric consistency in dimension200/512. k=floor(sqrt(n_fit)) gives one frozen locality scale, not a proven adequate sample size for these datasets.

TargetKNN vs LowKNN holds query representation, neighbor weights, action domain and policy rule fixed, changing only the budget of the response labels. TargetFixed tests whether query conditioning adds more than a globally preferable strategy. The single fit-row permutation preserves action/K response marginals while removing the query-response link. It does not establish a causal mechanism or eliminate every possible confound.

Lookup over thousands of training queries and exact routing banks is not a cheap online scorer. A positive result would establish only a development information signal and justify studying a cheap structural implementation. A negative result cannot bound all representations or all-H action selectors.

## Prior work and applicability

[Gupta and Roughgarden, A PAC Approach to Application-Specific Algorithm Selection](https://arxiv.org/abs/1511.07147) models algorithm selection statistically and studies capacity conditions. It supports treating the strategy family and input distribution as explicit parts of the learning problem; it does not make an exposed-query nearest-neighbor selector generalize automatically.

[Prokhorenkova and Shekhovtsov, ICML2020](https://proceedings.mlr.press/v119/prokhorenkova20a.html) analyzes graph search, shortcut edges and dynamic candidate lists under specified geometric regimes. Those assumptions do not automatically hold for this fixed raw-IP NSG and OOD queries. We do not borrow a metric or asymptotic guarantee for the measured finite-beam system.

[Mishra et al., ICLR2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/dd5d65bf0c81b539f00f57850c1774ad-Abstract-Conference.html) introduces a random-walk framework for graph ANN and a deletion method preserving hitting-time statistics. Its published abstract concerns dynamic updates, not our fixed-graph entrance decision. We reviewed that scope but have not derived a valid reduction from deterministic finite-beam search to its hitting-time objective; no such guarantee is claimed here.

E107 already measured the fixed actions used here, E117 tried an L128 four-action shallow selector, E118 had complete transfer curves through L800, and E119 tried strong response scorers. The new experiment's difference is narrowly defined: fill the missing target-region response points and directly separate budget-transfer error from local cross-query prediction error. Neither kNN nor budget conditioning alone is a paper contribution.

## Bridge to performance remains conditional

The primary practical objective remains complete time at 90% Recall, separately for each K/dataset. The local dR/dlogT argument in record123 explains why quality gain may permit a lower global fixed L; it is not an exact time conversion. This study measures true Recall and graph distance counts, not complete time. It cannot prove that extra routing or prediction is paid for, nor that a new rule reaches 90% on genuinely unexposed queries. Conditional information GO must therefore precede, not replace, cheap-method derivation and a new complete-cost protocol.
