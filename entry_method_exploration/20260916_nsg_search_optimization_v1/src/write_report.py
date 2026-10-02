"""Generate a result report from audited completed measurements only."""
import csv,json,pathlib,statistics,datetime
D=pathlib.Path(__file__).resolve().parent.parent;R=D.parent.parent
read=lambda p:json.loads(p.read_text())
assert read(D/'reviews/results_audit.json')['status']=='PASS'
with (D/'results/metrics.csv').open() as f: rows=list(csv.DictReader(f))
with (D/'results/paired_speedup.csv').open() as f: pairs=list(csv.DictReader(f))
with (D/'results/dataset_audit.csv').open() as f: datasets=list(csv.DictReader(f))
state=read(D/'state.json');assert state['status']=='MEASUREMENTS_COMPLETE'
pts=[(1,96),(100,100),(1,800),(100,1250)];methods=['NSG','GT10-hard','GT10-soft-t1','GATE']
f=lambda x:float(x)
gains=[f(x['speedup_percent']) for x in pairs]
head=f'WebVid四个预先固定预算、四种共享NSG内核的方法，平均QPS变化范围为{min(gains):+.2f}%至{max(gains):+.2f}%；16组比较中{sum(x>0 for x in gains)}组平均值提升。全部五集100个方法/版本/预算组合的返回ID、距离bits、入口及逐query距离计数与E97一致。'
parts=['# E99：NSG预取与候选池优化',head,
'代码已落到`ACSG/ACSG.cpp`及`ACSG/detail/CandidatePool.h`；可独立链接的优化库为`bin/libACSG.optimized.a`，本轮benchmark实际链接该库。原构建库、图、模型、数据和E97/E98结果保留。模型默认仍为WebVid soft / Yandex hard，hard仍是预先指定研究主线。',
'## 备份与实现',
'修改前已创建Git提交`2739b09a67f3ca0b6f145d43690d36345df3182c`，分支`backup/pre-nsg-optimization-20260916_103846`。6115个源码、脚本、配置及文档文件逐个从提交回读并核验字节；main与原暂存区未改变。大型数据、模型、索引及构建产物留在原位，不计入Git备份。[备份核验](reviews/git_backup.json)。',
'每query从当前DistanceComputer提取只读FlatCodes存储视图，可解包NegativeDistanceComputer；提前一个邻居预取visited和向量首缓存线。未知自定义DistanceComputer仅预取visited。无全局base指针、不改距离运算/API/对象布局。候选池仍使用完整L执行原二分定位和重复ID处理，仅复制有效候选前缀；非有限或FLT_MAX距离出现时退出压缩复制路径。',
'E98短池诊断将原函数的整个K缩短，存在等距插入顺序反例。E99已补上针对性差分测试并保留原定位规则，不能把E98的+13.15%直接当成本版收益。E98在原10K查询上的一致性实测仍保留。',
'## 固定测量范围',
'WebVid使用完整10K公开query、原2.505M/512维raw-IP底库和冻结图/模型。K1测L96/800，K100测L100/1250；每个点四种NSG方法都测旧、新版本，HNSW为同进程完整索引参考。旧/新共用同一base与邻接内存，独立visited/候选scratch，按方法及轮次交替顺序；warmup+3轮plain及独立count。CPU15，实际进程/OpenMP/BLAS/MKL均1线程，方法串行。QPS取三次N/wall的算术均值，计时包含完整路由与搜索，GT/文件核验/构建和加载在外。',
'Yandex、Deep、SIFT、GIST在全部原公开query、四种NSG方法、K1的L96/1250和K100的L100/1250做一次独立count回归，不作新QPS结论。Count包装器暴露同一存储视图，实际经过向量预取分支。无LAION、Recall@10、新训练、新GT或图构建。',
'K1原E97网格没有L100，启动任何真实搜索之前修订为已有L96，点数不增加。历史公开查询已有曝光，结果是工程回归及本机局部性能证据，不是新盲测，也没有按结果调参数。',
'## WebVid结果',
'所有Recall按严格ID重算。下表QPS均来自本轮同进程计时，绝对值不与E97或E98跨轮混算；百分比为优化后平均QPS / 原平均QPS − 1。\n\n| 指标 / L | 方法 | Recall | 原QPS | 新QPS | QPS变化 | 三次配对变化范围 |\n|---|---|---:|---:|---:|---:|---:|']
for k,L in pts:
 for m in methods:
  x=next(x for x in pairs if int(x['K'])==k and int(x['L'])==L and x['method']==m)
  parts.append(f'| R@{k} / {L} | {m} | {100*f(x["recall"]):.4f}% | {f(x["legacy_qps"]):.2f} | {f(x["optimized_qps"]):.2f} | {f(x["speedup_percent"]):+.2f}% | {f(x["paired_min_percent"]):+.2f}% ～ {f(x["paired_max_percent"]):+.2f}% |')
