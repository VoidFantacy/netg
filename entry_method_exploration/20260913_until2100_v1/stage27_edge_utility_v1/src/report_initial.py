from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();resources();gate=read(O/'results/gate.json');cost=read(O/'results/cost.json');pairs=list(csv.DictReader((O/'results/paired.csv').open()));fail=list(csv.DictReader((O/'results/failure_queries.csv').open()));ret=read(O/'results/gain_retention.json');figdir=O/'figures';figdir.mkdir(exist_ok=True)
def pair(ds,ref,split='all'):return next(r for r in pairs if r['dataset']==ds and r['candidate']=='utility10' and r['reference']==ref and r['split']==split)
fig,axs=plt.subplots(2,3,figsize=(14,7),layout='constrained')
for di,ds in enumerate(DS):
 name=['WebVid','Yandex'][di];edge=read(O/'results'/ds/'fit/edge_statistics.json');tr=read(O/'results'/ds/'fit/union_statistics.json')[0]
 axs[di,0].bar(np.arange(len(edge)),[r['net_hits'] for r in edge],color=['#18826c' if r['accepted'] else '#c75651' for r in edge]);axs[di,0].axhline(0,color='#555',lw=.6);axs[di,0].set(title=f'{name}: independent edge training',xlabel='Fixed candidate order',ylabel='Net GT10 hits vs compact')
 axs[di,1].bar(['Fit 20K','Aux 7952'],[tr['net_hits'],int(pair(ds,'compact10')['net_hits'])],color=['#7397c4','#c47d3b']);axs[di,1].axhline(0,color='#555',lw=.6);axs[di,1].set(title=f'{len(read(O/"models"/ds/"selected_edges.json"))} selected edges: merged graph',ylabel='Net hits; different pool sizes')
 refs=['baseline10','compact10','geometric10','neighbor10'];vals=[int(pair(ds,r)['net_hits']) for r in refs];axs[di,2].bar(['P','Compact','E84','Neighbor'],vals,color=['#18826c' if v>0 else '#c75651' for v in vals]);axs[di,2].axhline(0,color='#555',lw=.6);axs[di,2].set(title=f'{name} auxiliary acceptance: '+('PASS' if gate['datasets'][ds]['passed'] else 'FAIL'),ylabel='Utility graph net GT10 hits')
 for j,v in enumerate(vals):axs[di,2].annotate(f'{v:+}',(j,v),xytext=(0,3 if v>=0 else -12),textcoords='offset points',ha='center',fontsize=9)
fig.suptitle('E86 | Actual one-edge NSG supervision and frozen merged-graph acceptance\nQuality diagnosis only; no new QPS measurement',fontsize=13)
for ext in ['png','svg']:fig.savefig(figdir/('training_acceptance.'+ext),dpi=155)
plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(12,9),layout='constrained');names=['baseline10','compact10','geometric10','utility10','neighbor10']
for di,ds in enumerate(DS):
 fs=[r for r in fail if r['dataset']==ds];changed=[r for r in fs if r['changed_zero_status']=='True'];shown=changed[:24];matrix=np.array([[int(r[n+'_hits']) for n in names] for r in shown]);im=axs[di].imshow(matrix,vmin=0,vmax=10,cmap='RdYlGn',aspect='auto');axs[di].set_xticks(range(5),['P','Compact','E84','Utility','Neighbor'],rotation=20);axs[di].set_yticks(range(len(shown)),[r['source_row'] for r in shown]);axs[di].set(title=f'{["WebVid","Yandex"][di]}: {len(fs)} failure-union queries\n{len(changed)} with any zero-status change',ylabel='router_train source row')
 for y in range(len(shown)):
  for x in range(5):axs[di].text(x,y,str(matrix[y,x]),ha='center',va='center',fontsize=8,color='black')
fig.colorbar(im,ax=axs,label='GT10 hit count (failure = 0)',shrink=.65);fig.suptitle('First 24 changed failure queries per dataset; complete union retained in CSV\nAll five actual policies, same auxiliary rows and fixed L128')
for ext in ['png','svg']:fig.savefig(figdir/('failure_queries.'+ext),dpi=155)
plt.close(fig)
lines=['# E86：真实单边效用筛选静态小图','', '本阶段完成；整日21:00目标尚未完成。模型与选择规则已在aux接受前冻结。'+('至少一集预锁门通过，允许另建完整开发wall协议。' if gate['wall_measurement_allowed'] else '双集预锁门FAIL，本固定候选/筛边版本停止，不扩边数/阈值或按aux重训。'),'','训练用P-fit20K，逐条实际追加已锁定候选边并运行原NSG；合格边合并后重新实测。训练与辅助池均有历史使用，aux接受反馈计训练信息。本轮未打开E34最终原始query/GT或held-out。','', '| 数据 | 接受边 | 合并图fit净命中/失败变化 | aux对P | aux对compact | aux对E84 | aux对同节点度控制 |','|---|---:|---|---|---|---|---|']
for di,ds in enumerate(DS):
 tr=read(O/'results'/ds/'fit/union_statistics.json')[0];vals=[]
 for ref in ['baseline10','compact10','geometric10','neighbor10']:
  r=pair(ds,ref);vals.append(f"{int(r['net_hits']):+d} / {int(r['failure_change']):+d}")
 lines.append('| '+['WebVid','Yandex'][di]+f" | {tr['edges']} | {tr['net_hits']:+d} / {tr['failure_delta']:+d} | "+' | '.join(vals)+' |')
