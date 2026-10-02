from verify_candidates import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();jobs=read(O/'logs/jobs.json');assert len(jobs)==4 and all(j['status']=='COMPLETE' for j in jobs)
with (O/'results/paired.csv').open() as f:paired=list(csv.DictReader(f))
gate=read(O/'results/gate.json');cost=read(O/'results/cost.json');offline=read(O/'results/offline.json');ret=read(O/'results/gain_retention.json')
allpairs=[r for r in paired if r['split']=='all'];fig,axs=plt.subplots(2,3,figsize=(13,7),layout='constrained')
for di,ds in enumerate(DS):
 rr=[r for r in allpairs if r['dataset']==ds];x=np.arange(len(rr));labels=[r['candidate'].replace('10','')+'\nvs '+r['reference'].replace('10','').replace('baseline','P') for r in rr]
 for j,(key,title) in enumerate([('net_hits','Net GT10 hits'),('failure_change','Zero-hit failure change'),('total_NDC_change_pct','Total distance-count change (%)')]):
  a=axs[di,j];vals=[float(r[key]) for r in rr];a.bar(x,vals,color=['#267f70' if (v>=0 if j==0 else v<=0) else '#be5d4d' for v in vals]);a.axhline(0,color='#555',lw=.8);a.set_xticks(x,labels,fontsize=7);a.set_title(('WebVid' if di==0 else 'Yandex')+' · '+title,fontsize=10)
  for i,v in enumerate(vals):a.annotate(f'{v:+.0f}' if j<2 else f'{v:+.2f}',(i,v),xytext=(0,4 if v>=0 else -11),textcoords='offset points',ha='center',fontsize=8)
fig.suptitle('E79 target-space profiles | historical aux 7,952 per dataset | L128 | no QPS measurement',fontsize=12)
fig.savefig(O/'figures/target_modes.png',dpi=170);fig.savefig(O/'figures/target_modes.svg');plt.close(fig)
failed=[];union={};shown={}
for ds in DS:
 c=read(O/'inputs'/ds/'aux.json');gt=np.fromfile(c['gt_file'],np.int64).reshape(7952,100);rows=np.fromfile(c['row_ids'],np.int64);raw={m['model_name']:load_raw(O/'results'/ds/'aux'/m['name'],7952) for m in c['methods']};names=list(raw);H=np.stack([raw[n]['hits'] for n in names],1);take=np.flatnonzero(np.any(H==0,axis=1));changed=np.any(H==0,axis=1)&np.any(H>0,axis=1);union[ds]=dict(any_zero=len(take),changed_zero=int(changed.sum()),all_zero=int(np.all(H==0,axis=1).sum()))
 for i in take:
  r=dict(dataset=ds,namespace='router_train',source_row=int(rows[i]),changed_zero_status=bool(changed[i]),GT10=' '.join(map(str,gt[i,:10])))
  for n in names:r[n+'_hits']=int(raw[n]['hits'][i]);r[n+'_entries']=' '.join(map(str,raw[n]['entries'][i]));r[n+'_returns']=' '.join(map(str,raw[n]['ids'][i]))
  failed.append(r)
 ix=np.flatnonzero(changed)[:24];shown[ds]=(rows[ix],H[ix],names)
with (O/'results/failure_queries.csv').open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(failed[0]));w.writeheader();w.writerows(failed)
fig,axs=plt.subplots(1,2,figsize=(10,9),layout='constrained')
for a,ds in zip(axs,DS):
 rows,H,names=shown[ds];a.imshow(H,vmin=0,vmax=10,aspect='auto',cmap='YlGnBu');a.set_xticks(range(len(names)),[n.replace('10','').replace('baseline','P') for n in names],rotation=20);a.set_yticks(range(len(rows)),rows,fontsize=8);a.set_ylabel('router_train source row');a.set_title(('WebVid' if ds==DS[0] else 'Yandex')+f" | union {union[ds]['any_zero']} / changed {union[ds]['changed_zero']}")
 for (i,j),v in np.ndenumerate(H):a.text(j,i,str(v),ha='center',va='center',color='white' if v>5 else '#333',fontsize=8)
fig.suptitle('E79 zero-GT10-hit queries | first 24 changed rows per dataset\nFull union, including all-method failures, retained in CSV | L128 / historical aux / no QPS',fontsize=11)
fig.savefig(O/'figures/failure_queries.png',dpi=150);plt.close(fig)
dump(O/'results/failure_union.json',union)
lines=['# E79：以GT10目标方向分组的入口画像','', '新目标分组及固定置换对照已完成双数据集真实查询。'+('至少一集通过预锁质量门，可另立完整wall协议。' if gate['wall_measurement_allowed'] else '两集均未通过预锁质量门，停止本版本；不改选置换对照或扫分组参数。')+' 这不否认E73/E74 Yandex局部正信号，默认未替换。整日21:00目标未完成。','', '相对旧query方向分组，唯一新增训练信号是已有GT10目标方向；在线仍为一次小HNSW取7slot、去重三真实入口、原NSG/raw-IP。父P与原H815/821保持，GT只在返回后评分。','', '| 数据 | 候选 / 对照 | 净GT10命中 | ΔRecall pp | 救回 / 新增零命中 | 两半净命中 |','|---|---|---:|---:|---|---|']
for r in allpairs:
 halves=[next(x['net_hits'] for x in paired if x['dataset']==r['dataset'] and x['candidate']==r['candidate'] and x['reference']==r['reference'] and x['split']==s) for s in ['first_half','second_half']]
 lines.append(f"| {'WebVid' if r['dataset']==DS[0] else 'Yandex'} | {r['candidate']} / {r['reference']} | {int(r['net_hits']):+d} | {float(r['recall_delta_pp']):+.4f} | {r['rescued']} / {r['new_failures']} | {' / '.join(halves)} |")
