#!/usr/bin/env python3
"""Synchronize the clarified metric, preserving the previous document snapshots."""
from pathlib import Path
import csv
R=Path(__file__).resolve().parent;REPO=R.parents[1]
REL=str(R.relative_to(REPO));PDF='ACSG_低于10%召回的查询比例_全L修正版_20261024.pdf'
NEW=REL+'/'+PDF
OLD='reports/20261024_failure_rescue_residual_v1/ACSG_失败率_救回率与残差作用_20261024.pdf'
def update(name,fn):
    p=REPO/name;text=p.read_text();assert (R/'source_before'/name).exists()
    p.write_text(fn(text))
def replace(text,a,b):assert text.count(a)==1,(a,text.count(a));return text.replace(a,b)
def summary(text):
    start=text.index('## 失败与改进比例');end=text.index('## 残差与空间分布的判断')
    rr=list(csv.DictReader((R/'failure_by_L.csv').open()));cc=list(csv.DictReader((R/'paired_rescue_by_L.csv').open()))
    s={(r['label'],r['method'],int(r['L'])):r for r in rr};c={(r['label'],int(r['L'])):r for r in cc if r['comparison']=='B32_vs_GT10'}
    labels=['Deep10M','SIFT10M','GIST1M','WebVid','Yandex','COCO','Flickr30k'];ls=[100,128,200,400,800,1000,1200]
    lines=['## 失败与改进比例：严格Recall@100低于10%','',
        '**用户已澄清：失败是单条查询Recall@100低于10%，即命中0–9个GT100成员；恰好10个排除。** 分母是同集/方法/L全部query。此前主表的“未满100”不符合这个问题，旧图表与当时记录保留，但现行解读由[全L修正报告]('+REL+'/report_zh.md)取代。','',
        'GT10低召回失败率：','',
        '| 数据集 | '+' | '.join('L'+str(L) for L in ls)+' |','| --- | '+' | '.join(['---']*7)+' |']
    for lab in labels:lines.append('| '+lab+' | '+' | '.join(f"{float(s[lab,'GT10',L]['low_pct']):.2f}%" for L in ls)+' |')
    lines+=['','固定L200的三方法与残差增量：','',
        '| 数据集 | NSG失败率 | GT10失败率 | B32失败率 | 原低召回中有所改善 | 原低召回中升到≥10% |',
        '| --- | --- | --- | --- | --- | --- |']
    for lab in labels:
        q=c[lab,200];den=int(q['reference_low_count'])
        cells=[lab]+[f"{float(s[lab,m,200]['low_pct']):.2f}%" for m in ['NSG','GT10','B32']]
        cells +=[f"{q['low_net_improved_count']}/{den}" if den else '—（无原低召回）',f"{q['exit_low_count']}/{den}" if den else '—（无原低召回）']
        lines.append('| '+' | '.join(cells)+' |')
    lines+=['','Web L200改善26/53，但只有7/53（13.21%）脱离低召回，19条改善后仍低于10%；Yandex改善5/86，脱离1/86（1.16%）。达到10%不代表高召回或完整恢复。L200 GT10也新增Deep2条、COCO1条低召回，不能只报救出。','',
        '**残差总体收益主要来自原本≥10%的query。** L200 Web补回20257个GT成员，其中75个（0.37%）来自原低召回query；Yandex为8/570（1.40%）；COCO为0/13715。因此“总体Recall增加”不能直接解释为“严重失败已解决”。','',
        '成员遗漏修复率与未满100/恢复100统计仍是有效的辅助指标，但不是当前失败率。原E184的跨集/空间关联针对这些广义遗漏结果，不能直接当作低于10%尾部的证据。主L200残差损伤0、其他已有B32预算的边界事件保持原记录；本次只复算147个既有点，无新ANN/GT/训练/计时。','',]
    text=text[:start]+'\n'.join(lines)+'\n'+text[end:]
    text=replace(text,'**空间结构与主搜失败有关，静态残差收益另受遗漏目标重现、路由覆盖和容量保留约束。**','**空间结构与主搜遗漏量有关，静态残差收益另受遗漏目标重现、路由覆盖和容量保留约束。** 这一广义遗漏关联不自动适用于本次严格低于10%的稀少尾部。')
    text=replace(text,'[六页图表PDF：失败率、救回率与残差作用]('+OLD+')覆盖三方法失败、不同分母的救回/完整修复、遗漏分区、收益/费用及完整K100曲线；只重排E183/E184既有结果，无新增实验。',
        '[五页全L修正版PDF：Recall低于10%的查询比例]('+NEW+')覆盖严格失败口径、三方法全L曲线、低召回改善与脱离、残差收益来源以及更大L的同队列比较。147点原始返回已重算并经第二份stdlib实现核验；旧六页版未满100口径保留历史身份。')
    return text