lines += ['','表内为净GT10命中数/零命中查询变化；不是Recall百分点。失败严格为返回与GT10集合交集为0。训练池20K和aux7952数量不同，不直接比较原始净命中规模。','', '## 机制与迁移','', 'E33在原单画像图中学习删原边；E84用几何漏选票数追加边；本版固定E84前64/47候选，对每条实际新增边测全fit真实NSG边际效用，按全量正/两半非负/失败不增/总NDC上限筛选。在线仍是固定compact画像、一次小图路由、三个真实入口与原NSG，没有在线预测器。全部旧图边/上层/W/映射保持。单边收益不是并图收益，合并响应另测；未接受的正负/无效边也全部保存。']
for di,ds in enumerate(DS):
 tr=read(O/'results'/ds/'fit/union_statistics.json')[0];r=pair(ds,'compact10');halves=[int(pair(ds,'compact10',s)['net_hits']) for s in ['first_half','second_half']];rr=next(x for x in ret if x['dataset']==ds and x['candidate']=='utility10');lines += ['',f"{['WebVid','Yandex'][di]}：fit并图两半{tr['half_net_hits']}，aux对compact两半{halves}，救回/新增失败{r['rescued']}/{r['new_failures']}。相对P的原compact正收益{rr['old_gain']}保留{rr['retained_old_gain']}、丢失{rr['forgone_old_gain']}、新增{rr['new_gain']}；原损失避免{rr['avoided_old_loss']}，新增或放大损失{rr['new_or_amplified_loss']}。这些是逐query净命中记账，GT成员增损在paired.csv单列，不给单hub或单边因果信用。"]
lines += ['','同节点度控制使用相同source的既定最近其他hub边，边长未匹配；不能把控制差异全部归因于监督信息。原E84完整几何图与本版稀疏筛选图边数不同，报告其真实差异，不能当只变标签的等容量消融。','', '## 成本与验收','',f"新增{cost['NSG']:,} NSG（训练{cost['training_NSG']:,}、辅助{cost['aux_NSG']:,}）；{cost['HNSW']:,} HNSW（训练{cost['training_HNSW']:,}、辅助{cost['aux_HNSW']:,}），6静态安装含2首边回归图，2离线筛边拟合，0普通构图/梯度/新GT。编译{cost['compile_seconds']:.3f}s、训练操作{cost['training_operation_seconds']:.3f}s、辅助native操作{cost['aux_native_operation_seconds']:.3f}s。操作时间含load/count/cache/保存/I/O，有不同计量范围，不能转成QPS。继承GT/P总成本未知，E84候选生成成本另属旧阶段。",'', '全部ANN串行CPU15，进程及OMP/BLAS/MKL线程1；六原生训练/查询执行任务已完成。新NSG plain/count与每集32条三路原kernel回归通过；111边完整route hashes/patch与缓存完整键恢复、合并图全旧边/非邻接bytes、独立集合/mask、全部七slot/三入口、P/compact/E84旧结果回归通过。首个单边物理图128路由与内存图比对，余单边通过同一严格安装/恢复代码和完整plain/count；不虚称每条物理文件均另存。','',f"完整失败并集{cost['failures_union']}条，其中{cost['failure_state_changes']}条至少一方法zero状态不同；CSV包含所有query的GT10、五方法入口/完整返回，无截断。当前没有新QPS点，最近完整曲线仍为独立E74批次，不能和本阶段质量点拼接。",'', '![训练与接受](figures/training_acceptance.png)','', '![失败查询](figures/failure_queries.png)','', '[完整配对](results/paired.csv) · [失败全表](results/failure_queries.csv) · [门](results/gate.json) · [成本](results/cost.json) · [协议](protocol.md) · [训练核验](reviews/training_verification.json) · [查询核验](reviews/verification.json) · [最近完整QPS–Recall/失败曲线](../stage15_compact_wall_v1/report.md)']
(O/'report.md').write_text('\n'.join(lines)+'\n');resources();print('E86_REPORT_WRITTEN')
