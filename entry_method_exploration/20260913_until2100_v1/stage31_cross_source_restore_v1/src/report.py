from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();resources();pairs=list(csv.DictReader((O/'results/paired.csv').open()));fail=list(csv.DictReader((O/'results/failure_queries.csv').open()));cost=read(O/'results/cost.json');gate=read(O/'results/gate.json');figdir=O/'figures';figdir.mkdir(exist_ok=True)
fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
for di,ds in enumerate(DS):
 rr=[r for r in pairs if r['dataset']==ds and r['split']=='accept' and r['candidate']=='supported10']
 for ax,key,title in zip(axes[di],['net_hits','failure_change','total_NDC_change_pct'],['Net GT10 hits','Zero-hit failure change','Total NDC change (%)']):
  v=[float(r[key]) for r in rr];bars=ax.bar(['P','compact','E89','random'],v,color='#267f96');ax.axhline(0,color='black',lw=.7);ax.margins(y=.3);ax.bar_label(bars,fmt='%.3f' if key.endswith('pct') else '%+.0f',padding=4);ax.set_title(('WebVid' if di==0 else 'Yandex')+' — '+title);ax.set_xlabel('E90 minus reference');ax.grid(axis='y',alpha=.2)
fig.suptitle('E90 cross-source restoration | exposed acceptance suffix 3,976 | L128 | no QPS')
fig.savefig(figdir/'acceptance.png',dpi=170);fig.savefig(figdir/'acceptance.svg');plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for ax,ds in zip(axes,DS):
 rr=[r for r in read(O/'results'/ds/'union_statistics.json') if r['model']=='supported10'];v=[r['net_hits'] for r in rr];v.append(next(int(r['net_hits']) for r in pairs if r['dataset']==ds and r['candidate']=='supported10' and r['reference']=='compact10' and r['split']=='accept'));bars=ax.bar(['Support 3,976\ntraining','P-fit 20,000\ntraining','Acceptance 3,976\npreviously exposed'],v,color=['#c29647','#c29647','#267f96']);ax.bar_label(bars,fmt='%+.0f',padding=4);ax.axhline(0,color='black',lw=.7);ax.margins(y=.35);ax.set_ylabel('Net GT10 hits vs compact');ax.set_title('WebVid' if ds==DS[0] else 'Yandex (zero update)')
fig.suptitle('Different sample sizes and roles; no unseen-data or QPS claim');fig.savefig(figdir/'training_transfer.png',dpi=170);fig.savefig(figdir/'training_transfer.svg');plt.close(fig)
models=['baseline10','compact10','previous10','supported10','random10'];fig,axes=plt.subplots(1,2,figsize=(12,9),layout='constrained')
for ax,ds in zip(axes,DS):
 selected=sorted([r for r in fail if r['dataset']==ds and r['role']=='historically_exposed_acceptance' and r['changed_zero_status']=='True'],key=lambda r:int(r['source_row']))[:24];mat=np.array([[int(r[m+'_hits']) for m in models] for r in selected]);im=ax.imshow(mat,aspect='auto',vmin=0,vmax=10,cmap='YlGnBu');ax.set_xticks(range(5),['P','compact','E89','E90','random'],rotation=20);ax.set_yticks(range(len(selected)),[r['source_row'] for r in selected]);ax.set_ylabel('router_train source row');ax.set_title('WebVid' if ds==DS[0] else 'Yandex')
 for i in range(len(selected)):
  for j in range(5):ax.text(j,i,str(mat[i,j]),ha='center',va='center',color='white' if mat[i,j]>=6 else 'black',fontsize=8)
