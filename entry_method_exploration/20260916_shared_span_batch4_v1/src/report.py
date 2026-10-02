import pathlib,json
D=pathlib.Path(__file__).resolve().parent.parent
read=lambda p:json.loads(p.read_text())
s=read(D/'results/summary.json');rows=s['metrics'];a=read(D/'reviews/results_audit.json');assert a['status']=='PASS'
c=read(D/'configs/webvid2_5m_light_v1.json');state=read(D/'state.json');methods=['NSG','GT10-hard','GT10-soft-t1','GATE'];points=[(1,96),(100,100),(1,800),(100,1250)]
def row(m,kind,k,L):return next(r for r in rows if (r['method'],r['kernel'],r['K'],r['L'])==(m,kind,k,L))
def gain(m,k,L):return next(r for r in s['speedups'] if (r['method'],r['K'],r['L'])==(m,k,L))
ns=[gain('NSG',*p)['speedup_percent'] for p in points]
def fulltable(k):
 ps=[p for p in points if p[0]==k];lines=[f'| 方法 | 内核 | L{ps[0][1]} Recall@{k} | 平均QPS（最小–最大） | L{ps[1][1]} Recall@{k} | 平均QPS（最小–最大） |','|---|---|---:|---:|---:|---:|']
 for m in [*methods,'HNSW']:
  for kind in (['reference'] if m=='HNSW' else ['current','span-batch4']):
   x,y=[row(m,kind,*p) for p in ps];lines.append(f'| {m} | {kind} | {x["recall"]*100:.4f}% | {x["qps_mean"]:.2f}（{x["qps_min"]:.2f}–{x["qps_max"]:.2f}） | {y["recall"]*100:.4f}% | {y["qps_mean"]:.2f}（{y["qps_min"]:.2f}–{y["qps_max"]:.2f}） |')
 return '\n'.join(lines)
speed=['| 方法，新内核相对自身current | K1/L96 | K100/L100 | K1/L800 | K100/L1250 |','|---|---:|---:|---:|---:|']
for m in methods:speed.append('| '+m+' | '+' | '.join(f'{gain(m,*p)["speedup_percent"]:+.2f}%' for p in points)+' |')
fair=['| 都使用span+batch4 | Recall@1变化（pp） | QPS变化 | Recall@100变化（pp） | QPS变化 |','|---|---:|---:|---:|---:|']
for m in methods[1:]:
 x,y=[next(r for r in s['shared_kernel_comparisons'] if (r['method'],r['K'],r['L'])==(m,k,L)) for k,L in [(1,800),(100,1250)]]
 fair.append(f'| {m} 相对NSG | {x["recall_delta_pp"]:+.4f} | {x["qps_delta_percent"]:+.2f}% | {y["recall_delta_pp"]:+.4f} | {y["qps_delta_percent"]:+.2f}% |')
new,old=row('NSG','span-batch4',100,1250),row('NSG','current',100,1250)
entry_table=['| 固定预算，同一新内核 | NSG Recall / QPS | GT10-hard Recall / QPS | GT10-soft Recall / QPS | soft相对NSG的Recall / QPS变化 |','|---|---:|---:|---:|---:|']
for k,L in points:
 n,h,t=[row(m,'span-batch4',k,L) for m in ['NSG','GT10-hard','GT10-soft-t1']]
 entry_table.append(f'| K{k}/L{L} | {n["recall"]*100:.4f}% / {n["qps_mean"]:.2f} | {h["recall"]*100:.4f}% / {h["qps_mean"]:.2f} | {t["recall"]*100:.4f}% / {t["qps_mean"]:.2f} | {100*(t["recall"]-n["recall"]):+.4f}pp / {100*(t["qps_mean"]/n["qps_mean"]-1):+.2f}% |')
ndc=['| K100/L1250 | Recall@100 | QPS | 路由NDC | 图NDC | 总NDC | ms/query |','|---|---:|---:|---:|---:|---:|---:|']
for m in [*methods,'HNSW']:
 r=row(m,'reference' if m=='HNSW' else 'span-batch4',100,1250);ndc.append(f'| {m} | {r["recall"]*100:.4f}% | {r["qps_mean"]:.2f} | {r["route_ndc"]:.2f} | {r["graph_ndc"]:.2f} | {r["total_ndc"]:.2f} | {r["mean_ms"]:.4f} |')
