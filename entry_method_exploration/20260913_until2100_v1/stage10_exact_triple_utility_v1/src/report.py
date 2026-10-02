from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();p=list(csv.DictReader((O/'results/paired.csv').open()));points=list(csv.DictReader((O/'results/points.csv').open()));gate=read(O/'results/gate.json');cost=read(O/'results/cost.json')
labels=['P exact − P ANN','Mode exact − P exact','Mode exact − P ANN','Mode exact − Mode ANN','Mode exact − Dup ANN']
fig,axes=plt.subplots(2,3,figsize=(14,7.5),constrained_layout=True)
for di,ds in enumerate(DS):
 rr=[x for x in p if x['dataset']==ds and x['split']=='all']
 for j,(key,title) in enumerate([('recall_delta_pp','Recall change (pp)'),('failure_change','Failure count change'),('graph_NDC_change_pct','NSG distance work change (%)')]):
  vals=[float(x[key]) for x in rr];ax=axes[di,j];ax.barh(np.arange(5),vals,color=['#19786d' if (v>0 if j==0 else v<0) else '#bc555a' for v in vals]);ax.axvline(0,color='#555',lw=.7);ax.invert_yaxis();ax.set_yticks(np.arange(5),labels if j==0 else ['']*5);ax.set_xlabel(title);ax.set_title(('WebVid' if di==0 else 'Yandex')+' · L128');ax.grid(axis='x',alpha=.18)
fig.suptitle('E69 · Actual NSG results from fixed exact profile triples\n7,952 historical auxiliary queries/dataset · no online routing timing / no QPS',fontsize=13)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('exact_triple_utility.'+ext),dpi=160)
plt.close(fig)
lines=['# E69 完整画像前三的真实NSG效用','', '2026-09-13，第4串行会话。Yandex通过预锁的有限辅助质量接续门，WebVid未通过；当前默认未替换。该结果来自真实原NSG返回与完全相同输入的缓存，未计完整在线画像扫描，不是QPS或效用oracle。','', '| 数据 | 对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 失败净增 | 两半净命中 |','|---|---|---:|---:|---|---:|---|']
for ds in DS:
 for ref in ['exact_P','baseline','mode3P']:
  rr=[x for x in p if x['dataset']==ds and x['candidate']=='exact_mode' and x['reference']==ref];r=next(x for x in rr if x['split']=='all');halves=[int(next(x for x in rr if x['split']==s)['net_hits']) for s in ['first_half','second_half']]
  lines.append(f"| {'WebVid' if ds==DS[0] else 'Yandex'} | {ref} | {int(r['net_hits']):+d} | {float(r['recall_delta_pp']):+.4f} | {r['rescued']}/{r['new_failures']} | {int(r['failure_change']):+d} | {halves} |")
lines += ['', 'WebVid精确mode比approx mode改善191命中、净减19失败，但精确P本身更强；不能把修正近似的通用收益归因于多模态。Yandex精确P反而比approx P少35命中，精确mode比二者都好，说明该固定表示在此历史aux有局部NSG效用；不存在“精确排序一律更好”的结论。两集损伤与救回同时存在，不按新失败案例训练门控。','', '继任只测试一个固定ef10→30干预，P/duplicate/mode均有参照；不扫更大ef/种子。WebVid作为原样迁移反证保留，不期待从此结果推出双集提升。是否可部署、是否有完整Recall–QPS收益须独立测量，原E66开发门保持失败。','', '输入：原router_train[2048:10000]，7952及固定3976两半，全部历史辅助/选择训练反馈。P-fit含旧train/monitor；cal/audit已有暴露。E34最终validation及held-out本阶段未使用。','', '38,942次新NSG=31,808 baseline plain/count回放+7,070缺口plain/count+64原kernel reference。31,808逻辑exact结果中28,102复用旧三方法、3,535唯一新key、171互alias。旧缓存碰撞15,986项逐字段bits核对；全量原baseline15,904恢复。0HNSW/构图/新GT/梯度；计数和原生操作wall不能当QPS。','', f"原生进程{cost['native_elapsed_seconds']:.3f}s，其中加载{cost['load_seconds']:.3f}s；独立编译{cost['compile_seconds']:.3f}s，主评分{cost['analysis_seconds']:.3f}s，绘图/查表/I/O另计。CPU15，进程与数值库1线程；两个native实际terminal exit0后评分。42非法整批输入在零调用时拒绝，空输入类型/shape通过；79,520返回独立集合评分，30组GT成员增损/逐query净增损恒等。plain/count及64原wrapper ID/float bits/NDC通过。",'', '[完整配对](results/paired.csv) · [原值](results/points.csv) · [全部失败转换](results/failure_cases.csv) · [图](figures/exact_triple_utility.png) · [成本](results/cost.json) · [协议](protocol.md) · [缓存身份](reviews/cache_coverage.json) · [验收](reviews/verification.json)。']
(O/'report.md').write_text('\n'.join(lines)+'\n')
print('REPORT_READY',flush=True)
