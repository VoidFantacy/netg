from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();rows=list(csv.DictReader((O/'results/paired.csv').open()));rank=list(csv.DictReader((O/'results/ranking.csv').open()));gate=read(O/'results/gate.json');cost=read(O/'results/cost.json')
labels=['ModeD − P10','ModeD − Mode10','ModeD − Mode30','ModeD − DupD','DupD − Dup10','DupD − P10','PD − P10','Mode10 − P10']
fig,axes=plt.subplots(2,3,figsize=(14,8),constrained_layout=True)
for di,ds in enumerate(DS):
 rr=[x for x in rows if x['dataset']==ds and x['split']=='all']
 for j,(key,title) in enumerate([('recall_delta_pp','Recall change (pp)'),('failure_change','Zero-hit count change'),('route_NDC_change_pct','Routing distance work change (%)')]):
  vals=[float(x[key]) for x in rr];ax=axes[di,j];ax.barh(range(len(vals)),vals,color=['#19786d' if (v>0 if j==0 else v<0) else '#bc555a' for v in vals]);ax.axvline(0,color='#555',lw=.7);ax.invert_yaxis();ax.set_yticks(range(len(vals)),labels if j==0 else ['']*len(vals));ax.set_xlabel(title);ax.set_title(('WebVid' if di==0 else 'Yandex')+' · L128');ax.grid(axis='x',alpha=.18)
fig.suptitle('E72 · Width counted by 10 distinct real hubs on frozen micro-graphs\n7,952 historical auxiliary queries/dataset · D = distinct callback · counted work, no QPS',fontsize=13)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('distinct_control.'+ext),dpi=160)
plt.close(fig)
lines=['# E72 按真实hub计宽的小图搜索控制','', '2026-09-13，第5串行会话。原P/duplicate/mode各普通ef10与distinct10，固定原图/W/H/NSG/raw-IP；没有新画像训练或实际图构建。历史aux7952/L128及固定3976两半，全部选择反馈计训练，非最终validation。','', '| 数据 | distinct mode 对照 | 净命中 | ΔRecall pp | 救回/新增失败 | 两半净命中 | 路由/总NDC变化% |','|---|---|---:|---:|---|---|---|']
for ds in DS:
 for ref in ['baseline10','mode3P10','mode3P30']:
  rr=[x for x in rows if x['dataset']==ds and x['candidate']=='mode3PD10' and x['reference']==ref];r=next(x for x in rr if x['split']=='all');half=[int(next(x for x in rr if x['split']==s)['net_hits']) for s in ['first_half','second_half']]
  lines.append(f"| {'WebVid' if ds==DS[0] else 'Yandex'} | {ref} | {int(r['net_hits']):+d} | {float(r['recall_delta_pp']):+.4f} | {r['rescued']}/{r['new_failures']} | {half} | {float(r['route_NDC_change_pct']):+.2f}/{float(r['total_NDC_change_pct']):+.2f} |")
lines += ['', '预锁完整wall接续门：'+', '.join(('WebVid' if ds==DS[0] else 'Yandex')+('通过' if gate['datasets'][ds]['passed'] else '未通过') for ds in DS)+'。这是历史辅助质量与路由费用门，不是性能GO；E66/E70原门、原默认保持。', '', '回调只按external label映射的实际引用数计hub，不使用移除回调中不可靠的距离或影子堆。返回internal ID显式转换；singleton保留原堆截k子集，mode按完整候选distance/slot去重前三真实入口。每query状态复位，完整候选长度及最多30槽全部保存，未把前7槽当完整结果。', '', '完整画像前三一致率及候选占位：']
for ds in DS:
 for m in ['baselineD10','duplicate3PD10','mode3PD10']:
  r=next(x for x in rank if x['dataset']==ds and x['model']==m)
  lines.append(f"- {'WebVid' if ds==DS[0] else 'Yandex'} {m}: agreement {float(r['exact_three_agreement'])*100:.2f}%，平均{float(r['mean_candidate_slots']):.2f}槽，范围{r['min_candidate_slots']}–{r['max_candidate_slots']}，10不同hub。")
v=read(O/'reviews/verification.json')
lines += ['', f"实际{cost['NSG']} NSG/{cost['HNSW']} HNSW/0实际图build；合成另4图/512 HNSW/0NSG。原生四job {cost['native_job_seconds']:.3f}s、编译{cost['compile_seconds']:.3f}s。24 plain与24 count源图加载、0图副本；route-only/graph-only未单测为null，不换算QPS。", '', f"独立{v['set_scored_rows']}集合/mask评分，主批{v['full_old_and_singleton_recovered_rows']}原控制及singleton返回/距离bits/入口/两NDC恢复，全部plain/count与384原kernel对照、完整候选距离/映射/去重及预检前缀通过。{v['E69_same_triple_return_rows']}同三入口结果恢复E69。合成覆盖tie、非同一内外ID、引用增减/忽略移除dist、复位和重复候选；真实运行要求10hub、至少3入口，不足则拒绝。", '', 'strict failure=GT10集合零命中。GT成员找回/丢失与逐query净命中正负部独立记账，所有失败转换保存source namespace/row/三入口。所有原始aligned返回ID/距离/入口、hits/mask和路由/图NDC保留。GT在原生搜索后读取，双集工具terminal0后才分析。CPU15与进程/OMP/BLAS/MKL1核验；E34最终及held-out未进入。', '', '[完整配对](results/paired.csv) · [原值与成本](results/cost.json) · [失败转换](results/failures.csv) · [排名/占位](results/ranking.csv) · [图](figures/distinct_control.png) · [门](results/gate.json) · [协议](protocol.md) · [验收](reviews/verification.json)。']
(O/'report.md').write_text('\n'.join(lines)+'\n');print('E72_REPORT_READY')
