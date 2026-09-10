# Independent interpretation of the Fast diagnosis matrices

2026-09-08. This review independently read the raw matrices under `results/run_v1/main`, their metadata, prepared-v2 sample mappings and GT, real parity records, and the frozen runner/controller. It then compared its independently recomputed means with [analysis/v2](../analysis/v2/analysis.md). No graph search, new model or additional sampling was run. All numbers below concern the preselected historical pilot512, one paired-20K Fast build, the current hub pool and the original fixed-L kernel.

**The evidence supports a mismatch between Fast's geometric proxy and actual search utility, and contradicts making fixed anchor plus fixed three entries the default next mechanism. It does not establish theoretical unlearnability, and does not yet validate a deployable replacement.**

## 1. Anchor and entry count must be reopened

All entries in this table come from the same query's actual approximate C8 and the same original kernel. Numbers are mean Recall@10 percentages. Oracles choose using that query's true results and pay no selection cost.

| Dataset | L | Fast3 | C8 best single | C8 best pair | C8 best triple | Best triple retaining Fast rank0 | C8 best of 1–3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| WebVid | 64 | 65.801 | 73.438 | 73.184 | 72.500 | 69.395 | 73.516 |
| WebVid | 128 | 73.828 | 79.590 | 79.434 | 79.023 | 76.504 | 79.668 |
| Yandex | 64 | 83.398 | 88.555 | 88.203 | 87.910 | 85.254 | 88.555 |
| Yandex | 128 | 90.762 | 93.418 | 93.184 | 93.125 | 92.285 | 93.418 |

The best unrestricted triple loses 0.938/0.566 pp to the best single on WebVid and 0.645/0.293 pp on Yandex. Consequently, a mechanism restricted to exactly three C8 entries starts with a lower empirical quality ceiling than a single-entry mechanism on these four points. Allowing cardinalities 1–3 adds only 0.078 pp over the best single on each WebVid point and adds zero on both Yandex points. These are descriptive oracle comparisons, not a new statistical family or a performance GO.

This pattern is concentrated in a small number of queries, not universal single-entry dominance. The best triple is worse than the best single for 22/512 and 19/512 WebVid queries and 22/512 and 6/512 Yandex queries. It is better for only 4/512 and 2/512 WebVid queries and zero Yandex queries; all other queries tie. Therefore the correct interpretation is that **this action restriction lacks support and can discard useful outcomes**. It would be too strong to claim that multiple entries can never help, that single-entry deployment is optimal, or that every query needs fewer entries.

Retaining Fast rank0 costs 3.105/2.520 pp on WebVid and 2.656/0.840 pp on Yandex relative to the best unrestricted triple. It excludes a strictly better triple on 15.04%/11.72% and 13.09%/5.86% of queries. The predefined Bonferroni32 intervals in analysis/v2 remain positive at all four points: respectively [1.871,4.633], [1.387,3.929], [1.426,4.238], [0.352,1.523] pp. This is stronger evidence against treating the anchor constraint as harmless than the prior design-only rationale for retaining it.

The previous fixed-anchor triple proposal should be marked as an unsupported and now empirically challenged restriction. It should not proceed unchanged merely because an unrestricted triple oracle still beats Fast3. The current matrices justify reopening the action definition before choosing a predictor; they do not authorize or validate training another selector.

## 2. Exact ANN repair is insufficient; proxy and shortlist losses remain

| Dataset | L | Exact1 − Fast1 (pp) | Exact3 − Fast3 (pp) | All-H best single − exact1 (pp) | All-H best single − exact C8 best single (pp) |
| --- | ---: | ---: | ---: | ---: | ---: |
| WebVid | 64 | +0.547 | +0.352 | +14.160 | +6.660 |
| WebVid | 128 | +0.625 | +0.625 | +11.465 | +5.762 |
| Yandex | 64 | −0.371 | −0.449 | +11.016 | +4.941 |
| Yandex | 128 | −0.352 | −0.312 | +5.918 | +3.164 |

Approximate/exact top1 IDs coincide on 93.36% of WebVid queries and 96.88% of Yandex queries. Entire C8 sets coincide on only 59.96% and 80.47%, respectively, but ID mismatch does not measure actual graph-search loss. Exact prototype retrieval modestly helps WebVid and has negative mean differences on Yandex; it cannot explain the much larger remaining utility gap. The small positive WebVid L128 exact3 effect should not be erased by saying ANN makes no difference: its family interval is [0.020,1.687] pp. The appropriate conclusion is that ANN approximation is not the dominant explanation of the observed missed opportunities, not that its contribution is exactly zero.

Even exact C8 leaves 3.16–6.66 pp of all-H single-entry opportunity outside the shortlist. Thus “the right answer is already in C8; only joint ranking remains” is also too strong. Current H contains useful alternatives, but the current prototype geometry can rank them outside C8. This distinguishes shortlist construction from within-shortlist selection without claiming that the whole hub pool or frozen graph is globally sufficient.

