#!/usr/bin/env python3
"""Document completed measurements without running search or training."""
from pathlib import Path
import json, re, shutil

EXP=Path(__file__).resolve().parents[1]
ROOT=EXP.parents[1]
PUB=Path('/data/netg/ACSG-publish-20261009')
REL=EXP.relative_to(ROOT).as_posix()
SNAP='research_snapshots/20261009_nsg_gt_m5'
data=json.loads((EXP/'analysis_v2/metrics.json').read_text())
state=json.loads((EXP/'run_state_v2.json').read_text())
assert data['status']=='COMPLETE_TRUE_PUBLIC_TEST_NSG_GT_M5_60_POINTS'
assert len(data['points'])==60 and sum(j['completed_timed_batches'] for j in state['jobs'])==180
assert all(j['status']=='COMPLETED' and j['exit_code']==0 for j in state['jobs'])
lookup={(p['dataset'],p['K'],p['L'],p['method']):p for p in data['points']}
web='webvid2_5m_light_v1'
cross=[]
for a,b in [(800,1000),(1000,1200)]:
    m=lookup[(web,1,a,'M5')]; g=lookup[(web,1,b,'GT')]
    cross.append({'dataset':web,'K':1,'M5_L':a,'GT_L':b,'M5_recall_pct':m['recall_pct'],'GT_recall_pct':g['recall_pct'],
                  'M5_qps_median':m['qps_median'],'GT_qps_median':g['qps_median'],
                  'median_qps_change_pct':100*(m['qps_median']/g['qps_median']-1),
                  'three_round_ranges_separated':m['qps_min']>g['qps_max']})
cost={'new_training_seconds':0,'preflight_io_seconds':json.loads((EXP/'data_preflight.json').read_text())['io_preflight_seconds'],
      'discarded_v1_native_seconds':315.365954365,'formal_batches':180,'formal_points':60,
      'datasets':{j['dataset']:{'formal_timed_wall_seconds':sum(sum(p['wall_seconds']) for p in data['points'] if p['dataset']==j['dataset']),
                               'native_seconds_with_startup_and_audits':j['seconds_with_startup_and_audits']} for j in state['jobs']},
      'cost_scope':'test costs only; no claim that old full training met the 7200-second budget'}
(EXP/'delivery_costs.json').write_text(json.dumps(cost,ensure_ascii=False,indent=2)+'\n')
(EXP/'observed_cross_L_comparisons.json').write_text(json.dumps({'scope':'two discrete measured WebVid Recall@1 pairs; no interpolation or parameter tuning', 'pairs':cross},ensure_ascii=False,indent=2)+'\n')

conclusion='''本轮已完成 **60 个实测点、180 批单线程正式计时**，每点全部 10000 条查询计算真实 Recall。**M5 正在研究**，结构为 GT10 入口路由与主搜索之后的冻结残差表补全。

相对 NSG，同 L 的 GT10 和 M5 在 20 个场景点的 Recall 与 QPS 中位数均更高。两者分别有 19/20 点的三轮配对速度均更高；GT 的 WebVid K100 L800、M5 的 WebVid K100 L1200 各有一轮速度低于 NSG，不能说每轮都提高。

相对 GT10，同 L 的 M5 在 20/20 点提高 Recall，真值近邻成员损伤为 0；配对 QPS 中位变化均为负，下降约 0.16%–4.85%。WebVid Recall@1 提高 0.97–1.92 个百分点，Recall@100 提高 0.4134–0.6308 个百分点；Yandex 分别提高 0.01–0.09、0.0042–0.0254 个百分点，增益很小。

WebVid Recall@1 有两个离散实测的综合优势：M5 L800 为 91.94%、414.37 QPS，GT L1000 为 91.66%、333.49 QPS；M5 L1000 为 92.68%、332.23 QPS，GT L1200 为 92.33%、278.59 QPS。按 QPS 中位数比，分别约快 24.25%、19.25%，三轮速度范围分离。其余三个数据集/K 场景没有这样的跨 L 实测优势；未据连线插值推导等 Recall 吞吐。

这次复测支持 M5 的 WebVid Recall@1 局部价值，尚未确立跨数据集、双 K 的稳定综合替代。继续保留 WebVid GT10-soft-t1、Yandex GT10-hard 默认；M5 标为正在研究。本轮没有新增训练、选择集筛选或按 test 调参。测试来自有历史曝光的公共窗口，不称新盲测。
'''

