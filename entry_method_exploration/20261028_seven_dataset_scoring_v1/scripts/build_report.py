import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
import csv,json,time,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
R=Path(__file__).resolve().parents[1]
DS=['deep10m_l2_v1','sift10m_bigann_l2_v1','gist1m_l2_v1','coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']
LABEL=dict(zip(DS,['Deep10M','SIFT10M','GIST1M','COCO','Flickr30k','WebVid','Yandex10M']))
METHODS=['GT10','B32','REUSE-PQ','REUSE-SQ','MAIN-SQ'];NEW=['REUSE-SQ','MAIN-SQ']
# These are historical E185 diagnostics, not newly measured causal labels.
HISTORY={'deep10m_l2_v1':(5.80,.07),'sift10m_bigann_l2_v1':(5.16,0),'gist1m_l2_v1':(8.08,.43),'coco':(42.,10.51),'flickr30k':(33.61,3.48),'webvid2_5m_light_v1':(15.10,5.44),'yandex_t2i_official10M_ip_v1':(6.69,.57)}
def rows(p):return list(csv.DictReader(p.open())) if p.exists() else []
def table(path,data):
 if data:
  with path.open('w') as f:w=csv.DictWriter(f,list(data[0]));w.writeheader();w.writerows(data)
 else:path.write_text('dataset,K,method,L\n')