compat=['| 数据集 | 配置 | 搜索次数 | 不一致配置 |','|---|---:|---:|---:|']
for r in s['compatibility']:compat.append(f'| {r["dataset"]} | {r["configurations"]} | {r["search_calls"]} | {r["mismatched_configurations"]} |')
boundary='其它四集返回ID、距离bits、入口及逐query route/graph NDC全部一致。' if a['compatibility_status']=='PASS' else '其它四集存在不一致，不能把该内核当作通用无损替换；全部差异见results/summary.json。'
text=f'''# E102：NSG、GT10、GATE使用相同优化后的公平比较

本轮已完成WebVid四预算、四入口方法各新旧内核及同轮完整HNSW，共36配置、108轮单线程plain；再完成其它四集64配置一致性，合计 **2296000次真实搜索**。所有WebVid warm/plain/count返回ID、距离bits、入口及逐query距离次数与E99一致，真实batch4计数已直接转发底层接口。

**NSG自身在四点的平均QPS变化为{min(ns):+.2f}%至{max(ns):+.2f}%。** K100/L1250从{old['qps_mean']:.2f}提高至{new['qps_mean']:.2f} QPS，Recall@100保持{new['recall']*100:.4f}%。因此批量距离和尾部空槽优化的收益属于共享搜索实现，不能全部归功于GT10入口方法。GT10/GATE的剩余优势应看同样优化后的对照，见下表。

## 比较合同

NSG是项目固定单入口，GT10-hard/soft为原画像三入口，GATE使用原已修复正负冲突模型及原三入口映射。四者的span+batch4直接调用同一份E101 ResearchKernel、同一冻结图与向量storage；current实际链接E99优化库。原图、模型、router小图、query与GT不变，无训练、新构图或新GT。HNSW继续使用原完整图与原生度量。本轮NSG不是Faiss原生填满初始L的版本；原生Faiss 1.9.0比较保留在E101，不混入本轮表。

WebVid完整10K原public query，K1/L96、K100/L100、K1/L800、K100/L1250。CPU15，进程及OMP/BLAS/MKL均线程1，所有方法串行，每点warm1+plain3+count1。QPS为三次N/wall的平均，范围为最小–最大，不是置信区间。完整计时包含原路由、图搜索及输出写入；GT/校验/加载/写盘外置。三轮波动和全部正负结果均保留，没有挑最快轮或按公开结果选hard/soft。

## 统一优化后的方法结果

{fulltable(1)}

{fulltable(100)}

![相同内核的Recall–QPS](figures/shared_kernel_recall_qps.png)

图上仅新内核的NSG/GT10/GATE和同轮HNSW；每个K只有两个实测预算，连线仅辅助阅读，不构成完整实测前沿。以下方法间变化以同样优化的NSG为参照，分别是K1/L800及K100/L1250：

{chr(10).join(fair)}

这是同预算的局部比较。不同方法的Recall不一定相同，不能把QPS比例称作等Recall加速；若召回与QPS同时更高，也只支持这些已测点的优势，不能外推整条曲线或跨五集。

## GT10的入口选择是否仍有效

将公共内核保持一致后，GT10的独立贡献应直接与新NSG比较，而不是用GT10新内核对比NSG旧内核：

{chr(10).join(entry_table)}

低预算的两个点支持GT10同时改善Recall和QPS；高预算下仍有Recall收益，但速度差距变小。高预算的小幅QPS差应结合上表三轮范围，不能据平均值给hard/soft或其它接近的方法排稳定名次，也不能据此宣布GT10全面第一或已经无效。

与结果相符的一种机制解释是：更好的入口在有限搜索预算下更有价值；当预算增加，固定入口NSG通过更多探索可以缩小差距。这只是当前证据下的解释，没有单独的因果消融验证。后续若要判断方法在目标召回区间的最终价值，需要共同内核下的等Recall实测前沿，本轮没有追加该实验。

## 公共内核分别带来多少提速

{chr(10).join(speed)}

![各方法新旧加速](figures/shared_speedup.png)

相同方法的新旧返回逐位相同，所以这张表直接衡量实现变化的速度收益。它与上一节相同内核下的方法差异是两种不同结论。完整三轮配对范围和“新最慢轮/旧最快轮−1”的保守描述见[speedup.csv](results/speedup.csv)；小差异若落在轮次波动内，不作稳定胜出判断。batch4含邻居聚合和预取组织变化，未单独归因硬件缓存等待与SIMD算术。

## 距离次数与成本

{chr(10).join(ndc)}

距离次数没有计入邻接槽检查、visited、候选池维护等全部开销；在每种方法NDC与结果不变时，执行组织仍能改变端到端wall。span数组占{s['layout']['span_bytes']:,}字节，一次准备{s['layout']['span_build_seconds']:.4f}秒，计入加载阶段。

主WebVid程序含加载{s['cost'][0]['seconds_including_load']/60:.3f}分钟，其中查询及各轮检查{s['cost'][0]['seconds_excluding_load']/60:.3f}分钟；其余四集各程序含加载合计{sum(x['seconds_including_load'] for x in s['cost'][1:])/60:.3f}分钟。整体runner含前后身份核验{state['seconds_total']/60:.3f}分钟，编译与报告另计。主程序峰值RSS {s['cost'][0]['maxrss_kib']/1024**2:.3f}GiB。本轮新合成搜索0，继承E101已通过的6480配对组合普通及ASan/UBSan验证，未将继承成本冒充新执行；新包装由完整真实查询对照验收。

## 其他四集一致性

{chr(10).join(compat)}

{boundary}该阶段只做真实batch4 count，0正式QPS，不能由此宣称Yandex/Deep/SIFT/GIST也提速。原完整query规模10K/10K/10K/1K，四方法各四预算，共496000次；没有LAION或Recall@10。

## 状态与复现

所有优化已应用到本轮独立统一评测入口，原生产API/trace和默认库未覆盖。默认仍Web soft/Yandex hard；本轮没有按public结果更换模型或追加网格。修改前Git备份`8afd61cd5dae388f15e26890ce75109ffffd0f2f`，main/index及历史产物保留。若后续合入主内核，仍需保留完整API、trace、特殊值/未知DC回退和图生命周期约束。

- [协议](protocol.md)、[配置](configs/webvid2_5m_light_v1.json)、[运行状态](state.json)、[最终验收](reviews/final_review.json)
- [36配置指标](results/metrics.csv)、[108轮计时](results/wall_rounds.csv)、[实现加速](results/speedup.csv)、[同内核方法差异](results/shared_kernel_comparison.csv)、[跨集回归](results/compatibility.csv)
- [统一入口](src/compare.cpp)、[共享优化内核](src/kernels.hpp)、[评分](src/analyze.py)、[数值验收](reviews/results_audit.json)、[输入身份](reviews/assets.json)、[结束身份核验](reviews/post_run_identity.json)、[Git备份](reviews/git_backup.json)
'''
(D/'report.md').write_text(text);print('Report ready for manual review')
