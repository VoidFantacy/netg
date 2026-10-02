"""Cached session6 failed-query report. No ANN, model selection, or final data."""
from pathlib import Path
import os,json,csv,time,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
C=Path(__file__).resolve().parents[1];start=time.monotonic()
assert os.sched_getaffinity(0)=={15}
assert all(os.environ[k]=='1' for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS'])
assert next(int(s.split(':')[1]) for s in Path('/proc/self/status').read_text().splitlines() if s.startswith('Threads:'))==1
out=C/'session6_report';out.mkdir()
plan=dict(scope='Cached historical auxiliary failure report only',new_NSG=0,new_HNSW=0,new_builds=0,new_GT=0,new_training=0,final_input=False,
   source_namespace='router_train',source_rows=[2048,10000],all_auxiliary_exposed=True,selection_feedback_is_training=True,
   primary_models=['P','compact','E75_preserved','E77_shrink','E78_mass'],definition='Any GT10 zero hit among five models; changed zero-status rows are an explicit subset',
   example_rule='First 24 ascending source rows per dataset with changed zero status; complete union retained',output_cap_bytes=2*(1<<20),epoch=time.time())
(out/'derivation_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
ST={'P':('stage19_child_mass_norm_v1','baseline10'),'compact':('stage19_child_mass_norm_v1','compact10'),
    'E75_preserved':('stage16_preserved_levels_v1','preserved10'),'E77_shrink':('stage18_child_shrink_factorial_v1','shrink10'),
    'E78_mass':('stage19_child_mass_norm_v1','mass10')}
allrows=[];summary=[];tables=[];independent_rows=0
for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
 conf=json.loads((C/'stage19_child_mass_norm_v1/inputs'/ds/'aux.json').read_text());rows=np.fromfile(conf['row_ids'],np.int64);gt=np.fromfile(conf['gt_file'],np.int64).reshape(7952,100)[:,:10];raw={}
 for name,(stage,m) in ST.items():
  cfg=json.loads((C/stage/'inputs'/ds/'aux.json').read_text());assert np.array_equal(rows,np.fromfile(cfg['row_ids'],np.int64))
  p=C/stage/'results'/ds/'aux'/(m+'_L128');ids=np.fromfile(p/'ids.i32',np.int32).reshape(7952,10);hits=np.fromfile(p/'hits.u8',np.uint8)
  actual=np.array([len(set(x.tolist()) & set(y.tolist())) for x,y in zip(ids,gt)],np.uint8);assert np.array_equal(hits,actual);independent_rows+=len(rows)
  raw[name]=dict(ids=ids,hits=hits,entries=np.fromfile(p/'entry_ids.i32',np.int32).reshape(7952,3))
 H=np.stack([raw[m]['hits'] for m in ST],axis=1);union=np.any(H==0,axis=1);changed=union & np.any(H!=0,axis=1)
 for i in np.flatnonzero(union):
  rec=dict(dataset=ds,namespace='router_train',source_row=int(rows[i]),changed_zero_status=bool(changed[i]),GT10=' '.join(map(str,gt[i])))
  for name,a in raw.items():
   rec[name+'_hits']=int(a['hits'][i]);rec[name+'_entries']=' '.join(map(str,a['entries'][i]));rec[name+'_ids']=' '.join(map(str,a['ids'][i]))
  allrows.append(rec)
 rec=dict(dataset=ds,all_queries=7952,any_failure_queries=int(union.sum()),changed_failure_queries=int(changed.sum()),all_five_zero_queries=int((~np.any(H!=0,axis=1)).sum()),failures={m:int((a['hits']==0).sum()) for m,a in raw.items()},transitions_vs_compact={})
 for m in ['E75_preserved','E77_shrink','E78_mass']:
  r=raw['compact']['hits'];n=raw[m]['hits'];rec['transitions_vs_compact'][m]=dict(rescued=int(((r==0)&(n>0)).sum()),new_failure=int(((r>0)&(n==0)).sum()))
 summary.append(rec);idx=np.flatnonzero(changed)[:24];tables.append((ds,rows[idx],H[idx]))
with (out/'failure_queries.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
fig,axes=plt.subplots(1,2,figsize=(12,10),layout='constrained')
for ax,(ds,rows,H) in zip(axes,tables):
 ax.imshow(H,vmin=0,vmax=10,cmap='YlGn');ax.set_xticks(range(5),['P','Compact','E75','E77 A','E78 mass'],rotation=30,ha='right');ax.set_yticks(range(len(rows)),rows);ax.set_ylabel('router_train source row');ax.set_title(('WebVid' if ds.startswith('web') else 'Yandex')+' · first 24 changed-failure queries')
 for i in range(len(rows)):
  for j in range(5):ax.text(j,i,str(H[i,j]),ha='center',va='center',fontsize=8,color='#aa1122' if H[i,j]==0 else '#101010')
fig.suptitle('Session 6 · GT10 hits per historical auxiliary query · L128\n0 = failure; full union and all returned IDs in CSV; no QPS / final validation',fontsize=14)
for ext in ['png','svg','pdf']:fig.savefig(out/('failure_queries.'+ext),dpi=150)
plt.close(fig)
summary_obj=dict(status='PASS',datasets=summary,independently_scored_cached_rows=independent_rows,total_unique_dataset_source_queries=len(allrows),new_NSG=0,new_HNSW=0,actual_threads=1,cpu=15,seconds=time.monotonic()-start)
(out/'failure_summary.json').write_text(json.dumps(summary_obj,ensure_ascii=False,indent=2)+'\n')
lines=['# 第6串行研究会话报告：E75–E78\n','本会话完成一组层级、支持、方向与范数控制，未找到稳定整体改善；整日21:00目标未完成。E75/E77/E78主候选各自预锁门均失败，未追加其完整wall；E76只做旧返回诊断。E73/E74的Yandex局部正信号保留。\n',
'| 主候选相对compact，aux7952 L128 | Web净命中 / 失败净新增 | Y净命中 / 失败净新增 |\n|---|---|---|\n| E75保留原层级 | −59 / +2 | −22 / +3 |\n| E77半收缩A | +58 / 0 | −80 / +6 |\n| E78质量范数 | 0 / 0 | −44 / +3 |\n',
'E77的Web修复伴随大量旧收益丢失，Y主要评分方向损伤；E78保留更多旧收益，仍无净改善。低ESS不是共同损伤原因，恢复层级不恢复邻接。完整机制、控制、双半门和代价见各报告，不能把同LRecall或NDC当QPS。\n',
'本表失败严格为零GT10命中。以下统计来自五个已测主配置P/compact/E75/E77 A/E78 mass的全部7952源行；不是挑选最终集或新的查询。完整CSV含所有“任一配置失败”的query，包括五个配置都失败的行，并保留GT10、三入口及每个返回ID；图只显示按源行升序前24个失败状态变化query。\n',
'| 数据 | 任一配置失败query | 失败状态变化query | 五配置全失败query |\n|---|---:|---:|---:|']
for s in summary:lines.append(f"| {'WebVid' if s['dataset'].startswith('web') else 'Yandex'} | {s['any_failure_queries']} | {s['changed_failure_queries']} | {s['all_five_zero_queries']} |")
lines.extend(['\n| 数据 / 候选对compact | 救回 / 新增失败 |\n|---|---|'])
for s in summary:
 for m,v in s['transitions_vs_compact'].items():lines.append(f"| {'WebVid' if s['dataset'].startswith('web') else 'Yandex'} / {m} | {v['rescued']} / {v['new_failure']} |")
lines.extend(['\n[完整失败query CSV](failure_queries.csv) · [失败图](failure_queries.png) · [统计/派生验收](failure_summary.json)。\n',
'本会话实际388608 NSG/387840 HNSW，4真实build/8向量安装；合成另4图/512HNSW。12个native均终止返回0、CPU15及实际线程/数值库均1；native总331.602秒包含load/count/I/O，不是纯在线QPS。E75成功重编译5.527秒，首次失败编译时长未知；E77向量安装独立耗时未知，未将未知记零。没有新GT/梯度/正式QPS，E76另重评分143616旧返回，本报告派生独立重评分79520旧返回不计新ANN。继承E66画像训练30.286秒及历史GT成本不记零。\n',
'最新完整QPS图仍来自E74：55点275轮独立完整wall，Yandex保留局部Recall/失败改善，五轮QPS范围跨零，约1.9%～3.0%只是描述性插值；Web损伤保留。它是历史开发批次，不能与新L128诊断拼成曲线或称晚间最终验证。\n',
'[E74 QPS–Recall](../stage15_compact_wall_v1/figures/recall_qps.png) · [QPS–失败率](../stage15_compact_wall_v1/figures/failure_qps.png) · [按L三指标](../stage15_compact_wall_v1/figures/three_metrics_by_L.png) · [E74完整报告](../stage15_compact_wall_v1/report.md)。\n',
'[E75报告](../stage16_preserved_levels_v1/report.md) · [E76诊断](../stage17_child_support_diagnosis_v1/report.md) · [E77四格](../stage18_child_shrink_factorial_v1/report.md) · [E78质量权重](../stage19_child_mass_norm_v1/report.md)。\n',
'P-fit20K包含旧train/monitor，aux7952和两半/旧cal/audit都历史暴露，所有选型反馈计训练。E34历史validation今天最终对照尚未运行，不回流训练/选型；held-out未打开。下一方向及空间预算是未运行设计，见[接续设计](../next_stage_design_session6.md)；[安全交接](../handoff.md)由监督器接续，整日目标未完成。'])
(out/'report.md').write_text('\n'.join(lines)+'\n')
assert sum(p.stat().st_size for p in out.iterdir())<2*(1<<20)
print(json.dumps(summary_obj,ensure_ascii=False))
