# What a response capability can and cannot identify

This expands the locked reasoning, not the model or gates. It is written during
training and is not a new preregistered outcome prediction.

## A Sufficient Statistical Model

Scope clarification to the frozen research note: for a fixed deterministic
search/GT implementation and full raw query input, Recall is a deterministic
function, so its information-theoretic Bayes noise need not be positive. An
"irreducible information gap" applies to a compressed observation or a genuinely
hidden/random response; it must not be asserted merely because a small scorer
fails. The practical restriction here is a cheap policy class Pi_C plus finite
query support. The useful decomposition is

    oracle value - learned value
      = (oracle value - best value in Pi_C)
        + (best value in Pi_C - learned value),

followed by charging the learned policy's actual overhead. The first term is
computational/representation approximation, the second contains finite-sample
estimation and optimization. Time measurements add stochastic noise. This
clarification changes no frozen model, label, objective, gate, or input role.

For a fixed graph/action domain let m(q,h)=E[u(q,h)|I(q)]. Suppose there is a
shared response coordinate beta(h) and query map alpha(q) such that

    m(q,h) = alpha(q)^T beta(h) + e(q,h),  alpha(q) in the simplex.

If beta is estimated on independent support queries, a simplex query map
cannot amplify its sup-norm estimation error: |alpha^T(beta_hat-beta)| is at
most ||beta_hat-beta||_infinity. Including a query-map error delta and model
residual eta gives score error at most epsilon_beta + delta + eta, and plug-in
regret at most twice that sum. This is a standard approximation/estimation
decomposition, not a new theorem or a statement that our data satisfy it.

The nonlearned ClusterMean control directly tests the coarse-cluster special
case. The shared interaction model relaxes the simplex-mixture structure and
does NOT inherit its non-amplification property: its learned sensitivity to
capability features may amplify support noise. That is a reason to compare
with the simpler cluster rule and to retain complete learning curves.

For each cluster c, beta(c,h) is a conditional response mean, not a causal
effect of a semantic query type. For Recall deltas in [-1,1], with independent
support queries and min cluster size m, a union bound over C*H means gives

    P(max_c,h |beta_hat-beta| > epsilon)
      <= 2*C*H*exp(-m*epsilon^2/2).

Thus the relevant support cost grows with log(C*H), while the total H paired
responses from one query do not make H independent queries. This bound can be
vacuous at our support sizes. Shrinkage reduces variance at the cost of a bias
term tau/(m_c+tau) * |beta_global-beta_c|, plus estimation error in the global
mean. It does not create missing information. The timing part is not bounded
by this Recall inequality; its assumptions and repeated measurement variance
must be considered separately.

## Identifiability and Controls

The average-response metric can be arbitrarily misleading for selection. Take
a zero-value default and H singles: one single has true utility -1, all others
zero. Predict epsilon>0 for the bad single and zero elsewhere. The scorer's
action-averaged MSE is (1+epsilon)^2/H, which tends to zero with H, but its
selected regret remains one. More generally a uniform score-error bound is
controlled only by sqrt(H*MSE) in the unrestricted worst case, not by MSE alone.
This elementary counterexample motivates selected utility and rescue/harm as
the primary metrics. It does not prove that a particular ranking loss solves
the conditional decision problem; that is why the loss comparison is measured.

Recall-only oracle opportunity is deterministic for these cached outputs.
The utility oracle additionally maximizes over noisy timing measurements and
can exploit measurement noise. It is an ex-post label oracle, not a population
Bayes bound or an achievable speedup. The two kinds of headroom must remain
separate in reporting.

An arbitrary invertible linear transform of response coordinates and its
inverse query map produce the same scores. Coordinates alone are therefore
not unique explanatory mechanisms. The empirical claim is about transfer of
decisions, not interpreting an SVD axis or naming a latent basin.

The four primary arms have equal allocated parameter count. Zeroing capability
inputs does NOT equalize effective function-class capacity. A positive H1
contrast would support the utility of the whole capability-augmented system,
not isolate semantic response information from every form of extra-feature
capacity. A future independent protocol would need a matched noninformative
descriptor control to make the stronger causal claim. No such new training
arm is added after looking at monitor outcomes in this version.

The E118 additive reference has the same fit rows and reward but uses its
inherited direction features. Consequently H2 is an end-to-end scorer-family
comparison, not a factorial causal isolation of the multiplicative layer. No
positive contrast alone would prove that the product term caused the gain.
The fixed geometric information also omits raw hub norm as a separate feature;
the controls are not an upper bound over all cheap graph/geometry information.

GBDT and TabM have different inductive biases, not guaranteed optimization
upper bounds. A negative bounded run cannot disprove their fully tuned families.
Likewise a positive fit score with negative query-out score supports a transfer
problem in this version, but does not identify distribution shift, sparse
support, loss mismatch, or noise as its unique cause.

## Deployment Boundary

The main action family has H singles plus an existing dynamic triple. It can
test selection over measured single-entry responses, not learn the unknown
utility of a newly composed multi-entry set. Expanding to arbitrary sets
requires new joint labels and is outside this protocol.

Neither the conditional-mean derivation nor query-fold validation gives
arbitrary distribution-shift robustness. A paper would need a declared target
distribution, untouched queries, full paid search costs, and evidence against
simple same-supervision controls before claiming a new robust routing method.
