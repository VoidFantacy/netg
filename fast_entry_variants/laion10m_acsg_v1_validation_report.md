# LAION-10M Fast Entry Validation Report

> 状态：complete。完成时间：2026-08-30。该批次只读取独立 validation 10K，未访问 held-out test。

## 协议与 provenance

- dataset：`laion10m_acsg_v1`
- artifact：`roargraph-laion10m-unit-ip-acsg-v1`
- metric / normalization：inner product / base 与 query 显式 L2-unit normalization
- frozen NSG：`R64/L_build100/C512`
- NSG SHA256：`7040cd0a2b8f5d34b3e3affbbcb30ce19c947731a8a81c40ec64f0e0d99bb238`
- validation：10,000 queries，exact-IP top-100 GT
- hub budget：821
- build seeds：`20260828/20260829/20260830`
- timing：每个 seed、方法和 `L` 运行 3 次
- Recall@1：`L=64/128/200/400`
- Recall@100：`L=100/128/200/400`
- 逐 query Recall@10：`L=64/128/200/400`

机器汇总：`laion10m_acsg_v1_validation_multiseed_summary.json`。三个 seed 的原始 JSON、
manifest、日志和 `/usr/bin/time -v` 位于
`laion10m_acsg_v1_validation_seed{20260828,20260829,20260830}/`。

## Recall@1

| L | Medoid | QGT-Raw | Fast Prototype | Prototype - Medoid | QPS / Medoid |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.7101 | 0.7184 | 0.7308 | +2.067 pp | +11.88% |
| 128 | 0.7902 | 0.7942 | 0.8021 | +1.190 pp | +7.49% |
| 200 | 0.8318 | 0.8349 | 0.8417 | +0.990 pp | +5.25% |
| 400 | 0.8846 | 0.8880 | 0.8915 | +0.687 pp | +3.87% |

QPS 使用每个 seed 同次 Medoid 归一化后再求均值。Prototype 在四点均超过 QGT-Raw，
增益为 `+0.347~+1.233 pp`。

## Recall@100

| L | Medoid | QGT-Raw | Fast Prototype | Prototype - Medoid | QPS / Medoid |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 100 | 0.7081 | 0.7105 | 0.7147 | +0.667 pp | +9.33% |
| 128 | 0.7467 | 0.7485 | 0.7517 | +0.504 pp | +8.09% |
| 200 | 0.8059 | 0.8078 | 0.8105 | +0.458 pp | +5.49% |
| 400 | 0.8747 | 0.8773 | 0.8784 | +0.373 pp | +3.57% |

Prototype 在四点均超过 QGT-Raw，增益为 `+0.112~+0.418 pp`。

## 逐 query Recall@10 与 tail

| L | Medoid Mean R@10 | Fast Mean R@10 | Delta | R@10<0.1：Medoid -> Fast | 净救回均值 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 0.7241 | 0.7416 | +1.755 pp | 4.48% -> 2.53% | +195.3 |
| 128 | 0.8102 | 0.8199 | +0.968 pp | 2.20% -> 1.24% | +95.7 |
| 200 | 0.8520 | 0.8598 | +0.780 pp | 1.43% -> 0.75% | +68.0 |
| 400 | 0.9020 | 0.9074 | +0.539 pp | 0.84% -> 0.40% | +44.3 |

在四个 `L` 和预注册阈值 `0.1/0.2/0.5/0.8` 的全部 16 个点上，Fast 相对 Medoid
均为正净救回；newly-harmed 仍然非零，不能只报告 rescued。

## 资源与终态审计

- 三个 seed 分别用时约 `15:18/15:18/15:16`；全批次 wall time 约 46 分钟。
- 单个搜索进程 max RSS 约 21.6 GiB；无 swap。
- 每个 seed 的 Fast artifact 与结果约 9 MiB。
- 三个 build、Recall@1、Recall@100 和 tail 的 time 文件均为 exit status 0；日志无
  traceback、FATAL、segmentation fault 或非零退出。
- Fast builder 的热 page-cache wall time 小于 1 秒，不作为冷构建结论；exact train-GT
  生成成本仍未计入。

## 结论边界

LAION validation gate 通过：Fast Prototype 在全部 Recall@1/100、QPS 和 tail 点上都优于
Medoid，并且 prototype 在全部八个 Recall 点上都超过 QGT-Raw。下一步可以进入 held-out
10K 最终复验。

但 LAION 与 WebVid 的 public query 源文件相同，因此 LAION 只能作为不同 10M image corpus
与规模下的迁移 control，不能单独宣称是第三个完全独立的 query workload。
