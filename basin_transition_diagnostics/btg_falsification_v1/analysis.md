# Basin Transition Graph Minimal Falsification

## Decision

**NO-GO** — BTG transition score failed at least one preregistered cross-dataset validation condition.

No held-out queries or labels were read. One shared parameter tuple was selected on the last 2K rows of each independent prototype-train utility artifact, then evaluated once on WebVid and Yandex validation 10K.

## Selected shared configuration

- transition mode: `cross_stay_0.00`
- horizon: `1`
- target temperature: `0.5`
- reachability weight gamma: `0.5`
- conservative switch margin: `0.1`

## Validation

| Dataset | Utility delta vs rank-0 | Switch fraction | L | Recall delta vs rank-0 | graph NDC delta vs rank-0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| webvid | +0.001896 | 22.74% | 64 | +0.163 pp | -0.327% |
|  | +0.001896 | 22.74% | 128 | +0.185 pp | -0.131% |
| yandex | -0.001343 | 26.33% | 64 | -0.179 pp | +0.120% |
|  | -0.001343 | 26.33% | 128 | -0.067 pp | +0.176% |

## Gate

The mechanism passes only if both datasets have positive mean utility delta, neither L=64 nor L=128 loses Recall, and mean graph-NDC growth versus rank-0 is at most 0.5% on each dataset. This is a mechanism diagnostic over the existing top-32 sparse counterfactual matrix, not a final end-to-end result.
