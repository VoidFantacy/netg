from common import *

assert read(O/'reviews/output_verification.json')['status']=='PASS'
a=read(O/'results/analysis.json');jobs=read(O/'logs/jobs.json')
title={DS[0]:'WebVid',DS[1]:'Yandex-IP'}
def pm(v,d=3):return f'{v:+.{d}f}'
def base(ds):return 'gt10_soft' if ds==DS[0] else 'gt10_hard'
def pt(ds,m,L):return next(p for p in a['points'] if p['dataset']==ds and p['method']==m and p['L']==L)
def pair(ds,m,L):return next(p for p in a['paired'] if p['dataset']==ds and p['baseline']==m and p['L']==L)
def direct_table():
 rows=['| 数据集 | L | RL−起点 ΔRecall pp | ΔQPS % | 起点→RL失败数 | Δ失败率 pp |','|---|---:|---:|---:|---:|---:|']
 for ds in DS:
  for L in LS:
   p=pair(ds,base(ds),L);rows.append(f"| {title[ds]} | {L} | {pm(p['recall_delta_pp'])} | {pm(p['qps_change_pct'],2)} | {p['baseline_failed']}→{p['rl_failed']} | {pm(p['failure_delta_pp'])} |")
 return '\n'.join(rows)
intro=[]
for ds in DS:
 ps=[pair(ds,base(ds),L) for L in LS];fs=[p for p in a['same_recall_interpolation'] if p['dataset']==ds and p['baseline']==base(ds)]
 intro.append(f"{title[ds]}相对其直接起点，五L的Recall变化为{min(p['recall_delta_pp'] for p in ps):+.3f}～{max(p['recall_delta_pp'] for p in ps):+.3f}pp，QPS变化{min(p['qps_change_pct'] for p in ps):+.2f}%～{max(p['qps_change_pct'] for p in ps):+.2f}%；{sum(p['recall_delta_pp']>0 for p in ps)}/5点Recall上升，{sum(p['qps_change_pct']>0 for p in ps)}/5点QPS上升。同Recall三个描述性插值位置的QPS变化为{min(p['qps_change_pct'] for p in fs):+.2f}%～{max(p['qps_change_pct'] for p in fs):+.2f}%。")
lines=['# E34：HNSW-RL、NSG、Fast 与 FastGT10 性能比较','',
'2026-09-11。用户另行授权E33冻结图的QPS、Recall与查询失败率测试。本轮45个方法点、225次独立整批wall全部完成；E33原开发门失败及当时没有QPS的记录保持。这里只测已选图，没有新训练或重新选seed/checkpoint。','',
'## 1. 结果与图','',*intro,'',
'![Recall–QPS](figures/recall_qps.png)','',
'[Recall–QPS SVG](figures/recall_qps.svg) · [三指标随L变化 SVG](figures/metrics_by_search_L.svg) · [RL相对各基线变化 SVG](figures/rl_changes.svg) · [Excel数据](chart_data.xlsx)。全部PNG/PDF同名保存；原值CSV见[points](results/points.csv)、[五轮计时](results/qps_runs.csv)、[配对变化](results/paired_changes.csv)。','',
'## 2. 方法与公平比较边界','',
'NSG使用原图固定入口。Fast沿用原30K闭式GT1画像、构图seed100和legacy堆顺序。FastGT10-hard采用E24后20K的GT10硬画像、构图seed20260828。WebVid另列GT10-soft-t1，因为E33实际从这张图训练；Yandex的起点就是GT10-hard。Fast与GT10的训练量/构图seed不同，其差异不能全部归因GT数量。','',
'HNSW-RL为E33真实HNSW→NSG奖励训练后的静态底层删边图：WebVid seed20260912/step400；Yandex seed20260911/step300。本轮直接加载冻结物理图，原画像、真实ID、上层及NSG保持，线上没有策略网络、采样或训练hook。与直接起点的差异才隔离了本次边学习/导出造成的变化；本轮未加入新的随机对照，学习与随机删边的归因仍以[E33控制实验](../20260911_hnsw_edge_rl_v1/report.md)为准。','',
'两集历史validation2000，同一query/GT/row IDs、raw-IP、K10、L64/128/256/400/800、CPU15、实际进程/OMP/OpenBLAS/MKL1。每方法点一次完整warmup和五轮轮换plain整批wall；QPS取五轮中位数并显示min/max。完整计时包含路由/映射/原NSG/输出，GT、计数、I/O、hash和加载在timer外。所有搜索进程串行，没有并发训练/数值分析。','',
'查询失败严格定义为Recall@10<0.1，即10个返回结果对exact GT10零命中；它不是程序错误或超时率。Recall/失败率由相同query的保存结果计算，重复计时不会增加样本量。完整协议见[protocol](protocol.md)。','',
'## 3. 相对RL直接起点的全部五L结果','',direct_table(),'',
'下表固定列出训练使用的L128，避免事后挑最好点；完整45点见CSV与Excel。','',
'| 数据集 | 方法 | Recall@10 % | QPS 中位数 [最小,最大] | 失败数/2000 | 失败率 % |','|---|---|---:|---:|---:|---:|']
for ds in DS:
 for p in [x for x in a['points'] if x['dataset']==ds and x['L']==128]:
  lines.append(f"| {title[ds]} | {p['label']} | {p['recall_pct']:.3f} | {p['qps']:.1f} [{p['qps_min']:.1f},{p['qps_max']:.1f}] | {p['failed_queries']} | {p['failure_pct']:.2f} |")