Direct access to the true GT1 geometric basin still leaves 13.066/10.352 pp of all-H single-entry gap on WebVid and 7.754/4.805 pp on Yandex. Knowing that proxy label perfectly is therefore insufficient to recover the actual single-entry oracle. The observed basin-minus-Fast1 component is positive on these aggregate means, but this component is signed query by query; it must not be called a generally nonnegative fitting error. These comparisons support proxy mismatch, without uniquely identifying single-mean prototypes, prior smoothing, sample scarcity or another modeling choice as the cause.

## 3. Large tied sets and saturation change the learning target

The all-H A0 size medians are 50.5/61.5 on WebVid and 205.5/821 on Yandex for L64/L128. A1 medians are 681.5/815 and 815/821. A1 permits one fewer GT10 hit, a per-query Recall reduction of 0.1; it is not a negligible tolerance or a deployment acceptance rule.

In Yandex L128, 51.95% of pilot queries return Recall=1 from every hub. This largely explains its median A0=821 and weak specificity of unique oracle IDs. However, equal utility is not synonymous with successful saturation: all hubs have identical sub-perfect Recall on 1.95%/4.69% of WebVid queries and 0.39%/0.98% of Yandex queries. These rows have no single-entry selection gain within the fixed pool, even though search quality is imperfect.

Large A0 does not mean there is no useful selection problem. Fast1 is outside A0 on 70.12%/60.16% of WebVid and 53.52%/33.98% of Yandex queries. On those affected queries, its mean regret is still about 16–21 pp. The data instead argue for accepting all low-regret choices and separating quality from NDC, rather than treating one arbitrary tie-broken ID as the sole correct answer.

## 4. Cross-L and nearest-query evidence does not show unlearnability

For the same query, A0 at L64 and L128 has nonempty intersection on 92.19% of WebVid and 96.09% of Yandex cases; mean Jaccard is 0.643/0.651. This contradicts a narrative of universally unrelated optimal entries at adjacent budgets. Yet taking the source-L A0 representative selected by minimum source NDC and then base ID incurs 2.090 pp for WebVid 64→128, 4.414 pp for 128→64, and 1.250/4.551 pp on Yandex. There is practical budget dependence and representative-choice sensitivity despite substantial set overlap. Neither ID changes alone nor this representative regret proves that a budget-conditioned selector cannot learn.

Nearest-fit queries are geometrically much closer than random-fit controls: mean cosine 0.750 vs 0.424 on WebVid and 0.697 vs 0.166 on Yandex. However, nonzero GT10 overlap occurs for only 37.5%/17.2% of nearest pairs. The local-density test is limited to the first 128 predetermined pilot rows and a 20K fit reference set.

| Dataset | L | Nearest − random, source minimum-NDC A0 representative (pp) | Nearest − random, average over source A0 (pp) |
| --- | ---: | ---: | ---: |
| WebVid | 64 | +1.563 | −0.391 |
| WebVid | 128 | +3.594 | −0.691 |
| Yandex | 64 | −1.016 | −1.120 |
| Yandex | 128 | −0.547 | −0.613 |

All four predefined representative-transfer family intervals cross zero. The average-source-set metric is negative at all four points, while the representative statistic is positive only on WebVid. This does not support a robust nearest-query predictive mechanism across the two datasets. Conversely, it does not show that the representation contains no information or that other functions of the query cannot predict useful entries. Large source A0 sets and hub popularity can make target-best-over-source-A0 look impressive even for a random source; that target-best number consumes target labels and is an oracle, never the result of a deployed nearest-query selector.

## 5. Answer to the theoretical question

The implemented mapping is deterministic for fixed query, graph, ordered entries, L and numerical behavior; real plain/count/repeat acceptance passed. Its finite candidate actions have now been enumerated. The experiment therefore identifies outcomes and current proxy errors, rather than establishing a computational impossibility theorem.

A claim of statistical unlearnability would need a specified query distribution, available information, function/model class, loss, sample regime and a lower-bound or irreducible-uncertainty argument. This experiment supplies none of those. It tests one geometric proxy, one fit-set density, one build and two budgets. Poor nearby-query transfer can be an empirical difficulty under that representation and sample density; it is not a theorem about all predictors. Likewise, finite-beam path dependence in the source is a mechanism that can create discontinuities, not proof that useful low-regret choices are unpredictable.

No graph-navigation theorem needs to be stretched to support the conclusion here. Search guarantees and bad graph instances address different objects from the learnability of this query-to-entry decision. The separate [theory definitions review](theory_and_diagnostic_definitions.md) documents those literature boundaries. This interpretation review relies on the observed matrices and the original kernel, not on an imported hardness claim.

## Review outcome

**PASS for the bounded diagnostic evidence; request correction of any recommendation that preserves fixed anchor plus exactly three entries as an evidence-backed default, claims the short list always contains the best entry, equates ANN ID disagreement with utility loss, or claims oracle labels are theoretically unlearnable.** The supported next research question concerns a cost-aware way to retrieve/select low-regret entries while permitting the action definition to change. It remains an unvalidated direction; none of these free oracles establishes a deployed performance improvement.