report=EXP/'analysis_v2/report.md'
old=report.read_text()
assert '## 本轮结论' not in old
shutil.copy2(report,EXP/'analysis_v2/report_tables.original.md')
first,rest=old.split('\n',1)
report.write_text(first+'\n\n## 本轮结论\n\n'+conclusion+'\n'+rest+'\n## 本轮成本\n\n'+
    '正式计时 wall 合计：WebVid 1987.31 秒，Yandex 2039.06 秒；各 native 作业含加载、暖机和核验分别 2693.72 秒（44.90 分钟）、2770.95 秒（46.18 分钟）。另计完整输入 SHA 预检 160.77 秒、弃用 v1 作业 315.37 秒。新增训练 0 秒，历史训练成本与超预算记录保持原身份；本轮耗时不能替代历史完整训练成本。见 [成本记录](../delivery_costs.json)。\n\n'+
    '曲线：[Recall–QPS](../figures_v2/recall_qps_nsg_gt_m5.png)、[按实际 L 对比](../figures_v2/recall_qps_vs_L_nsg_gt_m5.png)。完整数据、图和评估脚本来自同一 v2 网格。\n')

blocks={
'summary.md':f'''2026-10-09：E173 已完成两集×三方法×两 K×五 L 的 60 点、180 批完整单线程复测，**M5 正在研究**，基于 GT10 增加冻结残差补全。WebVid/Yandex 各公共 test 前 10K；L=200/400/800/1000/1200，K=1/100 分别真实搜索。无新训练或 test 调参。

同 L 相对 GT，M5 的 20 点 Recall 全部提高、真值近邻成员损伤 0，QPS 配对中位约降 0.16%–4.85%。WebVid K1 提高 0.97–1.92 pp；Yandex 提升很小。WebVid K1 的 M5 L800 相对 GT L1000、M5 L1000 相对 GT L1200 有实测双升，QPS 中位比约 +24.25%、+19.25%；其他三场景没有跨 L 实测双升。相对 NSG，同 L 的 GT/M5 全部 20 点 Recall 与 QPS 中位数均更高，各 19/20 点三轮配对速度都提高。默认保留 GT，不据本轮局部优势宣称 M5 全面替代。

先读[本轮结论与网页阅读入口]({SNAP}/README.md)，再读[完整实验报告]({REL}/analysis_v2/report.md)、[五档曲线]({REL}/figures_v2/recall_qps_nsg_gt_m5.png)、[全部60点CSV]({REL}/analysis_v2/metrics.csv)。方法说明：[3页PDF]({REL}/advisor_report/concise_v1/GT与M5方法说明.pdf)、[简洁正文]({REL}/advisor_report/concise_v1/method_report.md)。

Native 含加载和核验：WebVid 44.90 分钟、Yandex 46.18 分钟；新增训练 0。公共 test 有历史曝光，不称新盲测。计数/parity 只覆盖预锁256条，全10K返回、Recall及M5线性合并核验通过。下文为此前时点的保留记录。''',
'spec.md':f'''2026-10-09：E173 的隔离测试合同已实际完成：[benchmark_v2]({REL}/src/benchmark_v2.cpp)、[协议v2]({REL}/protocol_v2.md)、[完整结果]({REL}/analysis_v2/metrics.json)。NSG 使用原图 enterpoint 单入口；GT10 使用冻结画像 Micro-HNSW 返回的三个真实 hub；正在研究的 M5 复用同 GT 路由和 scalar search_new，在返回后查冻结残差表、去重、原度量重评分并合并。三方法同图、raw-IP、实际 L、T1/CPU15，K1/K100 分别搜索；60点每点三轮完整wall，包含输出分配/释放和路由、搜索、补全全部线上成本。

完整10K用于真实返回、Recall、域/唯一性及M5独立线性合并核验；预锁均匀256-query只用于plain/count bits和NDC统计。post_dots已包含在graph_ndc，不重复求和。正式timed返回计时内释放，bits证据来自独立untimed完整plain、抽样count和全量合并oracle，不称逐timing轮bits被保存。读取旧迁卷源 /root/acsg-e172-storage-v2/campaign，不恢复旧runner/挂载；无新训练，未修改生产接口或原冻结模型。解释与文件入口见[当前研究快照]({SNAP}/README.md)。下文为此前契约和历史记录。''',
's-target.md':f'''2026-10-09：用户授权的 NSG/GT10/M5 两集五档 L 直接复测与曲线报告已经完成，见[最新结果]({SNAP}/README.md)。**M5 正在研究**；同L小幅提高质量但增加耗时，WebVid K1有两个离散跨L综合优势，Yandex增益很小。当前默认仍为WebVid GT10-soft-t1、Yandex GT10-hard；本次不自动改默认、不追加test调参或新训练、不恢复旧八方法队列。

本轮后续工作是结果/方法说明、图表与Git交接。若后续继续研究，先说明要验证的具体跨场景问题和预算；公共test不得转作调表选择集，已有历史训练超额不能通过本轮0训练回改。下文为此前阶段目标与边界。''',
's-experiment.md':f'''173 已完成：[直接公共测试复测]({REL}/analysis_v2/report.md)、[详细复盘](experiment_history/173_nsg_gt_m5_public_test_retest.md)。WebVid/Yandex各10K；NSG、GT10、正在研究的M5，K1/K100、实际L200/400/800/1000/1200，60点/180轮完整单线程wall，0新增训练。同L M5/GT 20点Recall全增、成员损伤0、配对QPS约降0.16%–4.85%；WebVid K1有两对实际跨L双升，其他三场景没有。GT默认保留。新用户直接test授权不沿用旧CAL停止门；旧171/172记录及停止边界保留原身份。下文为此前历史概览。'''
}
def prefix(title,text):return title+'\n\n<!-- E173_CURRENT_BEGIN -->\n'+text+'\n<!-- E173_CURRENT_END -->\n\n'
for name,text in blocks.items():
    p=ROOT/name; s=p.read_text(); block='<!-- E173_CURRENT_BEGIN -->\n'+text+'\n<!-- E173_CURRENT_END -->'
    assert re.search(r'<!-- E173_CURRENT_BEGIN -->.*?<!-- E173_CURRENT_END -->',s,re.S)
    p.write_text(re.sub(r'<!-- E173_CURRENT_BEGIN -->.*?<!-- E173_CURRENT_END -->',lambda _:block,s,count=1,flags=re.S))
    q=PUB/name; hist=q.read_text();title,rest=hist.split('\n',1);q.write_text(prefix(title,text)+rest.lstrip())

