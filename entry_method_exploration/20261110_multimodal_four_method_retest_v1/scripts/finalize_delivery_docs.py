"""Synchronize reviewed E200 findings while preserving preceding document bytes."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
from datetime import datetime, timezone, timedelta

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
OUT = RUN / 'analysis/final_v1'
REL = 'entry_method_exploration/20261110_multimodal_four_method_retest_v1'
DATE = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    evidence = json.loads((OUT / 'report_evidence.json').read_text())
    assert evidence['status'] == 'PASS_REPORT_DERIVATIONS_FROM_AUDITED_DATA'
    assert json.loads((OUT / 'independent_audit.json').read_text())['status'] == 'PASS_INDEPENDENT_STDLIB_ALL_POINTS'
    docs = [ROOT / x for x in ['summary.md', 'spec.md', 's-target.md', 's-experiment.md',
            'LOCAL_CODEX_START.md', 'experiment_history/README.md', 'experiment_history/200_multimodal_four_method_retest_v1.md']]
    docs += [RUN / 'README.md', OUT / 'report_zh.md']
    before = RUN / 'reviews/root_before_final'
    before.mkdir()
    snapshots = {}
    for p in docs:
        name = str(p.relative_to(ROOT)).replace('/', '__')
        shutil.copy2(p, before / name)
        snapshots[str(p)] = {'snapshot': str((before / name).relative_to(RUN)), 'sha256': sha(p)}
    (before / 'snapshots.json').write_text(json.dumps(snapshots, ensure_ascii=False, indent=2) + '\n')
    names = {'coco': 'COCO', 'flickr30k': 'Flickr30k', 'webvid2_5m_light_v1': 'WebVid', 'yandex_t2i_official10M_ip_v1': 'Yandex'}
    report_path = OUT / 'report_zh.md'
    original = report_path.read_text()
    findings = '''## 当前判断与方法取舍

**默认保持E99 GT10。此次完整重测支持在COCO、WebVid保留直接残差作为有用配置，Flickr按召回目标选择；Yandex优先GT10。** GATE是E97外部入口基线，和此前停止扩展的残差门控不同。本轮没有恢复这些学习导航或门控分支，也没有自动改变生产默认。

- **COCO：残差有清晰收益。** 95%召回门槛下，K1为95.530% / 7319.78 QPS，对GT10的95.670% / 4593.71提速59.34%；K100为95.513% / 2863.94，对GT10的95.344% / 2500.35提速14.54%。实际召回不同，属于门槛比较。下面另给召回与速度同时改善的实测点对。
- **Flickr30k：保留条件性收益。** 95%门槛下，残差相对GT10的K1/K100 QPS分别提高24.61%/5.07%；但K100在90%和99%门槛反而慢5.89%/1.95%。不能据曲线局部优势写成所有质量目标都应启用残差。
- **WebVid：两种K均有收益。** K1的残差L640为91.130% / 526.47 QPS，优于GT10 L800的90.750% / 427.63（QPS +23.11%）。K100达到90%门槛的QPS提高31.15%，但GT10 L1120实际为89.9997%，刚低于门槛；该百分比部分受离散预算跳档影响。更接近的实测点对是残差L960的90.0171% / 352.85对GT10 L1120的89.9997% / 305.80，QPS提高15.39%。本轮到L1600仍未达到95%，不向更大预算外推。
- **Yandex：入口改进有用，固定B32追加收益小。** L200时残差在K1/K100仅增加0.1400/0.0570个百分点召回，完整平均耗时增加1.64%/2.35%。所有本轮已达到的90%/95%/99%门槛组合均是GT10比残差快；99% K100四方法都未达到。很小的Recall增量也会造成有限网格“未被覆盖”，不能把这种计数当成有实际意义的整体提速。
- **GATE没有形成独立的实测前沿收益。** 其160个点均被同数据/K矩阵中的其他方法在Recall不低、平均QPS不低且至少一项严格更好的条件下覆盖。这只评价本轮冻结模型、预算、图与查询窗口，不代表所有GATE适配或学习入口都无效。

GT10与NSG也有明确边界：WebVid/Yandex的同L召回均提高，COCO/Flickr的K100则有微小降低（最大分别0.0691/0.0818个百分点），伴随本轮平均完整耗时下降。COCO还保留一条GT10新增的严重低召回查询，见后文。入口方法的均值收益不能解释成逐查询保证。

### 召回与速度同时改善的实测例子

下表从完整矩阵选取代表点，两个指标均直接来自实际返回和两轮完整wall；不是插值或严格相同Recall实验。对应两轮QPS范围均不重叠，但两次重复不足以证明统计显著性或跨机器稳定性。完整曲线和全部负例仍保留。

| 数据 | K | GT10：L / Recall% / QPS | ＋残差：L / Recall% / QPS | QPS变化 |
| --- | --- | --- | --- | --- |
'''
    for p in evidence['joint_improvement_examples']:
        a, b = p['GT10'], p['residual']
        findings += f'| {names[p["dataset"]]} | {p["K"]} | {a["L"]} / {float(a["recall_percent"]):.4f} / {float(a["qps_mean"]):.2f} | {b["L"]} / {float(b["recall_percent"]):.4f} / {float(b["qps_mean"]):.2f} | {p["qps_change_pct"]:+.2f}% |\n'
    findings += '\n较复杂的历史M5/SQ、区域扫描和学习残差方案仍按原实验范围保留条件有效或无效证据；本轮四方法比较没有重测这些版本，也不把跨实验绝对QPS拼入本表。论文取舍与训练GT说明继续遵循[写作约定](../../../../论文写作约定.md)。\n\n'
    original = original.replace('![Recall@1]', findings + '![Recall@1]', 1)
    extra = '''## 低召回尾部与成员替换

严重低召回固定为K100命中0–9个GT成员，即严格Recall@100<10%。L200统计如下，分母为该集全部测试查询；全20档对应计数在points.csv和paired.csv中保留。

| 数据 | NSG低召回 | GT10低召回 | ＋残差低召回 | GATE低召回 | GT10相对NSG救出/新增 | 残差相对GT10救出/新增 |
| --- | --- | --- | --- | --- | --- | --- |
| COCO | 0 | 1 | 1 | 0 | 0 / 1 | 0 / 0 |
| Flickr30k | 0 | 0 | 0 | 0 | 0 / 0 | 0 / 0 |
| WebVid | 142 | 53 | 46 | 112 | 113 / 24 | 7 / 0 |
| Yandex | 174 | 86 | 85 | 126 | 128 / 40 | 1 / 0 |

GT10在WebVid/Yandex减少了严重低召回的净数量，但也新增了24/40条；残差只进一步救出7/1条。COCO的平均残差收益没有救回该条尾部问题。因此，本轮支持“入口改进后仍存在可补的遗漏”，不能写成残差普遍解决搜索迷失，也不能据这些计数认定密度或连通性为原因。

残差160个同L配置中159个平均Recall增加，Yandex K1/L1600持平；本轮所有残差配对均未发现逐查询命中数下降。但正确成员集合并非严格包含原集合：COCO K100/L800 query 8121发生1个正确成员替换；WebVid query 92在K100/L960、1120、1280各发生1次。四次都是99命中→99命中，新进入和被替换的各有一个GT成员。边界实际float32分数非常接近；仍按原GT如实保留4个成员损失事件，不修改GT或把它们抹为0。详情见[报告派生证据](report_evidence.json)中的member_loss_details。这里的查询行号为零基。

## 完整费用与离线准备

同L残差的完整平均耗时在全部160点均增加，幅度0.32%–20.67%；小L时固定补点开销占比更大。L200的分阶段质量/费用见上表；较小L加补点能否优于较大L主搜索，需要同时看前面的实际点对和完整门槛表。

| 费用项 | 本轮记录 | 计量边界 |
| --- | --- | --- |
'''
    extra += f'| 1280个正式batch wall之和 | {evidence["formal_wall_sum_seconds"]:.2f} s（{evidence["formal_wall_sum_seconds"]/3600:.3f} h） | 正式查询完整生命周期，1120万次查询。 |\n'
    extra += f'| 八个原生测量进程之和 | {evidence["native_process_sum_seconds"]:.2f} s | 已包含上行；另含加载、预热、写出、hash/oracle等，不与上行相加。 |\n'
    extra += f'| 逐任务无损压缩及往返校验 | {evidence["archive_seconds"]:.2f} s | 在正式计时外串行完成。 |\n'
    suite = json.loads((RUN / 'reviews/pipeline_run_suite_receipt.json').read_text())
    extra += f'| run_suite完整命令进程 | {suite["seconds"]:.2f} s（{suite["seconds"]/3600:.3f} h） | 包含测量进程、压缩和输入身份复核，不能再重复加上前三行。 |\n'
    extra += '''| COCO/Flickr新GATE准备 | 已记录费用下界2079.17 s（34.65 min） | 特征/标签、训练已完成阶段和恢复阶段；中断未提交费用未知，不是完整总成本。 |
| 继承的图、GT10、B32、Web/Yandex GATE | 本轮复用，历史成本未重测 | 复用不表示离线成本为零；不能将本轮新训练费用视为公平的全历史构建费用比较。 |

新GATE离线训练使用16线程，正式查询始终CPU15实际1线程。COCO选epoch22，Flickr选epoch7，均按预定patience20结束。标签来自训练查询的实际单入口NSG/L64响应；线上只用导出的W和小图，不运行66M参数训练塔，也不读新查询GT。训练期间主机重启的恢复与成本未知部分见后文。

## 核验与复现入口

全部64个资格点通过；48个NSG/GT10/B32点与旧E183实际返回一致，16个GATE点与独立旧E97评测器一致。正式640点全部两轮返回逐字节/SHA一致、原生残差合并oracle通过。第二份stdlib实现复核640点GT交集、1280轮平均、480组配对、96行门槛、640行覆盖关系和2560个压缩payload的往返身份。独审为同执行者不同实现，不冒称独立人员审查。

两张PNG已实际查看；对应SVG均含16条曲线、每条20个标记，合计640个点，图例/单位/数据集与K标注完整。两轮范围是描述性波动，不是置信区间；高召回附近曲线重叠应查CSV数值。

[协议](../../protocol.md) · [冻结输入与代码](../../formal_freeze.json) · [测量完成收据](../../reviews/measurement_complete.json) · [独立核验](independent_audit.json) · [各阶段费用](../../reviews/formal_process_costs.json) · [GATE准备费用](../../reviews/gate_preparation_costs.json) · [交付验收目录](../../reviews/)。完整交付的最终状态以该目录delivery_validation.json为准；各阶段收据的pending字段保留生成时身份。

'''
    original = original.replace('## 数据、成本与解释边界', extra + '## 数据、成本与解释边界', 1)
    original = original.replace('独立整数/计时核验与实际图形审查完成后才作最终交付。', '独立整数/计时核验及实际图形审查均已完成，原始数值、科学资产与默认保持。')
    report_path.write_text(original)
    summary = f'''# ACSG 当前结论

更新于{DATE}。最新完成E200四多模态集四方法加密重测：COCO/Flickr30k/WebVid/Yandex、NSG/GT10/GT10＋直接残差/外部GATE、真实K1/K100、每K20档L，共640点、1280完整CPU15单线程批次、1120万正式查询。每点恰好两遍，主QPS为两次N/wall的算术平均。**默认保持E99 GT10；残差按数据与质量目标保留，未自动全局替换。**

完整结果读[中文报告]({REL}/analysis/final_v1/report_zh.md)、[640点]({REL}/analysis/final_v1/points.csv)、[1280轮计时]({REL}/analysis/final_v1/rounds.csv)及[Recall@1]({REL}/analysis/final_v1/figures/recall_qps_k1.png)/[Recall@100曲线]({REL}/analysis/final_v1/figures/recall_qps_k100.png)。全部方法共用原scalar主核，绝对QPS不与E103优化核或旧轮次拼接。

COCO、WebVid的直接残差有明确有效区间。COCO K1：残差L200为99.1200% / 2423.64 QPS，对GT10 L320的98.8800% / 1695.32，QPS +42.96%；K100：残差L200为96.7159% / 2397.12，对GT10 L256的96.6528% / 2038.59，+17.59%。WebVid K1：残差L640为91.1300% / 526.47，对GT10 L800的90.7500% / 427.63，+23.11%；K100：残差L960为90.0171% / 352.85，对GT10 L1120的89.9997% / 305.80，+15.39%。这些是实际召回与QPS均改善的离散点对，不是等Recall或插值结果。

Flickr有条件性收益：95%门槛下残差对GT10的K1/K100提速24.61%/5.07%，但K100的90%/99%门槛慢5.89%/1.95%。Yandex的B32追加收益小：L200的K1/K100仅增加0.1400/0.0570个百分点、完整平均耗时增加1.64%/2.35%；全部已达到的预定门槛组合仍以GT10更快。WebVid两K到L1600均未达到95%，Yandex K100未达到99%，不外推到未测预算。

GATE为E97外部入口基线，160个点均被同数据/K矩阵内其他方法覆盖；不等同所有学习入口无效。GT10相对NSG在Web/Yandex同L召回均提高；COCO/Flickr K100有微小下降，伴随本轮平均完整耗时减少。残差160个同L点159个Recall增加、1个持平，但每点完整耗时均增加0.32%–20.67%。默认替换不能只看有限网格未覆盖点数。

严重低召回为K100命中0–9个GT成员。L200时NSG→GT10→残差：COCO 0→1→1，Flickr 0→0→0，WebVid 142→53→46，Yandex 174→86→85；GATE分别0/0/112/126。残差进一步救出7/1条Web/Yandex问题，但没有修复COCO新增的那条，不能把平均Recall增加写成普遍解决迷失。本轮残差无逐查询命中数下降；仍有4个正确成员替换事件，涉及两个查询的不同L，均为99→99，原GT和事件计数保留。

正式batch wall合计13723.78s，完整run_suite进程14240.44s；前者已包含于后者，不重复加总。COCO/Flickr新GATE离线准备已记录费用下界2079.17s，Flickr主机重启前未提交费用未知；全部正式测量发生在恢复之后。继承资产的历史构建费用未清零。公开测试已有曝光，方法训练规模/角色不同，不称盲确认或等监督量因果消融。

全部64资格点、640点原生oracle/两轮bits、独立stdlib的640点/1280轮/480配对/96门槛/640覆盖关系与2560个payload核验通过，两张实际曲线已查看。复现与验收读[工作目录]({REL}/README.md)和[详细卡片](experiment_history/200_multimodal_four_method_retest_v1.md)。本轮不生成PDF。

研究主线继续为入口改进与直接补点；此前E199学习选点、短名单精排导航和残差门控的停止边界不变。历史E173/E191/E194 M5/B32/SQ条件有效证据仍保留[原身份](experiment_history/_maintenance/20261029_residual_positive_evidence_sync_v1/conclusion_zh.md)，不因新比较撤销。前一完成阶段E199及文档报告读[历史索引](s-experiment.md)，本次修改前根文档见[E200快照]({REL}/source_before/)及[测量期快照]({REL}/reviews/root_before_final/)。

论文继续按[写作约定](论文写作约定.md)：入口不够好→GT10；改善入口后仍有有限预算遗漏→直接残差。训练GT与测试评测分开，线上新查询不读GT，历史替代方案按完整费用解释取舍。
'''
    (ROOT / 'summary.md').write_text(summary)
    spec = (ROOT / 'spec.md').read_text()
    spec = spec.replace('更新于2026-11-05。', f'更新于{DATE}。', 1)
    start = spec.index('### 4.16 E200')
    end = spec.index('\n## 5.', start)
    section = f'''### 4.16 E200四方法评测适配（完整矩阵与核验已完成）

[独立目录]({REL}/protocol.md)复制E183 runner，四方法共用原scalar主核；直接残差使用复制的E194 fast_plan/fast_apply，GT10路由与完整16K/B32原表保持。GATE分支沿E97单位query、slot映射与heap-pop，主搜仍用raw query。WebVid GT10固定soft-t1，其余hard；真实K1/K100各20档L，共640点/1280批次/1120万查询。只计两遍，主QPS是两个N/wall的算术平均，另存平均wall和合并QPS。完整六数组生命周期计wall，实际CPU15/T1，加载/GT/写出/hash/oracle/压缩在外；未插桩NDC零值不代表没有距离计算。

四集64个资格点通过：48点NSG/GT10/B32与E183实际包逐字一致，16点GATE与独立旧E97评测器一致。正式640点两轮bits/SHA相同、全部残差与同K/L实际GT10主包的独立合并oracle通过。首轮四payload加两个零计数数组与形状构成packet SHA；2560个payload无损gzip并往返核验后才移除新冗余原始副本。全部101项冻结文件在正式前后完整SHA核验。

COCO/Flickr GATE补建沿E97标签/拓扑/训练流程，合法residual前10K训练、随后1024 monitor，与测试向量及身份组分离，但与旧B32监督共享。原GT10监督规模也不同，非等监督量消融。512真实hub、WL2/Doc2Vec10epoch、修正正负标签、原塔；线上只用导出W及小图。COCO选epoch22，Flickr选epoch7，patience20终止。Flickr因主机重启从epoch7完整模型/优化器/RNG接续epoch8，最终选定W与重启前最佳W逐字一致；全部正式计时在恢复之后。未知中断费用与已记录下界分列。Web/Yandex模型复用。

[主分析]({REL}/scripts/analyze.py)从原GT和实际timed包重算640点、480配对、96门槛和有限网格覆盖；[stdlib独立实现]({REL}/scripts/audit.py)另核全部整数、wall/平均、SHA和2560个archive payload。实际PNG审阅及SVG每条20标记核对完成，独审为同执行者不同实现。报告派生记录4个正确成员替换事件但无逐查询命中数下降，不改GT或返回；详细结果只读summary/report。

新产物预算6GiB、root可用f_bfree下限6GiB，不改文件系统保留比例。旧科学资产、seal和模型不改；当前根文档的原字节按source_before及reviews/root_before_final桥接。无新增生产API、图修改、残差门/导航、PDF或默认替换。当前交付见[README]({REL}/README.md)与[state]({REL}/state.json)。
'''
    (ROOT / 'spec.md').write_text(spec[:start] + section + spec[end:])
    (ROOT / 's-target.md').write_text(f'''# ACSG 后续研究边界

{DATE}，[E200四方法完整重测]({REL}/analysis/final_v1/report_zh.md)已完成640点/1280批次，四多模态集、真实K1/K100、各20档L、每点两遍完整单线程；原生/独立数值核验与实际曲线审阅已完成。没有待恢复的正式测量或训练队列。当前默认保持E99 GT10。

接下来可据已交付曲线组织论文：COCO/WebVid直接补点有实际Recall/QPS同时改善的离散点；Flickr按质量目标取舍；Yandex优先GT10。报告完整有效与无效区间、同L费用和低召回边界，不把两次重复当统计显著性或公开测试当新盲确认。已有640点足以完成本次比较，不按结果追加预算到通过。

研究主线继续为原搜索/GT10入口与直接残差补点。当前学习选点、短名单精排导航和残差前/后门仍停止扩展；本轮GATE仅外部入口基线，未恢复E199残差门。历史M5/B32/SQ条件有效场景保留各自身份。新数据窗、预算、状态续搜、修图或新模型不属于本次后续自动队列，需有新的明确任务与冻结范围。

论文要求读[写作约定](论文写作约定.md)，当前事实读[summary](summary.md)，实现合同读[spec](spec.md)，全部证据读[E200工作目录]({REL}/README.md)。此前目标及测量期状态保存在[E200原快照]({REL}/source_before/s-target.md)和[最终更新前快照]({REL}/reviews/root_before_final/)。
''')
    (ROOT / 'LOCAL_CODEX_START.md').write_text(f'''# ACSG 当前接续入口

{DATE}，工作区/data/netg/ACSG。最新完成[E200四多模态四方法重测]({REL}/README.md)：COCO/Flickr30k/WebVid/Yandex，NSG/GT10/GT10＋直接残差/外部GATE，真实K1/K100、每K20档L，每点两遍，共640点/1280完整单线程批次/1120万正式查询。测量、原生oracle、独立数值核验和实际图形审阅完成；没有待恢复测量队列，勿据旧PID重复启动。最终交付状态读[state]({REL}/state.json)及reviews/delivery_validation.json。

默认E99 GT10保持。COCO/WebVid残差有明确有效区间，Flickr按召回目标取舍，Yandex优先GT10；GATE160个点均被同期其他方法覆盖。先完整读AGENTS、summary、spec，再读s-target和s-experiment。性能主入口为[E200中文报告]({REL}/analysis/final_v1/report_zh.md)、[640点CSV]({REL}/analysis/final_v1/points.csv)和K1/K100曲线。全部使用原scalar核，不混旧绝对QPS。

此前残差学习选点/精排导航/门控停止边界保持；E200的GATE是E97外部入口方法。旧模型、科学原件、seal与PDF保留；旧根文档见[E200 source_before]({REL}/source_before/)和测量期root_before_final快照。历史M5/B32/SQ条件有效结果不撤销。

论文/汇报先读[论文写作约定](论文写作约定.md)：入口不够好→GT10；好入口后仍有遗漏→直接残差；训练GT、测试评测和线上未知答案分开，完整费用解释替代方案取舍。
''')
    p = ROOT / 's-experiment.md'; text = p.read_text(); paras = text.split('\n\n')
    assert paras[1].startswith('2026-11-10新增E200进行中')
    paras[1] = f'{DATE}最新完成[E200四多模态四方法加密重测]({REL}/analysis/final_v1/report_zh.md)：640点/1280完整CPU15单线程批次、1120万正式查询，每点两遍、每K20档L。COCO/WebVid残差有明确有效区间，Flickr按目标取舍，Yandex优先GT10；GATE160点均被同期其他方法覆盖。完整数值与实际图形已核验，默认不变。前一实验E199及复杂残差分支停止决定保留历史身份。当前结论读summary，实现读spec，后继读s-target。'
    text = '\n\n'.join(paras)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith('| E200 |'):
            lines[i] = '| E200 | 四多模态NSG/GT10/直接残差/GATE加密重测 | 完成640点/1280两遍T1；COCO/WebVid残差有效，Flickr条件性，Yandex优先GT10；默认保持 | [详细记录](experiment_history/200_multimodal_four_method_retest_v1.md) |'
    p.write_text('\n'.join(lines) + '\n')
    p = ROOT / 'experiment_history/README.md'; text = p.read_text(); paras = text.split('\n\n')
    assert '正式测量中' in paras[1]
    paras[1] = f'更新于{DATE}。最新完成[E200](200_multimodal_four_method_retest_v1.md)四多模态四方法加密重测：640点/1280完整T1批次，每点两遍平均，原生/独立数值核验与实际图形审阅完成。COCO/WebVid残差有明确有效区间，Flickr按目标取舍，Yandex优先GT10；默认保持。前一实验E199及学习导航/残差门停止边界保留历史身份，全部前序卡片与科学原件不改。当前结论见[summary](../summary.md)，简要索引见[s-experiment](../s-experiment.md)。'
    text = '\n\n'.join(paras).replace('E200：四多模态四方法加密重测（测量中）', 'E200：四多模态四方法加密重测（640点/1280批次完成）')
    p.write_text(text)
    history = f'''# E200：四多模态集NSG/GT10/直接残差/GATE加密重测

{DATE}完成。用户要求每点两次平均、增加预算点、沿既有口径比较。完整执行COCO/Flickr30k/WebVid/Yandex、四方法、真实K1/K100、各20档L，640点/1280批次/1120万查询；公开测试分别10000/5000/10000/10000条。只用新完整wall，默认E99 GT10保持。

GT10固定WebVid soft-t1及其余hard，残差完整16K/B32加返回等价工程优化。四方法共用原scalar主核与原raw-IP/base/图，CPU15实际T1，计时包括正常Batch分配/路由/搜索/补点/六数组复制销毁。QPS为两次N/wall算术平均，原wall、平均wall与合并QPS另存。GATE为E97外部入口基线，非E199残差门。

COCO/Flickr GATE沿原标签/拓扑/训练流程补建；合法residual前10K训练、随后1024 monitor，与测试向量/身份组分离，但与完整B32监督重叠，原GT10监督规模亦不同。Web/Y模型复用。Flickr训练主机重启后从完整epoch7模型/优化器/RNG接续epoch8，最终最佳W未变；全部正式计时在恢复之后，未提交训练费用未知，日志和检查点保留。

结果：COCO K1残差L200的99.1200% / 2423.64优于GT10 L320的98.8800% / 1695.32（+42.96% QPS）；K100残差L200为96.7159% / 2397.12，对GT10 L256的96.6528% / 2038.59（+17.59%）。WebVid K1残差L640为91.1300% / 526.47，对GT10 L800的90.7500% / 427.63（+23.11%）；K100残差L960为90.0171% / 352.85，对GT10 L1120的89.9997% / 305.80（+15.39%）。都是离散实际点，不是严格等Recall比较。

Flickr95%门槛残差对GT10的K1/K100提速24.61%/5.07%，K100在90%/99%门槛反而慢5.89%/1.95%。Yandex已达到的预定门槛均GT10更快，残差L200的K1/K100仅增0.1400/0.0570pp并增完整耗时1.64%/2.35%。GATE160点均被同期其他方法覆盖。不能把有限网格未覆盖点数当整体胜率；公开测试已曝光、两遍波动非置信区间、方法训练量不同。

L200严格低召回NSG→GT10→残差为COCO0→1→1、Flickr0→0→0、Web142→53→46、Yandex174→86→85；GATE0/0/112/126。残差不是普遍尾部修复。160个残差点159个Recall提高、1个持平，无逐查询命中数下降，但两个查询跨L共4个正确成员替换事件均99→99，原GT与事件保持。

费用：正式wall总13723.78s；八个原生进程总14037.69s；归档78.95s；完整run_suite命令14240.44s，均有包含关系，不重复求和。新GATE准备已记录下界2079.17s，不含未知未提交中断费用；继承资产历史成本未清零。

验证：64资格点（48旧E183包、16旧E97 GATE）通过；640点两轮bits/SHA及全量残差merge oracle通过；stdlib另核640点、1280轮、480配对、96门槛、640覆盖行和2560个gzip payload。101项冻结输入正式前后完整SHA一致。两PNG实际查看，SVG32条曲线各20标记；独审是同执行者不同实现。旧科学文件/模型/seal保持，根文档另留快照。未生成PDF、未恢复旧残差门/导航或修改默认。

[报告](../{REL}/analysis/final_v1/report_zh.md) · [全部点](../{REL}/analysis/final_v1/points.csv) · [两轮](../{REL}/analysis/final_v1/rounds.csv) · [协议](../{REL}/protocol.md) · [独立核验](../{REL}/analysis/final_v1/independent_audit.json) · [工作目录与验收](../{REL}/README.md)。
'''
    (ROOT / 'experiment_history/200_multimodal_four_method_retest_v1.md').write_text(history)
    (RUN / 'README.md').write_text(f'''# E200 多模态四方法加密重测

{DATE}，完整640点/1280正式单线程批次/1120万查询已完成；每点两遍、每K20档L。COCO/Flickr30k/WebVid/Yandex完整测试角色，NSG/GT10/GT10＋直接残差/GATE，真实K1/K100。原生与独立数值核验、实际图形审阅完成，默认E99 GT10保持。

结果：COCO/WebVid直接残差有明确收益，Flickr按质量目标取舍，Yandex优先GT10。GATE160点均被同矩阵其他方法覆盖；结论限于冻结模型/图/预算和已曝光查询。详细实际Recall、完整QPS、负例、尾部与费用读[中文报告](analysis/final_v1/report_zh.md)。

- [Recall@1曲线](analysis/final_v1/figures/recall_qps_k1.png)、[SVG](analysis/final_v1/figures/recall_qps_k1.svg)；[Recall@100曲线](analysis/final_v1/figures/recall_qps_k100.png)、[SVG](analysis/final_v1/figures/recall_qps_k100.svg)。
- [640点CSV](analysis/final_v1/points.csv)、[1280轮计时](analysis/final_v1/rounds.csv)、[480组配对](analysis/final_v1/paired.csv)、[门槛](analysis/final_v1/targets.csv)、[覆盖关系](analysis/final_v1/frontier.csv)、[派生证据](analysis/final_v1/report_evidence.json)。
- [协议](protocol.md)、[固定矩阵](config.locked.json)、[101项冻结文件](formal_freeze.json)、[配置](configs/)、[源码](src/)。
- [测量完成](reviews/measurement_complete.json)、[64点资格](reviews/qualification.json)、[独立核验](analysis/final_v1/independent_audit.json)、[复核与交付收据目录](reviews/)。最终完整交付收据为reviews/delivery_validation.json；阶段pending字段保留当时身份，当前状态读[state](state.json)。
- [正式进程/压缩费用](reviews/formal_process_costs.json)、[新GATE准备费用](reviews/gate_preparation_costs.json)、[训练重启恢复证据](reviews/recovery_boot1/)、[最初根文档](source_before/)、[最终更新前快照](reviews/root_before_final/)。

主QPS为两次N/wall算术平均，另存平均wall与合并QPS；CPU15实际T1、原scalar核、完整输出生命周期。首轮实际包保留，第二轮逐字/SHA相同；2560个payload按gzip无损压缩且往返核验。无PDF。继承构建费用非零，Flickr中断未提交费用未知；不将主机停机时间当训练费用。

自动阶段脚本finish_pipeline.py已结束。重放或复查先读协议、冻结身份与实际state；不要根据旧PID或历史“测量中”段落重启已完成计时。旧科学产物、模型、图、GT和seal保持。
''')
    print(json.dumps({'updated_documents': [str(p) for p in docs], 'snapshot_dir': str(before), 'date': DATE}, ensure_ascii=False))


if __name__ == '__main__':
    main()
