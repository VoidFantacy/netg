# 第5独立串行会话安全交接

2026-09-13 14:05:12 +0800，E72–E74已完成并封存，**整日21:00用户目标未完成**。本会话14:17:57前结束；监督器安全接续下一唯一写入/实验会话，不开并行CLI或子代理。所有10个真实native job及编译/合成/分析工具均已terminal exit0，当前无遗留实验/训练/分析进程。磁盘7.1546 GiB，新三个阶段合计78,501,951 bytes；free门仍7GiB，不清理旧产物。

## 当前结论

E72真实hub计宽distinct10保留Y对P局部正值，但双集原接续门失败，停止该版本，0QPS。E73同hub字节精简把2445/2463画像变成1771/2067，完整每hub max评分集合保持；Y完整aux7952对P +120命中/失败−13、对fullmode +71/−9，两半均正，质量门过；Web对P−59/失败+11，未过门。

E74固定精简候选同批55点275轮完整wall。Y对GT10-hard/P10五L净命中+99/+59/+38/+1/+15，失败−10/−7/−4/−1/0，QPS中位−1.565/−.961/−1.204/−.043/−.195%；QPS范围均跨零，描述性共同Recall插值+1.873/+2.455/+2.965%。保留Y局部前沿信号，未成为实测等Recall或独立最终验证。Web对匹配soft/P10五L+9/−23/+2/+28/+2、失败+2/+6/0/−1/+1，QPS中位略负、范围跨零；L128损伤明确，无稳定整体改善或默认替换。

[E74完整报告](stage15_compact_wall_v1/report.md) · [判断](stage15_compact_wall_v1/assessment.md) · [QPS–Recall](stage15_compact_wall_v1/figures/recall_qps.png) · [QPS–失败率](stage15_compact_wall_v1/figures/failure_qps.png) · [按L三指标](stage15_compact_wall_v1/figures/three_metrics_by_L.png) · [配对图](stage15_compact_wall_v1/figures/paired_deltas.png) · [失败query图](stage15_compact_wall_v1/figures/failure_query_cases.png)。五图另有SVG/PDF，均亲自查看且主监督独立验收。

失败严格零GT10命中，91个独立query、174个跨L事件、455个五L格。Web52/Y39个query、事件92/82；图每集24例，全量[失败CSV](stage15_compact_wall_v1/results/failure_query_summary.csv)保留。Y row2769全零变8/9/10/10/10，row3846全10变全0；Web3524全零变全7，2391变全零。救回和损伤都保留，事后案例不作在线选择器。

## 实际成本和验收

本会话新增1,080,816 NSG、936,000 HNSW、2真实小图；合成另4图/512HNSW/0NSG。10native总1341.027969秒、编译42.048536秒，E73精简0.030671799秒、两图build0.348454841秒。E74其中789360 NSG/645120 HNSW、275次独立完整wall合计772.446310秒，45plain+45count源图加载、0复制/新build。没有新画像训练、GT或梯度；继承E66画像训练30.286秒和早期GT等成本不记零，未重测项null+reason。

今日累计4,316,756 NSG、4,729,056 HNSW、348真实build，220开发点/1100wall；**final validation点仍0**。各阶段/批次成本分列，曲线不跨批拼接。所有真实查询CPU15/进程threads1和OMP/OpenBLAS/MKL/NUMEXPR/BLIS1；方法串行，完整路由/映射/原NSG/output在wall内，GT/count/hash/JSON/build/load在外。两个E74工具terminal0后才评分/绘图。

E74独立112640集合/mask、880原kernel、40960整行slot及五L身份、45图、275轮计时恒等和旧输出回归通过；本会话只读接续检查5968身份通过，最终session seal后再核查新增快照。主监督13:56已通过E72/E73原始与最终seal及E74raw/计时/五图，14:01通过32候选库存与更正；E74最终seal主监督可随后只读验收，不需等待许可。

**覆盖更正**：E72协议的“不足3hub拒绝”没有实际合成调用；末尾只测引用计数下溢，运行时有require不等于负例已测。[独立记录](reviews/e72_synthetic_scope_correction_session5.md)保留原E72封存，不为补标签重跑。E73/E74普通variable路径不含distinct回调。

根文档已同步；详细历史为[61](../../experiment_history/61_distinct_hub_width.md)、[62](../../experiment_history/62_compact_modes.md)、[63](../../experiment_history/63_compact_wall.md)。每阶段source_before/root_after和final_artifact_freeze均保留。原脏代码、旧图、GT、日志和全部原始结果未清理；全树git diff --check仍有既有源码/构建空白告警，本轮文档另作范围检查，不改无关脏源。

## 角色和下一命令

P-fit20K包含旧4096train/1024monitor；旧cal/audit/aux7952均历史暴露，任何辅助选择反馈都算训练。E74 source router_train[2048:4096]包含于已用aux7952；不能当新盲集。E34历史validation2000今天尚未进入，只供晚间冻结后最终对照，不回流训练/选型；held-out不自动打开，元数据余行不能证明全项目未使用。

[candidate_inventory_v5](candidate_inventory_v5.json)逐项保留v4旧24，另6个distinct配置和2个compact，共32且含控制；E74显示best_new=compact不是全局最终重选。原NSG/base/rawIP/GT/815或821真实H固定，Micro-HNSW只有这些真实hub的画像，非10M底图。

在项目根目录执行只读接续检查：

```bash
env PYTHONDONTWRITEBYTECODE=1 .venv_cpu/bin/python entry_method_exploration/20260913_until2100_v1/src/resume_inspect_v5.py
```

然后读[下一阶段设计](next_stage_design_session5.md)及[监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。阶段1–15全部完成，禁止重跑旧runner。监督review_078已经做compact排序/实际效用分组，先读原记录而不重复分析。

最有依据的下一受控方向：先0ANN核对保留slot随机层级，再独立版本实现“删槽时消耗原随机数、保留槽普通addPoint”的唯一新图控制；注意level=0接口不强制零层，保留层级不保持邻接，最高入口被删除时header可变。完整协议/预算/门已在design写成未运行草案，后继启动前冻结；不扫seed/ef，不要求本会话赶新实验。第二方向是Web画像实际损伤与支持关联的缓存诊断，第三是晚间冻结并完成最终对照。

20:00停止新训练，20:40停止新增查询，21:00完整报告。最终包含NSG/Fast30K/GT10-hard/Web匹配起点/best_all/真实best_new，在同批五L五轮完整计时并绘图，先冻模型再开E34反馈。现授权足够串行实施，不重复问批准；不得删除、外发、发布、推送或改Codex配置。
