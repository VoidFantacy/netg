from pathlib import Path
import sys,itertools
import numpy as np
O=Path(__file__).resolve().parents[1];C=O.parent
sys.path.insert(0,str(C/'stage32_final_tooling_v1/src'))
from common import read,dump,threads,table,freeze,sha
from scoring_v3 import raw,scores,inspect_serialized,verify_slots
threads();split=sys.argv[1];c=read(O/'inputs'/(split+'.json'));out=O/'results'/split;r=read(out/'results.json');n=c['num_queries'];ds=c['dataset']
assert r['status']=='COMPLETE' and r['GT_opened_after_all_raw_search'] and r['physical_graph_calls']==c['real_call_cap']
tc=read(out/'thread_contract.json');assert tc['process_threads']==tc['actual_openmp_threads']==1 and tc['cpu']==15
gt=np.fromfile(c['gt_file'],np.int64).reshape(7952,100)[:n];q=np.fromfile(c['queries_file'],np.float32).reshape(7952,c['dim'])[:n];rows=np.fromfile(c['row_ids'],np.int64)[:n];assert (out/'row_ids.i64').read_bytes()==rows.tobytes()
old={'baseline10':C/'stage14_compact_modes_v1/results'/ds/'aux/baseline10_L128','compact10':C/'stage14_compact_modes_v1/results'/ds/'aux/compact10_L128','shortcut10':C/'stage25_query_shortcuts_v1/results'/ds/'aux/shortcut10_L128','supported10':C/'stage31_cross_source_restore_v1/results'/ds/'aux/supported10_L128'}
arrays={};points=[];samekeys=0
for configured,m in zip(c['methods'],r['methods']):
 assert configured==m['configuration'] and m['full_plain_count_parity_queries']==n and m['original_kernel_parity_queries']==16
 name=m['model_name'];a=raw(out/m['name']);h=scores(a,gt,c['base_count']);arrays[name]=a
 assert int(h.sum())==m['total_hits'] and int((h==0).sum())==m['failed_queries']
 if name in old:
  b=raw(old[name])
  for k in a:assert a[k].tobytes()==b[k][:n].tobytes(),(name,k)
 mapping=np.fromfile(configured['mapping'],np.int32);W=np.fromfile(configured['W'],np.float32).reshape(len(mapping),c['dim']);inspect_serialized(configured['graph_file'],W,np.arange(len(W)) if configured.get('slot_labels') else mapping)
 if configured.get('multi_profile'):verify_slots(out/m['name'],mapping,W,q,a['entries'],(sha(configured['graph_file']),10))
 points.append(dict(model=name,queries=n,hits=int(h.sum()),recall_pct=float(h.mean()*10),failures=int((h==0).sum()),failure_pct=float((h==0).mean()*100),route_ndc=float(a['route_ndc'].mean()),graph_ndc=float(a['graph_ndc'].mean())))
for x,y in itertools.combinations(arrays,2):
 a,b=arrays[x],arrays[y];ix=np.flatnonzero(np.all(a['entries']==b['entries'],axis=1));samekeys+=len(ix)
 for k in ['ids','distances','graph_ndc']:assert a[k][ix].tobytes()==b[k][ix].tobytes()
verification=dict(status='PASS',set_mask_rows=5*n,old_fullfield_rows=4*n,original_kernel_rows=80,seven_slot_rows=4*n,same_triple_rows=samekeys)
dump(O/'reviews'/(split+'.json'),verification)
if split=='preflight':print(verification);sys.exit(0)
table(O/'results/points.csv',points);a=arrays['composed10'];pairs=[];gate={}
for ref,b in arrays.items():
 if ref=='composed10':continue
 d=a['hits'].astype(int)-b['hits'];f=int((a['hits']==0).sum()-(b['hits']==0).sum());half=[int(x.sum()) for x in np.split(d,2)];cost=float((a['route_ndc'].astype(float)+a['graph_ndc']).sum()/(b['route_ndc'].astype(float)+b['graph_ndc']).sum()-1)
 mg=sum((int(u)&~int(v)).bit_count() for u,v in zip(a['mask'],b['mask']));ml=sum((int(v)&~int(u)).bit_count() for u,v in zip(a['mask'],b['mask']));assert mg-ml==int(d.sum())
 item=dict(candidate='composed10',reference=ref,net_hits=int(d.sum()),half1=half[0],half2=half[1],failure_delta=f,rescued=int(((a['hits']>0)&(b['hits']==0)).sum()),new_failed=int(((a['hits']==0)&(b['hits']>0)).sum()),gain_hits=int(np.maximum(d,0).sum()),loss_hits=int(np.maximum(-d,0).sum()),member_gained=mg,member_lost=ml,total_ndc_relative=cost)
 pairs.append(item);gate[ref]=bool(d.sum()>0 and min(half)>=0 and f<=0 and cost<=.01)
