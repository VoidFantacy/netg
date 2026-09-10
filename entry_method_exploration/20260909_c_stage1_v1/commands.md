# 实际执行命令

以下为本轮已执行命令；输出采用拒绝覆盖策略，不能原路径直接复跑。工作目录均为`/data/netg/ACSG`。长搜索以`setsid`脱离交互终端，保留独立stdout/资源日志。每项精确argv、环境、UTC、退出码见[commands.jsonl](logs/commands.jsonl)。

最初输入准备及C0构建发生在durable launcher建立前，原始调用如下；其逐进程资源时间未单独记录，不补造：

```bash
cd /data/netg/ACSG
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/prepare.py prepare
bash entry_method_exploration/20260909_c_stage1_v1/src/build.sh calibrate > entry_method_exploration/20260909_c_stage1_v1/logs/build_calibrate.log 2>&1
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/prepare.py lock
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/extract_reference.py
```

下面逐条为实际child命令，其中`OMP_NUM_THREADS`、`OPENBLAS_NUM_THREADS`、`MKL_NUM_THREADS`、`NUMEXPR_NUM_THREADS`均为1：

- `c0_webvid`：

```bash
entry_method_exploration/20260909_c_stage1_v1/bin/calibrate entry_method_exploration/20260909_c_stage1_v1/inputs/webvid2_5m_light_v1/config.json entry_method_exploration/20260909_c_stage1_v1/results/calibration_webvid2_5m_light_v1.json
```

- `c0_yandex`：

```bash
entry_method_exploration/20260909_c_stage1_v1/bin/calibrate entry_method_exploration/20260909_c_stage1_v1/inputs/yandex_t2i_official10M_ip_v1/config.json entry_method_exploration/20260909_c_stage1_v1/results/calibration_yandex_t2i_official10M_ip_v1.json
```

- `build_parity_v1`：

```bash
bash entry_method_exploration/20260909_c_stage1_v1/src/build.sh parity
```

- `c1_synthetic_v1`：

```bash
entry_method_exploration/20260909_c_stage1_v1/bin/parity synthetic entry_method_exploration/20260909_c_stage1_v1/results/c1_synthetic_v1.json
```

- `build_parity_v2`：

```bash
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/build_version.py parity parity_v2
```

- `c1_synthetic_v2`：

```bash
entry_method_exploration/20260909_c_stage1_v1/bin/parity_v2 synthetic entry_method_exploration/20260909_c_stage1_v1/results/c1_synthetic_v2.json
```

- `c1_webvid_v2`：

```bash
entry_method_exploration/20260909_c_stage1_v1/bin/parity_v2 real entry_method_exploration/20260909_c_stage1_v1/inputs/webvid2_5m_light_v1/config.json entry_method_exploration/20260909_c_stage1_v1/config.locked.json entry_method_exploration/20260909_c_stage1_v1/results/c1_webvid_v2.json
```

- `c1_yandex_v2`：

```bash
entry_method_exploration/20260909_c_stage1_v1/bin/parity_v2 real entry_method_exploration/20260909_c_stage1_v1/inputs/yandex_t2i_official10M_ip_v1/config.json entry_method_exploration/20260909_c_stage1_v1/config.locked.json entry_method_exploration/20260909_c_stage1_v1/results/c1_yandex_v2.json
```

- `review_build_kernel_supplemental_v1`：

```bash
bash entry_method_exploration/20260909_c_stage1_v1/reviews/build_kernel_supplemental.sh
```

- `review_kernel_supplemental_v1`：

```bash
entry_method_exploration/20260909_c_stage1_v1/reviews/kernel_supplemental_v1 entry_method_exploration/20260909_c_stage1_v1/reviews/kernel_supplemental_v1.json
```

- `build_c2_v1`：

```bash
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/build_version.py c2 c2_v1
```

- `build_c2_v2`：

```bash
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/build_version.py c2 c2_v2
```

- `c2_smoke_webvid_v1`：

```bash
/data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/bin/c2_v2 /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/inputs/webvid2_5m_light_v1/config.json /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/config.locked.json /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/results/c2_smoke_webvid_v1 4
```

- `c2_smoke_yandex_v1`：

```bash
/data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/bin/c2_v2 /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/inputs/yandex_t2i_official10M_ip_v1/config.json /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/config.locked.json /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/results/c2_smoke_yandex_v1 4
```

- `c2_main_webvid_v1`：

```bash
/data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/bin/c2_v2 /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/inputs/webvid2_5m_light_v1/config.json /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/config.locked.json /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/results/c2_main_webvid_v1 2000
```

- `c2_main_yandex_v1`：

```bash
/data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/bin/c2_v2 /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/inputs/yandex_t2i_official10M_ip_v1/config.json /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/config.locked.json /data/netg/ACSG/entry_method_exploration/20260909_c_stage1_v1/results/c2_main_yandex_v1 2000
```

- `c2_offline_score_v1`：

```bash
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/score_c2.py
```

- `final_protection_audit`：

```bash
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/final_audit.py
```

stage控制调用（负责启动独立进程、budget reservation、持久日志和状态门）如下：

```bash
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py c1-gate
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py c2-run c2_smoke_webvid_v1 webvid2_5m_light_v1 4
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py c2-run c2_smoke_yandex_v1 yandex_t2i_official10M_ip_v1 4
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py smoke-gate
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py c2-run c2_main_webvid_v1 webvid2_5m_light_v1 2000
.venv_cpu/bin/python entry_method_exploration/20260909_c_stage1_v1/src/stage_control.py c2-run c2_main_yandex_v1 yandex_t2i_official10M_ip_v1 2000
```

执行入口外围实际采用`setsid ... > logs/<label>.launch.log 2>&1 < /dev/null &`；child与资源日志另存同label，不以脱离终端代替完成标记。
