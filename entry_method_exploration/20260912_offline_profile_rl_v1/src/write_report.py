from common import *

a=read(O/'results/analysis.json');selection=read(O/'results/cal_selection.json')['selection']
gate=read(O/'results/development_gate.json');jobs=read(O/'logs/jobs.json');processes=read(O/'logs/training_processes.json')
def dsname(ds):return 'WebVid' if ds==DS[0] else 'Yandex-IP'
def modelname(m):return {'baseline':'原GT10','fast30k':'Fast30K','nsg':'NSG'}.get(m,m.upper().replace('202609','seed'))
def fmt(x):
 if isinstance(x,bool):return '是' if x else '否'
 if x is None:return '—'
 if isinstance(x,float):return f'{x:.6f}'
 return str(x)
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'---|'*len(headers)]+['| '+' | '.join(fmt(v) for v in r)+' |' for r in rows])+'\n'
def points(phase):return [p for p in a['points'] if p['phase']==phase]
compact=[]
for ds in DS:
 for arm in ARMS:
  name=selection[ds][arm]['model'];cal=next(p for p in points('cal') if p['dataset']==ds and p['model']==name);audit=next(p for p in points('audit') if p['dataset']==ds and p['model']==name);wall=next(p for p in points('frontier') if p['dataset']==ds and p['model']==name and p['L']==128)
  compact.append([dsname(ds),modelname(name),cal['delta_recall_pp'],audit['delta_recall_pp'],audit['total_NDC_delta_pct'],wall['delta_QPS_pct']])
