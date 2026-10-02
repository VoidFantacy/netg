# 2026-09-13 首个独立研究会话交接

状态：`SESSION_PHASE_COMPLETE_SAFE_HANDOFF`，E60/E61/E62均已封存验收。当前会话约08:49启动，10:15前退出；整日21:00目标未完成。全部原生训练/评估工具session均已实际返回并回收，native_pids为空，无监督接管PID。用户今日研究授权持续，无需重复批准；后续由监督者串行启动下一会话，不同时开CLI/子代理。

## 确切结论与报告

- [E60 固定动作支持](stage1_support_v1/report.md)：E53双seed各20固定状态、三原确定动作，在历史cal/audit检查支持。双集0/40通过，约束全不动。WebVid辅助正动作9个仅来自5状态，且均train-J负；不能把无支持仅归为zero-hit惩罚过强。停止同类局部动作扩大。
- [E61 全fit遗漏画像](stage2_missing_targets_v1/report_v2.md)：实际实现lambda0.5真实遗漏GT10成员画像及随机目标控制，原P回归后冻结六模型。missing的fit/cal/audit ΔRecall：WebVid−0.1020/−0.3906/+0.0195 pp，Yandex−0.0260/−0.1465/+0.0684 pp；cal均新增净3条零命中。虽入口作用扩大，fit本身净负，不能只归为迁移失败。原零命中救回45/32条保留，但原全命中14/20条变零命中。report_v2只澄清40,000 fit+4,096开发缓存行，旧报告/源码/manifest保留。
- [E62 评分/拓扑四格](stage3_missing_factorial_v1/report.md)：固定E61端点C/A/S/T，S仅变评分、T仅变拓扑。S的cal −0.1855/−0.1953 pp，T −0.1758/−0.0488 pp，双集仍选C。WebVid T fit +0.007 pp局部信号保留，cal/audit负。34原全命中→零命中案例中，仅S零6/11、仅T零4/7、两者各自都零1/1、只有联合A零3/1；不能把损伤全部归给图或声称冻结评分足以解决。

三阶段没有替换原GT10-soft(WebVid)/GT10-hard(Yandex)，没有新正式QPS。失败定义严格为返回top10与exact GT10交集为空，hits=1不算失败。每阶段图均有PNG/SVG/PDF并已亲自查看，E62见[四格及失败图](stage3_missing_factorial_v1/figures/factorial_and_failures.svg)。主监督另只读复核E60/E61/E62，与本会话结果一致。

## 实际成本、保护与执行修正

| 阶段 | 新NSG | HNSW路由 | 小图构建 | 原生阶段含加载秒 |
|---|---:|---:|---:|---:|
| E60 | 17830 | 660640 | 322 | 63.127 |
| E61 | 28484 | 133056 | 6 | 34.190 |
| E62 | 19030 | 177408 | 8 | 29.754 |
| 合计 | 65344 | 971104 | 336 | 127.071 |

这些是开发/标签操作成本，不是QPS；E62另4次拓扑安装。画像聚合8.617秒、独立聚合验收15.799秒和数据身份准备另计，旧标签成本不当零。0新GT/梯度更新/正式QPS。缓存、路由、NSG、构建、安装、评分、I/O分项在各results/cost.json和逐状态identity.json；正式性能不能用缓存阶段wall或NDC代替。

E62首次只读分析早于Yandex原生退出，因query_complete尚未生成而退出。原analyze.log及reviews/execution_note.md保留，补双job完成门、核验工具terminal退出后已重跑通过。Yandex该段操作wall含短暂评分重叠，不能称严格独占性能。native始终仅一个，CPU15实际线程1；后续必须等待工具session实际exit，完成标记只是辅助。

昨日final_artifact_freeze的39项已再次通过：昨日历史文件原位不变；当时根文档/experiment_history README身份映射到本日source_before旧快照。当前根文档及README合法同步至E62，不用旧SHA阻止更新。E60 1488文件、E61 128文件、E62 124文件分别冻结；E61文字修订另存correction manifest。根文档after冻结的是各阶段快照，后续可合法更新当前根文件。未清理脏树，未删除旧产物/向量/图/模型/日志，未更改Codex配置/身份，未发送外部消息/推送。

当前资源、会话目录输出字节、完整成本与退出时间见[session closeout](reviews/session_closeout.json)。初始/data空余7.984GiB，收口约7.7GiB；后续启动现场核对，保持至少7GiB且单阶段压缩产物≤192MiB，不删除历史。

## 数据角色与下一命令

每集P-fit=router_train本地10000:30000的20K，包含旧4096 train及1024 monitor，旧monitor不盲。cal0:1024、audit1024:2048均历史及今日重复使用。Fast30K曾使用全router_train，不能宣称未命名行全新。不同query文件命名空间的数值ID相同不等于数据重叠。所有反馈用于动作接受/候选选择计开发训练。E34历史validation2000未进入本会话输入或反馈，只能用于后续冻结最终比较。

下一会话先完整读AGENTS、summary、spec、s-target、s-experiment和本交接，再读[next_stage_design](next_stage_design.md)、[next_input_inventory](next_input_inventory.json)及相关历史卡。可复制的第一条只读命令：

```bash
cd /data/netg/ACSG
env PYTHONDONTWRITEBYTECODE=1 .venv_cpu/bin/python entry_method_exploration/20260913_until2100_v1/src/resume_inspect.py
```

它只查阶段SHA、候选图、已完成jobs和资源/现存进程，不运行ANN或训练。禁止直接重跑E60–E62已经完成的run脚本；其旧09:50启动/10:00查询硬停仍保留。新方法必须新目录，例如`stage4_zero_hit_mass_v1`，独立protocol/config/src和新的会话截止时间，不能复用过期时间常量。

下一优先备选为保持原GT10归属、仅对原P零命中query增加2倍训练质量，归一总质量20K，加入同数量随机query身份控制；它与E09单入口signed/hardness residual不同，但不宣称难度重权创新。尚未实现/运行，监督者或下一会话可按证据前瞻调整；本轮没有证明它会有效。具体矩阵/输入/质量恒等/预算/停止规则见设计。此前同局部动作扩大、遗漏成员lambda扫描、去掉评分或拓扑都停止。

## 晚间必须交付的未完成工作

至少最后一小时保留正式性能与独立验收：20:00停止新训练，20:40停止新增查询，21:00交付。新的最终协议先用开发数据冻结best_all（允许原方法）和best_new（今天实际新方法，仅供诚实诊断展示），[candidate_inventory](candidate_inventory.json)已保存10个端点及W/图/映射身份。S/T必须加载物理图，不能按W普通重建；sham是诊断控制，不是本轮可选推荐。best_new当前未选择；即使没找到稳定改进，也须展示今天实际失败候选和同批NSG/Fast/FastGT10/匹配起点，不仅复用昨天曲线。

正式全部CPU15 threads1、OMP/OpenBLAS/MKL/NUMEXPR/BLIS1；一个方法一次运行，无训练/标签/评分并发。五L五轮、纯端到端整批wall、GT/计数/序列化不入timer；aligned返回和零命中定义验收。以同机Recall–QPS前沿判断，不由同L Recall/NDC/一轮QPS声称进步。E34重复最终评估反馈不回流选型或训练。用户整日目标保持未完成。
