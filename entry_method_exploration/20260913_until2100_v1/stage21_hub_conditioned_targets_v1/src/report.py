from verify_candidates import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();assert all(j['status']=='COMPLETE' for j in read(O/'logs/jobs.json'))
with (O/'results/paired.csv').open() as f:paired=list(csv.DictReader(f))
with (O/'results/conditional_support.csv').open() as f:support=list(csv.DictReader(f))
gate=read(O/'results/gate.json');cost=read(O/'results/cost.json');offline=read(O/'results/offline.json');ret=read(O/'results/gain_retention.json');allpairs=[r for r in paired if r['split']=='all'];fig,axs=plt.subplots(2,3,figsize=(13,7),layout='constrained')
for di,ds in enumerate(DS):
 rr=[r for r in allpairs if r['dataset']==ds];x=np.arange(len(rr));labels=[r['candidate'].replace('10','')+'\nvs '+r['reference'].replace('10','').replace('baseline','P') for r in rr]
 for j,(key,title) in enumerate([('net_hits','Net GT10 hits'),('failure_change','Zero-hit failure change'),('total_NDC_change_pct','Total distance-count change (%)')]):
  a=axs[di,j];vals=[float(r[key]) for r in rr];a.bar(x,vals,color=['#267f70' if (v>=0 if j==0 else v<=0) else '#be5d4d' for v in vals]);a.axhline(0,color='#555',lw=.8);a.margins(y=.22);a.set_xticks(x,labels,fontsize=7);a.set_title(('WebVid' if di==0 else 'Yandex')+' · '+title,fontsize=10)
  for i,v in enumerate(vals):a.annotate(f'{v:+.0f}' if j<2 else f'{v:+.2f}',(i,v),xytext=(0,4 if v>=0 else -11),textcoords='offset points',ha='center',fontsize=8)
fig.suptitle('E80 hub-conditioned target profiles | historical aux 7,952 per dataset | L128 | no QPS',fontsize=12)
fig.savefig(O/'figures/conditional_modes.png',dpi=170);fig.savefig(O/'figures/conditional_modes.svg');plt.close(fig)
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
fig.suptitle('E80 zero-GT10-hit queries | first 24 changed rows per dataset\nFull union, including all-method failures, retained in CSV | L128 / historical aux / no QPS',fontsize=11)
fig.savefig(O/'figures/failure_queries.png',dpi=150);plt.close(fig);dump(O/'results/failure_union.json',union)
lines=['# E80：按真实hub条件化的GT10目标分组','', '条件目标画像已完成双数据集构造和真实查询。'+('至少一集通过预锁质量门，下一步仅可独立冻结完整wall；尚非性能GO。' if gate['wall_measurement_allowed'] else '两集均未通过预锁门，停止本条件均值版本，不扫参数或改选旧对照。')+' 整日21:00目标未完成。','', '原A按GT每个目标分别归属hub；E79却给同一query的所有hub使用全GT10均值。E80仅将分组特征改为该hub条件权重beta下的目标均值，仍按原A和query聚合子画像。目标/query/base/raw-IP/原NSG/真实H固定，线上仍一次ef10小HNSW取7slot去重三真实入口。此为信息定义改变，尚不能把目标混合作为已确认的失败原因。','', '| 数据 | 候选 / 对照 | 净GT10命中 | ΔRecall pp | 救回 / 新增零命中 | 两半净命中 |','|---|---|---:|---:|---|---|']
for r in allpairs:
 halves=[next(x['net_hits'] for x in paired if x['dataset']==r['dataset'] and x['candidate']==r['candidate'] and x['reference']==r['reference'] and x['split']==s) for s in ['first_half','second_half']]
 lines.append(f"| {'WebVid' if r['dataset']==DS[0] else 'Yandex'} | {r['candidate']} / {r['reference']} | {int(r['net_hits']):+d} | {float(r['recall_delta_pp']):+.4f} | {r['rescued']} / {r['new_failures']} | {' / '.join(halves)} |")
