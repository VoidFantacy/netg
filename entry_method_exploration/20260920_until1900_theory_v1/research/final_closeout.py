from pathlib import Path
import json,time,shutil,subprocess,hashlib,sys,re
ROOT=Path('/data/netg/ACSG');TB=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(16<<20),b''):h.update(b)
    return h.hexdigest()
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
cfg=read(TB/'config.locked.json');assert time.time()>=cfg['deadline_unix'],'19:00 deadline has not arrived'
assert not (TB/'complete.json').exists();assert not (TB/'reviews/final_audit').exists()
state=read(TB/'state.json');assert state['completed_NSG_calls']==328448 and state['synthetic_calls']==12 and state['active_stage_reserved_NSG_calls']==0
snap=TB/'reviews/before_final_closeout';assert not snap.exists();snap.mkdir()
docs=['summary.md','spec.md','s-target.md','s-experiment.md','experiment_history/README.md']
for rel in docs:
    p=snap/'root'/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,p)
for rel in ['report.md','state.json']:shutil.copy2(TB/rel,snap/rel)
p=TB/'report.md';s=p.read_text();s=s.replace('2026-09-20，19:00限时研究的综合报告。当前为持续审查版本，最终完成身份见本目录的`complete.json`；尚未生成该文件时，不将本报告视为限时任务已结束。','2026-09-20，持续至北京时间19:00的理论研究综合报告。各阶段已完成；最终状态与身份记录为本目录的`complete.json`。',1)
s=s.replace('[路由工作恒等式](research/router_work_identity_v1/report.md) 进一步','[路由工作恒等式](research/router_work_identity_v1/report.md)\n\n进一步',1)
s=s.replace('最终任务状态、完整成本及保护检查将在19:00收尾时补充。本报告不产生新的训练、搜索或调参队列。','截至19:00，全部阶段与登记任务结束，原GT10默认及生产E99保持；本报告不产生新的训练、搜索或调参队列。两阶段文件约1.31GiB，最终测量口径见[完整成本账本](reviews/final_audit/cost_ledger.json)；已封存旧阶段的字节统计发生在它写入最后身份/文档回执之前，本次另记其实际目录大小，未改旧回执。\n\n[最终身份核验](reviews/final_audit/identity.json) · [文档检查](reviews/final_audit/documents.json) · [完成审查](reviews/final_audit/audit.json)。预检中历史文件名笔误和串行任务分类漏计分别保留修正记录；实验源数据、分数、门和默认未因文档修正而改变。',1)
p.write_text(s)
hist=ROOT/'experiment_history/116_theory_synthesis_1900.md';assert not hist.exists()
hist.write_text('''# 116｜19:00理论研究综合收尾

2026-09-20，用户目标“持续推进到下午七点”完成。E107–E111首阶段已独立封存；后阶段E112–E115、统计/目标支持、路由工作及表示能力核验全部收尾。未找到稳定GT10替换，Web GT10-soft-t1、Yandex GT10-hard和生产E99保持。

GT10实际学习相关query的加权方向，固定权重下有闭式最优；IID方向风险不等于Recall保证。系统相对固定NSG的收益不能全部归因于十目标平均：匹配GT10−GT1在L128有正有负，自适应真实hub入口已贡献明显收益，小图可检索性也影响成本。E115评分/完整图状态四格显示成本优势与质量交互；混合B两集质量门失败，不进入条件wall。

失败解释不能缩成“模型不够强”：WFree fit已标注C8最优集合100%，实际入口广泛改变，但开发救回与损伤相抵且完整QPS变差。区域代理即使使用真实目标也未必改善搜索；首行证书H、具体比较对字典信息门均失败。原八入口策略常汇合到同一局部终点，但不证明全H无空间。排名核心保证与NGFix有直接前作，不称新理论。

路由工作核验发现固定U评分时，GT10图展开略多但扫描邻边更少；图状态含不同层级/入口，不将全部成本归给一个平均度。保序集中化反例排除仅靠集中度解释图稀疏。人工XOR图说明两固定入口单线性分数可能不足，但多画像和简单非线性都能表达；没有证明真实QMLP必要或当前WFree不可能。

后阶段328448真实NSG、98560ANN、12次合成kernel调用、2张人工图、4混合小图副本及4份before副本；0普通构图/底图/新GT/梯度或画像训练/正式QPS/held-out访问。有图标签与离线H优化、旧模型分数残差计算，不称零计算。与旧阶段合计3125504真实NSG、18次合成调用；ANN总量未跨阶段聚合，98560只属于后阶段。原E106/E104/E105成本不混入两阶段账本。

理论决定：暂停相同代理、参数/seed/网络名称扩展。下次立项须给出不同于已做版本的可迁移图/query信息，解释它如何预测相对默认的净收益；先验证机制与同监督简单控制，再投入模型与完整单线程wall。没有自动待运行训练/调参/部署任务，不承诺CCF B录用概率。

[综合报告](../entry_method_exploration/20260920_until1900_theory_v1/report.md) · [成本账本](../entry_method_exploration/20260920_until1900_theory_v1/reviews/final_audit/cost_ledger.json) · [四格报告](../entry_method_exploration/20260920_until1900_theory_v1/stages/e115_score_topology_factorial/report.md)。
''')
def prepend(rel,text):
    p=ROOT/rel;head,rest=p.read_text().split('\n\n',1);p.write_text(head+'\n\n'+text+'\n\n'+rest)
