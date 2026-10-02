from common import *
import csv
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
points=list(csv.DictReader((O/'results/points.csv').open()));paired=list(csv.DictReader((O/'results/paired.csv').open()));interp=list(csv.DictReader((O/'results/frontier_interpolation.csv').open()));cost=read(O/'results/cost.json');fails=read(O/'reviews/failure_query_verification.json')
labels={'nsg':'NSG','fast30k':'Fast30K/GT1','gt10_hard':'GT10-hard/P10','baseline_soft':'匹配GT10-soft/P10','mode10':'多画像mode10','best_new':'精简多画像compact10'}
lines=['# E74 精简多画像的完整QPS–Recall与失败汇报','', '55个方法点、275轮独立单线程完整wall已完成。候选固定compact10，同批保留完整mode10及NSG/Fast30K/GT10-hard/Web匹配soft；E73 Y辅助质量门通过/Web未过，E66/E70/E72旧门均保持。此批仍是历史开发2048，不是E34晚间最终validation；当前不据本批回选模型或参数，整日目标未完成。','', '按L64/128/256/400/800，相对各参照的实际变化：','', '| 数据 | compact对照 | ΔRecall pp | QPS中位变化% | 失败净新增 | QPS五轮交叉范围全负/跨零/全正 |','|---|---|---|---|---|---|']
for ds in DS:
 for ref in [('baseline_soft' if ds==DS[0] else 'gt10_hard'),'mode10']:
  rr=sorted([r for r in paired if r['dataset']==ds and r['comparator']==ref],key=lambda x:int(x['L']))
  dr='/'.join(f"{float(r['delta_recall_pp']):+.4f}" for r in rr);dq='/'.join(f"{float(r['QPS_change_pct']):+.2f}" for r in rr);df='/'.join(f"{int(r['new_failures'])-int(r['rescued']):+d}" for r in rr)
  neg=sum(float(r['all_range_high_pct'])<0 for r in rr);pos=sum(float(r['all_range_low_pct'])>0 for r in rr)
  lines.append(f"| {'WebVid' if ds==DS[0] else 'Yandex'} | {labels[ref]} | {dr} | {dq} | {df} | {neg}/{5-neg-pos}/{pos} |")
lines += ['', 'QPS范围是五次完整wall的交叉范围，不是置信区间。Recall区间按query bootstrap2000次作历史开发描述，五次重复不是五份独立Recall样本；同L质量变化和单轮速度都不能替代同机完整前沿判断。画像精简是否划算必须同时看主曲线及零命中，画像排名接近完整参照也可能保留NSG损伤。','']
for ds in DS:
 vals=[r for r in interp if r['dataset']==ds];changes='/'.join(f"{float(r['change_pct']):+.3f}%" for r in vals)
 lines.append(f"{'WebVid' if ds==DS[0] else 'Yandex'}共同Recall区间三个内部点的log-QPS描述性插值：{changes}。这是实测点间插值，不是测得同Recall提速，也不是独立泛化证据。")
lines += ['', '固定真实H815/821和原base/rawIP/NSG/GT，完整mode有2445/2463画像、精简版1771/2067。只删除同hub完全相同画像，完整每hub max评分集合保持，普通重建的小图已在E73冻结；两版均ef10/search7slot再去重3真实入口。精简改变近似遍历和图结构，节点减少比例不能当QPS增量。原Fast30K保留其历史训练量/seed/heap规则。','', '| 数据 | 方法 | L | Recall@10 % | QPS中位 [五轮范围] | 零命中率 %（条数） |','|---|---|---:|---:|---:|---:|']
for p in points:
 lines.append(f"| {'WebVid' if p['dataset']==DS[0] else 'Yandex'} | {labels[p['model']]} | {p['L']} | {float(p['recall_pct']):.4f} | {float(p['QPS']):.2f} [{float(p['QPS_min']):.2f}, {float(p['QPS_max']):.2f}] | {float(p['failure_rate_pct']):.4f} ({p['failure_count']}) |")
