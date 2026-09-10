# Budgeted Probe-then-Reroute Gate

## Valid protocol

- frozen WebVid and official Yandex NSG: `R64/L_build100/C512`
- independent prototype-train 10K and validation 10K
- paid online probe: Fast top-3 at `L_probe=10` only
- candidate set: current Fast top-32 hubs
- target budgets:
  - WebVid: Fast `L=64/128` vs probe + restart/reroute `L=46/108`
  - Yandex: Fast `L=64/128` vs probe + restart/reroute `L=40/104`
- results from probe and second search are merged by distance before Recall@10

Earlier detectors that used separate `L=10/16/32` traces while charging only the
`L=10` probe are diagnostic-only and invalid for the budget claim. All conclusions
below use only the actually paid `L=10` trace.

## Actionable-failure detection

Adding the GT-free `L=10` graph trace improves over router-distance-only features:

| Dataset | Static AUROC / AUPRC | L10 trace AUROC / AUPRC | Top-risk 10% positive rate |
| --- | --- | --- | ---: |
| WebVid | 0.584 / 0.468 | 0.660 / 0.557 | 65.6% |
| Yandex | 0.620 / 0.337 | 0.759 / 0.469 | 55.3% |

The detector generalizes across both datasets.

## Fixed-budget selective oracle

Using the learned L10 risk score but an oracle alternate entry confirms mechanism
headroom. At top-risk 20%:

- WebVid: `+0.103 pp / -0.441% NDC` at the low budget and
  `+1.286 pp / -0.779% NDC` at the high budget.
- Yandex: the high budget gives `+1.359 pp / -0.589% NDC`; the low budget needs
  top-risk 30% to become positive (`+0.459 pp / -3.362% NDC`).

Thus selective rerouting is not ruled out by the total graph-computation budget.

## Learned alternate chooser

A continuous merged-Recall/NDC reranker was trained on all top-32 candidates. It
was tested with candidate-static features, query-level L10 trace, and finally
candidate-specific affinity to the ten probe result vectors. All fail on WebVid.
For the frontier-conditioned variant at top-risk 20%:

- low budget: `-3.412 pp`, `+2.593% NDC`;
- high budget: `-1.426 pp`, `+0.969% NDC`.

The same selected queries with the oracle alternate give `+0.103/+1.286 pp` and
lower NDC. Even selecting 50% remains below Fast, so this is not a threshold issue.

## Decision

Probe-based failure detection is a validated component, but probe-then-reroute v1
is a no-go as a complete method because alternate-entry identification fails. Do
not tune the current tree model, enlarge a generic MLP/dual tower, or claim a
working rerouter. Do not modify the bottom graph.

## Frozen-graph topology-aware final gate

The local GATE tree could not be reused as a fair result: `run_gate_generic.sh`
builds its own `R=50` NSG, uses one query file for both sample generation and
search, builds a separate 512-hub HBKM layer, and routes raw queries against hub
embeddings in cosine space. No WebVid/Yandex model or output artifact was present.
Those choices violate the frozen `R64/L_build100/C512`, physical split, and raw-IP
contracts, so old GATE scripts/results are not evidence for this project.

Before paying for a full standalone GATE port, the last selective-chooser gate
added GT-free topology features from the actual paid L10 trace on the existing
NSG. For every top-32 candidate they record: membership in the probe results,
one-hop adjacency to the probe frontier, one-hop overlap fractions in both
directions, rank-weighted frontier hits, a 0/1/2/3-hop proxy, and valid degree.
The same 10K train/10K validation split, risk model, candidates, budgets, merged
Recall@10 utility, and tree learner were retained. Thus the only new information
is frozen-graph topology; there is no graph repair or hidden extra probe.

At top-risk 20% on WebVid:

| Chooser | Target L=64: Recall / NDC delta | Target L=128: Recall / NDC delta |
| --- | ---: | ---: |
| topology-conditioned | `-3.577 pp / +2.402%` | `-1.381 pp / +0.860%` |
| frontier + topology | `-3.371 pp / +2.668%` | `-1.416 pp / +1.036%` |
| alternate oracle | `+0.103 pp / -0.455%` | `+1.286 pp / -0.779%` |

Both learned variants lose Recall and spend more NDC at every tested selection
fraction (`10/20/30/50%`) and both budgets. The failure is therefore not a single
threshold choice. The result is in
`trace_conditioned_rerouter_results/webvid_probe10_top32_topology_v4/report.json`.

This is a no-go for the current selective-reroute improvement branch, so the
pre-registered Yandex extension was not run. It does **not** prove that the full
published GATE model fails; it proves that the available L10 trace plus local
one/two-hop topology still does not make the alternate utility predictable. A
full contract-correct GATE port remains useful only as a standalone paper
baseline, not as justification for further chooser expansion.

Do not implement resumable search, tune more generic chooser models, broaden hubs,
repair the bottom graph, or launch held-out tests for this branch. Freeze the
validated Fast method and redirect work to standalone baseline parity, third-task
evidence, component/cost ablations, and honest paper positioning.
