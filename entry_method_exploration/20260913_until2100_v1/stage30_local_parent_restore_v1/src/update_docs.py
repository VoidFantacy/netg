from common import *
import csv
threads();resources();g=read(O/'results/gate.json');cost=read(O/'results/cost.json');assert read(O/'reviews/verification.json')['status']=='PASS'
cor='\n记录范围补充：协议要求在查询前给出未入选原因，实际只冻结了全事件、资格、排序规则和候选；显式[逐hub原因表](results/proposal_reasons_postfreeze.csv)在查询后从这些冻结输入重建，[更正](reviews/proposal_record_scope_correction.json)保留此时间边界。候选/模型/规则不变，没有额外ANN。\n'
with (O/'report.md').open('a') as f:f.write(cor)
history=R/'experiment_history/78_local_parent_restore.md'
history.write_text('# 78｜真实效用筛选局部父画像恢复（E89）\n\n两集完整门FAIL，停止此固定候选/全恢复/筛选版本。Web局部修复保留，Y训练收益未迁移，不替换默认。\n\n候选由P更好完整策略中compact独有且实际由子画像代表的hub提议，最多32/集；每次两子行逐字恢复父P，所有slot/邻接/层级/入口不动。全fit真实NSG效用筛选13/8个hub，合并重测；随机同数量恢复为控制。不是全局半收缩、低ESS剪枝、加边或单hub代理效用。\n\nWeb单项和297→并图224，186query非加性，fit失败−27；Y125→114，6query非加性，失败−10。辅助对compact Web+18命中/失败−6、对P−41/+5、对随机−11/−5；Y对compact−39/+5、对P+81/−8、对随机−43/+5。均未过完整接受门，不按结果改候选/阈值/幅度。\n\n新增182698NSG（20778训练+161920辅助）、2962624HNSW、6向量安装、2离线效用筛选拟合，0普通build/梯度/GT/QPS。编译13.194s，训练操作62.750s、辅助130.076s，不作QPS；继承GT/P成本未知。当前E73同SHA线上评测器与E69原NSG注入复用，新E89 helper只离线暂改/撤销图向量。\n\n全部缓存/集合/mask、64动作、合法来源、随机名单、6图非向量bytes、原kernel/物理首动作/撤销恢复/三个旧辅助对照验收通过。427失败query并集/193状态变化/2135完整五配置单元保存。拟合含旧train/monitor，aux及两半/cal/audit历史暴露；接受反馈算训练。E34最终与held-out未打开。\n\nPython wrapper草稿计数变量遮蔽在编译/训练冻结前修正，无失败ANN；未入选原因显式表查询后补录，原冻结输入/规则及候选不变，不能称该表在查询前存在。\n\n[报告](../'+str(O.relative_to(R))+'/report.md) · [协议](../'+str(O.relative_to(R))+'/protocol.md) · [训练](../'+str(O.relative_to(R))+'/src/train.py) · [门](../'+str(O.relative_to(R))+'/results/gate.json) · [成本](../'+str(O.relative_to(R))+'/results/cost.json) · [训练核验](../'+str(O.relative_to(R))+'/reviews/training_verification.json) · [查询核验](../'+str(O.relative_to(R))+'/reviews/verification.json)\n')
p=R/'s-experiment.md';s=p.read_text();needle='| E88 提议排名与实际响应诊断';at=s.index(needle);s=s[:at]+'| E89 局部父画像恢复 | 32hub/集实际两子行恢复、13/8效用筛选、并图与随机控制 | `COMPLETE_LOCAL_PARENT_RESTORE`；Web aux对compact+18/失败−6，Y−39/+5，双集门FAIL，182698NSG/0QPS | [78 父画像恢复](experiment_history/78_local_parent_restore.md) |\n'+s[at:];s=s.replace('当前最近完成记录为E88提议排名与实际响应诊断','当前最近完成记录为E89局部父画像恢复');p.write_text(s)
p=R/'experiment_history/README.md';s=p.read_text();s+='\n- [78 局部父画像恢复（E89）](78_local_parent_restore.md)：单组真实NSG效用筛选与固定图并图，双集接受门失败。\n';p.write_text(s)
(R/'summary.md').write_text('''# ACSG 当前结果摘要

2026-09-13第10串行会话E89局部父画像恢复已完成，双集接受门FAIL，默认未替换。整日21:00目标未完成，E34最终完整矩阵仍待运行。

| 数据 | 接受hub/32 | fit单项和→实际并图 | fit失败变化 | aux对compact命中/失败变化 | aux对P | aux对随机 |
|---|---:|---|---:|---|---|---|
| Web | 13 | 297→224，186非加性query | −27 | +18/−6 | −41/+5 | −11/−5 |
| Y | 8 | 125→114，6非加性query | −10 | −39/+5 | +81/−8 | −43/+5 |

E89针对P完整策略更好、compact额外选中的子画像hub提出恢复；每个动作将该hub两子行逐字复制原父P，原1771/2067slot、815/821真实入口、全部图邻接/层级/入口保持。实际全fit效用筛选后合并重测，线上仍单小图七slot去重三入口与原NSG。完整策略差只提议，不作单hub信用。

Web局部失败修复保留，但未胜P或随机控制；Y损失原compact增益。训练224/114命中增量不能当迁移/性能结论，原固定版本停止，不扩候选或扫恢复强度。所有真实响应、损益迁移、相互作用及随机控制保留。

新增182698 NSG/2962624 HNSW、6向量安装、2离线效用筛选拟合，0普通build/梯度/GT/QPS。编译13.194s，训练/辅助操作62.750/130.076s包含load/count/cache/I/O，不作QPS。继承GT/P总成本未知。全部ANN串行CPU15，实际进程及各库1线程，原kernel/缓存/原P与compact和E84对照回归通过。

427条失败并集、193条状态变化，完整五配置GT10/入口/返回保存。P-fit含旧train/monitor，aux7952及两半/cal/audit历史使用，接受反馈计训练；E34最终query/GT/row及held-out未打开。未入选原因表在查询后从预冻事件/规则补录，候选不变，时间边界明确披露。

旧正信号保留：E84 Web对compact+42/失败−4仍未及P；E73/E74 Y五L对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0，但五轮QPS范围跨零。最近完整QPS仍E74，不与E89质量点拼曲线。

[E89报告](entry_method_exploration/20260913_until2100_v1/stage30_local_parent_restore_v1/report.md) · [失败全表](entry_method_exploration/20260913_until2100_v1/stage30_local_parent_restore_v1/results/failure_queries.csv) · [最近完整QPS](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [下一阶段](s-target.md)。原E86–E88报告、根文档前件及历史卡完整保留。
''')
(R/'s-target.md').write_text('''# ACSG 下一阶段目标与接续

第10唯一串行会话，2026-09-13 19:21:48前安全交接；整日目标仍进行中，不开子代理或并行CLI。

1. E89完整停止：局部父恢复13/8hub训练净+224/+114，aux对compact+18/−39、失败−6/+5，均未过P/compact/随机完整门。不改候选/恢复强度/阈值，保留Web失败修复和Y原compact信号。
2. 可证伪的下一小步是检验E89这些已确定实际局部动作在另一源区间的支持：原P-fit及辅助前半均用于训练接受，辅助后半只作该新版本冻结后的整体模型检验，全部历史暴露仍明确。它与E60稀疏小半径RL固定状态不同，但跨源支持本身不是新概念；须另立协议、实际单项/合并响应及预算，不能传播旧反事实或把不动称成功。当前此方向尚未执行。
3. 继续优先保留晚间E34最终完整矩阵。20:00停新训练，20:40停新增query，21:00交付。只用暴露开发反馈冻结实际best_all/best_new及别名/选择规则后才开历史validation2000；最终反馈不回流，held-out不打开。原NSG/Fast/GT10-hard/Web匹配soft/实际新方法，同批五L五轮CPU15/实际与库1线程，完整wall及独立集合/zero失败/全部图表。

资源：session10全部新输出192MiB，E89阶段128MiB，额外晚间64MiB/交接8MiB，前瞻floor6.45GiB；大文件只/data，不清理旧封存。每新阶段预算需计入已完成E89全部文件，先检查剩余额度。

[E89报告](entry_method_exploration/20260913_until2100_v1/stage30_local_parent_restore_v1/report.md) · [campaign state](entry_method_exploration/20260913_until2100_v1/state.json) · [最终元数据准备](entry_method_exploration/20260913_until2100_v1/session9_final_preparation/readme.md) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。当前候选目录不等于最终选择，最终2000行不能套旧2048分析硬编码；E73 evaluator不支持distinct回调。
''')
p=R/'spec.md';s=p.read_text();s+='''

## E89 局部父画像恢复接口（2026-09-13）

[Routes](entry_method_exploration/20260913_until2100_v1/stage30_local_parent_restore_v1/src/routes.cpp)复制已验E86 public Policy，只在离线两个plain/count图的对应两子行暂时安装同hub父P，结束/异常恢复原W bytes；Policy.w作为不可变参考，线上多画像查询读取图向量。run(hub,rows)显式支持前缀长度，原生返回容量和请求rows分离；原NSG/hnswlib不变。物理首动作128与撤销后的原route128、全fit plain/count七slot/距离bits验收。

[trainer](entry_method_exploration/20260913_until2100_v1/stage30_local_parent_restore_v1/src/train.py)按完整fit真实效用筛选固定32候选，全部合格两行恢复一次合并，固定PCG64从其余双子hub抽同数量控制。W.f32和序列化graph向量同步导出，所有非向量字节、slot/映射/原父P保持，仍用原E73 evaluator加载。完整三入口缓存沿E87的P/mode/compact/新键四来源，routeNDC不复用。单动作patch、完整并图、随机名单/排列、逐query交互保持独立artifact；独立接受不保证合并或泛化收益。

画像/候选/反馈角色或图/metric/NSG/L/K/完整入口改变需要新协议/真实响应，不能复用旧单项增量模拟新联合图。全部模型/辅助集合和图字节已验收，方法判断由summary/历史78维护，0本阶段QPS。显式未入选原因表查询后从冻结输入补录，时间边界见[更正](entry_method_exploration/20260913_until2100_v1/stage30_local_parent_restore_v1/reviews/proposal_record_scope_correction.json)。
''';p.write_text(s)
for f in ['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
 dest=O/'root_after'/f;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/f,dest)
s=read(C/'state.json');assert s.get('stage30_status')!='COMPLETE_LOCAL_PARENT_RESTORE_NO_GATE';s.update(status='E89_COMPLETE_SAFE_STAGE_BOUNDARY',stage30_status='COMPLETE_LOCAL_PARENT_RESTORE_NO_GATE',stage='E89_complete',total_new_NSG=s['total_new_NSG']+cost['NSG'],total_HNSW=s['total_HNSW']+cost['HNSW'],session10_NSG=cost['NSG'],session10_HNSW=cost['HNSW'],session10_compile_seconds=cost['compile_seconds'],session10_training_aux_operation_seconds=cost['training_operation_seconds']+cost['aux_native_operation_seconds'],session10_failure_union_queries=427,session10_changed_failure_queries=193,native_pids=[],offline_pids=[],session10_final_feedback_used=False,next_action='E89 stopped; consider independently frozen source-support experiment, preserve evening final matrix time.');dump(C/'state.json',s)
freeze(O/'reviews/final_artifact_freeze.json',[p for p in O.rglob('*') if p.is_file()]);print('E89_DOCUMENTED_SEALED')
