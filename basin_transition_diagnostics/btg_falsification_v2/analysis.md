# Basin Transition Graph Minimal Falsification

## Decision

**NO-GO** — BTG transition score failed at least one preregistered cross-dataset validation condition.

No held-out queries or labels were read. One shared parameter tuple was selected on the last 2K rows of each independent prototype-train utility artifact, then evaluated once on WebVid and Yandex validation 10K.

## Selected shared configuration

- transition mode: `cross_stay_0.00`
- horizon: `4`
- target temperature: `0.25`
- reachability weight gamma: `0.1`
- conservative switch margin: `0.0`

## Validation

| Dataset | Utility delta vs rank-0 | Switch fraction | L | Recall delta vs rank-0 | graph NDC delta vs rank-0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| webvid | -0.000081 | 3.58% | 64 | +0.002 pp | +0.064% |
|  | -0.000081 | 3.58% | 128 | -0.010 pp | +0.029% |
| yandex | -0.000049 | 4.41% | 64 | -0.010 pp | +0.066% |
|  | -0.000049 | 4.41% | 128 | +0.009 pp | +0.032% |

## Gate

The mechanism passes only if both datasets have positive mean utility delta, neither L=64 nor L=128 loses Recall, and mean graph-NDC growth versus rank-0 is at most 0.5% on each dataset. This is a mechanism diagnostic over the existing top-32 sparse counterfactual matrix, not a final end-to-end result.
