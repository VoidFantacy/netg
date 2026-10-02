from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();rows=list(csv.DictReader((O/'results/paired.csv').open()));rank=list(csv.DictReader((O/'results/ranking.csv').open()));gate=read(O/'results/gate.json');cost=read(O/'results/cost.json')
labels=['P30 − P10','Dup30 − Dup10','Mode30 − Mode10','Mode30 − P10','Mode30 − P30','Mode30 − Dup30','Mode10 − P10']
fig,axes=plt.subplots(2,3,figsize=(14,8),constrained_layout=True)
for di,ds in enumerate(DS):
 rr=[x for x in rows if x['dataset']==ds and x['split']=='all']
 for j,(key,title) in enumerate([('recall_delta_pp','Recall change (pp)'),('failure_change','Failure count change'),('total_NDC_change_pct','Total distance work change (%)')]):
  vals=[float(x[key]) for x in rr];ax=axes[di,j];ax.barh(range(7),vals,color=['#19786d' if (v>0 if j==0 else v<0) else '#bc555a' for v in vals]);ax.axvline(0,color='#555',lw=.7);ax.invert_yaxis();ax.set_yticks(range(7),labels if j==0 else ['']*7);ax.set_xlabel(title);ax.set_title(('WebVid' if di==0 else 'Yandex')+' · L128');ax.grid(axis='x',alpha=.18)
fig.suptitle('E70 · Fixed micro-graphs, physical search width ef10 → ef30\n7,952 historical auxiliary queries/dataset · single thread · quality and counted work, no QPS',fontsize=13)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('width_control.'+ext),dpi=160)
plt.close(fig)
lines=['# E70 固定小图搜索宽度控制','', '2026-09-13，第4串行会话。P/duplicate3P/mode3P各ef10/30，原图/W/真实H/NSG/raw-IP固定，无训练/构图。历史aux7952/L128，固定3976两半；全部反馈计训练/开发，不是最终validation。','', '| 数据 | 比较 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |','|---|---|---:|---:|---|---|---|']
for ds in DS:
 for cand,ref in [('mode3P30','baseline10'),('mode3P30','baseline30'),('mode3P30','mode3P10'),('baseline30','baseline10')]:
  rr=[x for x in rows if x['dataset']==ds and x['candidate']==cand and x['reference']==ref];r=next(x for x in rr if x['split']=='all');half=[int(next(x for x in rr if x['split']==s)['net_hits']) for s in ['first_half','second_half']]
  lines.append(f"| {'WebVid' if ds==DS[0] else 'Yandex'} | {cand}−{ref} | {int(r['net_hits']):+d} | {float(r['recall_delta_pp']):+.4f} | {r['rescued']}/{r['new_failures']} | {half} | {float(r['route_NDC_change_pct']):+.2f}/{float(r['total_NDC_change_pct']):+.2f} |")
lines += ['', '预锁的后继完整wall质量门：'+', '.join(('WebVid' if ds==DS[0] else 'Yandex')+('通过' if gate['datasets'][ds]['passed'] else '未通过') for ds in DS)+'。原E66失败状态保持，不将更多计算或更高完整画像排名一致率称性能改进。', '', '完整画像前三一致率（ef10→30）：']
for ds in DS:
 for m in MODELS:
  vals=[float(next(x for x in rank if x['dataset']==ds and x['model']==m+str(ef))['exact_three_agreement'])*100 for ef in [10,30]]
  lines.append(f"- {'WebVid' if ds==DS[0] else 'Yandex'} {m}: {vals[0]:.2f}% → {vals[1]:.2f}%。")
lines += ['', 'E69精确P与精确mode的不同结果仍是解释参照，本阶段没有重新计算完整评分；近似路径与NSG效用不是单调关系。ef30是physical node宽度，不是10个不同hub或等工作量。新增路由费用必须在后继独立完整wall收费。', '',f"实际194304 NSG/193920 HNSW/0build；24源图plain加载、24count加载，未复制小图。原生四job {cost['native_job_seconds']:.3f}s、编译{cost['compile_seconds']:.3f}s；操作与count均不是QPS。970?占位" ]
lines[-1]=lines[-1].replace('970?占位','完整96960返回独立集合/mask核验；47712主批及768预检ef10恢复、1536预检/主批一致、63616完整slot去重距离与384原kernel对照。')
lines += ['', 'CPU15，进程/OMP/OpenBLAS/MKL/NUMEXPR/BLIS线程1，native全部实际退出后分析；五字段/slot/原kernel/图SHA/加载字节/调用预算均检查。source_diff只包含允许10/30的参数和reference_graph直接加载；原评测/计时循环逐字E66，所有输出aligned。E34最终与held-out未使用，失败严格GT10零命中。', '', '[完整配对](results/paired.csv) · [原值/完整成本](results/points.csv) · [失败案例](results/failures.csv) · [排名一致率](results/ranking.csv) · [图](figures/width_control.png) · [门](results/gate.json) · [协议](protocol.md) · [验收](reviews/verification.json)。']
(O/'report.md').write_text('\n'.join(lines)+'\n');print('E70_REPORT_READY')
