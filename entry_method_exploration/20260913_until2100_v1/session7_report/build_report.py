from pathlib import Path
import os,sys,json,csv,time,hashlib,shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
C=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent
sys.path.insert(0,str(C/'stage22_joint_view_partition_v1/src'))
from verify_candidates import load_raw
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];stages=['stage20_target_space_modes_v1','stage21_hub_conditioned_targets_v1','stage22_joint_view_partition_v1'];names=['baseline10','compact10','target10','conditional10','joint10'];display=['P','compact','GT-global','GT-conditional','joint Q+GT']
def read(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert os.sched_getaffinity(0)=={15};assert all(read(C/s/'state.json')['NSG']==129536 for s in stages)
# Rendering-only correction outside immutable E80 stage.
with (C/stages[1]/'results/paired.csv').open() as f:paired=list(csv.DictReader(f))
fig,axs=plt.subplots(2,3,figsize=(13,7),layout='constrained')
for di,ds in enumerate(DS):
 rr=[r for r in paired if r['dataset']==ds and r['split']=='all'];x=np.arange(len(rr));labels=[r['candidate'].replace('10','')+'\nvs '+r['reference'].replace('10','').replace('baseline','P') for r in rr]
 for j,(key,title) in enumerate([('net_hits','Net GT10 hits'),('failure_change','Zero-hit failure change'),('total_NDC_change_pct','Total distance-count change (%)')]):
  a=axs[di,j];vals=np.array([float(r[key]) for r in rr]);a.bar(x,vals,color=['#267f70' if (v>=0 if j==0 else v<=0) else '#be5d4d' for v in vals]);a.axhline(0,color='#555',lw=.8);span=max(float(vals.max())-float(vals.min()),float(abs(vals).max()),1);a.set_ylim(min(float(vals.min()),0)-.22*span,max(float(vals.max()),0)+.22*span);a.set_xticks(x,labels,fontsize=7);a.set_title(('WebVid' if di==0 else 'Yandex')+' · '+title,fontsize=10)
  for i,v in enumerate(vals):a.annotate(f'{v:+.0f}' if j<2 else f'{v:+.2f}',(i,v),xytext=(0,4 if v>=0 else -11),textcoords='offset points',ha='center',fontsize=8)
fig.suptitle('E80 hub-conditioned target profiles | historical aux 7,952 per dataset | L128 | no QPS',fontsize=12);fig.savefig(O/'conditional_modes_v2.png',dpi=170);plt.close(fig)
fail=[];union={};shown={};regression=0;scored=0
for ds in DS:
 cfg=[read(C/s/'inputs'/ds/'aux.json') for s in stages];rows=np.fromfile(cfg[0]['row_ids'],np.int64);gt=np.fromfile(cfg[0]['gt_file'],np.int64).reshape(7952,100);assert len(rows)==7952 and np.all(np.diff(rows)>0)
 for cc in cfg[1:]:assert Path(cc['row_ids']).read_bytes()==rows.tobytes() and Path(cc['gt_file']).read_bytes()==gt.tobytes()
 raw={n:load_raw(C/stages[0]/'results'/ds/'aux'/(n+'_L128'),7952) for n in names[:3]}
 raw[names[3]]=load_raw(C/stages[1]/'results'/ds/'aux'/(names[3]+'_L128'),7952);raw[names[4]]=load_raw(C/stages[2]/'results'/ds/'aux'/(names[4]+'_L128'),7952)
 for stage in stages[1:]:
  for n in names[:2]:
   other=load_raw(C/stage/'results'/ds/'aux'/(n+'_L128'),7952)
   for k in raw[n]:assert raw[n][k].tobytes()==other[k].tobytes()
   regression+=7952
 for n in names:
  a=raw[n];hits=np.array([len(set(x.tolist())&set(g[:10].tolist())) for x,g in zip(a['ids'],gt)]);assert np.array_equal(hits,a['hits']);scored+=7952
 H=np.stack([raw[n]['hits'] for n in names],1);anyzero=np.any(H==0,1);changed=anyzero&np.any(H>0,1);union[ds]=dict(any_zero=int(anyzero.sum()),changed_zero=int(changed.sum()),all_zero=int(np.all(H==0,1).sum()))
 for i in np.flatnonzero(anyzero):
  r=dict(dataset=ds,namespace='router_train',source_row=int(rows[i]),GT10=' '.join(map(str,gt[i,:10])),changed_zero_status=bool(changed[i]))
  for n in names:r[n+'_hits']=int(raw[n]['hits'][i]);r[n+'_entries']=' '.join(map(str,raw[n]['entries'][i]));r[n+'_returns']=' '.join(map(str,raw[n]['ids'][i]))
  fail.append(r)
 ix=np.flatnonzero(changed)[:24];shown[ds]=(rows[ix],H[ix])
with (O/'failure_queries.csv').open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(fail[0]));w.writeheader();w.writerows(fail)
fig,axs=plt.subplots(1,2,figsize=(12,9),layout='constrained')
for di,ds in enumerate(DS):
 a=axs[di];rows,H=shown[ds];a.imshow(H,vmin=0,vmax=10,aspect='auto',cmap='YlGnBu');a.set_xticks(range(5),display,rotation=23,fontsize=9);a.set_yticks(range(len(rows)),rows,fontsize=8);a.set_ylabel('router_train source row');a.set_title(('WebVid' if di==0 else 'Yandex')+f" | union {union[ds]['any_zero']} / changed {union[ds]['changed_zero']}")
 for (i,j),v in np.ndenumerate(H):a.text(j,i,str(v),ha='center',va='center',color='white' if v>5 else '#333',fontsize=8)
