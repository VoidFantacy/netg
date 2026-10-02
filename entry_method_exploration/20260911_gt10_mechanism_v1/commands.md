# E27实际执行与重放边界

工作目录`/data/netg/ACSG`。这些是本轮已执行记录，不是待启动队列。脚本/控制器拒绝已有完成分析、冻结配置或账本；旧资产不得覆盖。

1. 完整读取根五文档与历史13/14/15、E24–E26原协议/代码/manifest/结果。创建独立目录和根文档快照，既有分析协议新增查询上限0。
2. `PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 .venv_cpu/bin/python -u entry_method_exploration/20260911_gt10_mechanism_v1/src/analyze_existing.py`。首轮GT1 manifest schema读取错误，日志`logs/existing_analysis.log`；修正新读取器后同命令成功，日志`logs/existing_analysis_v2.log`。没有真实搜索。
3. 同8线程环境执行`src/analyze_target_links.py`；执行`src/write_existing_report.py`生成已有A–C报告，补测前明确局部exact缺口。两个脚本均不调用ANN/NSG。
4. 冻结`supplement/protocol.md`后，在8线程离线环境执行`src/prepare_supplement.py`，一个固定排列/数据集一份控制。实际编译argv、源码和binary身份在`supplement/bin/evaluate.build.json`。
5. `PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv_cpu/bin/python -u entry_method_exploration/20260911_gt10_mechanism_v1/src/run_supplement.py`。9个child job均通过`taskset -c 15`，实际argv、配置、预算、PID、耗时、RSS和线程在[supplement/reviews/search_jobs.json](supplement/reviews/search_jobs.json)。两恢复先验收，随后固定shuffle/局部exact，最后WebVid重复wall；无并发评测。
6. 搜索全部结束后，1线程环境运行`src/analyze_supplement.py`、`src/write_tables.py`、`src/figures.py`；生成最终报告并同步根文档/历史。
7. `src/final_audit.py`核验原5634文件及上游hash、锁/预算/独立标量画像参考、文档链接和状态。结果见[最终验收](reviews/final_audit.json)，成本见[完整成本边界](results/costs.json)。

每步stdout/stderr保存在`logs/`或`supplement/logs/`。没有安装新依赖、没有外部消息/发布、没有新方法训练或held-out读取。初次只读分析失败的外部wall未单独记录，不能伪造为0；真实搜索九个job全部一次成功。

最终审查首轮发现成本总表在文档链接检查之后才生成；已调整新审查器的生成顺序并补齐总表，日志`logs/final_audit.log`保留，复验使用`logs/final_audit_v2.log`。这仅为交付文件顺序修正，无新搜索。
