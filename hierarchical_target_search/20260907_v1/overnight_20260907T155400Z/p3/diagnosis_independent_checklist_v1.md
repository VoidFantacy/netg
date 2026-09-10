# P3 失败诊断独立验收清单

状态：冻结协议已读，实施源码待作者 READY 后审查。以下为独立预备清单，不是已通过的实现验收。未读真实 GT/标签/完整评测行，未运行 ANN。

协议 SHA：`4bdd1cd92b42d85f89bd69aec980068c9bed0d5aee90917d5ce2ad8db9823959`。

## 共同边界

- **C01 Frozen provenance**：Verify diagnosis protocol exact SHA, P3 NOPASS gate identity, P3 protocol, complete analysis/structure bindings, analyzer/source identity; source drift or mismatched complete markers fails before input use.
- **C02 Read boundary**：Source path audit must exclude graph/base/query vectors, validation/held-out and ANN. Target code alone may read strictly bounded pilot GT100 prefix and saved fit GT10; portal code reads saved metadata/count only.
- **C03 No gate or model mutation**：Output remains post-hoc descriptive, preserves P3 NOPASS, no confidence intervals/bootstrap/new threshold/seed/model/portal or auxiliary graph authorization.
- **C04 Completeness and preservation**：New exclusive output directory, INCOMPLETE until all required outputs bound, complete marker last, source/input binding retained; old output rejected and exceptions never report COMPLETE.
- **C05 Full family**：Both registered datasets, L64/128, all exact comparison/bin cells retained including empty groups; no best-bin/model selection or implicit filtering.
- **C06 Scientific counter semantics**：Exclude legacy Fast expanded/rejected/evicted zero sentinels; oracle counters available. Timing not used as Recall replicates, no cross-model paired wall claim.

## 目标泛化

- **T01 Physical GT bound**：Synthetic ivecs prefix with width100 per record, exactly 10000 records in actual mode; full first100-rank values SHA verification while metrics use only top10; never read byte beyond allowed prefix.
- **T02 GT rejection**：Wrong per-record header, truncation, rank99 byte tamper, duplicate top10 IDs, negative/out-of-range ID and prefix checksum mismatch fail; trailing records remain unread and do not affect prefix identity.
- **T03 Fit identity**：Fit rawGT10 SHA and shape20000x10 match fit manifest and P0 fit identity; all rows unique IDs, no pilot GT in fit support. Count f(u) by query incidence.
- **T04 Exact targets**：All256 leaf counts descending with leafID tie, high IDs above63 and top4 zero ties; exact D and M4, histograms D1..10 and targetcounts0..10 with empty bins.
- **T05 Saved oracle integrity**：Recomputed full-GT regions and conditional weights match all four models, both L and both queues; common initial/no-search structures are kept separate.
- **T06 Denominators**：Separate all-node, seen/unseen unique-node populations from pilot targetslot weighted populations. Every fit target is seen; optional subgroup ratios use correct nonzero slot denominator or null.
- **T07 Movement**：pass1 move followed by pass2 return counts anypass changed but not final changed; final leaf/coarse change versus init explicit; lambda0-versus1 final difference explicit; no population dump.
- **T08 Additive subgroup contributions**：Use same full-GT top4 for seen and unseen; covered_seen/10+covered_unseen/10==M4 and hits_seen/10+hits_unseen/10==Recall exactly in integer-count form. Never independently reroute subgroups or allocate NDC to targets.
- **T09 Query strata**：k_seen exact0..10 all eleven bins, all10K queries exactly once; synthetic one-per-bin and empty-bin fixtures; slot-level seen/unseen counts consistent.
- **T10 All ten contrasts**：Original8 plus lambda1-minus-lambda0 oracle_unified under frequency3 andgreedy3; 2Ds*2Ls*10=40 contrast cells. Explicit candidate/reference signs, saved resultID-derived hits, wins/losses/equal, NDC/expanded deltas in every k_seen bin.
- **T11 Compact artifacts**：Fit20K/pilot10K perquery CSV or NPZ with hashes, enough columns for D/M4/support decomposition; no rawGT or million-node dump. Source permits one dataset independently but completion scope explicit.

## 门户暴露

- **P01 Verification identity**：Each saved perleaf verification binds proper same-lambda models/portals, candidate/query/cache evidence and analysis model identity; changed verification SHA or reordered incompatible leaf mapping fails.
- **P02 Proxy denominators**：Exactly256 leaves per structure. Delta=greedy_unionhits-frequency_unionhits, eligible target support is the proper perleaf cached denominator; negative deltas preserved and not converted to population Recall.
- **P03 Fixed eight comparisons**：Only greedy3-minus-frequency3 oracle_probability, 2Ds*2lambda*2L; do not compare cross-lambda proxy totals or select favorable portal model.
- **P04 Actual entry classes**：Use deduplicated actual ordered seeds including shared/default/anchor context. Exactly same ordered, same set changed order, or changed set; duplicate list/missingshared seed rejected.
- **P05 Full route invariant**：Same full ordered route plus fixed labels implies exact result IDs/order, Recall, NDC, expanded, rejected and evicted; any mismatch is integrity failure, not averaged-away noise.
- **P06 Hidden route fields**：Entry equality alone cannot permit changed regions, conditional weights, default or Fast anchor. Same-lambda expected region/weight identity checked independently of entry-class summary.
- **P07 Result-set versus Recall**：Changed top10 order, changed top10 set, Recall wins/losses/equal kept separate; equal Recall may conceal changed ID set, and same ID set may have changed order.
- **P08 Exposure signs**：Compute integer sum-delta sign independently of weighted delta/support score; sign of unweighted sum may differ from weighted score. Use saved conditional weights without re-normalizing supported leaves.
- **P09 Empty proxy support**：No division by zero or silent evidence fabrication. Document null/missing-support policy; positive-weight unsupported leaf should yield explicitly missing weighted score or an equally transparent predefined treatment. Zero-weight unsupported leaf has no weighted contribution.
- **P10 Full paired summaries**：All3 route classes and all3 sign classes including empty bins; counts exhaust10000 per cell, correct paired mean orientation, all oracle counters. Retain compact query-level outputs and binding.

7 组合成反例及独立预期值见 [JSON](diagnosis_independent_checklist_v1.json)。重点防止：分组重新选 top4、把回迁漏算为未移动、混淆唯一节点与目标槽位、将相同 Recall 当相同结果、把 exposure 总和符号与加权分数混为一谈，以及对零支持叶默认为零效果。
