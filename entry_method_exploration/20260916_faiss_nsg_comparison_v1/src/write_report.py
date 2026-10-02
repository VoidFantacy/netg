import pathlib,json,statistics
D=pathlib.Path(__file__).resolve().parent.parent
read=lambda p:json.loads(p.read_text())
s=read(D/'results/summary.json');rows=s['metrics'];pairs=s['paired_speedups'];cost=s['cost'];state=read(D/'state.json');layout=s['layout']
assert read(D/'reviews/results_audit.json')['status']=='PASS'
def row(v,k,L):return next(x for x in rows if (x['variant'],x['K'],x['L'])==(v,k,L))
def delta(v,k,L,baseline='GT10-current'):return next(x for x in pairs if (x['variant'],x['K'],x['L'],x['baseline'])==(v,k,L,baseline))
names=read(D/'config.json')['variants'];points=[(1,96),(100,100),(1,800),(100,1250)]
cur=row('GT10-current',100,1250);native=row('Faiss-native',100,1250);fixed=row('NSG-current',100,1250);h=row('HNSW',100,1250);combo=row('GT10-span-batch4',100,1250)
combod=[delta('GT10-span-batch4',*p) for p in points]
paragraph='组合在四点的平均QPS均提高，值得进入共享生产内核的正式落地验证。' if all(x['speedup_percent']>0 for x in combod) else '组合并非四点均提高，不能无条件建议替换；应按下表保留各项正负结果。'
def table(k):
 ps=[p for p in points if p[0]==k];lines=[f'| 版本 | L{ps[0][1]} Recall@{k} | QPS（最小–最大） | L{ps[1][1]} Recall@{k} | QPS（最小–最大） |','|---|---:|---:|---:|---:|']
 for v in names:
  a,b=[row(v,*p) for p in ps];lines.append(f'| {v} | {100*a["recall"]:.4f}% | {a["qps_mean"]:.2f}（{a["qps_min"]:.2f}–{a["qps_max"]:.2f}） | {100*b["recall"]:.4f}% | {b["qps_mean"]:.2f}（{b["qps_min"]:.2f}–{b["qps_max"]:.2f}） |')
 return '\n'.join(lines)
speed=['| GT10控制，相对current | K1/L96 | K100/L100 | K1/L800 | K100/L1250 |','|---|---:|---:|---:|---:|']
for v in names:
 if not v.startswith('GT10-') or v=='GT10-current':continue
 speed.append('| '+v+' | '+' | '.join(f'{delta(v,*p)["speedup_percent"]:+.2f}%' for p in points)+' |')
ndctable=['| K100/L1250 | Recall@100 | QPS | 路由NDC | 图NDC | ms/query |','|---|---:|---:|---:|---:|---:|']
for v in ['Faiss-native','NSG-current','GT10-current','GT10-core','GT10-span','GT10-batch4','GT10-span-batch4','HNSW']:
 x=row(v,100,1250);ndctable.append(f'| {v} | {x["recall"]*100:.4f}% | {x["qps_mean"]:.2f} | {x["route_ndc"]:.2f} | {x["graph_ndc"]:.2f} | {x["mean_ms"]:.4f} |')
ranking=[]
for v in ['GT10-span','GT10-prefetch-filter','GT10-batch4','GT10-span-batch4']:
 ds=[delta(v,*p,'GT10-core') for p in points];ranking.append(f'- `{v}` 相对匹配core控制：四点平均QPS变化 {min(x["speedup_percent"] for x in ds):+.2f}% 至 {max(x["speedup_percent"] for x in ds):+.2f}%；最保守的“本控制最慢轮/基线最快轮−1”下界跨点最低为 {min(x["conservative_repeat_separation_percent"] for x in ds):+.2f}%。')
