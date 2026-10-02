from pathlib import Path
import json,hashlib,shutil,time,re
C=Path(__file__).resolve().parents[1];R=C.parents[1];O=C/'stage19_child_mass_norm_v1'
def ident(p):
 p=Path(p);s=p.stat();return dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not (O/'reviews/final_artifact_freeze.json').exists()
assert json.loads((O/'reviews/verification.json').read_text())['status']=='PASS'
assert not json.loads((O/'results/gate.json').read_text())['wall_measurement_allowed']
assert all(j['status']=='COMPLETE' for j in json.loads((O/'logs/jobs.json').read_text()))
# Detailed history first; rebase only relative report links.
history=R/'experiment_history/67_child_mass_norm.md';assert not history.exists()
report=(O/'report.md').read_text()
report=re.sub(r'\]\(([^)]+)\)',lambda m:'](../entry_method_exploration/20260913_until2100_v1/stage19_child_mass_norm_v1/'+m.group(1)+')',report)
history.write_text(report)
p=R/'s-experiment.md';t=p.read_text();needle='|---|---|---|---|\n';assert t.count(needle)>=1
row='| E78 固定图子质量范数 | rho^(1/d)与同平均log缩放对照；P/图/方向保持 | `COMPLETE_CHILD_MASS_NORM`；Web对compact净0，Y−44/失败+3，双集原门失败；129536 NSG/0QPS | [67 子质量范数](experiment_history/67_child_mass_norm.md) |\n'
t=t.replace(needle,needle+row,1).replace('当前最近完成记录为E77子画像半收缩四格','当前最近完成记录为E78固定图子质量范数');p.write_text(t)
p=R/'experiment_history/README.md';p.write_text(p.read_text()+'\n- [67 E78 固定图子质量范数](67_child_mass_norm.md)：质量占比与统一降权控制，旧收益保留/新损伤分列，双集门失败。\n')
(R/'summary.md').write_text('''# ACSG 当前结果摘要

2026-09-13，第6串行会话完成E75–E78。保留原层级、子方向半收缩、固定图质量占比权重均未通过各自预锁门；E73/E74 Yandex局部前沿信号保留，尚无稳定整体改进。整日21:00目标未完成，E34晚间最终未进入。

E78保持compact图全部非向量字节，子画像乘rho^(1/d)且不再单位化，rho仅来自P-fit子模态质量占比；P首槽不动。统一缩放控制匹配平均log权重，区分占比信息和一般降权。原H815/821、ef10、7slot去重三入口、原NSG/rawIP固定。

| aux7952主候选相对compact | 净GT10命中 | 失败净新增 | 原正命中保留 | 避免旧损失 / 新增损失 |
|---|---:|---:|---|---|
| WebVid | 0 | 0 | 797/820 | 23/14 |
| Yandex | −44 | +3 | 494/545 | 12/18 |

Web对原P−59命中/失败+11，对uniform+14但失败+1；Y对P+76/失败−10，对uniform−23/失败+3。双集原门失败，停止本权重版本，不追加其wall、改选uniform或扫指数。表内损益是逐query净命中正负部分解，GT成员得失另存，不作画像因果信用。

E77半收缩A对compact：Web+58/失败0，Y−80/+6；对P Web−1/+11、Y+40/−7，双集门失败。评分/构图/交互分别为Web+8/+61/−11、Y−129/−2/+51。监督缓存分解显示A只保留旧正命中Web60.37%/Y56.33%，修复旧损失同时抹去大量旧收益；拓扑控制的局部正值保留，但不改选S/T。E75原层级恢复对compact Web−59/+2、Y−22/+3停止；恢复层级不恢复邻接。E76低ESS子组Web fit/compact辅助/exact辅助+57/+18/+17，Y辅助−24/−22，不支持普遍按低ESS删除模式。

E73/E74普通compact的Y局部信号保持：E74五L对P命中+99/+59/+38/+1/+15、失败−10/−7/−4/−1/0；QPS五轮范围全部跨零，约1.9%～3.0%仅描述性插值。Web L128−23命中/失败+6损伤保留，默认未替换。

本会话388608 NSG/387840 HNSW、4真实build/8向量安装，合成另4图/512HNSW；12个native工具均terminal0，0新增正式QPS/GT/梯度。E76另143616旧返回重评分。E78独立64640集合/mask、31808旧对照全字段回归、256原kernel、全部7slot/图W/labels和非向量bytes通过。E75首次失败编译时长未知，成功重编译5.527秒不作总编译成本；独立更正保留原seal。E77安装独立耗时未知，E78四次安装0.124秒，完整成本各阶段保存。

aux7952与固定两半全部历史暴露，选择反馈计训练；P-fit含旧train/monitor、cal/audit已观察。E34历史validation只留晚间冻结后最终对照，held-out未打开。全部ANN串行CPU15/实际进程及数值库1线程、原生terminal0后评分。旧字节和各阶段source_before/root_after保留，inventory_v6含44项身份，其中有机制控制，不是44个可选新方法。

[E78报告与失败查询](entry_method_exploration/20260913_until2100_v1/stage19_child_mass_norm_v1/report.md) · [E77四格](entry_method_exploration/20260913_until2100_v1/stage18_child_shrink_factorial_v1/report.md) · [E74 QPS–Recall与失败图](entry_method_exploration/20260913_until2100_v1/stage15_compact_wall_v1/report.md) · [下一阶段](s-target.md)。
''')
(R/'s-target.md').write_text('''# ACSG 下一阶段目标与接续

2026-09-13，第6串行会话E75–E78完成；整日21:00目标未完成。唯一写入/实验者，不开并行CLI或子代理，本会话15:21:01前安全交接。

1. 不继续扫层级/收缩alpha/质量权重指数：E75/E77/E78各自原门已失败，S/T/uniform仍为机制控制。下一有实质区别的方向是按GT目标空间拆分同hub训练query，再用原query聚合入口画像；尚未实现、训练或查询。先新版本做0ANN、只用已有P-fit20K GT与base的可行性/空间预算检查，不能把目标分组等同NSG效用或直接启动完整网格。详细方法、控制、未知项与停步条件见[next_stage_design_session6](entry_method_exploration/20260913_until2100_v1/next_stage_design_session6.md)。
2. 保留E73/E74 Yandex局部正信号和Web损伤。后续诊断必须同时计算旧收益丢失、旧损失修复与新损伤；不把低支持/三入口关联当单画像因果。资源不够支持一组完整实验时先完成晚间协议和报告准备，不以少量新查询代替完整门。
3. 晚间20:00停新训练、20:40停新增query、21:00完整报告。先按历史开发反馈冻结best_all与实际best_new及选择规则，再开E34历史validation2000，不能回流训练/选型，held-out不自动打开。规定NSG/Fast/GT10匹配起点/实际新方法同批五L五轮完整wall，aligned返回集合独立评分、零命中失败救回/新增、QPS–Recall/QPS–失败率/按L三指标及失败query图齐备，不拼旧批次。

当前disk约7.06GiB，7GiB下限外另留至少32MiB给最终评测；以现场free减下限、最终预留及交接开销计算累计研究预算，不能再沿用64/128MiB旧阶段上限。新训练目标矩阵只在RAM中流式处理，不复制大输入/旧图、不清理任何旧产物。预算不足则不启动依赖步骤。全部ANN仍CPU15/threads1/数值库1线程串行，原base/NSG/rawIP/GT/真实H固定。

[inventory_v6](entry_method_exploration/20260913_until2100_v1/candidate_inventory_v6.json)逐字段保留旧32项，新增6个主候选配置和6个机制控制，共44；后六个控制不能自动转为最终新方法。fit/cal/audit/aux历史暴露，辅助选择计训练，元数据余行不证明全项目未使用。各阶段source_before/root_after及原seal保留。

[E78报告](entry_method_exploration/20260913_until2100_v1/stage19_child_mass_norm_v1/report.md) · [campaign状态](entry_method_exploration/20260913_until2100_v1/state.json) · [监督备注](/data/acsg_sessions/20260913_until2100_v1/supervisor_notes.md)。
''')
p=R/'spec.md';p.write_text(p.read_text()+'''

## 固定图子质量范数与会话6库存（E78，2026-09-13）

[prepare](entry_method_exploration/20260913_until2100_v1/stage19_child_mass_norm_v1/src/prepare.py)从E66训练质量/原slot恢复rho，子槽导出float32(rho^(1/d)*U)，P槽逐字保持；uniform对子槽统一乘exp(mean(log rho)/d)。不重新单位化，仅安装新序列化图向量区域，反向替换全文件恢复源；每个非向量byte、labels/有序邻接/层级/入口和映射保持原compact。0新图构建，4物理向量安装文件，旧图不改。在线引用E73同SHA evaluator，其finite非单位W由原内积路径直接加载，原NSG仍用原raw query/base/IP；没有新增在线权重计算。改变范数会改变遍历，不能继承旧输出/QPS。

[analyze](entry_method_exploration/20260913_until2100_v1/stage19_child_mass_norm_v1/src/analyze.py)保存完整aligned返回、集合/mask、GT成员得失、零失败转换及gain_retention。后者以每query相对P净命中的正负部分，分成保留/放弃旧正收益、新收益、避免旧损失、新增或放大损失；这些量不能与GT成员增损混用。主候选与uniform的门预锁并独立计算，失败不自动选控制。

[inventory_v6](entry_method_exploration/20260913_until2100_v1/candidate_inventory_v6.json)保留v5全部32项，新添E75两、E77六、E78四配置。六主候选和六机制控制分列；S/T/uniform不能自动入最终best_new。库存包含原配置/evaluator/W/图/mapping/tie及协议SHA，辅助反馈训练身份、失败门和无wall原因；实际失败新方法仅可按后继独立冻结最终对照协议选入，不能借库存绕过原阶段接续门。任何评分/构图/slot/数据/metric/kernel变更仍联动新结果与完整计时。
''')
state=json.loads((C/'state.json').read_text());state.update(status='E78_COMPLETE_PREPARING_SESSION6_HANDOFF',stage19_status='COMPLETE_CHILD_MASS_NORM_NO_GATE',session6_NSG=388608,session6_HNSW=387840,session6_builds=4,session6_vector_installs=8,total_new_NSG=4705364,total_HNSW=5116896,total_builds=352,native_pids=[],next_action='Seal session6, then independent target-space feasibility or evening frozen final protocol; no E75/E77/E78 enhancement wall.',candidate_inventory=str(C/'candidate_inventory_v6.json'),next_design=str(C/'next_stage_design_session6.md'),day_goal_complete=False)
write(C/'state.json',state)
root_after=O/'reviews/root_after';root_after.mkdir()
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']:
 dest=root_after/name.replace('/','__');shutil.copy2(R/name,dest)
write(O/'reviews/figure_review.json',dict(status='PASS',epoch=time.time(),figure=str(O/'figures/mass_norm.png'),visual_review='Six panels viewed; pairs, signs, axes, dataset scope and NDC rather than QPS match raw results.'))
files=[p for p in sorted(O.rglob('*')) if p.is_file()]+[history]
write(O/'reviews/final_artifact_freeze.json',dict(epoch=time.time(),files=[ident(p) for p in files]))
print(json.dumps(dict(status='E78_SEALED',files=len(files),bytes=sum(p.stat().st_size for p in files),free_GiB=shutil.disk_usage('/data').free/(1<<30))))
