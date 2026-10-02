from common import *
from verify_candidates import load_raw
import csv
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();pairs=list(csv.DictReader((O/'results/paired.csv').open()));g=read(O/'results/gate.json');cost=read(O/'results/cost.json');v=read(O/'reviews/verification.json');con=read(O/'results/construction.json');failed=[]
fig,ax=plt.subplots(2,3,figsize=(13,7.5),constrained_layout=True)
for di,ds in enumerate(DS):
 for j,(key,unit) in enumerate([('net_hits','Net GT10 hits'),('failure_change','Failure count change'),('total_NDC_change_pct','Total NDC change (%)')]):
  refs=['baseline10','compact10','neighbor10'];xs=[next(x for x in pairs if x['dataset']==ds and x['candidate']=='sibling10' and x['reference']==ref and x['split']=='all') for ref in refs];vals=[float(x[key]) for x in xs];a=ax[di,j];a.bar(['vs P','vs compact','vs neighbor'],vals,color=['#5382a1','#7aa675','#ca944c']);a.axhline(0,color='black',lw=.7);span=max(1,max(0,max(vals))-min(0,min(vals)));a.set_ylim(min(0,min(vals))-.25*span,max(0,max(vals))+.25*span);a.set_ylabel(unit);a.set_title('WebVid' if di==0 else 'Yandex')
  for i,x in enumerate(vals):a.text(i,x+(.035*span if x>=0 else -.035*span),f'{x:+.2f}' if j==2 else f'{int(x):+d}',ha='center',va='bottom' if x>=0 else 'top')
fig.suptitle('E83 sibling links | historical aux7952, L128 | counts only, no QPS');fig.savefig(O/'figures/sibling_links.png',dpi=150);plt.close(fig)
names=['baseline10','compact10','sibling10','neighbor10']
for ds in DS:
 cfg=read(O/'inputs'/ds/'aux.json');gt=np.fromfile(cfg['gt_file'],np.int64).reshape(7952,100);rows=np.fromfile(cfg['row_ids'],np.int64);raw={m:load_raw(O/'results'/ds/'aux'/(m+'_L128'),7952) for m in names};hs=np.stack([raw[m]['hits'] for m in names]);zero=hs==0;union=zero.any(0);changed=np.any(zero!=zero[0],axis=0)
 for i in np.flatnonzero(union):
  rec=dict(dataset=ds,namespace=read(C/'stage10_exact_triple_utility_v1/inputs'/ds/'provenance.json')['namespace'],source_row=int(rows[i]),changed_zero_status=bool(changed[i]),gt10=' '.join(map(str,gt[i,:10])))
  for m in names:rec[m+'_hits']=int(raw[m]['hits'][i]);rec[m+'_entries']=' '.join(map(str,raw[m]['entries'][i]));rec[m+'_ids']=' '.join(map(str,raw[m]['ids'][i]))
  failed.append(rec)
with (O/'results/failure_queries.csv').open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(failed[0]));w.writeheader();w.writerows(failed)
fig,ax=plt.subplots(1,2,figsize=(10.5,9),constrained_layout=True)
for di,ds in enumerate(DS):
 rows=[x for x in failed if x['dataset']==ds and x['changed_zero_status']][:24];mat=np.array([[x[m+'_hits'] for m in names] for x in rows]);im=ax[di].imshow(mat,cmap='viridis',vmin=0,vmax=10,aspect='auto');ax[di].set_xticks(range(4),['P','Compact','Sibling','Neighbor']);ax[di].set_yticks(range(len(rows)),[x['source_row'] for x in rows]);ax[di].set_title('WebVid' if di==0 else 'Yandex');ax[di].set_ylabel('router_train source row')
 for i in range(len(rows)):
  for j in range(4):ax[di].text(j,i,str(mat[i,j]),ha='center',va='center',color='white' if mat[i,j]<6 else 'black',fontsize=9)
