# LAION-10M Fast Entry Held-out Report

> 状态：complete。完成时间：2026-08-31。该批次为 public held-out 10K 最终复验。

## 协议与 provenance

- dataset：`laion10m_acsg_v1`
- artifact：`roargraph-laion10m-unit-ip-acsg-v1`
- metric / normalization：inner product / base 与 query 显式 L2-unit normalization
- frozen NSG：`R64/L_build100/C512`
- NSG SHA256：`7040cd0a2b8f5d34b3e3affbbcb30ce19c947731a8a81c40ec64f0e0d99bb238`
- held-out：public 10,000 queries，official top-500 截取并验证的 exact-IP top-100 GT
- hub budget：821
- build seeds：`20260828/20260829/20260830`
- timing：每个 seed、方法和 `L` 运行 3 次
- Recall@1：`L=64/128/200/400`
- Recall@100：`L=100/128/200/400`
- 逐 query Recall@10：`L=64/128/200/400`

三个 held-out seed 的 Fast artifact 与对应 validation seed 的 hubs、IDs 和 prototype
checksum 完全一致，test split 没有参与构建或调参。机器汇总：
`laion10m_acsg_v1_heldout_multiseed_summary.json`。

## Recall@1

| L | Medoid | QGT-Raw | Fast Prototype | Prototype - Medoid | QPS / Medoid |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.7112 | 0.7173 | 0.7284 | +1.723 pp | +11.82% |
| 128 | 0.7962 | 0.8012 | 0.8070 | +1.083 pp | +7.40% |
| 200 | 0.8405 | 0.8420 | 0.8468 | +0.627 pp | +6.22% |
| 400 | 0.8927 | 0.8929 | 0.8955 | +0.280 pp | +4.03% |

Prototype 在四点均超过 QGT-Raw，增益为 `+0.260~+1.113 pp`。

## Recall@100

| L | Medoid | QGT-Raw | Fast Prototype | Prototype - Medoid | QPS / Medoid |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.7090 | 0.7131 | 0.7168 | +0.777 pp | +9.77% |
| 128 | 0.7477 | 0.7514 | 0.7542 | +0.642 pp | +6.93% |
| 200 | 0.8074 | 0.8102 | 0.8126 | +0.515 pp | +5.42% |
| 400 | 0.8778 | 0.8792 | 0.8802 | +0.242 pp | +3.68% |

Prototype 在四点均超过 QGT-Raw，增益为 `+0.105~+0.369 pp`。

## 逐 query Recall@10 与 tail

| L | Medoid Mean R@10 | Fast Mean R@10 | Delta | R@10<0.1：Medoid -> Fast | 净救回均值 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.7237 | 0.7386 | +1.492 pp | 4.29% -> 2.72% | +156.7 |
| 128 | 0.8104 | 0.8199 | +0.949 pp | 2.12% -> 1.30% | +82.3 |
| 200 | 0.8540 | 0.8609 | +0.686 pp | 1.29% -> 0.75% | +54.0 |
| 400 | 0.9049 | 0.9082 | +0.329 pp | 0.58% -> 0.31% | +26.7 |

四个 `L` × 阈值 `0.1/0.2/0.5/0.8` 的全部 16 个点均为正净救回；newly-harmed
仍然非零，报告 tail 时必须与 rescued 同时保留。

## 资源与终态审计

- 三个 seed 分别用时约 `18:10/16:09/16:01`；全批次 wall time 约 50 分钟。
- 第一个 seed 包含冷索引加载；后续 seed 受 page cache 加速。
- 单个搜索进程 max RSS 约 21.6 GiB，无 swap。
- 每个 seed 的 Fast artifact 与结果约 9 MiB。
- 三个 build、Recall@1、Recall@100 和 tail 的 time 文件均 exit status 0；日志无
  traceback、FATAL、segmentation fault 或非零退出。
- 首 seed Fast 构建 wall time 约 19 秒，后续热 cache 约 1 秒；这些时间仍不包含 exact
  train-GT 生成成本。

## 结论边界

LAION held-out 正式复验通过：Fast Prototype 在全部 Recall@1/100、QPS 和 tail 点上优于
Medoid，并在全部八个 Recall 点上进一步超过 QGT-Raw。validation 与 held-out 方向一致，
说明结果不是 validation 偶然波动。

但 LAION 与 WebVid 的 public query 源文件相同，因此该结果增强的是跨 image corpus/规模
迁移证据，不能单独作为第三个完全独立 query workload。下一步优先补独立 query workload、
强端到端基线与完整成本消融，而不是继续在 LAION test 上调参。