fig.colorbar(im,ax=axes,label='GT10 hits; failure = 0',shrink=.7);fig.suptitle('First 24 changed failure rows per dataset from acceptance suffix\nAll support + acceptance zero-hit rows retained in CSV; L128; no QPS');fig.savefig(figdir/'failure_queries.png',dpi=170);fig.savefig(figdir/'failure_queries.svg');plt.close(fig)
text=['# E90 双来源支持的局部父画像恢复','', '固定复用E89通过P-fit20K筛选的13/8个动作，用aux前3976行作为明确的训练支持，再筛选一次。每个动作仍在原compact背景测量；两个训练来源均测量实际合并，不把单项效用和当合并收益。所有模型与门槛在本次合并辅助响应前冻结，后3976行仅接受完整模型。', '', 'P-fit为router_train[10000:30000]，含旧train/monitor；支持为[2048:6024]，接受为[6024:10000]。今天及历史已经观察全部aux，接受区不是未观察验证集，接受反馈计训练信息。原E34最终query/GT/row及held-out未打开。', '', '| 数据 | 角色 | 动作数 | 净命中 vs compact | 两半 | 救回/新增零失败 |','|---|---|---:|---:|---|---|']
for ds in DS:
 for r in read(O/'results'/ds/'union_statistics.json'):
  if r['model']=='supported10':text.append(f"| {'Web' if ds==DS[0] else 'Y'} | {r['role']} | {r['groups']} | {r['net_hits']:+d} | {r['half_net_hits']} | {r['rescued']}/{r['new_failed']} |")
text+=['','| 接受区3976 | 参照 | 净命中 | Recall变化pp | 救回/新增零失败 | 两个1988行子半 | 总NDC变化% |','|---|---|---:|---:|---|---|---:|']
for r in pairs:
 if r['split']!='accept' or r['candidate']!='supported10':continue
 halves=[int(z['net_hits']) for z in pairs if z['dataset']==r['dataset'] and z['candidate']==r['candidate'] and z['reference']==r['reference'] and z['split'] in ['accept_half1','accept_half2']];text.append(f"| {'Web' if r['dataset']==DS[0] else 'Y'} | {r['reference']} | {int(r['net_hits']):+d} | {float(r['recall_delta_pp']):+.5f} | {r['rescued']}/{r['new_failures']} | {halves} | {float(r['total_NDC_change_pct']):+.4f} |")
text+=['','完整预锁门：'+'；'.join(('Web' if ds==DS[0] else 'Y')+' '+('PASS' if gate['datasets'][ds]['passed'] else 'FAIL') for ds in DS)+'。'+('允许另立同批wall协议，尚非性能通过。' if gate['wall_measurement_allowed'] else '停止此固定双来源筛选版本，不据接受反馈扫阈值/子集/幅度；没有新增QPS。'),'', 'Y无动作通过支持筛选，主方法及随机控制均逐字等于compact，相关相对P信号全部继承compact，不是新模型改善。随机控制从原13/8候选的固定置换取相同动作数，允许与主方法重叠；主控差不构成纯标签因果效应。', '', f"新增{cost['NSG']} NSG（训练{cost['training_NSG']}、辅助{cost['aux_NSG']}），{cost['HNSW']} HNSW；{cost['physical_graph_exports']}物理副本，其中{cost['nonzero_vector_installs']}非零向量安装、{cost['zero_update_copies']}零更新；2离线筛选拟合，0构图/编译/梯度/新GT/QPS。准备{cost['preparation_operation_seconds']:.3f}s、训练{cost['training_operation_seconds']:.3f}s、辅助{cost['aux_native_operation_seconds']:.3f}s均为操作wall，不是查询QPS；继承P/GT总成本未知。", '', f"完整两角色失败并集{cost['failures_union']}行，其中{cost['failure_state_changes']}行五配置zero状态不同；[完整CSV](results/failure_queries.csv)保留角色、源行、GT10、各方法入口和全部返回。失败严格零GT10命中。图展示接受区每集源行排序前24个变化案例。", '', '全部ANN串行CPU15，实际线程及各库1；训练完整query-key缓存、plain/count/reference、真实模型向量与非向量图字节、7slot去重入口、全部返回集合/mask、辅助旧对照和训练支持前缀一致性均核验。不同批次不拼接曲线。', '', '[协议](protocol.md) · [训练核验](reviews/training_verification.json) · [辅助核验](reviews/verification.json) · [完整门](results/gate.json) · [逐对配对](results/paired.csv) · [成本](results/cost.json)', '', '![训练迁移](figures/training_transfer.png)', '', '![接受区](figures/acceptance.png)', '', '![失败query](figures/failure_queries.png)']
(O/'report.md').write_text('\n'.join(text)+'\n');print('E90_REPORT_WRITTEN')
