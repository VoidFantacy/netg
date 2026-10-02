# E25 执行与核验入口

工作目录`/data/netg/ACSG`，解释器`.venv_cpu/bin/python`。以下是本版本阶段顺序；已有目录不可直接重跑，runner拒绝覆盖输出、重复job名或突破调用账。未来复现应建立独立版本并重新锁协议，不能删除原结果绕过限制。

```bash
.venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/initialize.py initialize
.venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/build.py
.venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/check_synthetic.py
.venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/run_pairs.py recovery
.venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/run_pairs.py fit
.venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/run_pairs.py cal
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/train.py
.venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/initialize.py audit
.venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/run_pairs.py audit
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/audit_report.py
.venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/initialize.py validation
.venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/run_validation.py
```

所有真实搜索均由`jobs.py`启动`taskset -c 15 bin/evaluate <config> <new-output>`，显式threads=1、OMP/OPENBLAS/MKL=1、dynamic=false，检查/proc实际线程、RSS、进程时间、输出/磁盘和调用预算。每个方法依次运行，未并发训练/构建/其它测量。

实际完整argv、config/binary hash、PID、预留及实际调用、起止状态和进程资源见[真实调用账](reviews/search_jobs.json)；合成另见[合成调用账](reviews/synthetic_jobs.json)。每个job的日志在`logs/<job-name>.log`，配置在`configs/<job-name>.json`。

只读分析在全部查询结束后运行：

```bash
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/analyze.py
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/verify_integrity.py
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/figures_tables.py
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/costs_and_cases.py
.venv_cpu/bin/python entry_method_exploration/20260910_selective_profile_gate_v1/src/write_report.py
```

初次输入准备因缺少`Path`导入在创建数据集输入前失败，原`logs/initialize.log`保留；修复后的`initialize_v2.log`通过，协议锁未改变，无真实调用发生。首次预检编译后补上真实ID范围拒绝检查，在任何真实搜索前重新构建；初版`bin/evaluate_initial_preflight`及build记录保留。全部真实查询job均一次成功，修复调用预算使用0。报告细化记录在`write_report.log`和`write_report_v2.log`，没有重新测量或修改模型。
