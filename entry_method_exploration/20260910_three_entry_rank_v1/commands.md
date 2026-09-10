# 实际执行与版本边界

工作区`/data/netg/ACSG`。本版本均使用项目`.venv_cpu/bin/python`及已有CPU静态库，无新依赖安装、主build修改或原kernel修改。

已按以下顺序执行，全部主阶段退出码为0：

1. `src/initialize.py`：保存修改前根文档/原源码身份与快照，核对原base/graph/query/GT、链接源码/库及旧single标签，创建独立配置。日志`initialize.log`。
2. 在任何新标注/训练之前明确三个真实ID的共同消费顺序，保存[锁定澄清](reviews/pre_label_protocol_clarification.json)。`src/prepare_fit.py`准备隔离fit/cal/audit和每query24个三入口提案；旧single提议排序实际为hits降序、NDC升序、Fast几何分数降序、真实ID升序。
3. `src/build.py`将`label_triples.cpp`与`evaluate.cpp`编译到独立bin；`src/train.py --self-test`和`src/check_synthetic.py`验证梯度、已知偏好优化、完整/满秩因子一致、float32导出、三个入口、精确top3、五L及单线程拒绝。
4. `src/run_labels.py`依次执行WebVid与Yandex；`src/verify_labels.py`独立核对完整96万逻辑标签。标签OMP16、BLAS/MKL1；这些instrumented wall不作QPS。
5. `src/run_training.py`依次执行两dataset的Full/rank8×三λ，共12候选。OMP/BLAS/MKL16；训练器只读fit，完整命令、进程wall及每个目标轨迹保留。
6. `src/run_diagnostics.py --stage cal`单线程执行fit前1024条诊断及cal1024，精确/HNSW各一份；每族只按cal HNSW真实收益选择λ。诊断不输出QPS。
7. 校准后发现verification中一个warmup计数字段的显示错误，保留v1二进制/源码/输出并新增`evaluate_v2`；[修正记录](reviews/diagnostic_metadata_correction.json)及[all-tie/元数据检查](reviews/v2_metadata_tie_check.json)通过。此修正没有改路由、搜索、计时或候选选择。
8. `src/run_diagnostics.py --stage audit`仅评估已选候选及matched Fast；不据audit重新选模型。
9. `src/prepare_validation.py`先落盘[冻结记录](models/frozen_before_validation.json)，再读取并复制旧validation前2000条。`src/run_validation.py`顺序完成双数据集共50点；OMP/OpenBLAS/MKL显式1，实际team1，未并发其他训练/搜索/性能测量。
10. `src/analyze.py`完成原值、配对比较、全输出GT评分、NSG/Fast30K旧结果逐位回归和曲线；`src/analyze_models.py`仅读取既有模型/标签/结果，统计残差、入口变化及context偏好冲突；`src/make_costs.py`整理分项成本。没有新增搜索。
11. `src/verify_integrity.py`重新核对原base/graph、输入、源码/库、冻结模型、导出W及五L相同HNSW图；更新主文档和E23复盘后，以`src/finalize.py`检查交付链接、状态、全部模型及结果范围并收口。

每个编译的精确argv和源SHA在`bin/*.build.json`，每个真实搜索子进程的argv/exit/wall在`labels/jobs.json`、`diagnostics/*_jobs.json`、`results/jobs.json`，训练在`models/jobs.json`。各阶段日志位于`logs/`。

本目录的阶段脚本已经执行，输入和输出属于冻结证据。直接重跑会被拒绝；后续需要新版本，不能覆盖原目录来追求不同结果。
