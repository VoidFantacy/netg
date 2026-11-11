from pathlib import Path
import json,csv,hashlib,datetime
REPO=Path(__file__).resolve().parents[4];R=Path(__file__).resolve().parents[1];E191=REPO/'entry_method_exploration/20261028_seven_dataset_scoring_v1';E193=REPO/'entry_method_exploration/20261029_adaptive_completion_gate_v1'
def read(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def csvrows(p):return list(csv.DictReader(p.open()))
def csvwrite(p,rr):
 with p.open('w') as f:
  w=csv.DictWriter(f,rr[0].keys());w.writeheader();w.writerows(rr)
def table(h,rr):return '| '+' | '.join(h)+' |\n| '+' | '.join(['---']*len(h))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rr)
oldpath=REPO/'entry_method_exploration/20261009_nsg_gt_m5_test_v1/analysis_v2/metrics.csv';densepath=E191/'analysis/all_dense_points.csv';assessmentpath=E191/'analysis/candidate_assessment.csv';old=csvrows(oldpath);dense=csvrows(densepath);assessment=csvrows(assessmentpath);evidence=[]
def select(rows,ds,K,method,L):
 found=[r for r in rows if r['dataset']==ds and int(r['K'])==K and r['method']==method and int(r['L'])==L];assert len(found)==1;return found[0]
def pair(campaign,a,b,source,mode):
 qkey='qps_median' if campaign=='E173' else 'qps';aq=float(a[qkey]);bq=float(b[qkey]);ar=float(a['recall_pct']);br=float(b['recall_pct']);assert a['dataset']==b['dataset'] and a['K']==b['K'] and a['n']==b['n'];assert aq>bq
 if mode=='DISCRETE_RECALL_QPS_DOUBLE_GAIN':assert ar>br
 else:assert br+1e-10>=ar
 evidence.append(dict(campaign=campaign,dataset=a['dataset'],K=int(a['K']),n=int(a['n']),method=a['method'],L=int(a['L']),recall_pct=ar,qps=aq,GT_method=b['method'],GT_L=int(b['L']),GT_recall_pct=br,GT_qps=bq,QPS_gain_pct=(aq/bq-1)*100,comparison_type=mode,source_csv=str(source.relative_to(REPO))))
for L,GL in [(800,1000),(1000,1200)]:pair('E173',select(old,'webvid2_5m_light_v1',1,'M5',L),select(old,'webvid2_5m_light_v1',1,'GT',GL),oldpath,'DISCRETE_RECALL_QPS_DOUBLE_GAIN')
for ds,K,m,L in [('coco',1,'REUSE-SQ',100),('coco',1,'REUSE-SQ',200),('coco',1,'REUSE-SQ',400),('flickr30k',1,'REUSE-SQ',200),('flickr30k',1,'REUSE-SQ',400),('webvid2_5m_light_v1',1,'B32',200),('webvid2_5m_light_v1',100,'B32',800),('coco',1,'B32',200),('coco',100,'B32',200)]:
 a=select(dense,ds,K,m,L);rr=[x for x in dense if x['dataset']==ds and int(x['K'])==K and x['method']=='GT10' and float(x['recall_pct'])+1e-12>=float(a['recall_pct'])];b=max(rr,key=lambda x:float(x['qps']));pair('E191',a,b,densepath,'FASTEST_MEASURED_GT_AT_OR_ABOVE_CANDIDATE_RECALL')
