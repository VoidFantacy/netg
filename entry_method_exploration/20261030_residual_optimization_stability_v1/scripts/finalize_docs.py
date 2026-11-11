from common import *
import datetime
v=read(R/'analysis/verdict.json');pairs=list(csv.DictReader((R/'analysis/optimization_pairs.csv').open()));stable=list(csv.DictReader((R/'analysis/stability.csv').open()));points=list(csv.DictReader((R/'analysis/points.csv').open()))
link='entry_method_exploration/'+R.name
def yes(x):return str(x)=='True'
brief=[]
for ds in DS:
 for method in ['OPT-B32','OPT-SQ']:
    pp=[p for p in pairs if p['dataset']==ds and p['method']==method];ss=[s for s in stable if s['dataset']==ds and s['method']==method]
    brief.append(dict(dataset=ds,method=method,paired_points=len(pp),passes=sum(yes(x['screen_pass']) for x in pp),stable=sum(yes(x['both_windows_pass']) for x in ss),configs=len(ss),median_gain=float(np.median([float(x['qps_gain_pct']) for x in pp]))))
table='| 数据 | 优化 | 通过点 | 两窗均通过配置 | 完整QPS增幅中位数 |\n| --- | --- | --- | --- | --- |\n'
for a in brief:table+=f'| {a["dataset"]} | {a["method"]} | {a["passes"]}/{a["paired_points"]} | {a["stable"]}/{a["configs"]} | {a["median_gain"]:+.2f}% |\n'
kept=[s for s in stable if yes(s['both_windows_pass'])];names=['{}/{}/K{}/L{}'.format(s['dataset'],s['method'],s['K'],s['L']) for s in kept]
decision=f'保留{len(kept)}个跨窗口均通过的具体优化配置；其他配置保留原始效应，不默认推广。' if kept else '没有配置在两个窗口均达到预定>=2%且三轮同向的探索标准；保留原后端，未证明稳定省费。'
(REPO/'summary.md').write_text(f'''# ACSG 当前结论

更新于2026-10-30。E194等价省费与查询稳定性实验完成：COCO/WebVid、public与角色去重confirmation各2048query、真实K1/K100，共256正式点/768完整T1批次，另20资格点。全部原生和stdlib核验通过，无待恢复矩阵。默认E99 GT10保持：WebVid GT10-soft-t1、Yandex GT10-hard。

全部56个优化配对点六数组逐字节等价；B32候选次序、SQ的pool/扫描块/Top96与访问量一致。{v['optimization_screen_pass']}/56配对点通过预定同L完整QPS>=+2%且三轮配对同向筛选，{v['stable_configurations']}/28个配置在两窗口均通过。{decision}

{table}
两窗保留配置明确为COCO与WebVid的K100/L100 OPT-B32，完整QPS增幅分别为+2.18%/+2.53%、+2.34%/+2.24%（public/confirmation）。高L和K1尚未达到本轮稳定筛选；OPT-SQ的Top96改法不推广为稳定优化。

原B32的88点均未被当前GT10网格同时覆盖；原SQ的21/24点被GT10或B32覆盖，另COCO/K100/L400在两窗未被覆盖、COCO/K1/L400仅public未被覆盖。这些只是有限网格结论；尤其SQ对更强B32的费用余量小，不能称优于充分调节预算的B32。WebVid确认K100/L200的SQ救回5074成员并损失1个原命中，原/优化相同，该query净命中未下降。

省费相对原B32或原SQ；是否胜过更大L GT10及强B32，另看同窗口控制。优化不会改变原后端的候选支持与质量边界。完整逐L Recall/QPS、救损、严格失败、三轮范围和控制覆盖见[报告]({link}/report_zh.md)、[256点]({link}/analysis/points.csv)、[56配对]({link}/analysis/optimization_pairs.csv)、[跨窗配置]({link}/analysis/stability.csv)。GT10/B32共同11档L，有限网格不称全局最优或精确等Recall。

历史有效场景继续保留：[单列证据](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)记录WebVid M5/B32、COCO B32/SQ。E191 COCO/K1 SQ L400的99.64%/1072.26对GT10 L693的99.64%/817.09（+31.23%）属于原窗口，不能拼入本轮。E193有限学习门6/6组被GT10/B32覆盖，不否定历史有效后端或所有自适应。E192候选支持必要条件仍有效。

确认查询为COCO原未分配身份组、WebVid原源中新抽样并与已登记角色逐向量去重；确认GT全原base/raw-IP精确生成，各固定8条float64复核通过。不承诺全历史未曝光/语义独立；一套图/画像、三轮费用，非跨图/独立人员复现。旧科学产物/PDF/seal不回写；旧根字节由source_before/SHA桥接。大产物/root/acsg-e194-storage，无新PDF。
''')
(REPO/'s-target.md').write_text(f'''# ACSG 后续研究问题

2026-10-30。E194固定矩阵已完成，无待恢复队列，默认E99 GT10保持。当前结果读[summary](summary.md)，完整证据读[报告]({link}/report_zh.md)。以下为后继提案，未自动启动。

1. {decision} 以[28配置完整表]({link}/analysis/stability.csv)为准，判断相对原后端的真实省费及其三轮范围；先检查相对强GT10/B32的可用前沿，再决定具体集成配置。低于筛选阈值的效应不自动当零，也不根据单点把整条路线否定。
2. B32作为强主参照继续保留，先围绕两集K100/L100的小幅省费检查必要的新图/画像稳定性。COCO/K100/L400原SQ在两窗未被本轮网格覆盖，下一步若研究该点，应先补更紧的B32费用控制，不能将当前约2%的质量阈值余量直接当净胜。本轮只优化候选去重/K1合并和固定Top96选择，未改变源支持或扫描/精算预算。SQ省费不足，后继需以实际分段证据定位主要动作费用，再提出实质变化；不把计数或缓存预期当成本归因。
3. 自适应研究可在有效B32/SQ上继续，但要另冻合法训练/校准/确认角色，直接评价相对已有补全的增量。E193已经预测收益/费用，后继须改善信息或费用/召回取舍，不仅换模型名字。新候选固定完整计时和结束边界后再看确认数据；本轮确认窗口今后属于已曝光数据。
4. 本轮确认只涉及同源新query和一套图/画像。若有实用配置，后继用必要的新图/画像或合法新查询检查稳定性；不将本轮省费或有限网格未覆盖直接当全局默认替换。历史有效M5/B32/SQ保持其原身份。

原E194协议、全部成功/失败、源文件和封存保留。无自动追加矩阵、扩大数据集、改默认或新PDF。
''')
p=REPO/'spec.md';s=p.read_text().replace('### 4.9 E194等价省费实现（验证进行中）','### 4.9 E194等价省费实现（固定矩阵已完成）').replace('具体状态见state/report，不能凭源码存在判定通过。','已完成256点/768T1及20资格点，全部原生/stdlib核验通过；具体性能与保留配置见本轮report和analysis/stability.csv。');p.write_text(s)
p=REPO/'s-experiment.md';s=p.read_text().replace('当前E194等价省费/查询稳定性实验进行中，最新完成仍为E193','最新完成E194等价省费/查询稳定性实验（256点/768T1），前序E193保留原结果').replace('已授权256点/768T1计划；验证进行中，默认不变',f'完成256点/768T1；{v["stable_configurations"]}/28配置两窗通过，返回等价，默认不变');p.write_text(s)
(REPO/'LOCAL_CODEX_START.md').write_text(f'''# ACSG 当前接续入口

2026-10-30，/data/netg/ACSG。E194等价省费与查询稳定性固定矩阵完成，默认E99 GT10保持，无待恢复队列。先读AGENTS、summary、spec、s-target、s-experiment，再读[E194报告]({link}/report_zh.md)、[配对]({link}/analysis/optimization_pairs.csv)、[稳定配置]({link}/analysis/stability.csv)、[正式冻结]({link}/formal_freeze.json)、[状态]({link}/state.json)和delivery_validation。

两集两窗口真实两K共256点/768完整T1＋20资格点。56个优化点返回逐字节等价，{v['stable_configurations']}/28配置两窗口都通过预定省费筛选。省费相对原后端，与强GT10/B32的关系另看完整点表。数据/root/acsg-e194-storage经storage链接。新query仅角色去重，不称全历史盲确认；同一图/画像。保留历史有效M5/B32/SQ，旧科学原件/PDF/seal不回写。

可复制接续：请先只读核HEAD、根文档和E194完整wall/冻结/原始配对。固定矩阵已完成，无待恢复队列。按我本次明确任务继续，区分等价省费、补全增益、强控制覆盖和跨查询稳定性，不自动扩大矩阵、改默认或产生PDF。新确认窗口今后已曝光。
''')
(REPO/'experiment_history/194_residual_optimization_stability_v1.md').write_text(f'''# E194 残差后端等价省费与查询稳定性

2026-10-30用户授权“先优化和稳定方法，开始实验”。[协议](../{link}/protocol.md)在新性能前固定：COCO/WebVid、public及角色去重confirmation各2048条、真实K1/K100，256点/768完整T1，另20资格点，均完成并通过原生及stdlib核验。默认E99 GT10保持。

OPT-B32用固定512槽哈希保留三hub候选次序，并简化K1严格合并；OPT-SQ保持pool/2048码/96精算，只改连续数组Top96选择。全部56配对点的六数组、候选次序和访问等价。{v['optimization_screen_pass']}/56点通过>=2%完整QPS且三轮配对同向，{v['stable_configurations']}/28配置在两窗均通过。{decision}

{table}
本轮只证明这些组合实现的实测费用，不把全部QPS变化归因于单一操作。GT10/B32共同11档L控制，原SQ独立保留；是否被强控制覆盖另见全部点。确认query来源、GT、质量区间、实际费用、局限见[完整报告](../{link}/report_zh.md)。配对和跨窗表保留全部配置，不只展示阳性。无新图/画像、无新门拟合或默认替换。

新产物/root/acsg-e194-storage经storage链接，实际返回/三轮hash/完整wall及独立实现收据保留。旧E193科学封存不改，旧可变根文档通过source_before/SHA桥接。固定范围已收口，无待恢复队列，无新PDF。
''')
p=REPO/'experiment_history/README.md';s=p.read_text().replace('（2026-10-30进行中，实际状态见原目录state）。','（2026-10-30完成256点/768完整T1，实际结论见报告）。');p.write_text(s)
dump(R/'analysis/decision.json',dict(summary=brief,retained_configurations=names,decision=decision,default_changed=False))
dump(R/'state.json',dict(status='COMPLETED_EQUIVALENT_OPTIMIZATION_STABILITY_NO_DEFAULT_CHANGE',completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),formal_points=256,formal_batches=768,qualification_points=20,paired_points=56,stable_configurations=v['stable_configurations'],default_changed=False,pending_work=False,new_PDF=False))
print('E194_FINAL_ROOT_DOCS_UPDATED',flush=True)