table(O/'results/paired.csv',pairs);dump(O/'results/gate.json',dict(passed=all(gate.values()),rules=gate,old_gates_unchanged=True))
interaction=a['hits'].astype(int)-arrays['shortcut10']['hits']-arrays['supported10']['hits']+arrays['compact10']['hits']
np.savez_compressed(O/'results/factorial.npz',source_rows=rows,interaction=interaction,**{k:v['hits'] for k,v in arrays.items()})
fail=[]
for i in range(n):
 z=[v['hits'][i]==0 for v in arrays.values()]
 if any(z):
  for name,b in arrays.items():fail.append(dict(dataset=ds,namespace='router_train',source_row=int(rows[i]),role='E90_support_training' if i<3976 else 'historically_exposed_acceptance',model=name,hits=int(b['hits'][i]),changed_zero_status=len(set(z))>1,GT10=' '.join(map(str,gt[i,:10])),entries=' '.join(map(str,b['entries'][i])),returned=' '.join(map(str,b['ids'][i]))))
table(O/'results/failures.csv',fail)
jobs=read(O/'logs/jobs.json');cost=dict(NSG=sum(j['actual_NSG'] for j in jobs),HNSW=sum(j['actual_HNSW'] for j in jobs),query_operation_seconds=sum(j['seconds'] for j in jobs),new_builds=0,new_fits=0,new_GT=0,new_QPS_points=0,physical_vector_installs=1,inheritance='E84 + E90 existing training and GT costs retained; total GT-inclusive cost unknown')
dump(O/'results/cost.json',cost)
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,3,figsize=(13,4));names=[p['reference'].replace('10','') for p in pairs]
for ax,key,title in zip(axes,['net_hits','failure_delta','total_ndc_relative'],['Net GT10 hits','Zero-hit failure change','Total NDC change (%)']):
 vals=[p[key]*(100 if key=='total_ndc_relative' else 1) for p in pairs];ax.bar(names,vals);ax.axhline(0,color='k',lw=.7);ax.set_title(title);ax.tick_params(axis='x',rotation=25)
fig.suptitle('WebVid: fixed composed repair; historical auxiliary 7952; no QPS');fig.tight_layout();fig.savefig(O/'figures/composed_repair.png',dpi=150);plt.close(fig)
unique=len(fail)//5;changed=len({x['source_row'] for x in fail if x['changed_zero_status']})
text='# E92 固定补边与父恢复组合\n\n'+('完整开发门通过。' if all(gate.values()) else '完整开发门未通过，停止这个固定组合。')+' 所有辅助数据均已历史暴露，当前判断不代表独立泛化或性能GO。\n\n'
text+='| 对照 | 净命中 | 两半 | 救回/新增失败 | 总NDC变化 |\n|---|---:|---|---|---:|\n'
for p in pairs:text+=f"| {p['reference']} | {p['net_hits']:+d} | {p['half1']:+d}/{p['half2']:+d} | {p['rescued']}/{p['new_failed']} | {100*p['total_ndc_relative']:+.3f}% |\n"
text+=f'\n逐query交互总和{int(interaction.sum()):+d}命中，{int((interaction!=0).sum())}条非加性query。叠加的实际结果已经实测，未将单项加和当预测真值。Yandex父恢复零更新，组合逐字E84，沿其原-4命中/失败0判断，0新Y查询。\n\n新增{cost["NSG"]}NSG/{cost["HNSW"]}HNSW，1组合图安装、0拟合/普通构图/GT/QPS；操作wall{cost["query_operation_seconds"]:.3f}s含加载/计数/I/O。继承E84/E90训练及GT成本非零，总GT-inclusive缺项未知。CPU15/进程和库1线程，串行。\n\n完整保留{unique}条零命中query并集，其中{changed}条状态变化，{len(fail)}个方法单元；失败严格零GT10命中。四旧配置全字段恢复，全部集合/mask、物理图/7slot/原kernel验收通过。\n\n[配对](results/paired.csv) · [完整失败表](results/failures.csv) · [图](figures/composed_repair.png) · [协议](protocol.md) · [验收](reviews/aux.json)。整日目标未完成，下一步另行冻结最终选择。\n'
(O/'report.md').write_text(text)
dump(O/'state.json',dict(status='COMPLETE_COMPOSED_REPAIR',gate_passed=all(gate.values()),day_goal_complete=False,NSG=cost['NSG'],HNSW=cost['HNSW']))
print(text)
