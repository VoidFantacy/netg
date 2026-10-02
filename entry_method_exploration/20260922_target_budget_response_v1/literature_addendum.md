# Additional primary-paper check during the bounded measurements

This note does not change the frozen actions, labels, gates, or information-control design.

The full [ICLR2026 random-walk paper](https://proceedings.iclr.cc/paper_files/paper/2026/file/dd5d65bf0c81b539f00f57850c1774ad-Paper-Conference.pdf), sections3-4, makes the applicability gap concrete. Its twin search samples neighbors with a softmax of query-dependent squared distance; this is not the deterministic finite-beam state used here. Its local elimination argument concerns preservation of transition probabilities after deletion, and the paper separately discusses sparsification and a practical deterministic deletion procedure. We cannot replace our entry utility by an ordinary static graph hitting time without proving an additional bridge. Graph changes and deletion also fall outside this task. Reading this newer theory therefore does not authorize a random-walk or spectral scorer experiment.

The [PAC algorithm-selection paper](https://arxiv.org/pdf/1511.07147) treats input distributions and algorithm-family capacity as explicit objects. This is a useful framing for the finite strategy response study, not a reason to count query-action pairs as independent query samples. Here each dataset has4096 queries, not 4096 times7 statistically independent observations. Four overlapping training folds and repeated budgets do not multiply that independent sample count.

The actionable theoretical distinction remains budget-specific conditional action value versus hindsight response. Both source families can organize assumptions; neither proves that our particular cheap query representation predicts the target-budget net gain.