headline=table(['数据','cal所选模型','cal ΔRecall pp','audit ΔRecall pp','audit Δtotal NDC %','audit L128 ΔQPS %'],compact)
text='''# E37：离线训练入口画像，再构建普通HNSW

2026-09-12。独立版本`20260912_offline_profile_rl_v1`；完成两数据集、两种估计器、双seed的训练、冻结模型部署和五L完整wall。用户要求把学习费用移到离线，本版本在线为raw query→一次普通HNSW top3→原NSG，没有query MLP或56集合枚举。原H/真实ID/大图/metric不变，默认画像未替换。

## 结果与判断

'''+(O/'conclusion.md').read_text()+'\n'+headline+'\n'+(O/'interpretation.md').read_text()+f'''
预定双集开发门为`{gate['status']}`。该门要求每集RL cal≥+0.10pp、audit>0、两者total NDC≤+1%；不根据结果改变门。无论门是否通过，本轮都完成预定的历史audit曲线；`independent_formal_GO=false`。

## 方法：学习画像，而非在每次查询中运行RL

当前P为WebVid GT10-soft-t1、Yandex GT10-hard。train4096单位query二阶矩的前16方向形成固定B；动作X有256个共享参数，W=normalize(P+0.25(PB)(tanh(X)/4)Bᵀ)。零参数按原P字节恢复。每个采样W都真实重建M16/efConstruction200/seed20260828的普通小HNSW；efSearch10返回top3，真实ID升序执行原NSG L128/K10。这里只通过画像改变重建后的图，没有独立删边/换边动作，也不训练大NSG。

策略为μ+0.3ε的一步Gaussian参数搜索。RL用8个独立扰动和leave-one-out奖励基线；ES用4对正负扰动。两者同参数化、同高斯平滑目标、同batch日程和预算，差别在估计器；不能凭RL名称声称多步决策或新的表示能力。Adam、200更新、步长与σ均预先固定，随机候选的奖励不能替代确定均值模型的实际部署结果。

每query U=hits−hits₀−0.1(totalNDC/totalNDC₀−1)−0.1(零命中指示−原零命中指示)，batch均值再减画像均方漂移。C++先返回真实联合搜索，Python后读GT评分；不相加单入口收益、不使用固定C8未知标签、不复用旧56组合监督。NDC只是低噪声训练项，完整wall单独实测。

与旧实验的实质区别：E28优化全H教师代理；E32真实奖励受旧C8重排限制；E33只删固定画像图的原边；E36在线模型做query相关交换。E37直接优化最终HNSW→NSG路径的静态画像，但qᵀW仍是逐入口线性评分，无法表示任意三入口联合效用。固定rank16/256参数和单构图seed只界定本版本，不能据此否定所有离线画像学习。[协议](protocol.md)、[方法依据与一手参照](method_basis.md)。

## 数据、选择与实际训练

每集从E24历史fit20K取train4096/monitor1024，PCG64 seed20260912；cal/audit各历史1024。四角色源行互斥；B只用train，checkpoint只看monitor，全部训练和独立复算结束后才准备cal，cal选各臂seed并冻结后再准备audit。原画像与这些开发样本曾用于历史实验，因而不是全管线盲测。本轮没有读取或hash validation/held-out原始输入，没有新增GT。

每次200更新，每步8候选×128实际搜索，step0及20..200各评测确定性train512/monitor1024。表中“选中”依monitor U且graph NDC≤+1%选择非零checkpoint，cal只再选seed；所有seed和末点都保留。

'''
text+=table(['数据','臂','seed','选中step','选中train ΔR pp','选中monitor ΔR pp','末点train ΔR pp','末点monitor ΔR pp','cal选中','画像中位角度 °','拓扑变化'],[[dsname(m['dataset']),m['arm'],m['seed'],m['selected_step'],m['selected_train_delta_pp'],m['selected_monitor_delta_pp'],m['last_train_delta_pp'],m['last_monitor_delta_pp'],m['selected_by_cal'],m['selected_median_angle_deg'],m['topology_changed']] for m in a['models']])
text+='\n![完整训练监控](figures/training_progress.svg)\n\n## cal/audit：全部正负结果\n\n以下均L128、相对本轮相同行原GT10；baseline绝对Recall同列。未选seed的audit结果只供完整报告，未用于回选。\n\n'
text+=table(['数据','split','模型','Recall %','ΔR pp','失败率 %','Δtotal NDC %','mean U','受益/受损query'],[[dsname(p['dataset']),p['phase'],modelname(p['model']),p['recall_pct'],p['delta_recall_pp'],p['failure_pct'],p['total_NDC_delta_pct'],p['mean_U'],f"{p['helped']}/{p['harmed']}"] for p in a['points'] if p['phase'] in ['cal','audit']])
text+='\n配对query bootstrap 5000次的95%区间是历史开发样本的描述性不确定性；没有校正选点或历史复用，不能充当独立确认试验。\n\n'
pairs=[p for p in a['paired'] if p['phase'] in ['cal','audit'] and (p['reference']!='baseline' or p['model'] in [selection[p['dataset']][arm]['model'] for arm in ARMS])]
text+=table(['数据','split','模型','参照','ΔR pp','95%低 pp','95%高 pp'],[[dsname(p['dataset']),p['phase'],modelname(p['model']),modelname(p['reference']),p['delta_recall_pp'],p['CI_low_pp'],p['CI_high_pp']] for p in pairs])
text+='\n## 五L完整Recall–QPS与失败率\n\n历史audit1024，两集各5方法×5L；五次独立plain整批wall取中位QPS。CPU15、实际线程1、串行、无训练或重分析并发；count与原kernel核验、GT评分在timer外。不同L的同模型画像、小图和入口完全相同。Fast30K沿用原训练量/seed，不能把它与GT10的所有差别归为本轮优化。\n\n![Recall–QPS](figures/recall_qps.svg)\n\n'
for ds in DS:
 text+='### '+dsname(ds)+'\n\n'
 text+=table(['模型','L','Recall %','失败率 %','QPS中位','QPS最小','QPS最大','route NDC','graph NDC','ΔR pp','ΔQPS %'],[[modelname(p['model']),p['L'],p['recall_pct'],p['failure_pct'],p['QPS'],p['QPS_min'],p['QPS_max'],p['route_NDC'],p['graph_NDC'],p['delta_recall_pp'],p['delta_QPS_pct']] for p in points('frontier') if p['dataset']==ds])+'\n'
