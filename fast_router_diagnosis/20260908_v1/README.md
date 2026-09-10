# Fast入口诊断复现说明

结论见[report.md](report.md)，冻结范围见[protocol.md](protocol.md)。真实搜索已经完成；当前正式分析为`analysis/v2`，原始矩阵为`results/run_v1/main`，最终输入为`inputs/prepared_v2`。所有路径以`/data/netg/ACSG`为工作目录。

## 直接复算已有矩阵的统计

先查看帮助；使用未存在的输出目录。此步骤不搜索图、不训练模型、不打开原始validation/held-out。

```bash
.venv_cpu/bin/python fast_router_diagnosis/20260908_v1/tools/analyze_results.py --help
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv_cpu/bin/python fast_router_diagnosis/20260908_v1/tools/analyze_results.py \
  --input-root fast_router_diagnosis/20260908_v1/inputs/prepared_v2 \
  --results-root fast_router_diagnosis/20260908_v1/results/run_v1/main \
  --output fast_router_diagnosis/20260908_v1/analysis/reproduce_v1 --plots
```

验收：`completion.json`为COMPLETE、32主对比齐全、全部输入SHA/shape与返回ID→GT mask核对通过；结果应与analysis/v2的数值相同。时间、创建时刻及新输出路径不要求相同。合成算术验收命令为同脚本`--self-test`；独立复算均值、bootstrap流及区间端点的证据见[统计复核](reviews/independent_analysis_review.md)。

## 原搜索的精确命令与身份

四条实际命令、PID/PGID/启动身份、wall/RSS、日志和退出码见[results/run_v1/jobs.json](results/run_v1/jobs.json)。输入/编译对象SHA分别见[execution_freeze.json](results/run_v1/execution_freeze.json)、[build_manifest.json](bin/build_manifest.json)，程序语义见[src/README.md](src/README.md)。

历史controller `tools/run_diagnosis.py` 使用本次固定的`*_v1.log`并拒绝覆盖，不能更换output后直接重用它当通用重跑器。保留原日志和state。重放单个数据集时先使用原runner帮助和一个新的输出路径，例如：

```bash
fast_router_diagnosis/20260908_v1/bin/fast_router_diagnosis --help
OMP_NUM_THREADS=16 OPENBLAS_NUM_THREADS=1 \
  fast_router_diagnosis/20260908_v1/bin/fast_router_diagnosis \
  --config fast_router_diagnosis/20260908_v1/inputs/prepared_v2/webvid2_5m_light_v1/runner_config.json \
  --output fast_router_diagnosis/20260908_v1/results/reproduce_parity_webvid \
  --parity-queries 8 --parity-only
```

仅当该输出的parity为PASS且来源身份未变，才可把同一config的`--parity-queries`改为0、去掉`--parity-only`并使用另一个全新output来重放main。Yandex使用其对应config。不要并行启动两个重进程；完整重跑需另立执行版本，保留本轮300万调用/4小时、16线程、80GiB RSS、2GiB新增和10GiB磁盘余量约束及独立进程控制。以上命令是复现说明，本交付没有再次启动搜索。

如需重编译，`src/build.sh`接受源码和**新的二进制路径**两个位置参数；默认输出会覆盖本次binary，故不可无参数调用。库/编译器身份改变后必须新版本重验，不能混用旧验收。

## 文件口径

- `all_single`为767/768 ×815/821，每L独立保存；`pilot`为512×91。每动作保存hitcount u8、GT10 hitmask u16、NDC u32、返回top10 ID i32；输入GT为headerless i64。
- `exact.rank_local.i32`及`fast.top8_local.i32`保存hub局部行号；映射到真实base ID必须读取同目录`hub_ids.i32`。动作入口在`pilot.entry_local.i32`中，padding为-1。
- `A0`是全部并列最佳Recall入口；最优代表按最高Recall、最低该动作NDC、最小真实base ID选择。`A1`允许少一个GT10命中。最近源的选择不能查看目标query的标签。
- v1→v2分析仅修复NDC记账并补列，搜索矩阵和Recall推论未变。成本复算使用`tools/collect_costs.py --help`；正式结果为`results/costs_v2.json`，修正了v1把route开始事件当路由结束的误读，缺失计时明确为null。
- 本目录是离线诊断交付；当前行动以项目[s-target.md](../../s-target.md)为准。三入口组合模型及旧夜间/分层/Multi-view计划未重启。
