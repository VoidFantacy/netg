from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
assert read(R/'reviews/independent_numeric_audit.json')['status']=='PASS'
metrics=read(R/'results/metrics.json');paired=read(R/'results/paired.json');agg=read(R/'results/aggregate.json');gate=read(R/'results/gate.json');cost=read(R/'reviews/cost_ledger.json');fit=read(R/'results/fit_summary.json');short={d['dataset']:('WebVid' if d['dataset'].startswith('web') else 'Yandex') for d in fit}
def met(ds,m,K):return next(r for r in metrics if r['dataset']==ds and r['method']==m and r['K']==K)
lines=['# E117：四动作入口集合试验','',f'2026-09-20。`{gate["status"]}`。按用户“试试”完成独立版本。只选择主搜索开始前的真实入口集合，原GT10画像/小图、底图、raw-IP、L、展开及停止规则保持。Web soft/Y hard及生产E99没有替换。','']
if gate['status'].startswith('STOP'):
 lines+=['**主模型未通过预先冻结的接受门，停止本版。** 不追加深度、阈值、λ、seed、候选数量或失败query定向修复；条件完整预算比较未启动。下表保留全部正负结果，不能把拟合收益或免费oracle称为可部署提升。','']
else:
 lines+=['**L128主门通过，条件完整预算比较已执行。** 单个开发点的通过不等于最终泛化或生产替换；另见完整预算产物及最终判定。','']
lines+=['## 1. 实际做了什么','','每集原E24 fit20K的前10000条拟合，最后4096条接受，源行分别[10000:20000]和[25904:30000]；query字节互斥。原GT10画像曾使用这些query，所有源均属历史开发材料，因此只称“本版选择器拟合外接受”，不称画像未见或项目盲测。E105那批4096条没有进入本版。两集模型冻结后才打开接受载荷。','','一次原小图返回相同三个真实候选，按实际画像分数定义e1/e2/e3。动作仅为原三入口、e1单入口、e2单入口、e3单入口。选定后按原约定调用同一kernel；没有强制首展开、搜索中换点、剪枝、重启或调L。','','六特征是两项画像分数间隔、三项真实入口raw-IP间隔和实际分数最优者的画像rank；真实分数额外3次点积计入成本。深度≤2、叶支持≥512的固定贪心策略树：CostTree使用等K召回差−0.1×相对时间差，RecallTree不含时间项，ShuffledTree固定打乱完整动作标签向量。量化分裂候选只由fit特征生成，未用接受结果调超参数。此算法不是全局最优树保证，也不把共享评分器宣称新颖。','','训练时间标签按256条query的块轮换五种计时变体，每变体完成整块再换方法，共四遍。原GT10与计算特征后仍三入口的Feature3分开计时；single训练时间包含特征。真实树判断及返回输出成本最终以整批wall验收。训练K100同L首返回用于K1标签并经实际K1/原内核检查，接受K1/K100分别实际调用。','', '[冻结协议](protocol.md) · [配置](config.locked.json) · [训练源码](src/train.py) · [原搜索调用与计时](src/experiment.cpp)','', '## 2. CostTree相对原GT10的实际结果','', '每点4096条、L128、CPU15/线程1、预热后3轮完整wall；QPS主列为N/三轮平均wall，三轮QPS另存。Recall差为pp。','', '| 数据/K | GT10 Recall → CostTree | ΔRecall [98.75%配对区间] | GT10 QPS → CostTree | ΔQPS | 零命中救回/新增 |','|---|---:|---|---:|---:|---:|']
for d in fit:
 ds=d['dataset']
 for K in [1,100]:
  a=met(ds,'GT10',K);b=met(ds,'CostTree',K);p=next(r for r in paired if r['dataset']==ds and r['method']=='CostTree' and r['reference']=='GT10' and r['K']==K);ci=p['CI98_75_pp']
  lines.append(f'| {short[ds]}/{K} | {a["recall_pct"]:.4f}% → {b["recall_pct"]:.4f}% | {p["delta_recall_pp"]:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}] | {a["qps"]:.2f} → {b["qps"]:.2f} | {p["delta_qps_pct"]:+.3f}% | {p["rescued_zero"]}/{p["new_zero"]} |')
lines+=['','bootstrap以query为配对单位，20000次；动作/重复计时不增加独立query数。区间描述历史开发样本条件下的不确定性，不覆盖全部历次研究选择。微小速度均值差须结合三轮范围，不作稳定加速保证。','', '## 3. 必须与固定动作比较','', '| 数据 | fit冻结的最强固定动作 | CostTree对GT10等K差 [98.75%CI] | 对固定动作等K差 [98.75%CI] | 对ShuffledTree等K差 |','|---|---|---|---|---:|']
for d in fit:
 ds=d['dataset'];fixed=d['fixed_best_method']
 def ag(ref):return next(v for v in agg if v['dataset']==ds and v['reference']==ref)
 def fmt(v):return f'{v["equalK_delta_pp"]:+.4f} [{v["CI98_75_pp"][0]:+.4f}, {v["CI98_75_pp"][1]:+.4f}]'
 lines.append(f'| {short[ds]} | {fixed} | {fmt(ag("GT10"))} | {fmt(ag(fixed))} | {ag("ShuffledTree")["equalK_delta_pp"]:+.4f} |')