text+='![同L质量和完整成本变化](figures/quality_cost_changes.svg)\n\n同L Recall/QPS分别报告。下表仅在双方共同Recall范围内，对非支配点作log-QPS线性插值；它是五个实测点间的描述性比较，不是额外实测或独立前沿证据。\n\n'
text+=table(['数据','模型','参考Recall %','插值相对原GT10 QPS %'],[[dsname(p['dataset']),modelname(p['model']),p['reference_recall_pct'],p['speedup_pct']] for p in a['frontier'] if p['model'] in [selection[p['dataset']][arm]['model'] for arm in ARMS]])
text+='\n### 入口变化、收益与损伤（所选模型audit L128）\n\n'
text+=table(['数据','模型','入口变化query','受益query','受损query','新增命中总数','损失命中总数','挽救零命中','新增零命中'],[[dsname(p['dataset']),modelname(p['model']),p['entry_changed_queries'],p['helped'],p['harmed'],p['hits_gained'],p['hits_lost'],p['rescued'],p['new_failures']] for p in points('audit') if p['model'] in [selection[p['dataset']][arm]['model'] for arm in ARMS]])
text+='\n### 路由与图的分项时间（L128）\n\nroute-only和graph-only为timer外另开测量的分项，缓存/执行环境不同，不能相加充当完整wall。在线不再运行E36的MLP，但画像和图变化仍会改变普通HNSW与NSG的工作量；不能预设零时间差。\n\n'
text+=table(['数据','模型','route-only μs/query','graph-only μs/query','完整wall μs/query'],[[dsname(p['dataset']),modelname(p['model']),p['route_only_us'],p['graph_only_us'],1e6/p['QPS']] for p in points('frontier') if p['L']==128])
text+='\n## 离线成本和验收\n\n'
text+=table(['数据','训练进程秒','峰值RSS GiB','实测线程'],[[dsname(p['dataset']),p['seconds'],p['peak_RSS_KiB']/(1<<20),p['peak_threads']] for p in processes])
text+=f'''
8次训练共1600更新，采样12800套静态画像；训练/预检实际重建12912个HNSW。8次训练记录的构图累计{sum(m['build_seconds'] for m in a['models']):.3f}s。训练进程累计{sum(p['seconds'] for p in processes):.3f}s，含本轮实际反馈与导出；不含历史GT/原画像构建、准备编译、独立复核和后续部署，不能称为从原始数据开始的全部训练成本。

本轮新增NSG实际{sum(j['actual'] for j in jobs):,}次，预留{sum(j['reserved'] for j in jobs):,}次，硬上限2,800,000；实际调用与失败余量分开。12800次采样候选全部真实搜索，无旧标签复用；中心/基线/原kernel重复核验、cal/audit和完整wall也计入账。[逐job账本](logs/jobs.json)、[训练进程](logs/training_processes.json)。

数学预检包括Gaussian梯度解析积分/有限差分、LOO常奖励与平移不变性、ES缩放、Adam第一步、零参数字节恢复和扰动图确定性。原GT10 fit10240行与旧返回/距离/入口/NDC逐位一致。独立训练审计重放全部动作、奖励、参数/Adam更新和88checkpoint，导出模型再通过无训练hook评测器回归1280行。部署80点、50个前沿点、250轮plain wall输出核验，原GT10 cal/audit4096行回归旧结果。完整配对、五L相同图/入口及工作簿逐单元格复核见[最终验收](reviews/final_audit.json)。

旧E36整目录SHA、实际依赖SHA及此前36090个文件的大小/mtime复核；旧源/图/GT/标签/模型/日志保留。根四文档变更前件位于[source_before](source_before/summary.md)。独立版本未替换默认模型，未排队追加训练或新评估。

## 产物与复核入口

- [锁定配置](config.locked.json)、[输入和依赖SHA](reviews/upstream.json)、[模型冻结](reviews/models_after_training.json)、[cal选择冻结](reviews/selection_before_audit.json)。
- [训练源码](src/train.py)、[实际搜索环境](src/environment.cpp)、[无hook部署](src/deploy.py)、[独立训练复算](src/audit_training.py)。
- [训练审计](reviews/training_verification.json)、[输出审计](reviews/output_verification.json)、[状态](state.json)、[开发门](results/development_gate.json)。
- [完整结果JSON](results/analysis.json)、[原值CSV](results/points.csv)、[配对CSV](results/paired.csv)、[逐queryCSV](results/query_results.csv)、[250轮wall](results/timings.csv)、[Excel八表](results/offline_profile_rl.xlsx)。
- [Recall–QPS PNG](figures/recall_qps.png)/[SVG](figures/recall_qps.svg)/[PDF](figures/recall_qps.pdf)，另存完整训练和质量成本图。
- [历史26](../../experiment_history/26_offline_profile_rl.md)、[当前结果](../../summary.md)、[实现契约](../../spec.md)、[下一阶段](../../s-target.md)。

本目录是冻结结果，prepare/train/deploy控制器拒绝重用已存在的manifest/job/output，不能原地重复执行。复核优先读取JSON/CSV、校验final_artifact_freeze内SHA；如需重新训练或新增查询，先建立新版本与协议，并完整承接固定输入/模型身份及调用预算。既有执行命令和PID/线程证据保存在训练进程、continuation和各阶段日志中。
'''
(O/'report.md').write_text(text)
(O/'results/headline_table.md').write_text(headline)
print('REPORT_WRITTEN',len(text),flush=True)