entry=f'''当前项目研究入口：[GT10 与正在研究的 M5]({SNAP}/README.md)。E173 已完成两集、三方法、两K、五档实际L的60点和180批单线程计时；[实测曲线]({REL}/figures_v2/recall_qps_nsg_gt_m5.png)、[完整报告]({REL}/analysis_v2/report.md)、[3页方法说明]({REL}/advisor_report/concise_v1/method_report.md)。M5基于GT10；WebVid K1有局部综合优势，Yandex增益很小，当前默认仍为GT10。以下保留原NETG介绍。'''
for root in [ROOT,PUB]:
    p=root/'readme.md';hist=p.read_text();p.write_text(prefix('# ACSG：GT10 与正在研究的 M5',entry)+hist)

history=f'''# 173：NSG、GT10、M5 直接公共测试复测

状态：COMPLETED_TEST_MATRIX。**M5 正在研究**。用户要求两数据集的 NSG 基线、GT 与 M5 在实际 L=200/400/800/1000/1200 完整测试，不使用候选/选择集资格门。本轮独立于旧 E172，复用原冻结模型而不重新训练。

{conclusion}
## 方法与执行

M5=GT10路由+原NSG主搜索+冻结补全表。每画像最多8个目标ID，在线同一组三画像三行并集最多24个ID；目标不参与第二次图搜索，按原raw-IP重评分R∪C并返回TopK。教师方法稿采用[3页简洁版](../{REL}/advisor_report/concise_v1/GT与M5方法说明.pdf)、[正文](../{REL}/advisor_report/concise_v1/method_report.md)，M5标正在研究；只汇报机制。早期6页稿留在本地历史，不作为本次网页阅读入口。

两集各公共test前10K；Yandex取100K源的前10K。冻结模型FIT20K与本轮test真实向量字节重叠0，原SELECT4096、QGT5K、router TRAIN30K重叠也为0；Web test窗口有9行重复，保留原窗口顺序。公共test有历史曝光。输入/GT/图/模型身份见[完整数据预检](../{REL}/data_preflight.json)。

实际测60点，每点3轮完整wall，共180批/180万正式查询。原NSG图、scalar search_new、raw-IP、T1/CPU15、实际同L。K1和K100分别真实搜索。加载、GT评分、计数和写盘在wall外，正常输出分配释放与路由、查表、去重、重评分、合并在wall内。

原v1冗余全批audit估计成本过高，在未读质量反馈时停止重排，耗时315.37秒，见[v1费用记录](../{REL}/v1_cost_replan.json)。v2正式网格从头跑完，不拼接v1 partial；暖机256，完整plain输出及Recall仍全10K，独立M5线性合并oracle全10K，plain/count parity及NDC只在预锁均匀256条上执行。post_dots包含在graph_ndc。计时返回在stop前释放，未保存逐计时轮bits；不把untimed核验冒充计时轮完整bits证明。

原生作业WebVid2693.72秒、Yandex2770.95秒；正式wall分别1987.31、2039.06秒；完整SHA预检160.77秒，弃用v1费用另列；新增训练0秒。原历史训练成本保持记录，见[本轮费用](../{REL}/delivery_costs.json)。

## 结果与证据

[完整实测报告](../{REL}/analysis_v2/report.md)、[全部60点CSV](../{REL}/analysis_v2/metrics.csv)、[60组配对比较](../{REL}/analysis_v2/comparisons.csv)、[Recall–QPS曲线](../{REL}/figures_v2/recall_qps_nsg_gt_m5.png)、[按L曲线](../{REL}/figures_v2/recall_qps_vs_L_nsg_gt_m5.png)。源码、冻结配置、原生完成receipts和校验记录随本次快照保留。描述bootstrap不作为新质量门，当前模型不按此次结果修改。
'''
hp='experiment_history/173_nsg_gt_m5_public_test_retest.md'
for root in [ROOT,PUB]:(root/hp).write_text(history)
index=f'2026-10-09：[173 NSG/GT10/M5直接测试已完成](173_nsg_gt_m5_public_test_retest.md)，60点/180批；M5正在研究；WebVid K1局部优势、Yandex增益很小，默认保留GT。\n\n'
for root in [ROOT,PUB]:
    p=root/'experiment_history/README.md';s=p.read_text();s=re.sub(r'^2026-10-09.*173.*\n\n','',s,flags=re.M);first,rest=s.split('\n',1);p.write_text(first+'\n\n'+index+rest.lstrip())