ret=[r for r in assessment if r['decision']=='RETAIN_EXPLORATORY'];nd=[r for r in ret if r['median_nondominated_in_available_grid']=='True'];assert len(ret)==12 and len(nd)==7
csvwrite(R/'positive_examples.csv',evidence);csvwrite(R/'E191_retained_12.csv',ret);csvwrite(R/'E191_retained_nondominated_7.csv',nd)
verdict=read(E193/'analysis/verdict.json');assert verdict['learned_GT10_or_B32_covered_cases']==6 and verdict['positive_gain_ideal_covered_cases']==0 and verdict['positive_gain_cases']==4
paths=[oldpath,densepath,assessmentpath,E191/'analysis/confirmed_screens.csv',E191/'report_zh.md',E193/'analysis/case_summary.csv',E193/'analysis/verdict.json',E193/'report_zh.md',REPO/'experiment_history/173_nsg_gt_m5_public_test_retest.md',REPO/'experiment_history/183_gt10_residual_comprehensive_v1.md',REPO/'experiment_history/176_m5_residual_completion_curve_v1.md']
dump(R/'source_manifest.json',[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in paths])
labels={'coco':'COCO','flickr30k':'Flickr30k','webvid2_5m_light_v1':'WebVid'}
rows=[[x['campaign'],labels[x['dataset']]+'/'+str(x['K']),x['method']+'/'+str(x['L']),f"{x['recall_pct']:.4f}% / {x['qps']:.2f}",str(x['GT_L']),f"{x['GT_recall_pct']:.4f}% / {x['GT_qps']:.2f}",f"+{x['QPS_gain_pct']:.2f}%"] for x in evidence]
rel=str(R.relative_to(REPO));catalog=f'''# 残差补全的历史有效场景与本轮结论适用范围

2026-10-29，按用户“同步结论，而且之前有补残差方法很有效，可以记下来”的要求回查原始CSV。只同步与整理，不新增ANN/训练/性能、PDF或默认变更。默认仍为E99 GT10。

## 当前总判断

残差补全已经在特定数据集/K/预算下出现实测有效结果。当前应保留“有效的条件性基线＋后端优化＋自适应开关”三项：有效基线是比较与改进的起点，后两项是允许并行的研究方向。E193仅验证一种固定SQ后端、三集两K和一组保留>=90%校准增益的门选择策略；该门6/6组被GT10或B32覆盖，不等于历史M5/B32/SQ全部无效，也未检验WebVid门控。

## 原始实测正面例子

所有数值均从对应同一次实验的原始CSV读取，Recall/QPS成对保留，不跨时期混拼。QPS均为原完整单线程计时。

{table(['实验','数据/K','残差方法/L','候选Recall/QPS','GT的L','GT Recall/QPS','完整QPS优势'],rows)}

E173前两行是已测离散点Recall和QPS同时提高：WebVid/K1原M5每hub最多8个ID，三hub最多24个候选精确补全。该结果只属于当时的图/模型/核/窗口，不能把旧绝对QPS拼入E191/E193，也不自动延伸K100/Yandex。

E191行按同窗口密集GT10网格，选达到或超过候选Recall的最快已测GT10作为速度阈值参照。除相同Recall的行外，候选Recall可以略低于该参照，不能将全部行称为严格双升或精确等Recall实验。例：COCO/K1 SQ L400与GT10 L693同为99.64%，QPS1072.26对817.09，+31.23%；COCO L100/200的阈值优势为+21.50%/+32.64%。

B32固定ID表也应保留：E191 WebVid/K1 L200为83.63%/1540.31，K100 L800为88.7857%/423.85；COCO/K1 L200为99.12%/2194.03，K100 L200为96.7159%/2132.96。它们提供实际有用的参照，E191的WebVid三个新SQ保留点恰被已有B32覆盖，说明应选择更强的已实现补全基线，而非否定残差路线。

## 已有筛选与边界

E191一次密集GT10控制后保留12个SQ探索点（COCO4/Flickr3/WebVid3/Deep1/GIST1），其中5个被已有B32/PQ覆盖，剩7个未被当时已测方法网格覆盖：COCO/K1 REUSE-SQ L100/200/400，Flickr/K1 MAIN-SQ L32、REUSE-SQ L200/400，Deep/K1 MAIN-SQ L32。Deep只新增4个命中，Flickr高Recall点事件少；“7点保留”不是7个通用方法或盲确认。B32尚缺同样密集的预算控制，所以不宣称这7点已胜过充分调参的B32。

E183记录WebVid与COCO的B32 K1/K100共同Recall区间曲线改善，Flickr交叉、Yandex K100不佳；折线描述不当新等Recall测量。E176相对原M5有组合省费/召回收益，但相对工程等价基线M5OPT，残差新增0/20严格双升；工程省费与残差质量贡献仍需分开。

E193的GT知情全收益理想门在4个有增益组上未被当前网格覆盖，支持研究选择性补全的价值；它不可部署，也不是所有质量取舍下的最优上界。实际廉价门尚未兑现，不据其有限候选负结果禁止其他后端、其他门或更强特征。

以上公共query历史曝光、一图/画像，默认不改。旧共享证明仍限定候选支持/固定源，不将跨数据差别简单归因共享。未来以这些有效配置作为独立参照，再验证后端成本与门控增量；不将缺乏普适替换结论写成缺乏局部效果。

## 原始证据

- [11组原始点摘录](positive_examples.csv)、[E191保留12点](E191_retained_12.csv)、[7个有限网格未覆盖点](E191_retained_nondominated_7.csv)、[输入SHA](source_manifest.json)。
- [E173详细卡片](../../173_nsg_gt_m5_public_test_retest.md)、[E183详细卡片](../../183_gt10_residual_comprehensive_v1.md)、[E191详细卡片](../../191_seven_dataset_scoring_v1.md)。
- [E193结论](../../../entry_method_exploration/20261029_adaptive_completion_gate_v1/report_zh.md)与本记录各保留原时点身份，旧seal不回写；旧根文档由本目录source_before按SHA迁移读取。
'''
# R is experiment_history/_maintenance/<slug>; ../../../ reaches repo.
(R/'conclusion_zh.md').write_text(catalog)
(R/'README.md').write_text(f'''# 2026-10-29 残差正面证据同步

用户要求同步结论并记住以前有效的残差补全。当前结论见[总结](conclusion_zh.md)，原始点见[CSV](positive_examples.csv)。本次没有新实验编号或新性能；同步summary/spec/s-target/s-experiment/接续入口和历史目录，保留E193原根字节与seal桥接。

修改前7份根文档在[source_before](source_before/)，原始证据身份见[source_manifest](source_manifest.json)。E193旧seal核验映射与本次验收将在validation中记录，旧科学文件和manifest不回写。长期记忆仅按用户明确授权追加一份ad_hoc note，不改原MEMORY.md。
''')
# Synchronize current view without changing old experiment reports or sealed cards.
p=REPO/'summary.md';s=p.read_text();anchor='E192的严格结论仍有效：';addition=f'''历史有效场景继续保留，不能被本轮有限门模型的负结果覆盖。E173原M5在WebVid/K1有两组实际跨L双升（+24.25%/+19.25% QPS）；E191的COCO/K1 REUSE-SQ在L100/200/400对密集GT10质量阈值参照有+21.50%/+32.64%/+31.23%完整QPS优势。B32在WebVid/COCO也有实用价值，E191的部分新SQ点正是被更强B32覆盖。12个密集GT10后保留点中7点未被当时已测其他方法覆盖，但有限网格/稀少事件/公共曝光限制仍在，未替换默认。原始Recall/QPS、具体B32点及比较类型统一见[历史有效场景]({rel}/conclusion_zh.md)。

''';assert anchor in s;s=s.replace(anchor,addition+anchor,1);s=s.replace('尚未把理想开关空间变成可靠的净收益。','尚未把理想开关空间变成可靠的净收益；这仅限E193当前门与SQ后端，不外推所有历史补全方法。');p.write_text(s)
p=REPO/'s-target.md';s=p.read_text();anchor='1. 对理想开关';addition=f'''后继以[已有有效基线]({rel}/conclusion_zh.md)为起点：WebVid/COCO的固定ID B32、COCO/K1 SQ，以及当时保留的具体配置均应继续作参照。E193只测当前SQ条件门，未检验WebVid门控；不能用该有限结果否定其他有效后端。后端优化与自适应可以并行，后续须证明相对更强已有补全的增量。

''';assert anchor in s;s=s.replace(anchor,addition+anchor,1);p.write_text(s)
p=REPO/'spec.md';s=p.read_text();anchor='## 5. 指标、计时与证据';addition=f'''已有补全实现继续保留各自身份：M5三hub至多24个固定ID候选、B32单位query-target表、REUSE-SQ/MAIN-SQ块源均见各原合同。E193只对冻结REUSE-SQ新增条件调用，并未替换或穷尽这些后端。历史有效配置与原始费用见[证据目录]({rel}/conclusion_zh.md)，属于结果索引，不新增实现或默认依赖。

''';assert anchor in s;s=s.replace(anchor,addition+anchor,1);p.write_text(s)
p=REPO/'s-experiment.md';s=p.read_text();anchor='## 最近研究与当前依赖';addition=f'''2026-10-29结论同步：[历史有效残差场景]({rel}/conclusion_zh.md)单列E173 M5、E191 B32/SQ的实际正面证据和边界。E193有限门控未过门不撤销这些结果；本次纯整理，无新性能。

''';s=s.replace(anchor,addition+anchor,1);p.write_text(s)
p=REPO/'LOCAL_CODEX_START.md';s=p.read_text();s=s.replace('收益集中成立，',f'历史有效残差基线读[单列证据]({rel}/conclusion_zh.md)：WebVid原M5/B32、COCO B32/K1 SQ等局部结果继续保留；E193有限门失败不表示这些方法无效。\n\n收益集中成立，',1);s=s.replace('区分增量可救性、理想参考、可部署特征和付费收益','保留历史有效配置，区分增量可救性、理想参考、可部署特征和付费收益');p.write_text(s)
p=REPO/'experiment_history/README.md';s=p.read_text();anchor='## 全部详细卡片';addition='[2026-10-29残差正面证据同步](_maintenance/20261029_residual_positive_evidence_sync_v1/README.md)保留历史M5/B32/SQ有效场景，与E193有限门控负结果分别陈述；只读旧实测整理，无新实验。\n\n';s=s.replace(anchor,addition+anchor,1);p.write_text(s)
print('SYNCED_POSITIVE_RESIDUAL_EVIDENCE',len(evidence),'examples;',len(ret),'retained;',len(nd),'nondominated')
