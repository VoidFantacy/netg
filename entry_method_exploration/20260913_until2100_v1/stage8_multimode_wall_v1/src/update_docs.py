from common import *
import csv
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
paired=list(csv.DictReader((O/'results/paired.csv').open()));cost=read(O/'results/cost.json');E66=C/'stage7_multimode_index_v1';sections=[]
for ds in DS:
    rows=[r for r in paired if r['dataset']==ds and r['comparator']==('baseline_soft' if ds==DS[0] else 'gt10_hard')]
    dr='/'.join(f"{float(r['delta_recall_pp']):+.4f}" for r in rows)
    qr='/'.join(f"{float(r['QPS_change_pct']):+.3f}%" for r in rows)
    fr='/'.join(f"{int(r['new_failures'])-int(r['rescued']):+d}" for r in rows)
    cross=sum(float(r['all_range_low_pct'])<=0<=float(r['all_range_high_pct']) for r in rows)
    sections.append(f"{ds}：L64/128/256/400/800相对匹配GT10的ΔRecall={dr} pp，QPS中位变化={qr}，失败净新增={fr}；{cross}/5个QPS交叉范围跨零。全部曲线为本批独立完整wall，不能与E65拼接。")
hist=R/'experiment_history/56_multimode_wall.md';assert not hist.exists()
text='# E67 多画像与重复画像控制完整wall\n\n2026-09-13，55方法点、275轮同批完整单线程wall已完成。E66固定mode3P双集展示，duplicate3P为同容量控制；原E66开发门失败保持，不依本批调参。原NSG/Fast30K/GT10-hard与Web匹配soft同批，真实H/原NSG/base/raw-IP/GT不变。\n\n'+'\n\n'.join(sections)
text+='\n\nsource router_train[2048:4096]历史开发2048已用于E64/E66辅助选型，全部是历史暴露开发，不称最终泛化。E34最终validation及held-out未打开。GT在全部raw后评分；完整wall含一次7slot路由/去重/真实映射/原NSG/output，GT/count/hash/JSON/build/load在外。实际CPU15/进程与库1线程，单方法串行，两个native工具terminal实际退出后分析。\n\n'
text+=f"新增789360 NSG、645120 HNSW，45物理图源加载/复制与90 plain/count加载，0新图/训练/GT。112640集合/mask、880原kernelparity、全slot映射与五L图/入口/275wall、71680 E65基线及12288 E66 L128原返回回归通过。操作{cost['native_job_seconds']:.3f}秒不是QPS。\n\n"
link='../entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/'
text+=' · '.join(f'[{title}]({link}{path})' for title,path in [('报告和全部曲线','report.md'),('协议','protocol.md'),('原始wall','results/timings.csv'),('逐query失败','results/failure_query_summary.csv'),('验收','reviews/verification.json')])+'。\n';hist.write_text(text)
p=R/'experiment_history/README.md';s=p.read_text();p.write_text(s.replace('|---|---|','|---|---|\n| [56 多画像完整wall](56_multimode_wall.md) | E67：固定mode与duplicate、55点275轮、QPS/Recall/失败及完整回归 |',1))
p=R/'s-experiment.md';s=p.read_text();p.write_text(s.replace('| E66 GT10多画像单小索引','| E67 多画像完整开发wall | mode3P/duplicate3P与NSG/Fast/GT10，55点275轮 | `COMPLETE_MULTIMODE_DEVELOPMENT_WALL`；局部正负与旧门保持，未最终验证 | [56 多画像wall](experiment_history/56_multimode_wall.md) |\n| E66 GT10多画像单小索引',1))
summary='# ACSG 当前结果摘要\n\n2026-09-13，第三串行会话完成E66多画像开发与E67完整wall。双集E66开发门失败保持；当前原GT10默认未替换，整日21:00目标未完成。今日共有100个历史开发性能点、500轮独立wall，E34最终validation仍待晚间冻结对照。\n\n'
summary+='E66：固定3H、原P+两GT10加权模态、7slot去重3真实hub。Web合格478/815hub，fit−496/aux−106命中、aux失败+13；Y合格623/821hub，fit+164/aux+49、失败−4，但两半−14/+63。双集相对duplicate控制有增量，但单画像扩为3H的近似路由损伤不能忽略。该训练/开发局部信号不当完整性能GO。\n\n'
summary+='\n\n'.join(sections)+'\n\n'
summary+='E67原始112640返回独立评分、五轮/plain/count/880原kernelparity及全部基线恢复通过；失败严格zero GT10，GT成员增损与逐query净命中正负分列。E66新增337248 NSG/336960 HNSW/4build，E67新增789360 NSG/645120 HNSW；合成另1图/15路由。所有ANN单方法CPU15实际线程1；GT/count/hash/build/load在wall外。\n\n'
summary+='P-fit含旧train/monitor；cal/audit及aux7952均历史暴露，辅助反馈计训练。E67为aux的已观察子集，不能称最终泛化；E34最终与held-out未进入本会话。E63 fit局部正值、E64 Web拓扑+38且失败+2、E65 Web局部曲线正/Y混合均保留原批身份。\n\n[E67完整报告与图](entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/report.md) · [E66机制/控制](entry_method_exploration/20260913_until2100_v1/stage7_multimode_index_v1/report.md) · [下一阶段](s-target.md)。\n'
(R/'summary.md').write_text(summary)
p=R/'s-target.md';s=p.read_text().replace('已完成E66单3H多画像开发','已完成E66单3H多画像开发和E67同批完整wall')
start=s.index('1. ');end=s.index('3. ',start)
s=s[:start]+'''1. 优先查清重复原P后物理slot/近似遍历损失，保持E66/E67模型和门。可以另立0新ANN的完整画像分数诊断，比较原P、duplicate与mode的近似三hub及分数排序参照、7slot独立hub数；它不是NSG效用oracle。若有明确缺口，再前瞻锁单个multiplicity/ef控制，不扫簇数/支持阈值/seed。详细未运行设计见[next design](entry_method_exploration/20260913_until2100_v1/next_stage_design_session3.md)。
2. E67已完成新方法+duplicate与NSG/Fast/GT10匹配起点的55点275轮wall及三指标/失败query；E65另45点225轮保留，各批不能拼方法曲线。观察局部Recall/失败与完整QPS成本，不由同L或单轮差给GO。
'''+s[end:]
p.write_text(s)
p=R/'spec.md';s=p.read_text().replace('E60–E65支持、画像/四格、zero-hit质量、扩大开发及完整wall已验收','E60–E67支持、画像/四格、多画像与完整开发wall已验收')
s+='''\n\n## 多画像完整开发wall（E67，2026-09-13）

[prepare](entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/src/prepare.py)逐字复制E66已验收binary，冻结原NSG/Fast/GT10及mode3P/duplicate3P的图/W/mapping，55方法点五L五轮。原E66多slot接口/原kernel不变，没有新构图或训练；source[2048:4096]已观察开发2048，不读E34最终输入。

[run](entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/src/run.py)沿preexec绑CPU15及实际线程1、完整warmup/轮换wall、GT后评分合同，实际275wall/789360 NSG。独立[slot验收](entry_method_exploration/20260913_until2100_v1/stage8_multimode_wall_v1/src/verify_slots.py)复算全部7slot距离序/去重/真实映射并核验五L slot bytes；全部图向量/外部标签、112640集合/mask和880原kernelparity通过。原71680基线返回回归E65，12288 L128行回归E66；QPS不跨批复用。
''';p.write_text(s)
after=O/'reviews/root_after';after.mkdir()
for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:shutil.copy2(R/name,after/name)
shutil.copy2(R/'experiment_history/README.md',after/'history_README.md')
state=read(C/'state.json');state.update(status='SESSION3_E66_E67_COMPLETE',stage='E67_COMPLETE',stage8_status='COMPLETE_MULTIMODE_DEVELOPMENT_WALL',native_pids=[],
    total_new_NSG=2069814,total_HNSW=2810656,total_builds=346,formal_QPS_points=100,formal_wall_batches=500,day_goal_complete=False);dump(C/'state.json',state)
print('E67_DOCUMENTS_SYNCHRONIZED',flush=True)