def f(x,k):return float(x[k]) if x.get(k) not in ['',None] else float('nan')
def md(head,data):return '\n'.join(['| '+' | '.join(head)+' |','| '+' | '.join(['---']*len(head))+' |']+['| '+' | '.join(map(str,r))+' |' for r in data])
def screen(x):return (f(x,'target_speed_delta_pct')>=2 and x['target_speed_three_rounds_positive']=='True') or f(x,'budget_recall_delta_pp')>=.05
def main():
 t=time.perf_counter();assert (R/'primary_complete.json').exists() and (R/'dense_complete.json').exists();points=[];paired=[];coverage=[];strata=[];comp=[];densepoints=[];densecomp=[];cost=[];catalogue=[];decisions=json.loads((R/'dense_freeze.json').read_text())['decisions'];audits=[]
 for ds in DS:
  p=R/'analysis'/ds
  for name,dest in [('points.csv',points),('paired.csv',paired),('coverage.csv',coverage),('source_strata.csv',strata),('discrete_comparisons.csv',comp)]:dest.extend(rows(p/name))
  densepoints.extend(rows(R/f'dense_analysis/{ds}/points.csv'));densecomp.extend(rows(R/f'dense_analysis/{ds}/discrete_comparisons.csv'));audits.append(json.loads((R/f'reviews/results_audit_{ds}.json').read_text()));c=json.loads((R/f'configs/{ds}.json').read_text());model=json.loads((Path(c['models'])/'model.json').read_text());env=json.loads((R/f'storage/results/{ds}/environment.json').read_text());run=json.loads((R/f'reviews/formal_{ds}.receipt.json').read_text());prep=json.loads((R/f'reviews/prepare_aux_{ds}.receipt.json').read_text());sq=json.loads((R/f'reviews/prepare_{ds}.receipt.json').read_text());owned=sum(v.stat().st_size for v in Path(c['models']).iterdir() if v.is_file());anal=json.loads((p/'summary.json').read_text());dr=R/f'reviews/dense_{ds}.receipt.json'
  cost.append(dict(dataset=ds,N=c['base']['n'],d=c['base']['d'],metric='squared L2' if c['metric_id']==1 else 'raw IP',family=c['family'],PQ_M=c['PQ_M'],H=len(__import__('array').array('i',Path(c['router']['ids']).read_bytes())),test_queries=c['queries']['n'],owned_model_MiB=owned/2**20,auxiliary_array_MiB=env['auxiliary_array_bytes']/2**20,prepare_suite_seconds=prep['seconds'],SQ8_prepare_suite_seconds=sq['seconds'],formal_suite_seconds=run['seconds'],formal_internal_seconds=anal['internal_wall_seconds'],formal_sampled_peak_RSS_GiB=run['peak_sampled_rss_bytes']/2**30,formal_max_threads=run['max_observed_threads'],offline_max_observed_threads=prep['max_observed_threads'],dense_suite_seconds=json.loads(dr.read_text())['seconds'] if dr.exists() else 0))
  catalogue.append(dict(dataset=ds,source_config=str((R/f'configs/{ds}.json').resolve()),training_role_scope=c['training_role_scope'],old_GT100_overlap_pct=HISTORY[ds][0],old_nearest_training_missing_coverage_pct=HISTORY[ds][1],old_diagnostic_sample=512))
 assert len(points)==448;table(R/'analysis/all_primary_points.csv',points);table(R/'analysis/all_paired.csv',paired);table(R/'analysis/all_coverage.csv',coverage);table(R/'analysis/all_source_strata.csv',strata);table(R/'analysis/all_discrete_comparisons.csv',comp);table(R/'analysis/all_dense_points.csv',densepoints);table(R/'analysis/all_dense_comparisons.csv',densecomp);table(R/'analysis/cost_ledger.csv',cost)
 positives=[x for x in comp if x['method'] in NEW and screen(x)];confirmed=[]
 for x in positives:
  y=next(z for z in densecomp if z['dataset']==x['dataset'] and z['K']==x['K'] and z['method']==x['method'] and z['L']==x['L']);status='RETAIN_EXPLORATORY' if screen(y) else 'COVERED_BY_DENSE_GT10' if y['dominated_by_GT_L'] else 'NO_DENSE_SCREEN_PASS'
  confirmed.append(dict(dataset=x['dataset'],K=x['K'],method=x['method'],L=x['L'],primary_speed_delta_pct=x['target_speed_delta_pct'],primary_budget_recall_delta_pp=x['budget_recall_delta_pp'],dense_speed_delta_pct=y['target_speed_delta_pct'],dense_budget_recall_delta_pp=y['budget_recall_delta_pp'],dense_dominated_by_GT_L=y['dominated_by_GT_L'],decision=status))
 table(R/'analysis/confirmed_screens.csv',confirmed);retained=[x for x in confirmed if x['decision']=='RETAIN_EXPLORATORY'];get=lambda ds,K,m,L:next(x for x in points if x['dataset']==ds and x['K']==str(K) and x['method']==m and x['L']==str(L));pair=lambda ds,K,m,L:next(x for x in paired if x['dataset']==ds and x['K']==str(K) and x['method']==m and x['L']==str(L))
 headline=f"七集真实K1/K100：原矩阵448点/1344完整T1轮；另一次密集控制{len(densepoints)}点/{3*len(densepoints)}轮。112个SQ来源/预算点中，原网格{len(positives)}个通过探索筛选，密集同窗口后{len(retained)}个仍通过；默认E99 GT10保持。"
 lines=['# E191：七数据集、两K的候选来源与评分综合测试','2026-10-28启动；完整单线程、原metric/图/GT10保持。本轮不生成PDF。',headline,'## 先读结论的适用范围','本报告检验固定候选PQ→SQ8评分能否迁移，并加入无训练遗漏块表的MAIN-SQ。共享较强/弱是旧数据上的观测分层；完整结果按数据集、K、L和候选源分别保留，不用一个COCO结果代替全部数据。保留探索价值与默认替换分开判断。',('出现密集控制后保留的场景候选，见下表；它们是一图/画像、历史曝光query上的可复现局部证据，尚无新系统盲确认。' if retained else '本轮固定参数没有在密集同窗口控制后建立通过探索门的场景。仍须保留来源覆盖、筛选质量及费用的分别证据，不能据此推出所有补全/量化路线无效。'),'## 数据、角色与历史共享观测',md(['数据','N×d','metric','家族/H','test n','旧GT100重合','旧遗漏覆盖'],[[LABEL[x['dataset']],f"{x['N']}×{x['d']}",x['metric'],f"{x['family']}/{x['H']}",x['test_queries'],f"{HISTORY[x['dataset']][0]:.2f}%",f"{HISTORY[x['dataset']][1]:.2f}%"] for x in cost]),'后两列来自E185每集固定512query的“最近合法训练query”诊断；GT重合与遗漏覆盖分母不同，不是本轮新测，也不是因果/语义独立标签。Deep/SIFT并非近邻完全不重合，而是训练遗漏对test遗漏覆盖很弱。[E185原表](../20261024_manifold_residual_probe_v1/report_zh.md)。','原图/GT10与任务原metric不变，IP不变成cosine，L2不额外归一化。GT是特征近邻而非人工语义配对。家族在读新结果前固定；H、库规模、维度、metric、训练密度未因果配平。','## 机制与同预算条件','GT10不补全。B32为旧16K/K100L200目标ID表；新入口块表只用合法前12K同教师遗漏，每hub8块；末4K不拟合、不选配置。三个hub块表与真实主返回最高8块去重最多32，原metric中心排序，整块扫描≤2048。REUSE-PQ/SQ逐query pool、扫描块/顺序完全一致，各取96追加原metric精算/严格合并。','MAIN-SQ只用真实主返回最高8块，不使用训练遗漏块表；每块≤128，实际≤1024码，K1只有一个主返回块。它的来源信息及实际访问量同时变化，不能当纯共享因果消融；原GT10本身仍有监督，不称整个系统无监督。','K1真实只返回/使用一个主结果，命中仅对GT1；没有暗中取100个主结果。两K共享K100教师的同张块表/固定96精算上限是实验条件，不是各K最佳配置。B32含末4K标签，只作正式参考，不进校准选择。','SQ8原base全库逐维minmax编码，无query/GT训练；COCO/Deep沿旧块与表，其他集同机制新建。PQ通常M16，Yandex d200合法适配M20；这不是完全等码长跨数据因果控制。SQ8码为d字节，PQ码为M字节；更准确评分的内存和全部线上工作都支付，次数不能替代分段耗时。','## 固定L200的完整表现：两K、七集']
 for K in [1,100]:
  data=[]
  for ds in DS:
   def cell(m):
    x=get(ds,K,m,200);return f"{f(x,'recall_pct'):.4f}% / {f(x,'qps'):.2f}"
   data.append([LABEL[ds]]+[cell(m) for m in METHODS])
  lines+=['### K='+str(K),md(['数据','GT10 Recall/QPS','B32','REUSE-PQ','REUSE-SQ','MAIN-SQ'],data)]
 lines+=['所有QPS是本轮同一可执行程序的完整batch wall三轮中位数；实际返回来自计时包。绝对速度不拼接E190/E183；正常分配初始化、路由、主搜、补全、六数组复制与销毁均计入，加载/保存/GT/oracle在外。','## 原网格阳性与一次密集控制',md(['数据','K','方法','L','原阈值速度%','密集阈值速度%','密集预算Recall差pp','决定'],[[LABEL[x['dataset']],x['K'],x['method'],x['L'],x['primary_speed_delta_pct'],x['dense_speed_delta_pct'],x['dense_budget_recall_delta_pp'],x['decision']] for x in confirmed]) if confirmed else '原网格无SQ来源方法通过探索筛选，无追加控制矩阵。','探索门为达到候选Recall的最快已测GT10参照上速度≥+2%且三轮同向，或完整费用内最好GT10之上Recall≥+0.05pp。原网格阳性只作筛选；按协议一次性冻结质量括号内5个等距整数L并同窗口重测候选。无模型/预算修改、不迭代细分到通过。有限网格不等于精确等Recall；密集与原窗口绝对QPS不混用。[冻结决定](dense_freeze.json)。']
 # Per-dataset conclusions are generated from actual measured coverage and costs.
 for ds in DS:
  lines+=['## '+LABEL[ds]+'：分别看来源、排序和完整费用']
  for K in [1,100]:
   data=[]
   for m in METHODS:
    x=get(ds,K,m,200);p=pair(ds,K,m,200) if m!='GT10' else None;data.append([m,f"{f(x,'recall_pct'):.4f}",f"{f(x,'qps'):.2f}",f"{f(p,'recall_delta_pp'):+.4f}" if p else '—',f"{f(p,'extra_time_pct'):+.2f}" if p else '—',f"{p['members_rescued']}/{p['members_damaged']}" if p else '—',p['rescued_source_out'] if p else '—',f"{f(x,'scanned_codes_per_query'):.1f}" if m not in ['GT10','B32'] else '—',f"{f(x,'exact_scores_per_query'):.1f}" if m!='GT10' else '—'])
   lines += ['### K='+str(K)+'，L200',md(['方法','Recall%','QPS','ΔRecall pp','额外耗时%','救回/损伤','旧源外救回','扫码/query','追加精算/query'],data)]
  cv=[x for x in coverage if x['dataset']==ds and x['L']=='200'];lines += [md(['K','方法','原遗漏','池覆盖','扫描覆盖','短名单覆盖','最终救回'],[[x['K'],x['method'],x['members_missing'],x['pool_covered'],x['scanned_covered'],x['shortlist_covered'],x['rescued']] for x in cv])]
  a=next(x for x in cv if x['K']=='100' and x['method']=='REUSE-PQ');b=next(x for x in cv if x['K']=='100' and x['method']=='REUSE-SQ');s=float(b['scanned_covered']);missing=float(b['members_missing']);short=float(b['shortlist_covered']);lines += [f"K100/L200的固定候选池覆盖{b['pool_covered']}/{b['members_missing']}个遗漏，实际扫描覆盖{b['scanned_covered']}（{100*s/missing if missing else 0:.2f}%原遗漏）。相同扫描下，PQ短名单保留{a['shortlist_covered']}，SQ保留{b['shortlist_covered']}（{100*short/s if s else 0:.2f}%扫描内遗漏）。这是成员发生次数，不是修复同数量query。"]
  if missing and s/missing<.1:lines += ['这套候选来源/扫描路径对本集遗漏的覆盖较低，改善码评分不能越过这部分覆盖上限。该上限只约束当前来源与预算。']
  if s and short/s>.95:lines += ['SQ已保住绝大多数扫描内遗漏，后续收益更多受当前来源/扫描和完整费用约束；不能继续把大部分损失归给本轮SQ筛选。']
  elif s:lines += ['SQ短名单仍存在可见遗漏，需结合精确96只读诊断区分量化失真、96容量和GT/tie边界；不能仅看总体Recall。']
  sqp=pair(ds,100,'REUSE-SQ',200);mp=pair(ds,100,'MAIN-SQ',200);lines += [f"SQ K100/L200救回中的旧16K残差源外事件为{sqp['rescued_source_out']}，MAIN-SQ为{mp['rescued_source_out']}。源外仅表示不在旧残差ID并集，不表示从未出现在任何GT10监督中，也不自动证明不依赖邻域共享。"]
  d=[x for x in confirmed if x['dataset']==ds];keep=[x for x in d if x['decision']=='RETAIN_EXPLORATORY'];lines += [f"本集原网格阳性{len(d)}点，密集控制后保留{len(keep)}点。"+('保留对应K/L/来源作为场景候选；不将其扩写为其他K、全部预算或默认替换。' if keep else '本固定版本尚未建立通过密集探索门的综合收益；来源、排序和费用的机制证据仍分别保留。')]
  lines += [f"![{LABEL[ds]} Recall–QPS](figures/{ds}.png)"]
 # Full tail tables and sharing strata remain explicit and reproducible.
 tail=[x for x in paired if x['K']=='100'];lines+=['## 严重失败、完整恢复与损伤',md(['数据','方法','L','原0–9命中','现0–9','原失败改善','脱离','新增','完整恢复query'],[[LABEL[x['dataset']],x['method'],x['L'],x['original_lt10'],x['final_lt10'],x['lt10_improved'],x['lt10_escaped'],x['new_lt10'],x['complete_recovered_queries']] for x in tail]),'K100严重失败严格为0–9命中，恰好10排除。成员救回、查询有所改善、脱离严重失败和完整恢复分别计数。GIST仅1000query、Flickr5000；稀少尾部个例不外推。所有成员损伤保持严格GT-ID，重复向量不同ID及浮点边界只分类不改GT。','## 按旧训练遗漏源覆盖分层',md(['数据','K','方法','L','分层','query数','ΔRecall pp','救回','损伤','旧源外'],[[LABEL[x['dataset']],x['K'],x['method'],x['L'],x['stratum'],x['queries'],f"{f(x,'recall_delta_pp'):+.4f}",x['members_rescued'],x['members_damaged'],x['rescued_source_out']] for x in strata if x['L']=='200' and x['method'] in NEW]),'分层由实际GT/主返回事后计算，只解释来源覆盖，不是线上可见特征或可用门控器。no_old_source表示原遗漏成员均不在旧16K残差源；不同于一般语义/GT近邻不共享。原主返回已完整的query单列no_missing，零分母不包装成100%修复。','## SQ与精确96的只读诊断',md(['数据','K','方法','样本原遗漏','扫描覆盖','实际短名单','float64精确96'],[[LABEL[x['dataset']],x['K'],x['method'],x['original_missing'],x['scanned_missing'],x['actual_shortlist_missing'],x['float64_exact96_missing']] for x in rows(R/'analysis/scoring_diagnostic.csv')]),'每集固定128query/seed20261028，只在已有扫描ID上以原metric float64排序，未改模型/预算/测试点，不属于免费在线方法或原生反事实。全量短名单→最终返回损失另见[分类](analysis/merge_loss_summary.csv)与逐例CSV。','## 实际费用与可复现限制',md(['数据','离线准备秒','SQ准备秒','正式suite秒','内含timed秒','正式峰RSS GiB','辅助数组MiB','本轮模型MiB','线程'],[[LABEL[x['dataset']],f"{x['prepare_suite_seconds']:.2f}",f"{x['SQ8_prepare_suite_seconds']:.2f}",f"{x['formal_suite_seconds']:.2f}",f"{x['formal_internal_seconds']:.2f}",f"{x['formal_sampled_peak_RSS_GiB']:.2f}",f"{x['auxiliary_array_MiB']:.2f}",f"{x['owned_model_MiB']:.2f}",x['formal_max_threads']] for x in cost]),'suite包含内部timed、预热、输出及oracle，不重复相加。旧图/GT/画像/教师及复用块/码本的历史构建债不清零；完整冷启动总费用未知。共同benchmark装载的辅助数组/RSS不等于默认GT10部署依赖或某单方法最低内存。离线每库8线程，观察到的总线程可能更多，实际收据单列；正式全部实际1线程。','首轮actual timed包保留raw，后两轮bits/SHA；trace为wall外从实际主包重建，部分无损gzip且保留原SHA。新增大产物在/root/acsg-e191-storage，项目storage链接；没有删除旧证据。次数为原metric追加精算、块中心、PQ码、SQ码各自口径，不能相加冒充总NDC或阶段耗时占比。','配对bootstrap5000次只作描述，没有多比较调整或语义IID保证，未由stdlib脚本独立重算。三轮是计时重复，不是三份独立质量样本；所有query窗口历史曝光，一套图/画像，无新的系统盲确认。','## 核验与交付索引',f"全部{len(points)}原点、{len(densepoints)}密集点保存实际包；全部质量/救损/覆盖链/严格失败/预算比较由另一份stdlib实现复算。七集历史GT10/B32同K/L返回全包核对{sum(x['historical_full_packets_equal'] for x in audits)}点；资格140点、训练hub表全部重建、SQ编码与原metric/筛选阈值另抽检。不同实现均同一执行者，非独立人员复现。旧E190 seal保持。",'[协议](protocol.md) · [冻结](freeze.json) · [密集冻结](dense_freeze.json) · [448原点](analysis/all_primary_points.csv) · [密集点](analysis/all_dense_points.csv) · [全部救损](analysis/all_paired.csv) · [覆盖链](analysis/all_coverage.csv) · [来源分层](analysis/all_source_strata.csv) · [原离散比较](analysis/all_discrete_comparisons.csv) · [密集比较](analysis/all_dense_comparisons.csv) · [成本](analysis/cost_ledger.csv)']
 (R/'report_zh.md').write_text('\n\n'.join(lines)+'\n');font_manager.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc');plt.rcParams.update({'font.family':'Noto Sans CJK JP','font.size':10,'axes.unicode_minus':False})
 for ds in DS:
  fig,axes=plt.subplots(1,2,figsize=(14,5))
  for ax,K in zip(axes,[1,100]):
   for m in METHODS:
    pp=sorted([x for x in points if x['dataset']==ds and x['K']==str(K) and x['method']==m],key=lambda x:int(x['L']));ax.errorbar([f(x,'recall_pct') for x in pp],[f(x,'qps') for x in pp],yerr=[[f(x,'qps')-f(x,'qps_min') for x in pp],[f(x,'qps_max')-f(x,'qps') for x in pp]],fmt='-o',ms=3,capsize=2,label=m)
   ax.set_title(f'{LABEL[ds]} | K={K}');ax.set_xlabel('Recall (%)');ax.set_ylabel('完整单线程 QPS');ax.grid(alpha=.25);ax.legend(fontsize=8)
  fig.suptitle('E191：原矩阵实测点；线段非新增测量，误差线为三轮范围');fig.tight_layout();fig.savefig(R/f'figures/{ds}.png',dpi=150);fig.savefig(R/f'figures/{ds}.svg');plt.close(fig)
 rec=dict(status='PASS_E191_REPORT_BUILD',primary_points=448,primary_batches=1344,dense_points=len(densepoints),dense_batches=3*len(densepoints),primary_positive_points=len(positives),retained_exploratory_points=len(retained),retained=retained,confirmed=confirmed,headline=headline,no_PDF=True,default_changed=False,costs=cost,catalogue=catalogue,seconds=time.perf_counter()-t);(R/'reviews/report_build.json').write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:v for k,v in rec.items() if k not in ['catalogue','costs','confirmed','retained']}),flush=True)
if __name__=='__main__':main()
