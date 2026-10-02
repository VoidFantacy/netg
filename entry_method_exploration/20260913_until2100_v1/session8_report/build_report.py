from pathlib import Path
import os,sys,json,csv,time
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
C=Path(__file__).resolve().parents[1];O=Path(__file__).resolve().parent;sys.path.insert(0,str(C/'stage26_query_gate_feasibility_v1/src'));from common import load_raw
DS=['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];stages=['stage24_sibling_links_v1','stage25_query_shortcuts_v1'];names=['baseline10','compact10','sibling10','shortcut10'];fail=[];unions={};scored=matched=0
assert os.sched_getaffinity(0)=={15}
def read(p):return json.loads(Path(p).read_text())
fig,ax=plt.subplots(1,2,figsize=(11,9),constrained_layout=True)
for di,ds in enumerate(DS):
 cfg=[read(C/s/'inputs'/ds/'aux.json') for s in stages];rows=np.fromfile(cfg[0]['row_ids'],np.int64);gt=np.fromfile(cfg[0]['gt_file'],np.int64).reshape(7952,100);assert Path(cfg[1]['row_ids']).read_bytes()==rows.tobytes() and Path(cfg[1]['gt_file']).read_bytes()==gt.tobytes();raw={n:load_raw(C/stages[0]/'results'/ds/'aux'/(n+'_L128'),7952) for n in names[:3]};raw['shortcut10']=load_raw(C/stages[1]/'results'/ds/'aux/shortcut10_L128',7952)
 for n in names[:2]:
  other=load_raw(C/stages[1]/'results'/ds/'aux'/(n+'_L128'),7952)
  for k in raw[n]:assert raw[n][k].tobytes()==other[k].tobytes()
  matched+=7952
 for n,a in raw.items():
  hits=np.array([len(set(r.tolist())&set(g[:10].tolist())) for r,g in zip(a['ids'],gt)]);mask=np.array([sum(1<<j for j,v in enumerate(g[:10]) if v in r) for r,g in zip(a['ids'],gt)]);assert np.array_equal(hits,a['hits']) and np.array_equal(mask,a['mask']);scored+=7952
 H=np.stack([raw[n]['hits'] for n in names],1);zero=np.any(H==0,1);changed=zero&np.any(H>0,1);unions[ds]=dict(union=int(zero.sum()),changed=int(changed.sum()),all_zero=int(np.all(H==0,1).sum()))
 for i in np.flatnonzero(zero):
  rr=dict(dataset=ds,namespace='router_train',source_row=int(rows[i]),changed_zero_status=bool(changed[i]),GT10=' '.join(map(str,gt[i,:10])))
  for n,a in raw.items():rr[n+'_hits']=int(a['hits'][i]);rr[n+'_entries']=' '.join(map(str,a['entries'][i]));rr[n+'_returns']=' '.join(map(str,a['ids'][i]))
  fail.append(rr)
 ii=np.flatnonzero(changed)[:24];im=ax[di].imshow(H[ii],vmin=0,vmax=10,cmap='viridis',aspect='auto');ax[di].set_xticks(range(4),['P','Compact','Sibling','Shortcut']);ax[di].set_yticks(range(len(ii)),rows[ii]);ax[di].set_ylabel('router_train source row');ax[di].set_title(('WebVid' if di==0 else 'Yandex')+f" | {unions[ds]['union']} union / {unions[ds]['changed']} changed")
 for (i,j),v in np.ndenumerate(H[ii]):ax[di].text(j,i,str(v),ha='center',va='center',color='white' if v<6 else 'black',fontsize=9)
fig.colorbar(im,ax=ax,shrink=.7,label='GT10 hits; 0 = failure');fig.suptitle('Session 8 | four native methods, first 24 changed rows per dataset\nHistorical aux7952 / L128; cache-aligned quality report, no new QPS');fig.savefig(O/'failure_queries.png',dpi=160);plt.close(fig)
with (O/'failure_queries.csv').open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(fail[0]));w.writeheader();w.writerows(fail)
lines=['# ACSG 第8串行研究会话报告','', 'E82–E85四阶段完成。没有建立更好方法的完整性能证据；E84在WebVid对compact的局部修复值得保留，完整门仍失败。整日21:00目标尚未完成，E34晚间最终对照待执行。','', '| 阶段 | 实际结果与停止范围 |','|---|---|','| E82 新目标bank完整排名效用 | 真实补齐3593个缺失三入口键；六门均失败，不能仅凭修近似误差继续扩E79–E81目标bank。Web局部修复和精度分组保留。 |','| E83 同hub补边 | 对compact Web−1命中/失败−1，Y0/0；路由计数增加。固定同hub补边规则停止。 |','| E84 查询排名缺口补边 | 对compact Web+42/失败−4、两半+22/+20；对P仍−17/+7。Y对compact−4/0。固定最高票规则停止，不扩大其wall。 |','| E85 路由前query线性选择 | 后3976接受对P Web−35/+3、Y+24/−3；对compact Web+8/0、Y−57/+5。原收益保留约58%，双集门失败，在线未实现。 |','', 'E84的Web变化包含114正命中和72负命中，GT成员151增/109失；保留旧compact正收益774/820、丢失46，新增32，避免旧损失82、新增损失26。实际三入口集合改变405条，38条改善、24条损伤；Y仅35条入口变化，1条改善/2条损伤。这些是配对query描述，不能当每条新边的因果贡献。E73/E74 Yandex原局部前沿信号保持。','', '本会话新增 **266,834 NSG / 339,072 HNSW**、8静态图边安装、2图监督训练、4岭回归拟合；0普通HNSW build/新增GT。编译12.744s，E84图监督阶段4.989s，E83/E84查询native操作分别111.127/111.272s，E82 native21.140s。操作wall含加载/count/I/O，存在子阶段包含关系，不是QPS。E83安装计时因准备元数据错误未保存、继承GT/P成本未知；E84短路由进程RSS仅轮询样本，非实际峰值。','', '**新增QPS点0**。最新完整开发曲线仍为[E74 QPS–Recall、QPS–失败率和按L三指标](../stage15_compact_wall_v1/report.md)，其同批55点/五轮独立wall保持原身份，不能与本会话L128诊断拼成一组曲线。晚间必须冻结候选后同批测原NSG/Fast/GT10匹配起点/实际新方法。','',f'本报告四个真实方法的失败并集 **{len(fail)}** 条、状态变化 **{sum(v["changed"] for v in unions.values())}** 条，全方法均失败 **{sum(v["all_zero"] for v in unions.values())}** 条。独立集合/mask评分{scored:,}行、共有P/compact全字段回归{matched:,}行；全表含GT10、各方法三入口和返回ID。图按源行固定前24变化例展示；失败严格为零GT10集合命中。E82完整排名诊断的517条失败、E85含训练段的410条缓存失败在各阶段独立报告，不混作一批新在线实验。','', '[四真实方法完整失败表](failure_queries.csv) · [失败图](failure_queries.png)。','', '角色：P-fit20K含旧train/monitor；aux7952、旧cal/audit历史已暴露且选择反馈算训练。E84仅raw fit查询提供排名票；E85前3976真实命中差进入拟合，后3976只作本版拟合外接受，非项目未见数据。E25历史结果因避免重启旧机制被复盘，E34最终原始query/GT及held-out未打开。所有新ANN/数值训练串行CPU15和实际进程/数值库1线程，原NSG/base/rawIP固定。','']
for stage,eid in [('stage23_target_exact_utility_v1','E82'),('stage24_sibling_links_v1','E83'),('stage25_query_shortcuts_v1','E84'),('stage26_query_gate_feasibility_v1','E85')]:lines.append(f'[{eid}完整报告](../{stage}/report.md) · [协议](../{stage}/protocol.md) · [成本](../{stage}/results/cost.json) · [封存](../{stage}/reviews/final_artifact_freeze.json)')
(O/'report.md').write_text('\n'.join(lines)+'\n');(O/'verification.json').write_text(json.dumps(dict(status='PASS',set_mask_scored_rows=scored,old_P_C_full_fields=matched,unions=unions,NSG=0,HNSW=0,new_QPS=0),indent=2)+'\n');print('SESSION8_REPORT',unions)
