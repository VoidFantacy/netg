# E26 执行与复核入口

工作目录`/data/netg/ACSG`，解释器`.venv_cpu/bin/python`。以下记录本轮阶段顺序；已有结果不可直接重跑。runner拒绝已有输出、重复job名和调用超额，未来复现应另立版本、锁定协议，不删除原件绕过限制。

```bash
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/initialize.py initialize
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/build.py
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/build_profiles.py
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/check_synthetic.py
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/run_development.py recovery
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/run_development.py cal
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/select_alpha.py
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/initialize.py audit
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/run_development.py audit
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/audit_report.py
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/check_transitions.py cal
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/check_transitions.py audit
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/initialize.py validation
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/run_validation.py
```

真实评测统一由`jobs.py`启动`taskset -c 15 bin/evaluate <config> <new-output>`；线程配置、OMP/OpenBLAS/MKL及实际进程线程均为1，dynamic=false。每次一个被测方法，计时期间无并发训练、编译或其它性能测试。完整argv、config/binary hash、进程、预留/实际调用和资源使用见[真实job账](reviews/search_jobs.json)，合成另见[合成账](reviews/synthetic_jobs.json)。日志在`logs/<job-name>.log`。

查询全部结束后才进行下列分析；数值库线程同样限制为1：

```bash
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/check_transitions.py validation
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/analyze.py
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/verify_integrity.py
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/figures_tables.py
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/costs_and_cases.py
.venv_cpu/bin/python entry_method_exploration/20260910_profile_shrinkage_v1/src/write_report.py
```

四张PNG实际视觉检查后记录`reviews/visual_checks.json`；先更新历史15和索引，再同步根四文档。最后执行`src/finalize.py`核对最终产物、文档链接、115项上游资产、冻结身份和全部调用/输出，并写入最终状态、验收与交付manifest。

本轮真实查询job均一次成功，修复调用0；编译仅有既有vendor警告。开发前将易与Python标准库冲突的选择脚本名改为`select_alpha.py`，未发生相关查询失败或改变协议。所有原E25及更早源码、结果、图、GT和模型保留。收口时间按[用户最新更新](authorization_update.md)，不修改已锁协议或候选。