lines+=['','![三指标随搜索宽度变化](figures/metrics_by_search_L.png)','','## 4. 相对每个基线的配对变化','',
'ΔRecall和Δ失败率单位为绝对百分点；ΔQPS为两个五轮中位数的相对变化。挽救表示基线零命中、RL非零；新增失败表示基线非零、RL零命中。两者均按原query ID配对，完整95%描述性区间及所有轮速度比另存CSV。','',
'| 数据集 | 对照 | L | ΔRecall pp | ΔQPS % | Δ失败率 pp | 挽救/新增失败 |','|---|---|---:|---:|---:|---:|---:|']
for p in a['paired']:lines.append(f"| {title[p['dataset']]} | {LABELS[p['baseline']]} | {p['L']} | {pm(p['recall_delta_pp'])} | {pm(p['qps_change_pct'],2)} | {pm(p['failure_delta_pp'])} | {p['rescued']}/{p['newly_failed']} |")
lines+=['','![相对各基线变化](figures/rl_changes.png)','','## 5. 同Recall对照与不确定性','',
'同L质量或QPS单独上升不等于整条曲线更好。以下仅在两方法各自实测非支配点的共同Recall区间取25/50/75%位置，以log-QPS作线性插值；不外推。这是测量点之间的描述性估计，不是新增实测搜索宽度，也不是按validation选模型。五轮速度比范围仅反映该批计时变化，不包括查询/构图seed/模型选择不确定性。','',
'| 数据集 | 对照 | 共同区间位置 | 目标Recall % | RL相对QPS % | 五轮估计范围 % |','|---|---|---:|---:|---:|---:|']
for p in a['same_recall_interpolation']:lines.append(f"| {title[p['dataset']]} | {LABELS[p['baseline']]} | {p['overlap_fraction']:.0%} | {p['target_recall_pct']:.3f} | {pm(p['qps_change_pct'],2)} | [{pm(p['paired_run_min_pct'],2)},{pm(p['paired_run_max_pct'],2)}] |")
lines+=['',
'Recall/失败差的paired bootstrap为2000次、seed20260915、未做多重比较修正；历史validation重复使用且每集仅2000query（一个失败query=0.05pp）。只有一份预选RL图及一个原构图身份，没有跨seed性能复现或新held-out。因此本次提供实测曲线和局部信号，不自动更换默认图，不由删边数/NDC、单个正点或小幅五轮中位数差升级为稳定方法结论。','',
'## 6. 成本、验收与资产保护','',
f"实际原NSG调用630720=45×(7×2000+16)，修复0；225次计时、90000个aligned输出。两个查询进程总{sum(j['seconds'] for j in jobs):.2f}s（含索引加载、计数、核验和写盘，不能当QPS），峰值RSS {max(j['rss_peak_kib'] for j in jobs)/(1<<20):.3f}GiB，实际进程最大线程1。新优化步数0、GT生成0，冻结模型训练成本见E33；从零GT/QGT/NSG成本本轮未测。",'',
'全部90000输出独立GT复算；原NSG/Fast/GT10共70000输出的ID、距离bits、入口、hits/mask和两项NDC回归E30完全一致。所有五轮plain/count及16query原kernel核验通过；同方法跨五L图字节和逐query入口一致，失败配对恒等式通过。证据：[输出验收](reviews/output_verification.json)、[调用账](logs/jobs.json)、[binary来源](bin/provenance.json)。','',
'本轮在独立目录执行，原E33完整目录及实际依赖前后核验SHA；原训练、图、GT、labels、build和历史结果保留。只读取授权的历史validation样本，held-out未读取/hash。协议、配置、源码、输入、结果和图表保存来源；最终验收见[final_audit](reviews/final_audit.json)，接续状态见[state](state.json)。','']
assert not (O/'report.md').exists();(O/'report.md').write_text('\n'.join(lines))
(O/'README.md').write_text('# E34 HNSW-RL性能补测\n\n[完整报告](report.md) · [协议](protocol.md) · [Recall–QPS](figures/recall_qps.svg) · [三指标曲线](figures/metrics_by_search_L.svg) · [相对变化](figures/rl_changes.svg) · [Excel](chart_data.xlsx) · [状态](state.json)\n\n两数据集45点、每点2000历史validation query/五轮单线程wall，冻结E33图，不新增训练。失败=Recall@10<0.1（零命中）。原始aligned结果保存在results/数据集/方法_L目录，派生表和所有计时原值保存在results/*.csv。\n')
dump(O/'results/report_key_results.json',dict(direct_baseline_comparisons=[pair(ds,base(ds),L) for ds in DS for L in LS],L128_points=[pt(ds,m,128) for ds in DS for m in LABELS if any(p['dataset']==ds and p['method']==m for p in a['points'])],summary_sentences=intro))
print('REPORT_WRITTEN',flush=True)