fig.colorbar(im,ax=ax,label='GT10 hits; 0 = failure',shrink=.7);fig.suptitle('E83 failure queries | first 24 changed source rows per dataset\nHistorical aux, L128; complete union in CSV; no QPS');fig.savefig(O/'figures/failure_queries.png',dpi=150);plt.close(fig)
lines=['# E83 compact同hub画像连接补全','', '双集固定追加边实验完成。'+('至少一集预锁质量门通过，可另立完整双集wall检验费用。' if g['wall_measurement_allowed'] else '双集预锁质量门失败，停止本固定追加规则，不扫连边数/顺序或改选控制。')+' 整日21:00目标未完成，原compact局部信号保留。','', '| 数据 | 主方法相对 | 净命中 | 救回 / 新增零命中 | 两半命中 | 路由 / 总NDC变化 |','|---|---|---:|---|---|---|']
for ds in DS:
 for ref in ['baseline10','compact10','neighbor10']:
  x=next(x for x in pairs if x['dataset']==ds and x['candidate']=='sibling10' and x['reference']==ref and x['split']=='all');halves=[int(next(y for y in pairs if y['dataset']==ds and y['candidate']=='sibling10' and y['reference']==ref and y['split']==s)['net_hits']) for s in ['first_half','second_half']];lines.append(f'| {"WebVid" if ds==DS[0] else "Yandex"} | {ref} | {int(x["net_hits"]):+d} | {x["rescued"]} / {x["new_failures"]} | {halves} | {float(x["route_NDC_change_pct"]):+.2f}% / {float(x["total_NDC_change_pct"]):+.2f}% |')
lines += ['', '原compact每hub最多3画像，主方法仅在原32容量内追加缺失同hub有向边，旧边及次序不变；控制同节点同新增度，改为最高完整画像内积的其他hub非邻居。两者不匹配新边长度，不能从边数控制单独宣称语义因果。Web新增1359、Y1285条/臂，图旧边15834/23063全部保留；缺边节点1140/1264，实际修改1139/1263，容量有限节点2/1。画像/label/header/层级/上层和原NSG均不变，没有新聚类或在线补偿。', '', '全部4物理图独立解析、原边前缀/只改计数与未用邻接槽/回填原字节恢复及逐节点度匹配通过；近邻控制固定受影响行独立内积排序检查。在线原E73同SHA evaluator保持ef10/七slot去重三入口。所有ANN CPU15/实际进程及数值库1线程，四工具实际退出后分析。', '',f'实际{cost["NSG"]:,} NSG / {cost["HNSW"]:,} HNSW、4静态边安装、0普通build/训练/新GT/编译；native操作wall {cost["native_job_seconds"]:.3f}s，非QPS。安装/第一次prepare耗时未保存为未知；成功恢复检查耗时 {con["successful_recovery_verification_seconds"]:.3f}s。继承GT/画像训练成本未知。', '', f'完整集合/mask {v["set_scored_rows"]:,}行、旧P/compact全字段{v["old_recovered_rows"]:,}行恢复、原kernel{v["original_kernel_parity_rows"]}与完整plain/count、7slot/图身份通过。同三入口比较{v["same_triple_return_rows"]:,}行返回保持。失败并集{len(failed)}条，其中{sum(x["changed_zero_status"] for x in failed)}条状态变化，全GT10/三入口/返回ID保留。旧收益丢失、旧损失修复、新损伤和GT成员变化分别在完整表。', '', '准备阶段两个纯I/O元数据修正均保留：首次freeze把__pycache__目录当文件；恢复后四图均已安装/验收，但NumPy整型计数JSON失败。最终脚本仅核验既有图与转为Python int、冻结剩余配置，0重新安装/ANN。原源/失败记录/图不覆盖；未知耗时不填0。', '', '全部aux7952/固定两半是历史router_train[2048:10000]选择训练反馈；P-fit包含旧train/monitor，cal/audit有历史暴露。E34最终/held-out未读，不改变旧门或默认。', '', '[前瞻协议](protocol.md) · [完整配对](results/paired.csv) · [原值](results/points.csv) · [收益保留](results/gain_retention.json) · [质量门](results/gate.json) · [完整失败query](results/failure_queries.csv) · [质量/成本图](figures/sibling_links.png) · [失败图](figures/failure_queries.png) · [构图记录](results/construction.json) · [验收](reviews/verification.json) · [成本](results/cost.json)']
(O/'report.md').write_text('\n'.join(lines)+'\n');dump(O/'reviews/failure_union.json',dict(union_queries=len(failed),changed_queries=sum(x['changed_zero_status'] for x in failed),all_zero_queries=sum(not x['changed_zero_status'] for x in failed),source_namespace_preserved=True));print('REPORT_COMPLETE',len(failed))
