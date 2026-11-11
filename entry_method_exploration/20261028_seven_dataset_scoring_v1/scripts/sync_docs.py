import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];REL='entry_method_exploration/'+R.name
LABEL={'deep10m_l2_v1':'Deep10M','sift10m_bigann_l2_v1':'SIFT10M','gist1m_l2_v1':'GIST1M','coco':'COCO','flickr30k':'Flickr30k','webvid2_5m_light_v1':'WebVid','yandex_t2i_official10M_ip_v1':'Yandex'}
def main():
 rec=json.loads((R/'reviews/report_build.json').read_text());points=list(csv.DictReader((R/'analysis/all_primary_points.csv').open()));covers=list(csv.DictReader((R/'analysis/all_coverage.csv').open()));pairs=list(csv.DictReader((R/'analysis/all_paired.csv').open()));ret=rec['retained'];total=448+rec['dense_points'];batches=1344+rec['dense_batches'];headline=rec['headline'];get=lambda ds,K,m:next(x for x in points if x['dataset']==ds and x['K']==str(K) and x['method']==m and x['L']=='200')
 overview='| 数据 | K | GT10 Recall/QPS | REUSE-SQ Recall/QPS | MAIN-SQ Recall/QPS |\n| --- | --- | --- | --- | --- |\n'
 for ds in LABEL:
  for K in [1,100]:
   overview+='| '+LABEL[ds]+' | '+str(K)+' | '+' | '.join(f"{float(get(ds,K,m)['recall_pct']):.4f}% / {float(get(ds,K,m)['qps']):.2f}" for m in ['GT10','REUSE-SQ','MAIN-SQ'])+' |\n'
 decision=('保留密集控制后通过的对应数据/K/L/来源候选，先看实际费用、救损和跨点一致性；不等于全局默认替换。' if ret else '本固定版本没有在密集同窗口控制后建立通过探索门的场景；来源覆盖、筛选质量和费用结论分别保留。')
 source=[]
 for ds in LABEL:
  p=next(x for x in covers if x['dataset']==ds and x['K']=='100' and x['L']=='200' and x['method']=='REUSE-PQ');s=next(x for x in covers if x['dataset']==ds and x['K']=='100' and x['L']=='200' and x['method']=='REUSE-SQ');z=next(x for x in pairs if x['dataset']==ds and x['K']=='100' and x['L']=='200' and x['method']=='REUSE-SQ');source.append(f"{LABEL[ds]}：原遗漏{s['members_missing']}，扫描覆盖{s['scanned_covered']}，PQ→SQ短名单覆盖{p['shortlist_covered']}→{s['shortlist_covered']}，SQ实际救回{s['rescued']}，其中旧16K残差源外{z['rescued_source_out']}。")
 summary=f'''# ACSG 当前结论

更新于2026-10-28启动的E191交付。默认E99 GT10保持：WebVid GT10-soft-t1、Yandex GT10-hard。[七集两K综合测试]({REL}/report_zh.md)已完成。{headline}

{decision} 固定矩阵及一次密集补充收口，无待恢复队列。

## 本轮L200完整表现

{overview}

QPS为E191同一可执行程序的完整单线程三轮中位数；不拼接E190/E183绝对速度。补充只与同一补充窗口控制比较。完整B32/PQ及全L原表见报告/CSV。

## K100/L200覆盖与来源

'''+ '\n\n'.join(source)+f'''

REUSE-PQ/SQ逐query pool、扫描块顺序一致；MAIN-SQ不读训练遗漏块表，但主返回信息和实际访问量同时变化，不是纯共享因果消融。K1只用真实一个主返回。新法跨K固定共享K100教师表/96追加精算上限，不称各K最优。旧B32是16K参考，新块表前12K，无配置选择。

## 核验与限制

全部448原点/1344轮和{rec['dense_points']}密集点/{rec['dense_batches']}轮实际timed包、三轮bits/SHA、全量主包补全oracle、逐query预算和扫描一致性通过；stdlib第二实现复算全部质量/救损/覆盖链/严格0–9命中失败/预算比较。140资格点、历史返回、训练表与编码另核验；不同实现同一执行者，非独立人员复现。

共享强弱来自旧E185观测，不是人工因果分组。源外指旧16K残差ID源外，不等于从未出现于任何监督。单图/画像、公共test历史曝光，无新系统盲确认；GIST仅1K，Flickr5K。SQ8/PQ内存和完整费用分别付齐；无分段耗时归因或总NDC测量，次数不当耗时比例。旧E190科学seal保持。

用户未要求PDF，本轮未生成PDF。新增大产物/root/acsg-e191-storage经项目storage链接，原timed包raw保留，trace无损gzip及原SHA可重放。

[详细文字报告]({REL}/report_zh.md) · [全部原点]({REL}/analysis/all_primary_points.csv) · [确认筛选]({REL}/analysis/confirmed_screens.csv) · [来源分层]({REL}/analysis/all_source_strata.csv) · [下一门](s-target.md) · [历史](s-experiment.md)。
'''
 (REPO/'summary.md').write_text(summary)
 p=REPO/'spec.md';s=p.read_text();lo=s.index('### 4.6 E191');hi=s.index('## 5. 指标、计时与证据',lo);contract=f'''### 4.6 E191七集两K综合实现

[源码]({REL}/src/benchmark.cpp)沿E183冻结主核/加载/路由/完整计时，支持真实K1/K100。GT10/B32控制与旧实际包一致；REUSE-PQ/SQ相同pool/扫描ID，MAIN-SQ仅真实主返回块。K1不暗取100返回。K100教师块表前12K拟合，每hub8块，跨K固定共用；B32原16K表只作正式参考。

COCO/Deep复用E188/E189块/表，其余同机制在全base建立coarse1024/global PQ/最多128点块。Yandex d200适配M20，其余M16；原metric不变。SQ8原C++Faiss QT_8bit minmax全base训练、无query/GT；码按block ID顺序。REUSE扫描≤2048、MAIN实际≤1024/K1仅一块，各最多96原metric追加精算并严格合并。计数分别保存PQ/SQ/块中心/追加精算，不是总NDC。

正式原矩阵448点/1344轮，另一次密集{rec['dense_points']}点/{rec['dense_batches']}轮，预热256、3轮实际包bits/SHA与全量补全oracle。每集正式结束后才分析/二实现核验/无损gzip trace，再串行下一集；不并发数值工作。实际timed返回原raw保持，trace为wall外实际主包的全排序重建并保留未压缩SHA；io_data.read_array透明解压重放。

模型与结果在/root/acsg-e191-storage，项目storage链接明确索引；共享benchmark RSS不等于默认依赖或单独部署增量。新五集PQ编码有完整消费向量流SHA；复用资产/大base及图沿旧来源并核stat，小输入/模型/库/二进制完整SHA见[freeze]({REL}/freeze.json)。补充身份见[dense freeze]({REL}/dense_freeze.json)。当前用户要求无PDF，文字/CSV/PNG/SVG交付；结论见[report]({REL}/report_zh.md)。

''';p.write_text(s[:lo]+contract+s[hi:])
 target=f'''# ACSG 后续研究问题

E191七集两K全面测试已完成：原448点/1344完整T1轮，密集补充{rec['dense_points']}点/{rec['dense_batches']}轮。无待恢复矩阵，默认E99 GT10保持，无PDF。目标仍为可靠Recall–QPS综合改进。

## 当前证据与候选

{headline}

{decision}

具体场景读[确认筛选]({REL}/analysis/confirmed_screens.csv)，全七集两K读[详细报告]({REL}/report_zh.md)。不能用共享组有效代表低共享组有效，不能用一个L未通过否定全部方向。

## 下一门（提案，未启动）

'''
 if ret:target+='1. 对密集控制后保留的数据/K/L/来源冻结部署配置和费用，再用合法未参与选择的新查询/图实例确认；已有公共test不能改称盲确认。先处理损伤、重复向量/ID和跨相邻预算一致性。\n'
 else:target+='1. 保留本轮所有来源/排序/费用证据，优先选择有可支付空间的具体问题；低覆盖场景先看来源，已保住扫描内目标的场景先看完整费用。不自动扩大表、预算或量化参数到通过。\n'
 target+='2. 需要更广候选来源时，先在合法开发query上诊断全块代表检索在固定访问预算的覆盖机会，再决定是否实现块代表ANN；只读精确诊断不是免费线上方法。\n3. 若考虑更低费用的评分实现，先核解码/访存/筛选成本并验证返回语义，再完整T1复测；采用新编码或选择器另立冻结版本。若研究逐query跳过，先验证收益异质性与廉价特征可预测性。\n\n任何后继不回改E191/E190科学seal。保留不补全、B32和同窗口密集GT10控制；新确认不得参与选择。当前授权已完成，无自动追加队列。\n';(REPO/'s-target.md').write_text(target)
 p=REPO/'s-experiment.md';s=p.read_text();s=s.replace('E191七集两K综合矩阵正在执行；最近已完成正式性能为E190 COCO/K100固定候选排序实验','最新完成E191七集两K综合矩阵；E190为此前COCO/K100固定候选实验');old=next(z for z in s.splitlines() if z.startswith('| E191 |'));s=s.replace(old,f"| E191 | 七集两K来源与评分综合测试 | 原448点/1344T1＋密集{rec['dense_points']}点；保留探索筛选{rec['retained_exploratory_points']}点，默认不变，无PDF | [卡片](experiment_history/191_seven_dataset_scoring_v1.md) |");p.write_text(s)
 card=f'''# E191：七数据集、两K的来源与评分综合测试

2026-10-28用户要求“测试的全一点，给出详细的结论”，此前明确无要求不做PDF。本轮无PDF。{headline}

{decision}

覆盖COCO/Flickr/WebVid/Yandex/Deep/SIFT/GIST，原图/metric/GT10/GT保持。GT10、旧B32、REUSE-PQ/SQ、MAIN-SQ真实K1/K100；K1只一个主返回，固定K100教师前12K入口块表跨K共享。共享强弱沿E185旧观测，不构成人工因果分组。

REUSE-PQ/SQ逐query pool/扫描块一致，≤2048码/96追加原metric精算。MAIN-SQ无训练遗漏表，实际访问量也不同。SQ8全base无query/GT训练；新global PQ通常M16，Yandex适配M20。原矩阵不选超参，对表面阳性按协议一次冻结密集GT10控制并同窗口重测，原筛选/窗口保留，不混拼绝对速度。

全量actual timed包三轮bits/SHA、主包补全oracle、预算、源外/源内救损/严格失败和stdlib复算通过。140资格点、56历史前缀、训练表行及编码另核验。旧E190 seal保持；同执行者不同实现，非独立人员/新盲确认。大产物/root/acsg-e191-storage独立目录，实际返回raw保持，trace无损gzip保留原SHA。

[完整文字报告](../{REL}/report_zh.md) · [全部原点](../{REL}/analysis/all_primary_points.csv) · [密集点](../{REL}/analysis/all_dense_points.csv) · [确认筛选](../{REL}/analysis/confirmed_screens.csv) · [协议](../{REL}/protocol.md) · [冻结](../{REL}/freeze.json) · [密集冻结](../{REL}/dense_freeze.json)。
''';(REPO/'experiment_history/191_seven_dataset_scoring_v1.md').write_text(card)
 p=REPO/'experiment_history/README.md';s=p.read_text();s=s.replace('最新正式实验是[E190](190_coco_fixed_candidate_scoring_v1.md) COCO/K100固定候选评分','最新正式实验是[E191](191_seven_dataset_scoring_v1.md)七集两K来源与评分综合测试');s=s.replace('| [190_coco_', '| [191_seven_dataset_scoring_v1.md](191_seven_dataset_scoring_v1.md) | E191：七集两K来源与评分综合测试，无PDF |\n| [190_coco_',1);p.write_text(s)
 start=f'''# ACSG 当前接续入口

工作区/data/netg/ACSG，分支research/state-20261002，HEAD 96cf05d5410cf51272048cd1f90b4bb194e23c62，近期成果主要未提交。2026-10-28启动的E191已完成，无待恢复矩阵，默认E99 GT10保持。

先读[AGENTS](AGENTS.md)、[summary](summary.md)、[spec](spec.md)、[s-target](s-target.md)、[s-experiment](s-experiment.md)，再读[E191报告]({REL}/report_zh.md)、[原448点]({REL}/analysis/all_primary_points.csv)、[密集点]({REL}/analysis/all_dense_points.csv)、[确认筛选]({REL}/analysis/confirmed_screens.csv)和[state]({REL}/state.json)。

{headline}

七集原metric/图/GT10保持，真实K1/K100，K1只一个主返回；共享强弱只是旧观测。覆盖链、源外救回、费用和预算前沿分别看；MAIN-SQ无训练遗漏表但仍继承GT10监督。不同实现同执行者，公开test历史曝光，无新系统盲确认。

用户明确没有要求就不做PDF，本轮无PDF。新增大产物/root/acsg-e191-storage（storage链接）；保留实际timed raw，trace gzip保留原SHA。旧E190/E191 seal保持，不自动重跑、扩预算或修改默认。

可复制接续：请只读核当前分支/HEAD与根文档，再读E191报告和确认筛选。448点/1344轮原矩阵与一次密集补充已结束，无待恢复队列。按我的当前明确任务继续，未经要求不生成PDF。
''';(REPO/'LOCAL_CODEX_START.md').write_text(start);print('PASS E191 roots/history synchronized')
if __name__=='__main__':main()
