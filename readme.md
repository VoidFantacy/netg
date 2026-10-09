# ACSG：GT10 与正在研究的 M5

<!-- E173_CURRENT_BEGIN -->
当前项目研究入口：[GT10 与正在研究的 M5](research_snapshots/20261009_nsg_gt_m5/README.md)。E173 已完成两集、三方法、两K、五档实际L的60点和180批单线程计时；[实测曲线](entry_method_exploration/20261009_nsg_gt_m5_test_v1/figures_v2/recall_qps_nsg_gt_m5.png)、[完整报告](entry_method_exploration/20261009_nsg_gt_m5_test_v1/analysis_v2/report.md)、[3页方法说明](entry_method_exploration/20261009_nsg_gt_m5_test_v1/advisor_report/concise_v1/method_report.md)。M5基于GT10；WebVid K1有局部综合优势，Yandex增益很小，当前默认仍为GT10。以下保留原NETG介绍。
<!-- E173_CURRENT_END -->

# NETG: Navigation-Enhanced Topology-aware Graph Indexing

NETG is a lightweight, non-intrusive **entry-point optimization** layer for
graph-based Approximate Nearest Neighbor Search (ANNS). It mines topology-aware
routing hubs offline (Ant Colony Optimization + Density Peak Clustering) and
projects them into an optimized inner-product space via a small neural router,
so that online search starts from high-quality entry points at **zero neural
cost** at query time.

---

## 1. Prerequisites

**C++ Backend**

- C++17 compiler (GCC 9+ / Clang 10+)
- CMake 3.15+
- OpenMP
- Faiss (CPU version required). Configure `FAISS_ROOT` in
  `benches/CMakeLists.txt` to point to your local Faiss installation.

**Python Frontend**

- Python 3.8+
- PyTorch, NumPy
- Matplotlib (for reproducing the figures)

---

## 2. Build Instructions

Compile the C++ core algorithms from the root directory:

```bash
mkdir build && cd build
cmake ../benches
make -j
```

---

## 3. Execution Pipeline

To reproduce the NETG pipeline, run the following steps **in order**:

**Step 1 — Topology Hub Discovery (ACO).** Discover routing hubs on the base
graph via Ant Colony Optimization:

```bash
./build/bench_ACO --dataset <dataset_name> --index_file <output_index_path>
```

**Step 2 — Global Entry-Point Selection (DPC).** Perform two-layer Density Peak
Clustering to select a compact set of global hubs:

```bash
./build/kph_dpc_clustering --acpg_file <index_file_from_step1> --output_file dpc_results.json
```

**Step 3 — Generate Training Labels.** Extract optimal topological labels for
training:

```bash
python3 benches/run/run_gen_labels.py
```

**Step 4 — Train Asymmetric Neural Router.** Train the lightweight neural router
and export the pre-warped, L2-normalized hub features for zero-overhead online
search:

```bash
python3 benches/run/train_router.py
```

---

## 4. Reproducing the Paper Results

All plotting scripts should be launched **from the repository root**. Each
command below regenerates a specific figure/result reported in the paper from
the measured experiment data; outputs are written as both `.pdf` and `.png`.

| Paper item | What it shows | Command | Output | Data source |
|------------|---------------|---------|--------|-------------|
| **Fig. 1** | Tail-query failure rate & mean Recall@10 vs. search budget (Yandex T2I) | `python3 benches/run/plot_final_paper.py` | `per_query_recall_plots/paper_combo_threshold01.pdf` | `per_query_recall_results_r10/*.json` |
| **Fig. 2** | NETG pipeline schematic (ACO → DPC → asymmetric projection) | `python3 benches/run/netg_figure.py` | `netg_figure.pdf` | illustrative (no data) |
| **Fig. 3** | QPS vs. Recall@1 (top) and Recall@100 (bottom) across five benchmarks | `python3 benches/run/plot_result.py` | `benches/run/netg_results.pdf` | measured QPS–Recall curves embedded in the script |
| **Fig. 4** | Dual-metric ablation (QPS & Recall@100) at L=150/250, Yandex T2I | `python3 benches/run/plot_ablation_bars.py` | `benches/run/xr.pdf` | `test/yandex_t2i_results/yandex_t2i_final_report.json` |

### Regenerating the per-query recall data (input to Fig. 1)

The per-query Recall@10 distributions consumed by Fig. 1 are produced by:

```bash
python3 benches/run/run_per_query_recall_r10.py
```

This writes one JSON per dataset into `per_query_recall_results_r10/`, each
containing the per-query recalls for `NSG_Medoid`, `NETG_AsymHNSW`, and
`Raw_HNSW_Ablation` across all search budgets `L`.

---

## 5. Repository Layout

| Path | Contents |
|------|----------|
| `benches/` | C++ benchmark sources and `CMakeLists.txt` |
| `benches/run/` | Python pipeline (ACO/DPC helpers, router training) and plotting scripts |
| `per_query_recall_results_r10/` | Per-query Recall@10 results (Fig. 1 input) |
| `test/yandex_t2i_results/` | Yandex T2I ablation report (Fig. 4 input) |
| `benches/image/` | Figures embedded by the paper (`.pdf`) |
