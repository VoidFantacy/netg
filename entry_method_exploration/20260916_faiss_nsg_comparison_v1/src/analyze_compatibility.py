import pathlib,json,csv,datetime
import numpy as np
D=pathlib.Path(__file__).resolve().parent.parent;X=D/'compatibility'
read=lambda p:json.loads(p.read_text())
done=read(X/'complete.json');assert done['search_calls']==496000 and done['configurations']==64
datasets=[];details=[]
for ds in done['datasets']:
 name=ds['dataset'];c=read(X/f'configs/{name}.json');progress=read(X/'results'/name/'progress.json');assert len(progress)==16
 counts={kind:sum(z['checks'][kind]['different_elements'] for z in progress) for kind in ['ids','distance_bits','entries','route_ndc','graph_ndc']}
 datasets.append(dict(dataset=name,status=ds['status'],configurations=16,mismatched_configurations=ds['mismatched_configurations'],**{k+'_different_elements':v for k,v in counts.items()}))
 gt=None
 for z in progress:
  if z['status']=='PASS':continue
  if gt is None:
   g=np.fromfile(c['gt'],dtype='<i4');width=int(g[0]);gt=g.reshape(-1,width+1);assert gt.shape[0]==c['n'] and np.all(gt[:,0]==width);gt=gt[:,1:]
  K,L=z['K'],z['L'];p=X/'results'/name/f'{z["method"]}_K{K}_L{L}'
  actual=np.fromfile(p/'ids.i32',dtype='<i4').reshape(c['n'],K);expected=np.fromfile(z['checks']['ids']['reference'],dtype='<i4').reshape(c['n'],K)
  hits=lambda a:np.array([np.intersect1d(i,g).size for i,g in zip(a,gt[:,:K])])
  ah,bh=hits(actual),hits(expected);ad=np.fromfile(p/'distances.f32',dtype='<f4');bd=np.fromfile(z['checks']['distance_bits']['reference'],dtype='<f4')
  # Error bounds only for identical returned IDs; different positions are not comparable scores.
  same_id=(actual.reshape(-1)==expected.reshape(-1));finite=np.isfinite(ad)&np.isfinite(bd)&same_id
  details.append(dict(dataset=name,method=z['method'],K=K,L=L,actual_recall=float(ah.mean()/K),reference_recall=float(bh.mean()/K),queries_with_changed_recall=int((ah!=bh).sum()),queries_with_changed_ordered_ids=int(np.any(actual!=expected,axis=1).sum()),max_absolute_score_difference_same_id=float(np.max(np.abs(ad[finite].astype(float)-bd[finite]))) if finite.any() else None,checks=z['checks']))
result={'status':done['status'],'reviewed_at':datetime.datetime.now().astimezone().isoformat(),'search_calls':496000,'configurations':64,'datasets':datasets,'mismatch_details':details,'new_formal_qps':0}
(X/'analysis.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
with (X/'dataset_summary.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(datasets[0]));w.writeheader();w.writerows(datasets)
lines=['## 其它四集一致性补充','',f'按用户此前指定的范围，在WebVid计时结束后另做496000次搜索，64个配置，无新QPS。总状态：**{done["status"]}**。实际计数包装调用真正的Faiss batch4，没有用scalar代替批量数值。','', '| 数据集 | 配置数 | 不一致配置 | ID位置差异 | 距离bits差异 | graph NDC不同query数 |','|---|---:|---:|---:|---:|---:|']
for x in datasets:lines.append(f'| {x["dataset"]} | 16 | {x["mismatched_configurations"]} | {x["ids_different_elements"]} | {x["distance_bits_different_elements"]} | {x["graph_ndc_different_elements"]} |')
lines+=['','差异数按全部配置累加，重复预算不增加独立query数。兼容性调度含加载与前后身份核验 '+f'{done["seconds_including_load_and_identity"]/60:.3f}分钟；主比较与本补充共2496000次真实搜索，另有两次12960合成搜索。','']
if details:lines+=['存在不一致，不能把span+batch4当作所有度量/数据集上的无损替换。完整返回差异、Recall变化与同ID分数误差见[兼容性分析](compatibility/analysis.json)；失败产物和原E99结果均保留，生产没有替换。','']
else:lines+=['64个配置的ID、距离bits、入口、路由/图NDC全部与E99一致。这扩展了数值兼容性证据，仍不能用count轮耗时宣称四集QPS加速；生产接入和共享内核正式验证尚未执行。','']
lines+=['[补充协议](compatibility/protocol.md) · [逐集结果](compatibility/dataset_summary.csv) · [完成记录](compatibility/complete.json)','']
p=D/'report.md';text=p.read_text();assert '## 其它四集一致性补充' not in text;p.write_text(text+'\n'+'\n'.join(lines))
print(json.dumps(result,ensure_ascii=False,indent=2))