fig.suptitle('Session 7 | zero-GT10-hit queries, first 24 changed source rows per dataset\nFive primary methods; complete union retained in CSV | L128 / historical aux / no QPS',fontsize=12);fig.savefig(O/'failure_queries.png',dpi=160);plt.close(fig)
lines=['# ACSG 第7串行研究会话汇报','', 'E79–E81三组固定改进均完成两数据集构造和真实ANN，判定以各自预锁门为准。本会话结束，整日21:00目标未完成；E34晚间最终对照仍待执行。','', '| 实验 / 数据 | 对原P净命中 / 失败变化 | 对compact净命中 / 失败变化 | 原门 |','|---|---:|---:|---|'];costs=[]
for stage,eid,main in zip(stages,['E79','E80','E81'],names[2:]):
 gate=read(C/stage/'results/gate.json');costs.append(read(C/stage/'results/cost.json'))
 with (C/stage/'results/paired.csv').open() as f:rr=list(csv.DictReader(f))
 for ds in DS:
  x={r['reference']:r for r in rr if r['dataset']==ds and r['candidate']==main and r['split']=='all'};p=x['baseline10'];c=x['compact10'];lines.append(f"| {eid} / {'WebVid' if ds==DS[0] else 'Yandex'} | {int(p['net_hits']):+d} / {int(p['failure_change']):+d} | {int(c['net_hits']):+d} / {int(c['failure_change']):+d} | {'PASS，尚待wall' if gate['datasets'][ds]['passed'] else 'FAIL'} |")
lines+=['','E79将父hub内分组特征由query换成全GT10目标均值；E80用原GT逐rank归属权重，形成该hub条件目标；E81恢复原query分区，再以query与条件目标的等权双视角目标更新。同一真实hub始终保留父P，最后子画像聚合原query、使用原rawhub先验。变更均在离线，小HNSW仍只覆盖815/821个真实入口，NSG/base/GT/rawIP未变。','', '几何目标提高、训练集分区改变或NDC变化均不等于NSG效用。目标方向也影响子支持、画像容量和图，当前比较不是单一中介因果识别。各版旧收益保留、丢失、新收益/损伤与GT成员集合增损均在分阶段报告；E73/E74 Yandex局部正信号保持，不能被三个新版本的失败抹去。','', '本会话新增QPS点 **0**，没有新的完整性能改进证据。最新完整开发曲线见[E74 QPS–Recall、QPS–失败率与按L三指标](../stage15_compact_wall_v1/report.md)，这是其独立历史批次，不能与本会话L128质量点拼成一条曲线。晚间最终必须冻结候选后同批比较原NSG/Fast/GT10匹配起点/实际新方法。','', f"实际新增{sum(x['NSG'] for x in costs):,} NSG / {sum(x['HNSW'] for x in costs):,} HNSW / {sum(x['builds'] for x in costs)}真实build / 8离线画像训练；另2套E66原Q分区复现。离线总操作wall {sum(x['offline_total_seconds'] for x in costs):.3f}s，构图 {sum(x['micro_graph_build_seconds'] for x in costs):.3f}s，native {sum(x['native_job_seconds'] for x in costs):.3f}s。0新增GT/梯度/编译。继承GT/P成本未知，操作wall包括加载/count/I/O，不是QPS。",'', f"五主方法失败并集 **{len(fail)}** 个dataset/source-row，**{sum(x['changed_zero'] for x in union.values())}** 条失败状态变化；Web/Y全方法失败分别{union[DS[0]]['all_zero']}/{union[DS[1]]['all_zero']}条。失败严格为零GT10集合命中。已独立评分{scored}条返回，跨批共有P/compact {regression}行全字段复现；此处仅缓存质量诊断。全表含GT10、各方法入口/返回ID，图按源行展示每集前24变化例，不挑好例。",'', '[完整失败查询](failure_queries.csv) · [失败图](failure_queries.png) · [E80标签留白修正版](conditional_modes_v2.png)。E80原图、原源码和原封条保持，修正版仅改变y轴留白。','', 'P-fit20K包含旧train/monitor，aux7952及两半为已观察且用于训练决策的辅助反馈，cal/audit历史使用。E34历史validation2000与held-out本会话未打开。后继会话不得将这些开发反馈包装为未见数据。所有ANN CPU15、实际进程/库1线程串行，native工具实际退出后才分析。','']
for stage,eid in zip(stages,['E79','E80','E81']):lines.append(f'[{eid}完整报告](../{stage}/report.md) · [协议](../{stage}/protocol.md) · [成本](../{stage}/results/cost.json) · [封存](../{stage}/reviews/final_artifact_freeze.json)')
(O/'report.md').write_text('\n'.join(lines)+'\n');dump(O/'verification.json',dict(status='PASS',set_scored=scored,old_full_field_rows=regression,union=union,NSG=0,HNSW=0,new_final_feedback=False,derived_seconds=None,render_correction='E80 original immutable; corrected y headroom only'))
assert sum(p.stat().st_size for p in O.rglob('*') if p.is_file())<4*(1<<20);assert shutil.disk_usage('/data').free>=6.8*(1<<30)+68*(1<<20);print('SESSION7_REPORT_PASS',union,flush=True)
