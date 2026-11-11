import csv,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];REL=R.relative_to(REPO).as_posix()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for v in json.loads((R/'reviews/live_docs_binding.json').read_text()):assert sha(Path(v['path']))==v['sha256'],v['path']
 report=(R/'report_zh.md').read_text();rec=json.loads((R/'reviews/report_build.json').read_text());note=json.loads((R/'interpretation.json').read_text());ps=list(csv.DictReader((R/'analysis/points.csv').open()));roles=json.loads((R/'reviews/role_model_audit.json').read_text())['checks'];overlap='；'.join(f"{x['dataset']} fit/cal={x['fit_cal_identical_vector_hashes']}、fit/test={x['fit_test_identical_vector_hashes']}、cal/test={x['cal_test_identical_vector_hashes']}" for x in roles)
 headline=f"18个新复用点中{rec['dominated']}个被实测GT10同时覆盖Recall与QPS；离散速度筛选通过{rec['speed_screen']}点，预算召回筛选通过{rec['budget_recall_screen']}点。"
 table=['| 数据 | 方法 L200 | Recall@100 | 完整QPS |','| --- | --- | --- | --- |']
 for ds in ['coco','deep10m_l2_v1']:
  for m in ['GT10','B32','BLOCK-R2048','REUSE-REG','REUSE-BLOCK','MAIN-BLOCK']:
   p=next(x for x in ps if x['dataset']==ds and x['method']==m and x['L']=='200');table.append(f"| {'COCO' if ds=='coco' else 'Deep10M'} | {m} | {float(p['recall_pct']):.4f}% | {float(p['qps']):.2f} |")
 summary=f'''# ACSG 当前结论

更新于2026-10-28。**默认保留E99 GT10：WebVid GT10-soft-t1、Yandex GT10-hard。** 最新完成[E189复用信息的补全路由实验]({REL}/report_zh.md)：两集真实K100，正式70点/210完整单线程轮，另64点/192轮校准。固定矩阵已收口，无待恢复队列；可靠Recall–QPS研究目标尚未完成。

**{headline}** {note['conclusion']}

## 本轮实际结果：固定L200

{chr(10).join(table)}

QPS是本轮同一二进制的三轮中位数；含正常分配、GT10路由/主搜、补全、六数组复制和销毁，不拼接E188绝对速度。实际离散阈值对照不等于精确等Recall，完整曲线见[六页PDF]({REL}/ACSG_复用路由与补全成本实验_20261028.pdf)。

## 成本与实际救回

{note['cost_finding']}

{note['coverage_finding']}

REUSE-REG用入口小表与主返回提出最多32区域，沿旧ridge选择最多2区；REUSE-BLOCK直接提出最多32块，MAIN-BLOCK只用主返回最多8块。块/PQ只读复用，总上限2048码/96精算；区域每区48与直接块全局96不同，不能把全部差额解释为纯路由因果。新池与原全1024粗路由的可见信息不同，不是返回等价工程优化。

## 角色、核验与限制

新表前12K fit、后4K诊断，不做配置选择；旧16K B32含末4K标签，完全排除本轮校准，保留正式参考。历史GT10可能使用合法fit，正式10K历史曝光，无新盲确认。源行角色分开；相同向量SHA交集计数：{overlap}。这些计数不证明语义独立。

全部timed包/三轮SHA、真实主包补全oracle、逐query预算、旧完整包一致、第二份stdlib集合统计、原metric分数及路由/PQ抽检已核验；E188的2145文件seal保持。第二实现为同一执行者，非独立人员复现。失败严格为单query Recall@100<10%（0–9命中），改善、脱离、成员救损、源外救回分开；稀少尾部不外推。

新映射/小表相对E188新增存储与旧后端常驻负担分别报告；suite内含formal wall，不相加。仅COCO raw-IP/Deep squared-L2真实K100，无其他五集/K1新证据；没有逐query跳过或完整搜索状态复用。

七集两K综合证据仍为[E183](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)；E184/E185为关联诊断；E188的预算负结果及角色修正保留[历史记录](experiment_history/188_completion_cost_budget_v1.md)。

[实现合同](spec.md) · [下一门](s-target.md) · [历史索引](s-experiment.md) · [70点]({REL}/analysis/points.csv) · [实际预算对照]({REL}/analysis/discrete_comparisons.csv) · [核验]({REL}/reviews/results_audit.json)。
'''
 hist=f'''# E189：复用GT10信息的稀疏补全路由

2026-10-28，用户明确要求“继续研究吧”。正式两集K100共70点/210完整T1轮，校准64点/192轮，预定范围全部完成。默认E99 GT10保持。

{headline}

{note['conclusion']}

{note['cost_finding']}

{note['coverage_finding']}

三个新方法：REUSE-REG将三个入口每hub8区域与主返回最高8区域合并，最多32粗代表评分，沿冻结REG-R模型选最多2区，其余沿E188每区1024码/48候选；REUSE-BLOCK对应每hub8块与主返回最高8块，最多32块代表评分，整块访问上限2048码、全局PQ96；MAIN-BLOCK只保留主返回8块。旧图/PQ/块/metric/GT10不改，主核仍E183冻结scalar。区域与直接块的候选分配不同，不作纯路由因果。与E174的posting seed/NSG一跳不同，本轮不以主图邻接扩展候选。

新表只用合法前12K L200教师遗漏及入口频次，ties按ID，无超参选择；末4K只是诊断，不决定或取消正式范围。旧16K B32明确排除校准，正式保留参考，不是训练量匹配对照。原16K完整遗漏并集作为旧来源外审计，不能与新12K源混称。向量SHA交集：{overlap}；历史GT10训练及公开测试曝光仍须披露。

CPU15、实际1线程、单方法串行；warm256、三轮轮转，完整Batch正常分配初始化/GT10路由主搜/补全/六数组复制销毁。首轮实际包保留，另两轮字/SHA一致；真实主包全排序PQ/合并oracle、预算上限、旧控制完整包、另一实现整数统计与原metric分数通过。块候选池/扫描选择/PQ阈值另用第二实现抽检64query/方法/数据集；L200全部覆盖链从实际主包重建oracle trace。第二实现同一执行者，不称独立人员审查。严格0–9命中失败及救损见完整表，不从稀少尾部外推。

新持久数组约COCO0.55MiB/Deep38.24MiB，主要为N×4 ID→block映射；旧全库后端常驻成本仍在，进程共同装载的RSS不是新增量。构建、suite、内部wall分别见报告，内含费用不相加。E188 2145件seal未变，当前根文档旧版另存source_before，不回写旧交付身份。

固定版本收口，后续方向见当前s-target；无新盲确认/K1/其他五集证据或默认替换。

[完整报告](../{REL}/report_zh.md) · [六页PDF](../{REL}/ACSG_复用路由与补全成本实验_20261028.pdf) · [协议](../{REL}/protocol.md) · [冻结](../{REL}/freeze.json) · [核验](../{REL}/reviews/results_audit.json)。
'''
 (REPO/'experiment_history/189_reuse_completion_routing_v1.md').write_text(hist)
 p=REPO/'s-experiment.md';s=p.read_text().replace('最新正式性能为E188两集K100费用与硬预算实验','最新正式性能为E189两集K100复用信息的补全路由实验');s=s.replace('| E188 |',f'| E189 | 入口/主返回提出稀疏区域与块 | 正式70点/210T1；新18点中{rec["dominated"]}点被GT10覆盖，默认不变 | [卡片](experiment_history/189_reuse_completion_routing_v1.md) |\n| E188 |',1);p.write_text(s)
 p=REPO/'experiment_history/README.md';s=p.read_text().replace('最新正式实验是[E188](188_completion_cost_budget_v1.md)两集K100费用与硬预算','最新正式实验是[E189](189_reuse_completion_routing_v1.md)两集K100复用补全路由');s=s.replace('| [188_', '| [189_reuse_completion_routing_v1.md](189_reuse_completion_routing_v1.md) | E189：GT10入口/主返回复用与稀疏补全路由 |\n| [188_',1);p.write_text(s)
 (REPO/'summary.md').write_text(summary)
 p=REPO/'spec.md';s=p.read_text();marker='## 5. 指标、计时与证据';assert marker in s
 section=f'''### 4.4 E189稀疏补全路由实现

[源码]({REL}/src/reuse.cpp)复用只改main符号名的E188局部快照及原静态库；原E188/E187源码只读，非生产主核变更。[prepare.py]({REL}/scripts/prepare.py)用合法前12K L200教师实际遗漏，分别按已有三入口统计region/block成员出现频次，每hub保留最高8项、ties按ID；另存全base ID→block i32映射。块/PQ/图/GT10复用原件。

REUSE-REG将三hub表与R中频次最高8区域合并去重（最多32），原metric评分后取最多8，沿原REG-R ridge选最多2区；少于8时跨度取实际末位，rank仍除7，少于2不补位。后续沿E188每区1024码/48候选。REUSE-BLOCK直接合并最多32块，按原metric中心距离/块ID排序，整块访问累计≤2048码，跳过放不下的块；全局PQ96、排除R、原metric精算及严格合并。MAIN-BLOCK只用R的最高8块，实际扫码≤1024，总体上限仍2048。辅助查表/统计/去重/评分均计wall；没有在线GT或新门控/完整搜索状态缓存。

正式70点/210轮、校准64点/192轮，真实K100/两集/CPU15/T1，L100/200/400补全及20档GT10控制。旧B32只做正式参考，因校准标签重叠而不进校准矩阵；本轮不做配置选择。3轮实际包一致、全主包oracle及预算核验；trace为L200实际主包的wall外全排序重建，非另外的timed内部trace。模型与源码/输入绑定见[freeze]({REL}/freeze.json)，未改原base/metric/kernel。新ID→block映射为N×4字节，旧后端常驻成本并未清零。

''';p.write_text(s.replace(marker,section+marker))
 (REPO/'s-target.md').write_text(f'''# ACSG 后续研究问题

更新于2026-10-28。目标为可靠Recall–QPS综合改进，默认E99 GT10保持。E189已完成正式70点/210轮、校准64点/192轮，没有待恢复矩阵。{headline}

## 当前判断与停止边界

{note['conclusion']}

{note['coverage_finding']}

本轮池/预算/模型固定收口；不按已曝光test扩池、扩预算或重训直到通过。E188及E189原科学文件/选择历史/冻结身份保留。旧B32训练重叠资格本轮已提前排除，不用其表内收益批准泛化。完整证据读[summary](summary.md)和[E189报告]({REL}/report_zh.md)。

## 下一门（提案，未启动）

{note['next_gate']}

任何后继版本先冻结信息来源、角色、实际预算和停止点，付齐查表/路由/候选筛选/精算/合并的完整wall，保留不补全与密集附近GT10 L。新确认不得参与模型选择；若研究逐query门控，先证明收益异质性与廉价特征的可预测性。旧16K B32自动选择须新合法校准或重建fit-only表。

## 泛化与指标

仅COCO/Deep两集真实K100，不能替代K1及SIFT/GIST/WebVid/Yandex/Flickr。公开test历史曝光；精确向量不重叠也不证明语义独立。严格0–9命中失败、改善、脱离、成员救损、来源外救回分开；不把少访问或几何关联当可靠性能。

从[LOCAL_CODEX_START.md](LOCAL_CODEX_START.md)接续。已有授权范围已完成，无自动追加队列。
''')
 (REPO/'LOCAL_CODEX_START.md').write_text(f'''# ACSG 当前接续入口

更新于2026-10-28；工作区`/data/netg/ACSG`，分支`research/state-20261002`，HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–189主要是本地未提交工作，HEAD/旧远端不代表完整产物。E189已完成，无待恢复矩阵。

## 阅读顺序

1. [AGENTS.md](AGENTS.md)，再读[summary](summary.md)→[spec](spec.md)→[s-target](s-target.md)→[s-experiment](s-experiment.md)。
2. [E189报告]({REL}/report_zh.md)、[六页PDF]({REL}/ACSG_复用路由与补全成本实验_20261028.pdf)、[70点]({REL}/analysis/points.csv)、[实际预算比较]({REL}/analysis/discrete_comparisons.csv)。
3. [覆盖链]({REL}/reviews/formal_trace_audit.json)、[角色/模型审计]({REL}/reviews/role_model_audit.json)、[核验]({REL}/reviews/results_audit.json)、[状态]({REL}/state.json)。旧方案先从历史卡片进入原协议与产物。

## 已收敛结论

{headline} 默认E99 GT10保持。{note['conclusion']}

{note['coverage_finding']}

新表12K fit、末4K诊断，无配置选择；旧16K B32不进校准、只做正式参考。仅两集K100、历史曝光test，无新盲确认。旧E188的2145件seal未变。

## 可复制接续提示词

```text
请接续/data/netg/ACSG，先只读核分支/HEAD与LOCAL_CODEX_START、AGENTS和四根文档，再读E189报告/覆盖链/角色审计。
E189已完成正式70点/210完整T1轮与校准64点/192轮，默认E99 GT10保持，没有待恢复矩阵。
稀疏入口/主返回候选的费用、覆盖、PQ筛选和最终救回分别见实测；不把少评分/少扫码等同可靠Recall–QPS。
旧B32只作正式参考，禁止用表内校准决定泛化。两集K100历史曝光，不外推其他K/数据。
旧E188/E189科学seal保持；不自动重跑、扩池、修改默认或恢复旧队列。按我的当前明确任务继续。
```

本轮修改前根文档在[E189 source_before]({REL}/source_before/)，旧根SHA保持当时身份；本轮交付收据在[E189目录]({REL}/)。
''')
 (R/'reviews/docs_sync.json').write_text(json.dumps(dict(status='PASS_E189_DOCS_SYNC',original_live_bindings_verified=True,old_scientific_artifacts_untouched=True),indent=2)+'\n');print('PASS E189 root/history synchronization')
if __name__=='__main__':main()
