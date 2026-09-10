# 命令和阶段

以下路径根为 `/data/netg/ACSG`；实际参数和PID同时保存在state及controller日志。所有输出要求新路径，禁止覆盖已完成或部分产物。

已执行：

```bash
OPENBLAS_NUM_THREADS=8 OMP_NUM_THREADS=8 .venv_cpu/bin/python entry_method_exploration/20260909_ab_experiment_v1/src/prepare.py
bash fast_router_diagnosis/20260908_v1/src/build.sh entry_method_exploration/20260909_ab_experiment_v1/src/labels.cpp entry_method_exploration/20260909_ab_experiment_v1/bin/labels
entry_method_exploration/20260909_ab_experiment_v1/bin/labels --self-test
# 两个dataset的runner_config分别执行 --parity-only，PASS后才启动controller。
.venv_cpu/bin/python entry_method_exploration/20260909_ab_experiment_v1/src/run_labels.py
```

label controller通过subprocess start_new_session启动，子搜索进程也拥有独立process group；独立持久日志，10秒资源检查，block进度落盘。

标签完成后执行（须以实际stage状态判断是否已运行）：

```bash
.venv_cpu/bin/python entry_method_exploration/20260909_ab_experiment_v1/src/run_models_eval.py
# controller顺序：verify_labels → 12个dataset/seed/L训练 → freeze
# → calibration_check → audit → validation10K → heldout10K，均不同时占用CPU。
OPENBLAS_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260909_ab_experiment_v1/src/analyze.py
```

模型训练与正式结果不能由命令清单推断完成，必须检查相应complete/results.json。

## 2026-09-09单线程修订后的正式入口

全部标签和12个模型已完成；旧16线程评测按用户要求停止并保留。原run_models_eval.py及重启恢复runner不再启动。正式入口为：

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  .venv_cpu/bin/python entry_method_exploration/20260909_ab_experiment_v1/src/run_single_thread_eval.py
```

该命令已通过独立session启动（控制器PID5513，日志`logs/controller_single_thread.log`），拒绝覆盖输出，请勿重复运行。内部为所有基线/方法生成`threads=1`的配置，并调用`bin/benchmark_single_thread`；分析只使用`single_thread_v1/results/`。设置错误会在启动前拒绝，结果另保存实际OpenMP线程记录。当前命令清单只说明执行身份；完整结果仍以新目录的完成状态为准。

## NSG补充比较

用户要求新增NSG后，已经通过独立session注册`src/run_baseline_comparison_after_single.py`（PID8259，日志`logs/controller_baseline_comparison_queue.log`）。它以pidfd退出事件等待当前单线程控制器5513，期间不运行编译或其他性能任务；完成后依次编译固定入口扩展、合成/真实图验收、NSG/Fast30K-3/Fast20K-3/A+B同批单线程评测和完整汇总。输出`baseline_comparison_v1/`，队列状态`baseline_pipeline.json`。

不能直接重复启动队列或旧控制器；新NSG编译/验收/测量目前为待执行，最终以对应acceptance/results为准。
