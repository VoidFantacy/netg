from pathlib import Path
import csv
R=Path(__file__).resolve().parents[1]
def read(name):return list(csv.DictReader((R/'analysis'/name).open()))
A=read('stage_attribution_four_multimodal.csv');S=read('stage_effects_and_costs.csv');P=read('original_point_metrics.csv')
DS=['coco','flickr30k','webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1'];CN=dict(zip(DS,['COCO','Flickr30k','WebVid','Yandex']))
LS=[100,128,200,400,800,1000,1200]
def get(rows,ds,L):return next(x for x in rows if x['dataset']==ds and int(x['L'])==L)
def fmt(x,d=2):return '—' if x in ['',None] else f'{float(x):.{d}f}'
def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)+'\n'

t='''# GT10与B32分别解决了多少低于10%的查询

2026-11-05。按用户定义，“几何迷失率”在本报告中指**单条Recall@100严格低于10%的查询比例**。两阶段都能使部分查询脱离低召回：在当前四多模态数据中，GT10主要修复WebVid、Yandex的严重低召回；B32对WebVid的小预算有补充，对Yandex补充很少。COCO/Flickr的B32平均召回收益主要来自常规遗漏补回。

**本轮不做PDF。** 已有逐查询结果足够，无需补搜索实验。复用E183完整窗口（COCO/WebVid/Yandex各10,000条，Flickr5,000条），覆盖七个L；不是E199两个512条窗口的新确认。三阶段为原NSG→GT10→GT10+B32，B32为完整16K固定ID表，保留原任务metric、图与固定家族。旧与新绝对时间不混拼。

## 1. 口径及两阶段的分母

- 命中0–9个原GT100成员计为低召回，恰好10个排除。救出指从0–9升到至少10；不等于达到90%或找齐100个。
- GT10救出率的分母为原NSG低召回队列；B32救出率的分母为GT10之后的低召回队列。两个百分比不能当作同一任务难度下的独立模型比较。
- 同时统计救出与新增低召回。`后续低召回数 = 原低召回数 − 救出数 + 新增数`。净失败率下降以全部query为分母。
- 这里用“几何迷失”作用户指定的操作标签；统计本身不分辨路由、搜索预算、图结构等成因。顺序分解是记账，不是两个方法作用独立的因果贡献。

若F是原低召回比例、s是其中被救出的比例、新增低召回为u条、总查询为N，则`低召回比例净下降 = F × s − u/N`（比例使用0–1单位）。原迷失率高只提供更大潜在空间，实际下降还取决于能救出的比例及新增损伤。

## 2. L200：GT10完成大部分净下降，B32有条件追加

'''
rows=[]
for ds in DS:
    a=get(A,ds,200)
    rows.append([CN[ds],a['n'],f"{a['NSG_low']} / {fmt(a['NSG_low_pct'])}%",f"{a['GT10_low']} / {fmt(a['GT10_low_pct'])}%",f"{a['B32_low']} / {fmt(a['B32_low_pct'])}%",a['GT10_rescued']+' / '+a['GT10_new_low'],a['B32_rescued']+' / '+a['B32_new_low']])