parts+=['\n三次范围只描述本次计时波动，不是置信区间；重复时间测量不增加独立query数。仅四个预算点，不宣称完整前沿改善或全部数据集加速。',
'### 完整HNSW参考\n\n| 指标 / L | HNSW Recall | HNSW QPS | GT10-soft 新QPS | 同点QPS差异 |\n|---|---:|---:|---:|---:|']
comparisons=[]
for k,L in pts:
 h=next(x for x in rows if x['dataset'].startswith('webvid') and int(x['K'])==k and int(x['L'])==L and x['method']=='HNSW')
 s=next(x for x in rows if x['dataset'].startswith('webvid') and int(x['K'])==k and int(x['L'])==L and x['method']=='GT10-soft-t1' and x['kernel']=='optimized')
 change=100*(f(s['qps_mean'])/f(h['qps_mean'])-1)
 parts.append(f'| R@{k} / {L} | {100*f(h["recall"]):.4f}% | {f(h["qps_mean"]):.2f} | {f(s["qps_mean"]):.2f} | {change:+.2f}% |')
 comparisons.append({'K':k,'L':L,'hnsw_recall':f(h['recall']),'hnsw_qps':f(h['qps_mean']),'soft_recall':f(s['recall']),'soft_qps':f(s['qps_mean']),'soft_vs_hnsw_percent':change})
parts+=['\n同L的Recall不同，不能只以同L的QPS差异宣布方法优势。高召回点可分别核对是否满足共同90% Recall门槛；其他预算及完整前沿未经本轮重测，不按L混选hard/soft。',
'![WebVid四个固定预算的Recall–QPS](figures/webvid_recall_qps.png)',
'![与旧内核的配对速度比较](figures/webvid_speedup.png)',
'## 一致性、边界和成本',
'35,856个候选池用例及8,656次合成图查询差分通过，覆盖IP/L2、等距/重复向量、无效/重复邻接、不连通图、不同入口和mode、K1/100、复用缓冲、visited轮回、trace及非有限边界。对新内核和测试程序的ASan/UBSan通过，外部参考库未全部插桩。初次回归的trace失败来自JSON把默认NaN判为不等，测试改用序列化表示核对后通过；生产代码未因该validator修复改变，旧日志保留。',
'真实数据的500个raw文件已独立SHA比对，全部Recall和逐query route/graph NDC与E97一致；Web每次warmup/plain/count也在native程序内逐位核对，原返回和计数均未因优化改变。\n\n| 数据集 | 比较组合 | 每组合query | 实际search调用 | 计时轮数 | 查询阶段秒数（不含加载） | 峰值RSS GiB |\n|---|---:|---:|---:|---:|---:|---:|']
for x in datasets:parts.append(f'| {x["dataset"]} | {x["points"]} | {x["queries_per_point"]} | {x["search_calls"]} | {x["timed_rounds"]} | {f(x["seconds_excluding_load"]):.1f} | {f(x["max_rss_gib"]):.2f} |')
parts+=[f'\n合计2,296,000次真实查询、108轮plain计时，主测量调度含加载{state["wall_seconds"]/60:.2f}分钟。正常与sanitizer合成查询各8,656次，首次validator失败尝试另保留；合成合计低于预锁20,000次。编译/单元回归、备份与后处理不计入上述查询wall。新数据写入受1GiB上限检查，最终大小见完成验收。',
'本轮收益只证明共享NSG实现可以减少每次查询的时间，不改变GT10训练、入口选择或搜索工作量，也不能证明剩余HNSW差距已完全消失。其余四集只确认结果不变；要回答它们的吞吐变化，需另做公平端到端计时，不能使用count运行时间充当QPS。',
'## 产物与接续',
'[完整点表](results/metrics.csv) · [逐轮计时](results/wall_rounds.csv) · [配对变化](results/paired_speedup.csv) · [逐集验收](results/dataset_audit.csv) · [数值核验](reviews/results_audit.json) · [冻结源码与二进制](reviews/frozen_code.json) · [构建与恢复说明](src/README.md) · [协议](protocol.md)。PNG另附同名PDF。',
'原 `build/ACSG/libACSG.a` 保留，可随时对照；生产源码已采用优化，正常重编译将使用它。本轮可直接链接 `bin/libACSG.optimized.a`。无需重训入口模型或重建原NSG/HNSW；历史QPS不会被改写成优化后的性能。']
# Keep table rows contiguous while separating ordinary prose blocks.
body=''
for p in parts:
 body+=p+('\n' if p.startswith('|') else '\n\n')
import re
body=re.sub(r'(?m)(^\|[^\n]*\|)\n\n(?=\|)',r'\1\n',body)
(D/'report.md').write_text(body)
summary={'headline':head,'gain_min':min(gains),'gain_max':max(gains),'positive_cells':sum(x>0 for x in gains),'web_hnsw_comparison':comparisons,'measurement_minutes':state['wall_seconds']/60}
(D/'reviews/report_values.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