text=f'''# E101：原生 Faiss NSG 同图比较与优化价值

本轮完成40个固定点、120轮单线程plain、2,000,000次真实搜索。原生Faiss、当前项目内核及六个GT10实现控制均保留完整结果。主矩阵的batch4计数包装默认使用四次scalar，完整批量NDC结论还须由[80000次直接转发核验](actual_batch4_count_protocol.md)收口；最终状态见报告末尾补充。生产内核仍为E99，本轮只交付独立比较代码和候选，不改变入口模型、图或默认。

GT10的span+batch4组合相对当前实现，在四点的平均QPS变化为 **{min(x['speedup_percent'] for x in combod):+.2f}% 至 {max(x['speedup_percent'] for x in combod):+.2f}%**。所有GT10控制的返回ID、距离bits、入口和逐query NDC与E99一致。{paragraph}这证明本轮图访问/计算组织存在可利用的实现空间，而不是模型重新训练的收益。

## 比较对象和库边界

本轮`Faiss-native`指项目内置的 **Faiss 1.9.0**。本地NSG搜索主体和IndexNSG公开搜索包装与官方v1.9.0源码对照，去除注释/空白后相同，核查见[版本审计](reviews/library_version_audit.json)。原生版本实际调用本地库`faiss::IndexNSG::search`，借用项目冻结NSG的同一邻接与storage地址，保持Faiss入口邻居加随机点填满初始L的算法。没有调用建图、修改邻接或改变IP度量。因此这是原生Faiss 1.9.0搜索在项目冻结图上的表现，不能冒称重新构建的整套原生索引，也不是最新版Faiss的速度结论。库公开接口见[Faiss官方文档](https://faiss.ai/cpp_api/struct/structfaiss_1_1IndexNSG.html)。

另查阅了上游当前main：`Graph::get_neighbors`在第一个负值处结束邻接读取，搜索只遍历返回的有效邻居；visited接口也已变化。上游仍保留填满初始L和逐邻居scalar距离调用。这是源码事实，尚未构建/计时新版库，不能据此声称升级必然更快或无效。[上游Graph实现](https://raw.githubusercontent.com/facebookresearch/faiss/main/faiss/impl/NSG.h)、[上游搜索实现](https://raw.githubusercontent.com/facebookresearch/faiss/main/faiss/impl/NSG.cpp)。本轮span支持内部空洞，而上游前缀读取依赖负值是尾部终止标记。

`NSG-current`与`GT10-current`实际链接原E99优化库，分别注入固定单入口与GT10-soft原三入口。`GT10-minimal`沿用Faiss的候选排序/插入与遍历机制，适配三入口和未满池；它是研究适配代码，不是原生库。`GT10-core`在同一小内核启用E99预取和有效前缀复制，作为其余控制的匹配基线，隔离简化历史模式/trace等代码带来的差异。

`span`仅将固定R扫描收缩到该行最后一个有效邻接位置，内部空洞仍跳过，保留有效边顺序；`prefetch-filter`只跳过已visited目标的向量预取；`batch4`按原顺序聚合至多四个新邻居、预取向量首cache line、调用Faiss批量距离，再依原顺序插入；`span-batch4`是事先指定的两项组合。batch4控制包含聚合及预取组织变化，不能把其全部收益都归因于SIMD算术本身。

## 实测 Recall 与 QPS

所有查询来自原WebVid完整10K public集合；单线程CPU15，同机串行。QPS是三轮N/wall均值，括号是实测最小–最大，不是置信区间。

{table(1)}

{table(100)}

![四点Recall–QPS](figures/recall_qps.png)

图中每个K仅两个实测L，虚线只连接观测值，不代表连续前沿。原生与项目初始化不同，不能只凭相同L时间判定算法优劣；GT10各实现控制则逐query结果相同，其速度差具有更直接的可比性。

## 哪些改造值得优化

{chr(10).join(speed)}

![实现控制收益](figures/optimization_controls.png)

为避免把去掉历史代码的效果误归给某项控制，还比较同一个研究内核的core基线：

{chr(10).join(ranking)}

三轮重复不能证明所有环境下稳定获益；较小差异或重复范围重叠，应保留不确定性。原始每轮QPS、配对差和保守范围在[paired_speedup.csv](results/paired_speedup.csv)，不是按最快一轮挑结论。

## 距离次数与总成本

{chr(10).join(ndctable)}

在高预算点，原生Faiss图距离次数为{native['graph_ndc']:.2f}/query，项目固定单入口为{fixed['graph_ndc']:.2f}，GT10为{cur['graph_ndc']:.2f}，另有{cur['route_ndc']:.2f}路由距离。Faiss初始化填满L与项目最多三个初始点不同，所以原生版本的额外工作不能全部解释成“库实现慢”。Faiss循环本身也扫描graph.K，库替换并不自动去除尾部padding。

GT10各候选保持总NDC {cur['total_ndc']:.2f}和Recall@100 {cur['recall']*100:.4f}%，组合却将高预算平均wall从{cur['mean_ms']:.4f} ms改为{combo['mean_ms']:.4f} ms。这是“计算次数相同，执行组织不同”的直接控制。E100观察到71.82%的槽检查是尾部空槽；E101测量实际跳过的价值，不能把空槽比例直接当作时间节省比例。

span辅助数组共{layout['span_bytes']:,}字节，一次生成耗时{layout['span_build_seconds']:.4f}秒，放在加载阶段而不隐藏进每query操作。原生和项目共用图/向量内存；HNSW继续使用原完整图、原生度量。没有为了加速增加查询线程或改变返回K。

## 正确性、成本及后继范围

6,480组配对合成用例覆盖IP/L2、4/32/512维、等距向量、重复/空入口、内部空洞、无效邻居、结果不足、K1/K100、visited轮回；普通和ASan/UBSan均通过，分别12,960次合成搜索。检查实际Faiss scalar/batch4的距离bits及调用顺序；sanitizer覆盖新研究代码，既有链接静态库未重新插桩。真实查询中36个项目/GT10/HNSW组合的180份raw文件与E99逐位一致；原生4点的warm/plain/count使用其真实public API结果核验，并检查合法ID、唯一性、顺序与有限分数。Recall另外从原GT严格按ID重算。

正式计时与count合计2,000,000次search、120轮plain，查询阶段含各点检查用时{cost['seconds_excluding_load']/60:.3f}分钟；主runner含加载和前后身份核验共{state['seconds_total']/60:.3f}分钟，编译、合成回归及报告另计。峰值RSS {cost['maxrss_kib']/1024**2:.3f} GiB。实际进程、OMP/BLAS/MKL均为1线程、CPU15、方法串行。主数据、模型、图、库和冻结源码前后身份一致；无训练、新图或新GT。

修改前备份为`dba6986eb9baa645e9ad1231f9d112bb06550c5d`，原main/index保持。原E97/E99/E100数据和报告不改；默认仍Web soft/Yandex hard。本轮只比较WebVid固定四点，不声称跨五集速度收益或完整前沿，也没有部署新的生产实现。

后继若落地有收益的控制，应将其作为小范围共享内核改动，保留现有API/trace、非有限与未知DistanceComputer回退、图生命周期约束；再公平验证NSG/hard/soft/GATE，重点测WebVid Recall@1/100，并对Yandex/Deep/SIFT/GIST回归。原生Faiss对照继续单独命名，不能覆盖旧“NSG”结果。此次无需重训GT10，也不因局部速度优势追加训练或参数网格。

## 复现入口

- [协议](protocol.md)、[配置](config.json)、[完成记录](complete.json)、[状态](state.json)
- [完整指标](results/metrics.csv)、[120轮时间](results/wall_rounds.csv)、[控制差异](results/paired_speedup.csv)、[汇总](results/summary.json)
- [原生与项目调用](src/compare.cpp)、[独立控制](src/kernels.hpp)、[合成回归](src/regression.cpp)、[评分](src/analyze.py)、[绘图](src/plot.py)
- [数据身份](reviews/assets.json)、[结束身份核验](reviews/post_run_identity.json)、[数值验收](reviews/results_audit.json)、[Git备份](reviews/git_backup.json)
'''
(D/'report.md').write_text(text)
print('Report written:',D/'report.md')