t+=table(['数据','查询总数','NSG低召回','GT10低召回','GT10+B32低召回','GT10救出 / 新增','B32再救出 / 新增'],rows)
t+='''WebVid：GT10救出113/142（79.58%），同时新增24条，净减少89条，失败率下降0.89个百分点；B32再救7/53（13.21%），无新增，失败率再下降0.07个百分点。净下降合计96条，按当前顺序记账GT10贡献89条、B32贡献7条。

Yandex：GT10救出128/174（73.56%），同时新增40条，净减少88条；B32再救1/86（1.16%），无新增，净减少1条。失败率依次为1.74%→0.86%→0.85%。

COCO：原NSG在此L没有低召回查询，GT10新增1条，B32未修复。Flickr三阶段均为0/5,000；零队列无法评估救出率，不能写成“0%有效”。

![全L失败率](figures/01_failure_rate_all_L.png)

## 3. B32救回的是原NSG遗留，还是GT10新增问题

![L200三阶段来源分解](figures/03_L200_source_decomposition.png)

WebVid原NSG低召回142条，其中113条由GT10救出，剩29条；GT10另外新增24条，形成53条队列。B32从原NSG遗留中救出5条、从GT10新增中救出2条。最终仍有24条原NSG遗留与22条GT10新增，共46条。

Yandex原NSG174条中，GT10救出128条、遗留46条，再新增40条，形成86条。B32只修复其中1条原NSG遗留问题；最终45条遗留＋40条GT10新增＝85条。

本次全部七集七L中，未观察到B32新增低召回查询；这是现有返回的观测，不是数值实现永不损伤或搜索单调性的保证。GT10在多处会救出一些查询、同时使另一些查询落入低召回，不能只报救出数。

## 4. 不同预算：不能把L200结论推广到所有L

下表中每格为原窗口中的查询数，顺序固定为NSG→GT10→GT10+B32。

'''
t+=table(['数据']+['L'+str(L) for L in LS],[[CN[ds]]+[f"{get(A,ds,L)['NSG_low']}→{get(A,ds,L)['GT10_low']}→{get(A,ds,L)['B32_low']}" for L in LS] for ds in DS])
t+='''WebVid的B32额外救出数依次为48、30、7、4、0、0、0条；救出率分别为25.00%、22.56%、13.21%、20.00%、0%、0%、无定义。末项GT10原队列已为空，不能当作0%救出率。Yandex依次为0、0、1、1、1、1、1条。

COCO在L100/128有1→2→2条，在L200/400为0→1→1条，L800及以上均0；Flickr七个预算都没有低召回事件。这些稀疏尾部不足以支持数据集天然“适合/不适合”的普遍结论。相同query在多个L重复出现，不能把逐L救出数相加称为独立救出人数。

![救出与新增](figures/02_rescued_and_introduced.png)

## 5. 与平均Recall收益有什么关系

低召回占比、低召回队列救出率、平均Recall是不同指标。平均Recall的变化可按本阶段之前的低召回队列与其他query精确相加：

`平均Recall净增益 = 原低召回群体贡献 + 其他查询贡献`。

以下均为L200，单位是Recall百分点；“原低召回”对GT10指原NSG队列，对B32指原GT10队列。

'''
rows=[]
for ds in DS:
    for stage,label in [('GT10_vs_NSG','GT10相对NSG'),('B32_vs_GT10','B32相对GT10')]:
        s=get([x for x in S if x['stage']==stage],ds,200)
        rows.append([CN[ds],label,fmt(s['net_recall_gain_from_reference_low_pp'],4),fmt(s['net_recall_gain_from_other_queries_pp'],4),fmt(s['mean_recall_gain_pp'],4)])
t+=table(['数据','阶段','原低召回群体贡献','其他query贡献','总平均Recall变化'],rows)
t+='''COCO的B32平均Recall增加1.3715个百分点，却没有救出那1条低召回query；全部13,715个新增命中来自原本Recall≥10%的query。Flickr没有低召回队列，仍有0.4280个百分点平均增益。

WebVid的B32救回20,257个GT成员，仅75个来自原低召回队列，占0.37%；Yandex为8/570（1.40%）。所以当前B32的平均收益主要来自常规遗漏补回，而不是严重低召回查询越过门槛。

对固定ID表而言，低召回本身不保证遗漏目标就在表中；当前训练源是否支持这些目标、三个路由是否取到、每行32个容量是否保留，决定了可补回的候选。它们与低召回率是不同环节。

GT10的收益结构不同：WebVid平均Recall净增1.1877个百分点，其中原NSG低召回群体贡献0.6905；Yandex原低召回群体贡献1.1077，但其他query净损失0.4004，合计只增加0.7073。尾部改善可以与其他query损伤同时出现，不能用平均数代替队列转移。

![低召回修复与平均收益](figures/04_tail_repair_vs_mean_recall.png)

## 6. 完整成本与判断边界

同L只用于分开记账，不能当成等费用结论。下表引用E183原三轮完整单线程QPS的中位数及对应每query耗时差；没有重新计时。B32的“额外救出”还须支付候选评分/合并费用，不能仅按少量尾部救出来宣称前沿胜出。

'''
rows=[]
for ds in DS:
    vals={m:next(x for x in P if x['dataset']==ds and x['L']=='200' and x['method']==m) for m in ['NSG','GT10','B32']}
    b=get([x for x in S if x['stage']=='B32_vs_GT10'],ds,200)
    rows.append([CN[ds],fmt(vals['NSG']['complete_qps']),fmt(vals['GT10']['complete_qps']),fmt(vals['B32']['complete_qps']),fmt(b['complete_extra_us']),fmt(b['complete_qps_change_pct'])+'%'])
