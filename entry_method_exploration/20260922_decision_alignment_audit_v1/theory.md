# From learning loss to entry decisions and Recall-QPS

## 1. The object to learn

Let x contain only online-observable information and a=0 be the original GT10 policy. For fixed graph/kernel/K/L, define U_a = R_a-R_0-lambda*(T_a-T_0)/T_ref. The Bayes action for this scalar objective maximizes m_a(x)=E[U_a|x], including m_0=0. A hindsight oracle E[max_a U_a] is generally larger than E[max_a E(U_a|x)]. An oracle is not transferable supervision by itself. A restricted representation may pool different deterministic queries; this is not proof of irreducible randomness conditional on the complete raw query.

For exact greedy choice from scores s, decision regret obeys

    m_best - m_chosen <= 2 max_a |s_a-m_a|.

This follows by inserting s_best and s_chosen and using s_chosen>=s_best. It concerns conditional means, not noisy observed labels. Average per-action MSE controls this only through an action-count-dependent bound (at most 2 sqrt(H * average squared error) when default is exact). Low average MSE can coexist with wrong extreme selections. Selected-score optimism alone does not identify its cause.

Squared loss is conditional-mean consistent for unrestricted predictions. That does not solve finite-sample generalization, representation approximation, maximum selection, or scoring cost. The failed E119 MSE/GBDT/TabM arms cannot be explained by a flaw exclusive to Rank.

## 2. A counterexample for the actual E119 Rank objective

For one nondefault action, let U=1 with probability 0.1 and U=-0.01 otherwise in one indistinguishable context. E[U]=0.091, so the correct expected-utility action is to switch. E119 normalizes each query's pairwise loss by that query's total gap, cancelling the magnitude of the harm/benefit in this binary case. Its complete population objective, including the MSE term, is

    F(s) = .1 softplus(-s/.1) + .9 softplus(s/.1)
           + .1[.1(s-1)^2 + .9(s+.01)^2].
    F'(s) = (sigmoid(s/.1)-.1)/.1 + .2(s-.091).

F is strictly convex; F'(0)=3.9818 and its unique optimum is about -0.2131393372. Deployment chooses default, contrary to the expected-utility optimum. The test executes the original source function as well as an independent scalar implementation. This is a general-consistency counterexample, NOT a runtime bug or proof that it caused all E119 failure. The original protocol already avoided a universal consistency claim. Removing normalization repairs this binary sign mechanism but is not a proof for arbitrary multiclass pairwise objectives.

## 3. Bridge to matched Recall

The performance objective is min T(pi,L) subject to R_K(pi,L)>=rho, with T the entire query pipeline. Near a differentiable baseline operating point with R'(L)>0, a small entry intervention (delta_R, delta_T), scoring overhead c, and a global fixed-budget adjustment give

    delta_L ~= -delta_R/R'(L)
    delta_T_matched ~= delta_T+c - [T'(L)/R'(L)] delta_R.

When T'(L)>0, dividing by T yields the local equivalent utility delta_R-lambda*(delta_T+c)/T, with lambda=dR/dlogT. This is a first-order, local bridge, not an exact property of discrete finite-beam curves. Nonmonotonicity, large changes, and timing noise require actual complete curves. E119's T_ref is a support-set baseline mean and its labels exclude router/scorer; it cannot certify this objective.

Use E103's already exposed default curves to describe the 90% region: Web R1 L640-800, Web R100 L1120-1250, Y R1 L96-128, Y R100 L200-256. Their adjacent empirical dR/dlogT are approximately .066, .085, .089, .108. These are descriptive secants, not learned causal derivatives. Lambda=.1 is not orders of magnitude wrong; changing lambda is not an established remedy. The serious mismatch is treating one L128 proxy gate as evidence about all target budgets and omitting complete online costs.

## 4. What the papers do and do not justify

[Liu and Grigas, NeurIPS 2021](https://proceedings.neurips.cc/paper/2021/file/b943325cc7b7422d2871b345bf9b067f-Paper.pdf), Theorem 2.1, gives SPO+ Fisher consistency under continuous, centrally symmetric conditional costs, a suitable feasible set, and a unique mean optimum. The risk bounds add further distributional conditions. Our sparse, asymmetric, baseline-anchored action outcomes do not automatically satisfy them. Its least-squares calibration discussion supports a conditional-mean regret bridge, not guaranteed finite-query or QPS improvements. We do not adopt SPO+ by name.

[Mandi et al., ICML 2022](https://proceedings.mlr.press/v162/mandi22a.html) relates decision-focused learning to pointwise/pairwise/listwise ranking of feasible solutions. It motivates checking decision order and magnitude, but does not validate our arbitrary normalized composite loss.

Earlier E119 research already compared ALORS, bilinear ranking for algorithm selection, UniRoute, RouteLLM, and TabM. Latent service descriptors, interaction networks and strong tabular scorers are prior ideas, not an ACSG contribution. E25 already tried cost-weighted binary profile gating; E32/E36 directly optimized policy rewards. This version claims only a sharper diagnosis and objective contract, not a novel scorer.

## 5. Falsifiable next decision

Action ranking and query-level switching are distinct. A scorer can select better-than-average entries but still propose entries worse than GT10, or rank switch benefit in the wrong direction. The fixed cache audit distinguishes these cases. Only positive, stable, predeclared confidence discrimination supports the minimal monitor-only calibration control. A failure stops that specific reuse path. A future high-Recall method needs new, target-budget evidence and a concrete cheap information/structure hypothesis; merely repairing a loss is not sufficient.