lines += ['', f"失败严格零GT10命中，hits1不算失败。共{fails['unique_queries']}条独立query、{fails['zero_transition_events']}个跨L转换事件；{fails['all_five_L_pairs_checked']}个五L格全部保留。图每集最多24例，按最大绝对命中变化/源行固定排序展示，全量CSV不截断。救回/新增、GT10成员找回/丢失、逐query净命中正负部各自分列，不将跨比较或跨L事件称独立query。",'']
for ds in DS:
 rec=list(csv.DictReader((O/'results/failure_query_summary.csv').open()));rr=[x for x in rec if x['dataset']==ds]
 for kind in ['new_failure_Ls','rescued_Ls']:
  eligible=[r for r in rr if r[kind]]
  if eligible:
   r=sorted(eligible,key=lambda x:(-len(x[kind].split()),int(x['source_row'])))[0]
   lines.append(f"{'WebVid' if ds==DS[0] else 'Yandex'}示例source row{r['source_row']}：五L原命中[{r['baseline_hits_by_L']}]→compact10[{r['new_hits_by_L']}]；入口[{r['baseline_entries']}]→[{r['new_entries']}]。这是事后案例，不生成在线选择特征。")
lines += ['', f"本阶段新增{cost['NSG_calls']:,} NSG、{cost['HNSW_calls']:,} HNSW，45 plain源图加载及45 count加载，0新构图/训练/GT/梯度，0小图物理副本。原生两job总{cost['native_job_seconds']:.3f}s含load/count/I/O，完整wall单独存timings。route-only/graph-only未另测，null+原因，不由count估算QPS。raw中policy_build_seconds在graph_file分支实际为源图加载/核验时长，cost另列source_policy_load_seconds及count_policy_load_seconds，不计新构图。", '', '计时包含完整raw-query路由/7slot排序去重/映射/canonical三入口/原NSG/输出；GT/count/hash/JSON/build/load在外。CPU15/实际进程与OMP/OpenBLAS/MKL/NUMEXPR/BLIS1，方法和数据集串行；先一次完整预热、五轮按dataset/repeat/L轮换。两个工具terminal exit0后才评分/绘图。112640集合/mask及全plain/count、880原kernel、45源图加载字节和五L入口/slot/275wall恒等核验。71680原基线恢复E65、20480 mode10恢复E67、12288 L128结果恢复E73，全部数值回归仅验身份，QPS本批独立重测。', '', 'source router_train[2048:4096]包含于已使用aux7952；P-fit含旧train/monitor，旧cal/audit和辅助反馈历史使用全部披露，任何选型反馈计训练。E34最终validation与held-out未进入本轮。晚间仍需独立冻结best_all与真实best_new后完整最终对照，不能把本批开发结果包装为最终完成。', '', '[协议](protocol.md) · [全部点](results/points.csv) · [275轮wall](results/timings.csv) · [配对](results/paired.csv) · [成员损益](results/member_deltas.csv) · [失败query全表](results/failure_query_summary.csv) · [成本](results/cost.json) · [验收](reviews/verification.json)', '', '[QPS–Recall](figures/recall_qps.png) · [QPS–失败率](figures/failure_qps.png) · [按L三指标](figures/three_metrics_by_L.png) · [配对差](figures/paired_deltas.png) · [失败案例](figures/failure_query_cases.png)；所有图另存SVG/PDF。']
lines += ['', '离线继承成本：E73精简0.030672秒、两小图构建0.348455秒、该阶段编译25.432077秒；E66画像训练30.286秒及更早GT成本另属历史来源，不记成零。E74没有新增训练、构图或GT；原始GT-inclusive总成本未在本轮重测，缺项保持null及来源说明。']
(O/'report.md').write_text('\n'.join(lines)+'\n');print('E74_REPORT_READY')