lines+=['','条件化对P/compact要求全量正、两半非负/失败不增，对global全量及两半非负/失败不增。全门在训练/查询前锁定，global是E79冻结target原件在本批的对照身份。门失败不由同LRecall或NDC升级成效率结论。','', '旧收益保留与损伤迁移（相对P的逐query净命中正负部；GT成员集合增损另列）：','']
for r in ret:
 if r['candidate']=='conditional10':lines.append(f"- {'WebVid' if r['dataset']==DS[0] else 'Yandex'}：保留旧compact正命中 {r['retained_old_gain']}/{r['old_gain']}；丢失 {r['forgone_old_gain']}、新增收益 {r['new_gain']}；避免旧损失 {r['avoided_old_loss']}、新增/放大损失 {r['new_or_amplified_loss']}。")
lines+=['','离线目标支持只用于解释输入/表示，没有把逐hub几何差异当NSG因果信用：','']
for x in offline['datasets']:
 rr=[r for r in support if r['dataset']==x['dataset']];weights=np.array([float(r['parent_mass']) for r in rr]);drift=np.array([float(r['weighted_target_drift']) for r in rr]);eff=np.array([float(r['effective_target_count']) for r in rr]);disc=np.array([float(r['weighted_partition_disagreement_modulo_labels']) for r in rr]);lines.append(f"- {'WebVid' if x['dataset']==DS[0] else 'Yandex'}：{x['active_hubs']}个active父hub，{x['eligible_hubs']}个合格双子，{x['physical_profiles']}物理画像；按父mass加权目标1−cos均值 {np.average(drift,weights=weights):.6f}、条件有效GT目标数 {np.average(eff,weights=weights):.3f}、对global分区无标签差异 {100*np.average(disc,weights=weights):.2f}%。")
lines+=['','全部rank权重/A SHA、父P字节及E79全局目标digest恢复。每集固定32query×12hub条件特征独立逐rank参考、12hub独立query聚合通过；正支持零目标退化按协议记录，A=0只表示无该hub权重。全部beta/目标在RAM，逐hub流式，不持久化N×H×d大矩阵。条件化也可改变子支持、画像容量和图，不能把最终差异只归于某个中介。','', f"实际 {cost['NSG']} NSG / {cost['HNSW']} HNSW、2离线画像分组训练、2真实build，0梯度/新GT/编译/合成ANN。离线 {cost['offline_total_seconds']:.3f}s（含rank恢复 {cost['rank_reconstruction_seconds']:.3f}s）、图build {cost['micro_graph_build_seconds']:.3f}s、四native {cost['native_job_seconds']:.3f}s。操作wall含加载/count/I/O，不能当QPS；继承GT/P成本未知。",'', '旧P/compact/global47712条完整返回/距离bits/入口/两NDC恢复、全部plain/count及256原kernel、完整7slot/图W/labels/邻接/集合mask均通过。CPU15/实际进程与数值库1线程，方法/数据集串行，工具terminal0后分析。', '', f"失败并集 {sum(x['any_zero'] for x in union.values())}个dataset/source-row，其中{sum(x['changed_zero'] for x in union.values())}个失败状态变化。全表保留GT10/入口/返回ID及所有方法都失败的行，图仅按源行取每集前24个变化例。",'', 'P-fit20K含旧train/monitor，aux7952及两半已观察且接受反馈计训练；cal/audit历史使用。E34最终/held-out本阶段未打开，旧E79门和seal保持。资源独立锁64MiB阶段上限、6.8GiB下限外留64MiB晚间+4MiB交接，不清理旧产物。', '', '[协议](protocol.md) · [完整配对](results/paired.csv) · [质量门](results/gate.json) · [条件支持](results/conditional_support.csv) · [完整失败query](results/failure_queries.csv) · [失败图](figures/failure_queries.png) · [质量与计数图](figures/conditional_modes.png) · [成本](results/cost.json) · [验收](reviews/verification.json)。','', '本阶段新增QPS点0。E73/E74 Yandex局部信号和Web损伤保留；最新独立完整性能曲线仍见[E74报告](../stage15_compact_wall_v1/report.md)，不能拼接本批L128点。晚间冻结后最终同批对照仍待完成。']
(O/'report.md').write_text('\n'.join(lines)+'\n');resources();print('E80_REPORT',union)