t+=table(['数据','NSG完整QPS','GT10完整QPS','GT10+B32完整QPS','B32额外µs/query','B32 QPS变化'],rows)
t+='''完整Recall–QPS是否值得采用仍需对照附近搜索预算；这里不由同L表推导等费用优势，也不把E183绝对QPS拼入E199新窗口。当前默认保持GT10，已停止双塔/门控分支没有恢复。

## 7. 来源、核验与可下载数据

本分析覆盖原七集147个K100点、49个三阶段组合、392个状态计数、98个阶段比较；四多模态为主表，非多模态仅保留已有数据附录。读取旧封存NPZ作向量化分析，再用独立stdlib集合实现从原GT和真实timed返回逐条复算全部147点、三阶段状态及平均收益分解，原163项输入SHA全部复核。独立指同执行者的不同实现与数据读取路径，不是独立人员或新盲样本。

- [四多模态全L阶段分解CSV](analysis/stage_attribution_four_multimodal.csv)
- [七集全L附录CSV](analysis/stage_attribution_all_datasets.csv)
- [救出、平均召回与完整成本CSV](analysis/stage_effects_and_costs.csv)
- [三阶段八种状态计数](analysis/three_stage_paths.csv)
- [低召回query索引与三阶段命中数](analysis/low_query_transitions.csv)
- [原三轮完整指标引用](analysis/original_point_metrics.csv)
- [分析收据](analysis/analysis_receipt.json) · [原GT/实际返回第二实现核验](reviews/raw_audit.json)
- [固定口径](protocol.md) · [来源与修改前根文档](source_before/identity.json) · [交付收据](delivery_validation.json)

没有新增ANN、GT、训练、模型、计时或PDF；必要补实验的授权本次未触发，因为旧保存结果已经完整覆盖所问比较。原E183/E184、旧报告/源码/模型/raw/seal/manifest均保持原件，根文档修改单独保留字节桥接。
'''
(R/'report_zh.md').write_text(t)
(R/'README.md').write_text('''# GT10与B32低召回分阶段分析

2026-11-05。按用户定义，低召回是单条Recall@100<10%（命中0–9，恰好10排除）。[完整中文分析](report_zh.md)对照原NSG→GT10→GT10+B32，报告救出、新增、净变化、B32救出来源及与平均召回/完整成本的关系。

主要四个多模态集，全七个L；使用E183原完整窗口，已另从原GT与实际返回复核。没有补做搜索实验，不生成PDF。

- [四集全L失败率图](figures/01_failure_rate_all_L.png) · [SVG](figures/01_failure_rate_all_L.svg)
- [两阶段救出与新增图](figures/02_rescued_and_introduced.png)
- [L200原NSG遗留 / GT10新增问题分解](figures/03_L200_source_decomposition.png)
- [低召回修复与平均Recall收益](figures/04_tail_repair_vs_mean_recall.png)
- [全L阶段分解CSV](analysis/stage_attribution_four_multimodal.csv) · [七集附录](analysis/stage_attribution_all_datasets.csv)
- [原始返回独立实现核验](reviews/raw_audit.json) · [交付收据](delivery_validation.json)

L200核心计数：COCO 0→1→1，Flickr 0→0→0，WebVid 142→53→46，Yandex 174→86→85。GT10有救出也有新增；B32在WebVid额外救出的7条中，5条为原NSG遗留、2条为GT10新增。当前默认、研究停止边界及旧报告原件保持。
''')
print('Wrote Chinese analysis, all-L tables, costs and evidence links; no PDF')