link='[综合报告](entry_method_exploration/20260920_until1900_theory_v1/report.md) · [记录116](experiment_history/116_theory_synthesis_1900.md)'
prepend('summary.md','2026-09-20 **19:00理论研究已收尾，未找到稳定GT10替换**。GT10有闭式查询画像目标，但系统收益还来自真实入口和小图；十目标相对单目标的匹配增量有正有负。后继E112图覆盖、E113具体比较对、E115评分/图组合均按门停止；小图工作量、终点与表示能力核验只提供有条件机制解释。后阶段328448真实NSG、98560ANN、12合成调用，0新梯度/画像训练和正式QPS；两阶段3125504真实NSG。全部任务结束，Web soft/Y hard与生产E99保持，无自动训练或网格队列。'+link+'。以下逐阶段文字保留发生时的历史状态，当前以本段为准。')
prepend('spec.md','2026-09-20 **理论研究工具版本已封存**：E112图标签/H选择、E113比较记录、E114终点审查、E115评分/完整小图状态交叉、后继工作计数和两项合成反例均与生产隔离。真实指标K1/K100、CPU15/线程1；E115缓存路由诊断不计QPS，人工L1例子不计真实评测。原图/GT/默认和E99 API保持，输入、代码、结果、计数修正及完整身份在'+link+'。')
prepend('s-target.md','2026-09-20 **“持续推进到下午七点”已完成**，没有待运行研究进程、训练、参数网格或部署。默认Web GT10-soft-t1/Yandex GT10-hard及生产E99保持。后继先解决“哪种可跨query共享、在线可计算的信息，能预测改变入口后救回相对损伤的净收益”，提出明确条件/反例及相对已有版本的实质区别；只在机制和同监督简单控制通过后考虑MLP/双塔/RL及完整wall。现有充分条件、XOR和可达理论不单独构成立项或论文创新依据。本轮曝光query不可再标作新测试；旧停止版本不重启。'+link+'。以下限时段进展和旧下一步保留历史身份。')
prepend('s-experiment.md','2026-09-20 **至19:00理论研究综合完成**：收益拆分、统计/图搜索条件、失败净增损及四格机制完整收口；没有稳定方法替换。后阶段328448真实NSG、98560ANN、12合成，0新训练/正式QPS，默认保持。'+link+'。')
p=ROOT/'experiment_history/README.md';p.write_text(p.read_text().replace('|---|---|\n','|---|---|\n| [116 19:00理论综合](116_theory_synthesis_1900.md) | 两阶段收益解释、停止条件、成本与最终身份 |\n',1))
job=dict(argv=[sys.executable,str(TB/'research/prepare_final_audit.py'),'reviews/final_audit'],started_unix=time.time(),kind='final_readonly_integrity_audit')
with (TB/'reviews/final_audit.log').open('x') as f:
    p=subprocess.Popen(job['argv'],cwd=TB,stdout=f,stderr=subprocess.STDOUT);job['pid']=p.pid;dump(TB/'reviews/final_audit_job.json',job);p.wait(timeout=120)
job.update(exit_code=p.returncode,seconds=time.time()-job['started_unix'],finished_unix=time.time());dump(TB/'reviews/final_audit_job.json',job);assert p.returncode==0,'See preserved final_audit.log'
audit=read(TB/'reviews/final_audit/audit.json');assert audit['owned_jobs_closed']==21 and audit['serial_query_jobs']==7
state.update(status='COMPLETE',stage='Theory research complete at 19:00',completed_unix=time.time(),pending=[],completed_ANN_calls=98560,synthetic_calls=12,default_changed=False,production_changed=False,overall_goal_complete=True,no_queued_training_or_search=True)
dump(TB/'state.json',state)
done=dict(status='COMPLETE',completed_unix=time.time(),deadline_unix=cfg['deadline_unix'],objective=cfg['objective'],decision='NO_STABLE_GT10_REPLACEMENT_THEORY_REVIEW_COMPLETE',NSG_calls=328448,ANN_calls=98560,synthetic_calls=12,combined_NSG_calls=3125504,combined_synthetic_calls=18,default_changed=False,production_changed=False,new_training=0,new_GT=0,new_formal_QPS=False,pending=[],report=ident(TB/'report.md'),state=ident(TB/'state.json'),audit=ident(TB/'reviews/final_audit/audit.json'),cost=ident(TB/'reviews/final_audit/cost_ledger.json'),final_audit_job=ident(TB/'reviews/final_audit_job.json'),history=ident(hist),closeout_source=ident(__file__))
dump(TB/'complete.json',done)
assert time.time()>=cfg['deadline_unix'] and read(TB/'state.json')['pending']==[]
print(json.dumps(dict(status='COMPLETE',report=done['report'],NSG_calls=done['NSG_calls'],ANN_calls=done['ANN_calls'],synthetic_calls=done['synthetic_calls'],unique_SHA_files=audit['unique_SHA_files'],jobs_closed=audit['owned_jobs_closed'],links=audit['local_links'],bytes_at_audit=audit['combined_logical_bytes_at_measurement'],default_changed=False),indent=2))
