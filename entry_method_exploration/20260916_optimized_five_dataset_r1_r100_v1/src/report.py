from common import *
import csv,collections,datetime
read=lambda p:json.loads(p.read_text())
assert read(RUN/'reviews/raw_results_verified.json')['status']=='PASS'
assert read(RUN/'reviews/post_run_identity.json')['status']=='PASS'
rows=list(csv.DictReader((RUN/'results/metrics.csv').open()));ts=list(csv.DictReader((RUN/'results/recall_targets.csv').open()));assert len(rows)==800
lock=read(RUN/'config.locked.json');ds_order=lock['datasets'];methods=lock['methods'];names={'webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex','deep10m_l2_v1':'Deep','sift10m_bigann_l2_v1':'BIGANN-SIFT','gist1m_l2_v1':'GIST'}
def metric(ds,K,m,L):return next(r for r in rows if (r['dataset'],int(r['K']),r['method'],int(r['L']))==(ds,K,m,L))
comparisons=[]
for ds in ds_order:
 for K in [1,100]:
  for target in [.9,.95,.99]:
   candidates=[]
   for m in methods:
    t=next(x for x in ts if (x['dataset'],int(x['K']),x['method'],float(x['target_recall']))==(ds,K,m,target))
    if t['achieved']=='True':candidates.append(metric(ds,K,m,int(t['L'])))
   best=max(candidates,key=lambda r:float(r['qps_mean'])) if candidates else None
   group=[r['method'] for r in candidates if float(r['qps_max'])>=float(best['qps_min'])] if best else []
   comparisons.append(dict(dataset=ds,K=K,target=target,mean_fastest=best['method'] if best else None,mean_fastest_qps=float(best['qps_mean']) if best else None,gt10_mean_fastest=bool(best and best['method'].startswith('GT10-')),repeat_range_overlap_group=group,gt10_in_overlap_group=any(m.startswith('GT10-') for m in group),candidates=[dict(method=r['method'],L=int(r['L']),recall=float(r['recall']),qps_mean=float(r['qps_mean']),qps_min=float(r['qps_min']),qps_max=float(r['qps_max'])) for r in candidates]))
dump(RUN/'results/threshold_comparisons.json',comparisons)
reached=[x for x in comparisons if x['mean_fastest']];first=sum(x['gt10_mean_fastest'] for x in reached);group=sum(x['gt10_in_overlap_group'] for x in reached)
cost=read(RUN/'results/completed_datasets.json');hours=sum(x['seconds_including_load'] for x in cost)/3600
text=['# E103：统一优化后的五集完整Recall@1/100比较','',f'五集800配置、2400轮正式单线程计时、32800000次真实搜索全部完成。所有新返回ID/距离bits/入口及逐query路由/图NDC均与E97一致，Recall重新从原GT评分。原模型、图、查询及默认保持；没有新训练、构图或GT。','',f'在90%/95%/99%三个预先列出的门槛、五集×两种K共30个组合中，{len(reached)}个至少有一种方法达到；GT10家族在其中{first}个组合的平均QPS最快，在{group}个组合进入与均值最快者三轮实测范围重叠的一组。范围重叠不是显著性检验，也不代表方法等价；这些计数不是整条曲线或未测召回区间的胜率。hard、soft均完整保留，没有据公开结果改选默认。','','![Recall@1](figures/recall_qps_k1.png)','','![Recall@100](figures/recall_qps_k100.png)','','图中每种方法包含全部16个实测点；阴影为三轮QPS的最小–最大，不是置信区间。HNSW也重新计时，主图没有混入历史QPS。NSG/hard/soft/GATE共用逐字相同span+batch4，计时包含原路由、归一化、图搜索与返回写入，加载、评分及磁盘I/O在外。CPU15、进程及OMP/BLAS/MKL单线程，方法串行。','']
for target in [.9,.95,.99]:
 text += [f'## 达到{target*100:g}% Recall门槛的最快实测点','','表格为QPS；选择达到该门槛的最快实测预算，不插值、不外推。各点实际Recall与预算可能不同，不能称严格等Recall加速。详细Actual Recall/L/三轮范围保留在下节与CSV。','','| 数据集 | K | NSG | GT10-hard | GT10-soft | GATE | HNSW |','|---|---:|---:|---:|---:|---:|---:|']
 for ds in ds_order:
  for K in [1,100]:
   rec=next(x for x in comparisons if (x['dataset'],x['K'],x['target'])==(ds,K,target));by={x['method']:x for x in rec['candidates']};vals=[f'{by[m]["qps_mean"]:.1f}' if m in by else '未达到' for m in methods]
   text.append('| '+names[ds]+' | '+str(K)+' | '+' | '.join(vals)+' |')
 text.append('')
text += ['## 各集判断与波动','']
for ds in ds_order:
 text += [f'### {names[ds]}','']
 for rec in [x for x in comparisons if x['dataset']==ds]:
  title=f'K={rec["K"]}，目标Recall≥{100*rec["target"]:g}%'
  if rec['mean_fastest'] is None:text.append(f'- {title}：全部方法在本轮预算内未达到。');continue
  best=next(x for x in rec['candidates'] if x['method']==rec['mean_fastest']);overlap='、'.join(rec['repeat_range_overlap_group'])
  text.append(f'- {title}：均值最快为{best["method"]}，L={best["L"]}，实际Recall={100*best["recall"]:.4f}%，QPS={best["qps_mean"]:.2f}（三轮{best["qps_min"]:.2f}–{best["qps_max"]:.2f}）；与其范围重叠的方法组：{overlap}。')
 text.append('')
text += ['## 成本与边界','',f'五集原生程序累计{hours:.3f}小时（含加载、warmup、计数、核对和写出，不能倒算QPS）；峰值RSS最大{max(x["maxrss_kib"] for x in cost)/1024**2:.3f}GiB。各集span准备、加载及执行耗时见results各集layout.json/complete.json。构建与评分/画图的阶段耗时见reviews/stage_*.json和reviews/build.json，复用图/模型旧成本未冒充本轮新成本。','', '这是原有公开查询上的重复测量，没有新增held-out证据。GIST原下载校验清单缺失的来源限制仍保留；SIFT使用E97标准BIGANN首10M及独立查询。IP/L2按原生度量，K只取1/100。单个同L点不支持整条曲线支配结论，门槛比较也保留离散预算差异。','', '优化应用于本轮独立统一评测入口，生产API/trace和默认库未覆盖；默认Web soft/Yandex hard保持。所有历史产物和Git main/index保留，运行前备份cd3a3229ea0a63f186c407f0ff82b463e66e12ad。','', '图像已自动生成，人工目视检查状态单列于complete.json；自动流水线不声称完成未实际进行的视觉验收。','', '- [固定协议](protocol.md)、[条件判定](reviews/conditional_gate.json)、[配置](config.locked.json)、[状态](state.json)。','- [800点完整指标](results/metrics.csv)、[2400轮计时](results/wall_rounds.csv)、[门槛表](results/recall_targets.csv)、[门槛分析](results/threshold_comparisons.json)、[逐query配对](results/paired_queries.csv)。','- [图像清单与PDF](figures/manifest.json)、[数值验收](reviews/raw_results_verified.json)、[4000文件历史对照](reviews/reference_raw_checks.json)、[输入身份](reviews/assets.json)、[运行后身份验收](reviews/post_run_identity.json)。','']
(RUN/'report.md').write_text('\n'.join(text));print('Report and threshold analysis generated')