lines+=['','主门各条件：','']
names={'recall_means_nondecreasing_vs_both':'两K召回均值对GT10/冻结固定动作均不降','positive_equalK_CI_vs_both_each_dataset':'两集对两个参照的等K增量区间下界均正','qps_nondecreasing_vs_both':'两K完整QPS对两个参照均不降','not_below_shuffled_quality':'两集等K召回不低于打乱标签对照'}
for k,v in gate['criteria'].items():lines.append(f'- {names[k]}：{"PASS" if v else "FAIL"}。')
lines+=['','这里的FixedBest由训练侧冻结；接受侧全部固定动作也展示，不能事后把较好的固定规则算作学到的收益。两个K的平均只用于主汇总，各K下降仍会使门失败。','', '## 4. 完整八方法结果','', '| 数据/方法 | R1% | QPS1 | K1零命中 | R100% | QPS100 | K100零命中 |','|---|---:|---:|---:|---:|---:|---:|']
for d in fit:
 for m in d['methods']:
  ds=d['dataset'];a=met(ds,m['name'],1);b=met(ds,m['name'],100)
  lines.append(f'| {short[ds]}/{m["name"]} | {a["recall_pct"]:.4f} | {a["qps"]:.2f} | {a["zero_hit_queries"]} | {b["recall_pct"]:.4f} | {b["qps"]:.2f} | {b["zero_hit_queries"]} |')
lines+=['','Feature3与GT10的质量/入口/图NDC逐query相同，只为观察增加特征的完整时间影响。CostTree和RecallTree若选同动作，质量相同；分别计时的细小速度差不能归为不同算法作用。其它模型不通过接受结果晋升为新主候选。','', '[全部指标及三轮时间](results/metrics.json) · [全部参照配对](results/paired.csv) · [主门](results/gate.json)','', '## 5. 拟合、动作空间与迁移','', '| 数据/模型 | fit动作数[三入口,e1,e2,e3] | accept动作数 | fit ΔR1/ΔR100 pp |','|---|---|---|---|']
for d in fit:
 for r in d['records']:
  a=met(d['dataset'],r['method'],1)
  lines.append(f'| {short[d["dataset"]]}/{r["method"]} | {r["actions"]} | {a["actions"]} | {r["delta_recall_pp"][0]:+.4f}/{r["delta_recall_pp"][1]:+.4f} |')
lines+=['','以下四动作oracle在接受侧逐query免费选择，两个K分别最大化，选择时看GT且不付额外成本；仅说明实测动作空间，不能作为一个真实策略同时取得的结果。','', '| 数据/K | 四动作oracle Recall% | 对GT10空间pp | 对接受侧最强固定动作空间pp | 四动作Recall非恒定query |','|---|---:|---:|---:|---:|']
for d in fit:
 ds=d['dataset'];o=read(R/'results'/f'{ds}.action_oracle.json')
 for K,v in o.items():lines.append(f'| {short[ds]}/{K} | {v["oracle_recall_pct"]:.4f} | {v["gain_vs_GT10_pp"]:.4f} | {v["gain_vs_best_fixed_pp"]:.4f} | {v["nonconstant_queries"]} |')
lines+=['','动作空间有余量与低成本特征能预测净收益仍是两回事。CostTree与RecallTree的拟合差别表明成本项是否改变实际决策；当前版本的负结果只约束这组特征、动作域和训练法，不能推出所有入口选择不可学习，也不支持转去修改主搜索。','', '## 6. 成本、核验和停止边界','',f'实际NSG {cost["totals"]["search_calls"]:,}次、路由 {cost["totals"]["router_calls"]:,}次、额外入口特征点积 {cost["totals"]["feature_distance_calls"]:,}次，六次浅树拟合。控制器{cost["controller_seconds"]:.2f}秒（{cost["controller_seconds"]/60:.2f}分钟），两次编译共{cost["compile_seconds"]:.2f}秒单列，训练/评分时间见账本；采样最大RSS {cost["max_observed_rss_bytes"]/1024**3:.3f}GiB。不是线上QPS，也不是全部实现和复盘用时。0新GT/大小图/梯度网络/未曝光held-out。','', '验证覆盖：原Router成员恢复；训练重复/plain/count与实际K1前缀；全部实际接受K1/K100前缀及NDC；每个学习策略的完整返回等于所选固定动作；全部接受GT10默认恢复同query的E116原返回/距离bits/入口/NDC；Python/C++全量动作；原始query/GT角色与源行字节；特征独立算术及定点向量校验；独立GT重评分与救回/损伤；调用账本；单线程、模型/源码冻结和原件保护。kernel与E116逐字相同，原ACSG.cpp未改。大base/NSG沿用原SHA来源和当前stat身份，不宣称本次重hash全图。','', '[独立核验](reviews/independent_numeric_audit.json) · [成本账本](reviews/cost_ledger.json) · [模型冻结](reviews/models_frozen.json) · [串行任务](reviews/jobs.json) · [完成状态](state.json)','', '当前试验所有结果与模型保留。本版门失败则停止，不按接受失败query改规则；若未来另有实质新信息与假设，须建立独立版本。默认仍为Web GT10-soft-t1、Yandex GT10-hard，生产保持E99。']
(R/'report.md').write_text('\n'.join(lines)+'\n')
print(R/'report.md')