reader=f'''# GT10 与正在研究的 M5：方法和完整测试结果

**当前状态：M5 正在研究；E173 直接测试已完成，默认仍为 GT10。** WebVid 使用 GT10-soft-t1，Yandex 使用 GT10-hard。GT10 用真实近邻的 hub 归属监督训练查询侧画像，并通过小型 Micro-HNSW 路由到真实图入口。M5 复用该入口和原搜索结果，用训练时搜索遗漏构造的冻结小表补全输出；每行8个目标，在线3行合并最多24个候选，原度量重评分后返回TopK，不增加第二次图搜索。

## 最新测试结论

{conclusion}
## 图与阅读顺序

![两数据集Recall与完整单线程QPS](../../{REL}/figures_v2/recall_qps_nsg_gt_m5.png)

1. [简洁方法正文：GT10、M5与流程图](../../{REL}/advisor_report/concise_v1/method_report.md)，[3页PDF](../../{REL}/advisor_report/concise_v1/GT与M5方法说明.pdf)。
2. [完整实验报告与全部五档表](../../{REL}/analysis_v2/report.md)。
3. [全部60点CSV](../../{REL}/analysis_v2/metrics.csv)、[同L配对比较CSV](../../{REL}/analysis_v2/comparisons.csv)、[完整JSON含三轮wall](../../{REL}/analysis_v2/metrics.json)。
4. [按实际L查看Recall和QPS](../../{REL}/figures_v2/recall_qps_vs_L_nsg_gt_m5.png)、[可打印曲线PDF](../../{REL}/figures_v2/recall_qps_nsg_gt_m5.pdf)。
5. [测试协议](../../{REL}/protocol_v2.md)、[M5冻结源码和范围](../../{REL}/frozen_m5_source/README.md)、[实际在线测试调用](../../{REL}/src/benchmark_v2.cpp)、[独立结果审查](../../{REL}/final_result_review.json)。

## 测试范围与费用

两集各公共test前10000查询；Yandex为公共100K源的前10K。三个方法同原NSG图、raw-IP、scalar内核、CPU15单线程。K1/K100分别真实搜索，五档L200/400/800/1000/1200；60点各3轮，180批。QPS包括正常输出分配释放和入口、主搜索、M5全部补全成本；数据/模型加载、GT 真值评分和诊断计数在计时外。

全10K返回与Recall及M5独立线性合并核验完成，count/parity/NDC只覆盖事先固定均匀256查询。Native含加载和核验为WebVid44.90分钟、Yandex46.18分钟；本轮新增训练0。完整SHA预检160.77秒和弃用v1作业315.37秒单列，原历史完整训练超预算记录不回改。[本轮费用](../../{REL}/delivery_costs.json)、[冻结输入身份](../../{REL}/data_preflight.json)。

公开测试窗口有历史曝光，不能视为未见过的盲测。冻结FIT20K与本轮test字节重叠0；Web10K的9行重复按原窗口保留。没有候选筛选/选择集门，也没有在test上调参。曲线连线仅用于阅读；图上范围是三个完整timing轮的min–max，不是总体置信区间。

这是便于网页阅读的代码与聚合证据快照。大规模向量、图、冻结二进制模型和逐查询原始返回留本地；此公开快照不是独立可直接运行的全量实验包。[发布范围与身份](publication.md)、[逐文件清单](manifest.json)。此前[2026-10-06八方法快照](../20261006_results/README.md)保留历史身份。
'''
publication='''# 发布范围与身份

目标仓库 VoidFantacy/netg，分支 research/state-20261002；父提交9026dc60ca4f29983792e0f5dcfb33d7ef9335b5。当前研究工作区HEAD为96cf05d5410cf51272048cd1f90b4bb194e23c62，两者分别记录。发布使用独立工作树ACSG-publish-20261009，保留父提交的旧文件和20261006快照，只增加E173白名单产物、当前说明与入口。

本次根文档只将E173当前结论/合同/目标/历史索引同步到旧已发布正文之前，未批量发布主工作区的其他未提交改动。实验native源码SHA3340bdb510f013bceae08639e17337d26950e07b7cf79c4dbbde20d6ffdcde5d，ELF SHA c1c1e970bf77def76edc7fddb5c10f9650ed5fc9ccc74ea0278893af8a4fe467。新训练0，compile_postings等为旧冻结源码字节复制，并非重新执行训练。

清单含正式v2协议、配置、源码、构建/核验记录、60点全部聚合数据及每点完成receipt、曲线PNG/SVG/PDF、简洁3页方法稿和冻结M5编译源码说明。不含base/图/二进制模型、逐查询raw结果、scored npz、200000行配对CSV、本地deps/ELF、旧6页PDF或作业日志。报告中的绝对源路径用于身份追溯，网页阅读请用README中的相对链接。

manifest.json从实际发布字节生成，含路径、大小、SHA256与Git blob SHA；其自身不纳入自己的摘要以避免自引用。提交身份由Git提交页给出，未在提交自身文件中伪造其SHA。最终远端ref及入口文件须在发布后回读核验。
'''
for root in [ROOT,PUB]:
    p=root/SNAP;p.mkdir(parents=True,exist_ok=True);(p/'README.md').write_text(reader);(p/'publication.md').write_text(publication)
shutil.copy2(report,Path('/mnt/data/NSG_GT10_M5_完整测试报告.md'))
print(json.dumps({'status':'DOCS_AND_READER_UPDATED','points':60,'rounds':180,'M5_status':'正在研究','default_replaced':False,'cross_L_pairs':cross},ensure_ascii=False))
