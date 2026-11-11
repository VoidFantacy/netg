import csv,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1];D=R.name;REL='entry_method_exploration/'+D

def main():
 rec=json.loads((R/'reviews/report_build.json').read_text());rows=list(csv.DictReader((R/'analysis/points.csv').open()));pairs=list(csv.DictReader((R/'analysis/paired.csv').open()));get=lambda m:next(x for x in rows if x['method']==m and x['L']=='200');newmethods=['SQ8-96']+(['PQ384-SQ8'] if (R/'results/coco/PQ384-SQ8_L200').exists() else []);cov=json.loads((R/'reviews/scoring_formal_audit.json').read_text())['coverage'];select=json.loads((R/'selection.json').read_text());p=get('SQ8-96');pq=get('REUSE-BLOCK');c=next(x for x in cov if x['method']=='SQ8-96' and x['L']==200);cp=next(x for x in cov if x['method']=='REUSE-BLOCK' and x['L']==200);head=rec['conclusion'].replace('\n',' ')
 perf='| 方法 L200 | Recall@100 | 完整QPS |\n| --- | --- | --- |\n'+'\n'.join(f"| {m} | {float(get(m)['recall_pct']):.4f}% | {float(get(m)['qps']):.2f} |" for m in ['GT10','B32','REUSE-BLOCK']+newmethods)
 effect=f"同一候选pool/扫描块逐query一致。COCO L200扫描覆盖{c['scanned_covered']}个遗漏；旧PQ短名单覆盖/救回{cp['shortlist_covered']}/{cp['rescued']}，SQ8为{c['shortlist_covered']}/{c['rescued']}。SQ8相对PQ Recall增加{float(p['recall_pct'])-float(pq['recall_pct']):.4f}pp。质量机会与完整费用分开，不把扫描覆盖当免费收益。"
 dense=json.loads((R/'reviews/dense_control_results_audit.json').read_text());dc=dense['candidate_comparison'];condition=f"原矩阵29点/87轮，另冻密集GT10补充9点/27轮；补充同窗口SQ8 L400相对阈值GT{dc['target_GT_L']}速度{dc['target_speed_delta_pct']:+.2f}%，预算Recall差{dc['budget_recall_delta_pp']:+.4f}pp。原矩阵L400阳性筛选保留其原身份，候选/参数未改。预设PQ384两级方案{'触发' if select['cascade_triggered'] else '未触发'}：校准PQ384遗漏覆盖/SQ8-96遗漏覆盖={select['coverage_ratio']:.4f}，门槛0.75；未试其他宽度。"
 summary=f'''# ACSG 当前结论

更新于2026-10-28。**默认保留E99 GT10：WebVid GT10-soft-t1、Yandex GT10-hard。** 最新完成[E190固定候选排序实验]({REL}/report_zh.md)：COCO真实K100，正式{rec['total_formal_points']}点/{3*rec['total_formal_points']}完整T1轮，primary校准26点/78轮。固定矩阵收口，无待恢复队列；可靠Recall–QPS综合目标尚未完成。

**{head}** {rec['judgment']}

## 本轮实际结果：固定L200

{perf}

QPS为本轮同一二进制三轮中位数，包含正常Batch分配/初始化、GT10路由主搜、全部补全、六数组复制和销毁；不拼接E189绝对速度。

## 得到的机制证据

{effect}

SQ8使用全部原base的逐维minmax编码，不读query/GT训练；码额外57.75MiB，另有trained及运行时ID→位置映射，旧辅助后端负担仍在。{condition}

## 角色、核验与限制

原块表只用前12K fit，后4K按预设条件决定是否进入固定384两级方案；旧16K B32含校准标签，完全排除选择，仅正式参考。公共10K历史曝光，无新盲确认。GT10历史训练/数据角色仍沿原身份。

实际timed包三轮bits/SHA、全量实际主包补全oracle、逐query2048扫码/96原metric精算上限、第二份stdlib整数统计和预算比较通过；SQ8编码另一实现全base逐字一致，扫描pool/块顺序全query一致，原metric评分与短名单另抽核。不同实现同一执行者，非独立人员复现。旧E189的1570件seal保持。

仅COCO/K100、一图/画像；不替代K1、Deep或其余五集。SQ8结果只约束本轮具体库/编码/实现，不能推广为所有量化评分路线的性能结论。

七集两K综合证据仍为[E183](entry_method_exploration/20261017_gt10_residual_comprehensive_v1/analysis/delivery_v2/report_zh.md)，E184/E185为离线诊断；E187–189费用/覆盖结论沿[历史索引](s-experiment.md)读取。

[六页PDF]({REL}/ACSG_COCO固定候选排序与完整费用_20261028.pdf) · [原29点]({REL}/analysis/points.csv) · [补充9点]({REL}/dense_control_analysis/points.csv) · [预算比较]({REL}/analysis/discrete_comparisons.csv) · [实现](spec.md) · [下一门](s-target.md)。
'''
 (REPO/'summary.md').write_text(summary)
 spec=(REPO/'spec.md').read_text();marker='## 5. 指标、计时与证据';section=f'''### 4.5 E190固定候选评分实现

[源码]({REL}/src/scoring.cpp)在只改main符号及相对include路径的E189局部快照上增加SQ8；旧科学源码/图/metric/GT10/块/PQ不改。[协议]({REL}/protocol.md)固定原REUSE-BLOCK的pool、原metric块中心排序、2048码及96原metric精算上限。SQ8使用原C++Faiss QT_8bit、RS_minmax arg0，全原base无query/GT训练，输出trained和按原block IDs顺序的码；运行期新增ID→码位置映射。SQ8分数取负IP，稳定短名单，再沿原精算/合并。

SQ8-96对所有扫描且不在R中的码评分；无用PQ LUT不创建。条件PQ384-SQ8则沿旧PQ取384，再SQ8取96，代码已资格核验；本轮条件{'触发' if select['cascade_triggered'] else '未触发，未作为正式在线方法执行'}。选择记录见[selection]({REL}/selection.json)，不增加其他宽度/模型。

正式{rec['total_formal_points']}点/{3*rec['total_formal_points']}轮，primary校准26点/78轮；仅COCO/K100。实际timed包三轮一致，全量主包补全oracle，所有评分版本pool/扫描块顺序逐query一致；SQ8近似评分数与原metric精算数分别计。trace是wall外从实际主包重建，非timed内部trace。完整费用包含正常输出生命周期；共载SQ8数组的benchmark RSS不等于GT10生产依赖或单独部署增量。来源/二进制/静态库/配置身份见[freeze]({REL}/freeze.json)，结果/结论见[报告]({REL}/report_zh.md)。

'''
 assert marker in spec and '### 4.5 E190' not in spec;(REPO/'spec.md').write_text(spec.replace(marker,section+marker))
 target=f'''# ACSG 后续研究问题

更新于2026-10-28。目标仍为可靠Recall–QPS综合改进，默认E99 GT10保持。E190 COCO固定评分版本已完成正式{rec['total_formal_points']}点/{3*rec['total_formal_points']}轮及primary校准26点/78轮，无待恢复矩阵。

## 当前判断与停止边界

{head} {rec['judgment']}

{effect} {condition} 原E189/E190科学文件、角色、协议和seal保留；本轮不追加短名单宽度/预算，不按曝光test重训直到通过。

## 后继问题（提案，未启动）

1. Deep先诊断覆盖全base的块代表排序：在合法开发query上，用全部块代表的精确排序检查固定访问预算能覆盖多少遗漏；这只是wall外机会诊断。覆盖有价值再考虑独立小型块代表ANN并核算全部检索/扫码/精排费用。候选代表失真与ANN近似损失分别判断，不直接扩大训练高频表。
2. COCO保留本轮SQ8的质量与费用分离证据。若研究保持评分语义的实现省费，需先核具体静态库/解码/访存费用，保持返回逐字一致后再测完整wall，不能把代数等价或少运算当性能通过。采用新量化器/新筛选器则另立版本，先冻结合法角色与预算。
3. 若存在可支付后端，再研究逐query选择或跳过补全；先验证收益异质性及廉价特征可预测性。SQ8编码是既有工具，不能直接作方法创新主张。

任何后继先冻结来源、fit/校准/新确认角色、完整预算及结束点；保留不补全、附近密集GT10 L和适用B32。旧16K B32不能进入含其训练标签的自动选择。新确认不得参与配置选择。

## 泛化与指标

E190仅COCO/K100；E189/188另有Deep/K100，均历史曝光公共test，无新系统盲确认。K1及其余五集仍读E183。严格0–9命中失败、改善、脱离、成员救损、源外救回分别计数。

[最新结论](summary.md) · [E190报告]({REL}/report_zh.md) · [接续入口](LOCAL_CODEX_START.md)。本轮授权范围完成，无自动追加队列。
'''
 (REPO/'s-target.md').write_text(target)
 p=REPO/'s-experiment.md';s=p.read_text();s=s.replace('最新正式性能为E189两集K100复用信息的补全路由实验','最新正式性能为E190 COCO/K100固定候选排序实验');row=f'| E190 | 固定候选SQ8评分与完整费用 | {rec["total_formal_points"]}点/{3*rec["total_formal_points"]}T1；{head}默认不变 | [卡片](experiment_history/190_coco_fixed_candidate_scoring_v1.md) |\n';s=s.replace('| E189 |',row+'| E189 |',1);p.write_text(s)
 card=f'''# E190：COCO固定候选的评分质量与完整费用

2026-10-28，用户授权“做吧”。正式{rec['total_formal_points']}点/{3*rec['total_formal_points']}完整T1轮，primary校准26点/78轮。范围COCO raw-IP、真实K100；默认E99 GT10保持。

{head} {rec['judgment']}

{perf}

{effect}

原pool/块排序/扫描顺序逐query一致，2048码/96原metric精算上限保持；只改扫描后的评分。SQ8码按原base全库QT_8bit minmax编码，无query/GT训练；新增57.75MiB及码位置映射，不清零旧后端费用。原GT10、B32、PQ控制全包与E189一致。

{condition}

前12K冻结块表/后4K条件校准/正式10K历史曝光，B32完全排除校准。原E189 1570件seal保持；全量补全oracle、三轮bits/SHA、stdlib set第二实现、全base SQ8编码逐字核验及评分抽检通过。不同实现同一执行者，无新盲确认/K1/跨集证据。固定版本收口；Deep块检索未启动。

[完整报告](../{REL}/report_zh.md) · [六页PDF](../{REL}/ACSG_COCO固定候选排序与完整费用_20261028.pdf) · [协议](../{REL}/protocol.md) · [冻结](../{REL}/freeze.json) · [条件决定](../{REL}/selection.json) · [核验](../{REL}/reviews/formal_results_audit.json)。
'''
 (REPO/'experiment_history/190_coco_fixed_candidate_scoring_v1.md').write_text(card)
 p=REPO/'experiment_history/README.md';s=p.read_text();s=s.replace('最新正式实验是[E189](189_reuse_completion_routing_v1.md)两集K100复用补全路由','最新正式实验是[E190](190_coco_fixed_candidate_scoring_v1.md) COCO/K100固定候选评分');s=s.replace('| [189_reuse', '| [190_coco_fixed_candidate_scoring_v1.md](190_coco_fixed_candidate_scoring_v1.md) | E190：COCO固定候选评分与完整费用 |\n| [189_reuse',1);p.write_text(s)
 start=f'''# ACSG 当前接续入口

更新于2026-10-28；工作区`/data/netg/ACSG`，分支`research/state-20261002`，HEAD `96cf05d5410cf51272048cd1f90b4bb194e23c62`。E174–190主要是本地未提交工作，HEAD不能恢复完整产物。E190已完成，无待恢复矩阵。

## 阅读顺序

1. [AGENTS](AGENTS.md)，再读[summary](summary.md)→[spec](spec.md)→[s-target](s-target.md)→[s-experiment](s-experiment.md)。
2. [E190报告]({REL}/report_zh.md)、[六页PDF]({REL}/ACSG_COCO固定候选排序与完整费用_20261028.pdf)、[实测点]({REL}/analysis/points.csv)、[预算比较]({REL}/analysis/discrete_comparisons.csv)。
3. [条件决定]({REL}/selection.json) · [补充冻结]({REL}/dense_control_freeze.json)、[评分/覆盖核验]({REL}/reviews/scoring_formal_audit.json)、[质量核验]({REL}/reviews/formal_results_audit.json)、[状态]({REL}/state.json)。

## 已收敛结论

{head} {rec['judgment']}

{effect} {condition}

仅COCO/K100；旧B32只作正式参考，排除含其训练标签的校准。SQ8全base无query/GT拟合。公开test历史曝光，无新盲确认；旧E189 seal保持。

## 可复制接续提示词

```text
请接续/data/netg/ACSG，先只读核分支/HEAD与LOCAL_CODEX_START、AGENTS及四根文档，再读E190报告、selection和核验。
E190固定COCO评分矩阵已完成：正式{rec['total_formal_points']}点/{3*rec['total_formal_points']}完整T1轮，primary校准26点/78轮；默认E99 GT10保持，无待恢复队列。
候选池/扫描块逐query相同；SQ8排序质量与完整费用分开，原PQ384条件结果保留，不按曝光test追加宽度到通过。
旧E189/E190科学seal不改，不自动重跑或扩大范围；按我的当前明确任务继续。
```

本轮修改前根文档见[E190 source_before]({REL}/source_before/)，历史根SHA保持当时身份。
'''
 (REPO/'LOCAL_CODEX_START.md').write_text(start)
 print('PASS E190 root documents and history synchronized')
if __name__=='__main__':main()