lines+=['','每dataset的target须同时胜P与compact全量、两半非负且失败不增；对permuted全量/两半非负且失败不增。所有条件在查询前锁定。只看训练分离度、净同LRecall、NDC或置换差异都不是完整性能改善。','', '旧收益保留与损伤迁移（按相对P的逐query净命中正负部，不是GT成员实际集合变化）：','']
for r in ret:lines.append(f"- {'WebVid' if r['dataset']==DS[0] else 'Yandex'} {r['candidate']}：保留旧compact正命中 {r['retained_old_gain']}/{r['old_gain']}；丢失 {r['forgone_old_gain']}、新增收益 {r['new_gain']}；避免旧损失 {r['avoided_old_loss']}、新增/放大损失 {r['new_or_amplified_loss']}。")
lines+=['','原A SHA/P bytes、完整旧Q分配/支持/聚合/W已恢复；目标行维度头/ID/范数、固定32行独立标量目标参考/集和固定12个hub独立query聚合/变体通过。分区差异按A加权并消除二元标签交换，完整表保存。','']
for x in offline['datasets']:
 for v in x['variants']:lines.append(f"- {'WebVid' if x['dataset']==DS[0] else 'Yandex'} {v['model']}：{v['eligible']}个合格双子hub，{v['physical_profiles']}画像；相对旧Q分区加权无标签差异均值 {100*v['mean_weighted_disagreement_modulo_labels']:.2f}%。")
lines+=['','置换只打乱目标特征行，A/Q/源行固定；它也改变支持、合格数和物理图，因此不是仅有目标身份改变的严格等容量因果控制。新目标均值是否覆盖同hub真正有用目标仍未定因，不从几何结果补故事。','',f"本阶段 {cost['NSG']} NSG / {cost['HNSW']} HNSW、4离线分组训练/2旧分组复现、4真实小图构建、0梯度更新/0新GT/0编译。离线总 {cost['offline_total_seconds']:.3f}s，四新分组/聚合/导出 {cost['offline_partition_training_seconds']:.3f}s，目标构造 {cost['target_construction_seconds']:.3f}s，原Q复现 {cost['old_Q_reconstruction_seconds']:.3f}s，构图 {cost['micro_graph_build_seconds']:.3f}s，四native {cost['native_job_seconds']:.3f}s。此操作wall含加载/计数/I/O，不是QPS。继承GT/P成本未重测为unknown。",'', '完整plain/count、256原kernel、P/compact旧返回31808行全字段恢复、全部7slot/图W/labels/合法邻接和集合/mask通过；原始输出与成本见链接。CPU15/进程及数值库1线程，四工具实际terminal0后评分，无并发被测方法。','',f"失败并集 {sum(x['any_zero'] for x in union.values())} 条dataset/source-row，其中 {sum(x['changed_zero'] for x in union.values())} 条失败状态变化；全方法均失败的行也完整保留GT10/各入口/各返回ID，图仅显示每集前24个变化源行。",'', 'P-fit20K含旧train/monitor；aux7952与两半是已观察选择训练反馈，cal/audit历史使用。E34最终与held-out本阶段未打开；不能把本结果当独立盲测。磁盘使用独立前瞻6.9GiB下限、64MiB阶段上限，另32MiB晚间/4MiB交接；此前各版本7GiB与旧封存不改。','', '[完整配对](results/paired.csv) · [质量门](results/gate.json) · [画像分区](results/partition_comparison.csv) · [完整失败query](results/failure_queries.csv) · [失败图](figures/failure_queries.png) · [质量与成本图](figures/target_modes.png) · [成本](results/cost.json) · [验收](reviews/verification.json)。','', '本阶段无新增QPS点。最近完整QPS图仍来自独立E74开发批次：[QPS–Recall](../stage15_compact_wall_v1/figures/recall_qps.png)、[QPS–失败率](../stage15_compact_wall_v1/figures/failure_qps.png)、[按L三指标](../stage15_compact_wall_v1/figures/three_metrics_by_L.png)；不得把本次L128结果拼到旧速度曲线。晚间最终对照仍待执行。']
(O/'report.md').write_text('\n'.join(lines)+'\n');resources();print('E79_REPORT',union)
