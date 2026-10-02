from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();resources();pairs=list(csv.DictReader((O/'results/paired.csv').open()));fail=list(csv.DictReader((O/'results/failure_queries.csv').open()));cost=read(O/'results/cost.json');gate=read(O/'results/gate.json')
figdir=O/'figures';figdir.mkdir(exist_ok=True)
fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
for di,ds in enumerate(DS):
 rr=[r for r in pairs if r['dataset']==ds and r['split']=='all' and r['candidate']=='restore10'];labels=['P','compact','E84','random']
 for ax,key,title in zip(axes[di],['net_hits','failure_change','total_NDC_change_pct'],['Net GT10 hits','Zero-hit failure change','Total NDC change (%)']):
  v=[float(r[key]) for r in rr];bars=ax.bar(labels,v,color=['#177d8d' if x>=0 else '#ce5f50' for x in v]);ax.axhline(0,color='black',lw=.7);ax.margins(y=.3);ax.bar_label(bars,fmt='%.3f' if key.endswith('pct') else '%+.0f',padding=4);ax.set_title(('WebVid' if di==0 else 'Yandex')+' — '+title);ax.set_xlabel('Restored model minus reference');ax.grid(axis='y',alpha=.2)
fig.suptitle('E89 local parent restoration | historically exposed aux 7,952 | L128 | no QPS')
fig.savefig(figdir/'parent_restore.png',dpi=170);fig.savefig(figdir/'parent_restore.svg');plt.close(fig)
models=['baseline10','compact10','geometric10','restore10','random10'];names=['P','compact','E84','restore','random']
fig,axes=plt.subplots(1,2,figsize=(12,9),layout='constrained')
for ax,ds in zip(axes,DS):
 selected=sorted([r for r in fail if r['dataset']==ds and r['changed_zero_status']=='True'],key=lambda r:int(r['source_row']))[:24]
 mat=np.array([[int(r[m+'_hits']) for m in models] for r in selected]);im=ax.imshow(mat,aspect='auto',vmin=0,vmax=10,cmap='YlGnBu');ax.set_xticks(range(5),names,rotation=20);ax.set_yticks(range(len(selected)),[r['source_row'] for r in selected]);ax.set_ylabel('router_train source row');ax.set_title('WebVid' if ds==DS[0] else 'Yandex')
 for i in range(len(selected)):
  for j in range(5):ax.text(j,i,str(mat[i,j]),ha='center',va='center',color='white' if mat[i,j]>=6 else 'black',fontsize=8)
fig.colorbar(im,ax=axes,label='GT10 hits; failure = 0',shrink=.7)
fig.suptitle('First 24 changed failure rows per dataset; full union retained in CSV\nHistorical aux7952, L128; no final evaluation / no QPS')
fig.savefig(figdir/'failure_queries.png',dpi=170);fig.savefig(figdir/'failure_queries.svg');plt.close(fig)
text=['# E89 局部父画像恢复：完整实测结果','', '固定少数hub，将其两个子画像逐字恢复为父P，原compact全部slot、真实hub映射、图邻接/层级/入口保持。候选由P优于compact的完整训练响应提议，但只按单组真实NSG效用接受；这不把完整策略差当单hub信用。线上仍一张静态小图、七slot去重三入口、原NSG。','', '| 数据 | 接受hub/候选 | 单项净命中和/实际并图 | fit两半 | fit失败变化 |','|---|---:|---|---|---:|']
for ds in DS:
 tr=next(r for r in read(O/'results'/ds/'fit/union_statistics.json') if r['model']=='restore10');inter=read(O/'results'/ds/'merged_interaction.json');text.append(f"| {'Web' if ds==DS[0] else 'Y'} | {tr['groups']}/32 | {inter['independent_sum']:+d}/{inter['actual_merged']:+d}，{inter['nonadditive_queries']}非加性query | {tr['half_net_hits']} | {tr['failure_delta']:+d} |")
text+=['','| aux7952数据 | 参照 | 净命中 | Recall变化pp | 救回/新增零失败 | 两半净命中 | 总NDC变化% |','|---|---|---:|---:|---|---|---:|']
for r in pairs:
 if r['split']!='all' or r['candidate']!='restore10':continue
 halves=[int(z['net_hits']) for z in pairs if z['dataset']==r['dataset'] and z['candidate']==r['candidate'] and z['reference']==r['reference'] and z['split']!='all']
 text.append(f"| {'Web' if r['dataset']==DS[0] else 'Y'} | {r['reference']} | {int(r['net_hits']):+d} | {float(r['recall_delta_pp']):+.5f} | {r['rescued']}/{r['new_failures']} | {halves} | {float(r['total_NDC_change_pct']):+.4f} |")
text+=['','预锁完整质量门：'+ '；'.join(('Web' if ds==DS[0] else 'Y')+' '+('PASS' if gate['datasets'][ds]['passed'] else 'FAIL') for ds in DS)+'。所有规则见gate.json；局部训练收益与辅助迁移分开，未替换默认。'+('可以另立同批完整wall协议，尚不是性能通过。' if gate['wall_measurement_allowed'] else '双集均未过门，停止此固定候选/恢复/筛选版本，不扫阈值或幅度。'),'',f"完整失败并集{cost['failures_union']}条，{cost['failure_state_changes']}条发生五配置间zero状态变化；全部GT10、三入口与返回ID在[failure_queries.csv](results/failure_queries.csv)，图只取每集前24个变化案例。失败严格GT10零命中。",'',f"新增{cost['NSG']} NSG（训练{cost['training_NSG']}、辅助{cost['aux_NSG']}）；{cost['HNSW']} HNSW。{cost['physical_graph_exports']}物理导出/{cost['nonzero_vector_installs']}非零向量安装/{cost['zero_update_copies']}零更新副本，2离线效用筛选拟合，0普通构图/梯度/新GT/QPS。编译{cost['compile_seconds']:.3f}s；训练操作{cost['training_operation_seconds']:.3f}s，辅助操作{cost['aux_native_operation_seconds']:.3f}s含load/count/cache/I/O，不是QPS。继承GT/P总成本未知；准备总wall包含编译，不与编译重复相加。",'', '单组收益和不是合并收益，实际交互逐query保存。随机控制匹配恢复hub/子行数与非向量图字节，但不匹配支持/位移/损伤，因此主控差不是标签纯因果效应。恢复为父P仍保留重复物理slot，近似路径变化包含在此整组干预效果中。', '', '所有ANN串行CPU15，实际进程及各库1线程；原compact训练缓存、三个辅助旧对照、plain/count/原kernel、第一动作物理图和撤销恢复、全部集合/mask与非向量图bytes独立核验。P-fit20K含旧train/monitor，aux7952和两半/cal/audit历史暴露，接受反馈计训练。E34最终query/GT/row及held-out未打开；本阶段没有QPS，不能与E74拼接曲线。', '', '[协议](protocol.md) · [门](results/gate.json) · [原值](results/points.csv) · [全部配对](results/paired.csv) · [损益迁移](results/gain_retention.json) · [训练核验](reviews/training_verification.json) · [查询核验](reviews/verification.json) · [成本](results/cost.json)', '', '![辅助质量与成本计数](figures/parent_restore.png)', '', '![失败query](figures/failure_queries.png)']
(O/'report.md').write_text('\n'.join(text)+'\n');print('E89_REPORT_WRITTEN',cost['failures_union'])