update('summary.md',summary)
def spec(text):
    text=replace(text,'- K100查询失败可定义未满100或少于90，须声明门槛。逐query改善、完整恢复、成员救回/损伤及其分母分开。',
        '- 当前用户所指K100查询失败严格为Recall@100<10%，即与GT100交集0–9个，恰好10个排除；失败率分母为同集/方法/L全部query，必须逐L报告。原低召回中命中数增加与升至≥10%分别计为“有所改善”与“脱离低召回”，零分母记无定义。未满100/少于90、完整恢复、成员救损是另外的辅助指标，不能替代本失败率。')
    text=replace(text,'[六页图表PDF](reports/20261024_failure_rescue_residual_v1/README.md)在独立reports目录只读E183/E184 CSV；输出矢量PDF、逐图PNG/SVG、图表CSV及实际PDF渲染/数值核验收据。未重测性能或修改原实验manifest；PDF中的K1/查询级K100/成员级K100统计各保留其分母。',
        '[五页低于10%全L修正版PDF]('+REL+'/README.md)从E183原GT及实际raw/ids.i32逐条复算147个K100点；固定原家族与B32，输出逐L失败、成对改善/脱离/新增、全命中分布、低召回query行、跨L逐query转移与完整QPS引用。`per_query_hits.npz`按原query行对齐；恰好10命中单列。第二份stdlib set/array实现核验全部点和98组配对，属于同执行者不同实现；输入SHA前后核对。输出矢量PDF、PNG/SVG、实际PDF渲染及交付收据。旧六页版未满100口径保留原件；未重测性能或改原实验manifest。')
    return text
update('spec.md',spec)
update('LOCAL_CODEX_START.md',lambda t:replace(t,'[六页图表PDF]('+OLD+')集中展示失败率、救回率与残差作用，供快速阅读；只复用E183/E184数据。',
    '[五页全L修正版PDF]('+NEW+')展示Recall@100严格低于10%的查询比例、低召回改善与脱离，以及残差作用。用户已澄清失败门槛；旧六页版的未满100口径不再作为当前失败率。147个E183原始返回点已逐条复算，无新ANN或计时。'))
update('readme.md',lambda t:replace(t,'[失败率、救回率与残差作用六页PDF]('+OLD+')。',
    '[低于10%召回查询比例：全L修正版PDF]('+NEW+')；严格0–9个GT100命中，区分有所改善与升到≥10%，替代旧未满100口径。'))
update('s-experiment.md',lambda t:replace(t,'[六页PDF]('+OLD+')','[低于10%全L修正版PDF]('+NEW+')'))
update('s-target.md',lambda t:replace(t,'几何在粗分层后仍有条件关联，不是因果证明或在线预测器。实际数值和完整费用只在[summary](summary.md)维护。',
    '几何在粗分层后仍有条件关联，不是因果证明或在线预测器。用户澄清的失败指标为Recall@100<10%，要逐L区分有所改善与脱离低召回；旧遗漏量关联不能直接当作该尾部规律，多数集样本仅0–几条。实际数值和完整费用只在[summary](summary.md)维护。'))
def card(t):
    mark='## 2026-10-24 用户澄清：失败为Recall@100低于10%'
    assert mark not in t
    return t+'\n'+mark+'\n\n用户明确失败是单条query召回低于10%，原未满100/少于90指标不符合这次失败口径。新增[五页全L修正版PDF](../'+NEW+')与[报告](../'+REL+'/report_zh.md)：从E183原GT与真实返回逐条重算7集、7L、NSG/固定GT10/同家族B32共147点；严格0–9命中，恰好10排除。无新ANN/GT/训练/计时。\n\nWeb GT10失败率L100/200/1200为1.92%/0.53%/0%；Yandex为1.67%/0.86%/0.14%。L200残差Web改善26/53，脱离低召回7/53；Yandex5/86与1/86。COCO唯一低召回query未改善，总体13715成员增益来自原≥10%的query。原几何关联仍只支持广义遗漏结果，不能移植成严格尾部结论。\n\n新版本保留147点逐query命中数、全L统计/成对转移与低召回query索引，另一份stdlib set/array实现全部核验；旧E183/E184及六页v1原件与seal不回写。现行文档已同步新门槛，旧“失败率”表保留历史身份。\n'
update('experiment_history/184_residual_geometry_diagnosis_v1.md',card)
print('Updated seven current/index documents; snapshots preserved')
