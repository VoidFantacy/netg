# 夜间执行前的依赖交接

2026-09-07。状态：`READY_FOR_PLAN_RESUMPTION`；研究计划依用户要求暂停，本轮只下载、安装、编译依赖和运行依赖级小检查。未执行真实数据上的分区、模型拟合、ANN pilot、validation 或 held-out。

## 1. 从哪里接续

先读项目 `AGENTS.md`，再完整读 `summary.md`、`spec.md`、`s-target.md`，以及本目录 `manifest.json` 和上一级 `state.json`。新对话明确授权恢复后，解除 `PAUSED_BY_USER`，从未完成的 P0/P1 接续；不能将依赖准备算作 P0/P1 PASS。

暂停前已有草稿：`ACSG/RegionalSearch.h` 和 `benches/test_regional_search.cpp`，CMake 新增 `test_regional_search` target；该 target 已成功编译，**测试尚未运行**。新 evaluator、正式 protocol/输入 manifest、P1 gate、P2 分区和真实 pilot 均未完成。先审查草稿、运行必要正确性测试，再按计划补齐计时与机制对照。

旧底图、旧核心搜索、旧 Multi-view gate 与结果均保留。不能因前一轮停止或草稿存在就重建旧图、重启旧 Multi-view 或跳过 P2。

## 2. 已就绪的工具

| 工具 | 位置 / 状态 |
| --- | --- |
| METIS v5.2.1 | `tools/local/bin/gpmetis`、`tools/local/lib/libmetis.so`、`tools/local/include/metis.h`；idx_t 64 位、real_t 32 位；C API 六节点安装检查 PASS |
| GKlib | `tools/local/lib/libGKlib.a`；固定提交，源码见 tools/GKlib |
| 核心 Python | `/data/netg/ACSG/.venv_cpu/bin/python`；NumPy/SciPy/PyTorch CPU/Faiss/hnswlib/sklearn/gensim/matplotlib/networkx 均可导入；原包版本完全未改 |
| 基线 Python | `tools/python/bin/python`；Faiss 1.9.0、h5py 3.14.0、transformers 4.46.3、prettytable 3.16.0 及其依赖；pip check 与 CPU 导入/算子检查 PASS |
| LIRA | `tools/LIRA`，官方固定提交；模型定义可在 CPU 做合成 forward。原主脚本选择 CUDA，尚需未来 CPU 与本项目数据契约适配 |
| kRt / gp-ann | `tools/gp-ann/build/{Partition,SmallScaleQueries,QueryAttribution,OracleRecall,GraphQualityBench,...}`；已完成 MIPS_DISTANCE=ON 构建及所需子模块 |
| RoarGraph | `tools/RoarGraph/build/tests/{test_build_roargraph,test_search_roargraph}`；已编译，帮助入口可执行 |
| DiskANN exact GT 工具 | `tools/RoarGraph/build/thirdparty/DiskANN/tests/utils/compute_groundtruth`；已编译，帮助入口可执行；没有计算项目 GT |
| GATE | 复用现有 `GATE/` 及 `GATE/build/tests/`；动态依赖已核验，无需覆盖现有源码或结果 |
| C++ 基础依赖 | 新增 TBB、libaio、gperftools、Eigen、Boost program_options、GTest 等共 15 个系统包；0 个既有包升级/删除 |
| MKL | `tools/mkl` 指向局部提取的 Ubuntu MKL 2020.4 与 OpenMP；没有安装为系统 BLAS |

所有相对 tools 路径相对 `hierarchical_target_search/20260907_v1/`。源码提交、子模块、二进制 checksum、包版本和保护检查在 `manifest.json`。

## 3. 环境入口

```bash
cd /data/netg/ACSG
source hierarchical_target_search/20260907_v1/tools/env.sh
```

该脚本只修改当前 shell：添加 METIS 和现有 CMake 路径，不写 shell 启动文件。变量 `ACSG_HTS_PYTHON` 是原研究环境；`ACSG_HTS_BASELINE_PYTHON` 是基线环境。不能将解释器的符号链接解析为 `/usr/bin/python3.10` 后执行，那会丢失虚拟环境。

基线环境自己的 site-packages 优先，并通过 `.pth` 只读复用原环境的 CPU Torch 等大包；Faiss 1.9.0 仅覆盖基线环境。不要在原环境升级包。基线环境可继续安装新增依赖，但必须检查是否影响兼容性。

仅运行 RoarGraph/DiskANN 时另开子 shell，source `tools/roargraph-env.sh`，使其局部 MKL/OpenMP 生效；不要将该环境全局带入 ACSG 的构建与计时。原 ACSG 继续沿用已有数学库契约。

METIS C++ 链接需 `-I$METIS_ROOT/include -L$METIS_ROOT/lib -lmetis -lGKlib -lm`，运行时需要本地 lib 路径。可复用 `dependencies/metis_smoke.c` 的接口范例。

## 4. 后续必须区分的事项

- 依赖就绪不等于论文基线适配、性能或测量已合格。GATE 当前是项目适配；LIRA 主脚本仍有 GPU 假设；gp-ann 的原论文 README 还要求调整 HNSW metric increments，本轮未修改它，未来测量审计需处理。
- GATE 使用现有 `cluster/graph2vec_embed.py` 的 gensim WL+Doc2Vec 实现，并显式提供输出 CSV。不要让旧脚本因缺少 karateclub 而静默退化为均值池化；原版 karateclub 并非该指定适配路径的依赖。
- 已下载源码包括嵌套的必要子模块；未下载论文的大型额外数据集或预建索引。继续复用项目正式数据，split 和 GT 核验仍属 P0。没有下载遥测模型或任何云端训练服务。
- 原项目环境、核心源码、新草稿和旧 gate 的保护检查均 PASS，见 `protected_after.json`。这一结果不替代将来的源码/数据正确性审计。

## 5. 资源与定时交接

准备结束时 /data 约余 20 GiB；未删除任何压缩包。删除压缩包只能释放磁盘，不能解决进程 RAM 不足。内存不足应先限制并发、批量或换用更节省内存的实现。只有磁盘不足时，才在确认解压产物完整且来源可恢复后删除冗余下载包，并记录路径/大小/理由；源码快照、base/GT/图、结果、日志、唯一备份不在此授权内。

新对话的方法开发和实验硬截止：北京时间 **2026-09-08 07:00:00**，即 UTC **2026-09-07 23:00:00**。当前没有启动截止计时器或研究任务；必须由新对话在恢复授权后建立本次独立任务的截止机制。不能假定这份文件本身会触发定时停止。07:00 后只核查/整理既有证据并编写 `/data/netg/ACSG/实验总结.md`：标题后第一段简洁概括整晚成果，后文再详细报告；不得为补报告启动新实验。报告路径冲突时保留旧文件，在新时间戳 artifact 子目录保存同名文档并报告路径。

建议 06:40 后不启动预计跨越截止的新重任务，06:50 开始整理报告，06:59 保存检查点并向本次任务进程组发 TERM，07:00 前确认剩余研究进程停止；仅处理本次创建且重新核对身份的进程，不触碰其他用户/系统任务。中断结果记为 INCOMPLETE，不能伪装成算法 no-go。

新对话提示词见 `../overnight_prompt.md`。本轮结束后研究计划保持暂停，等待新对话明确恢复。
