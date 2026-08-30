# ACSG / Fast-Entry 一键运行命令

> 工作目录：`/data/netg/ACSG`。默认命令复用冻结 WebVid NSG，不修改公共 ACO C++，不覆盖正式 `acpg/`、`dpc/` 或 `drl/` 产物。详细原理与结果见 `aco_router_fast_entry.md`。

## 一键复现三种子验证

```bash
cd /data/netg/ACSG && bash benches/run/run_fast_entry_validation.sh
```

默认使用 seeds `20260828,20260829,20260830`，每个 seed 在完整 10K held-out query 上运行 Recall@1 × 3、Recall@100 × 3 和逐 query Recall@10。当前 16-vCPU 服务器从头运行预计约 24 分钟；已有契约匹配的结果会自动跳过，因此重复执行通常只需不到 1 秒并重新生成汇总：

```text
fast_entry_variants/webvid2_5m_light_v1_multiseed_summary.json
```

强制从头重跑所有 fast-entry 构建和评测：

```bash
cd /data/netg/ACSG && FORCE=1 bash benches/run/run_fast_entry_validation.sh
```

自定义三个或更多聚类 seed：

```bash
cd /data/netg/ACSG && SEEDS=20260828,20260829,20260830,20260831 bash benches/run/run_fast_entry_validation.sh
```

## 只重做日志审计

```bash
cd /data/netg/ACSG && .venv_cpu/bin/python benches/run/analyze_training_bottlenecks.py \
  --aco-log logs/webvid2_5m_light_v1/train_aco.log \
  --router-log logs/webvid2_5m_light_v1/router.log \
  --output logs/webvid2_5m_light_v1/training_bottleneck_audit.json
```

## 一键运行 Yandex-IP 轻量复现

```bash
cd /data/netg/ACSG && bash benches/run/run_yandex_qgt_fast_light.sh
```

默认使用 seed `20260829`、821 hubs、完整 5K/30K 训练 split 和 10K held-out test，预计约 8 分钟。已有结果会自动复用；强制重跑或更换 seed：

```bash
cd /data/netg/ACSG && FORCE=1 SEED=20260830 bash benches/run/run_yandex_qgt_fast_light.sh
```

汇总输出：

```text
fast_entry_variants/yandex_t2i_official10M_ip_v1_seed20260829/evaluation_summary.json
```

## 只构建一个 fast-entry seed

```bash
cd /data/netg/ACSG && OPENBLAS_NUM_THREADS=16 OMP_NUM_THREADS=16 \
  .venv_cpu/bin/python benches/run/build_fast_entry_variants.py \
  --dataset webvid2_5m_light_v1 \
  --qgt-only --target-hubs 815 \
  --seed 20260828 \
  --output-dir /data/netg/ACSG/fast_entry_variants/webvid2_5m_light_v1_seed20260828
```

冷启动约 12–13 秒；page cache 热时约 1–2 秒。该时间不包含公共 NSG 和 exact train-GT 的准备成本。

## 只重新汇总已有多种子结果

```bash
cd /data/netg/ACSG && .venv_cpu/bin/python benches/run/summarize_fast_entry_multiseed.py \
  --dataset webvid2_5m_light_v1 \
  --seeds 20260828,20260829,20260830
```

## 快速检查产物

```bash
cd /data/netg/ACSG && jq '{recall1,recall100,tail_recall10,limitations}' \
  fast_entry_variants/webvid2_5m_light_v1_multiseed_summary.json
```

```bash
cd /data/netg/ACSG && .venv_cpu/bin/python -m py_compile \
  benches/run/analyze_training_bottlenecks.py \
  benches/run/build_fast_entry_variants.py \
  benches/run/summarize_fast_entry_results.py \
  benches/run/summarize_fast_entry_light.py \
  benches/run/summarize_fast_entry_multiseed.py \
  && bash -n benches/run/run_fast_entry_validation.sh \
  benches/run/run_yandex_qgt_fast_light.sh
```

## 双数据集 QPS / Recall / Tail 稳定性复验

```bash
cd /data/netg/ACSG && bash benches/run/run_two_dataset_fast_benchmark.sh
```

报告输出：

```text
fast_entry_benchmark_results/benchmark_summary.md
fast_entry_benchmark_results/search_metrics.csv
fast_entry_benchmark_results/tail_metrics.csv
```

从已有汇总结果重画两张 QPS–Recall 图（不重跑搜索）：

```bash
cd /data/netg/ACSG && .venv_cpu/bin/python benches/run/plot_two_dataset_qps_recall.py
```

图片输出：

```text
fast_entry_benchmark_results/figures/webvid_qps_recall.{png,pdf}
fast_entry_benchmark_results/figures/yandex_qps_recall.{png,pdf}
```
