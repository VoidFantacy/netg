"""Attach reviewed interpretation to the frozen-run closeout, preserving drafts."""
import difflib
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
now = datetime.now(ZoneInfo('Asia/Shanghai'))
stamp = now.strftime('%Y%m%d_%H%M%S')
backup = RUN / 'ops' / ('analysis_closeout_before_' + stamp)
backup.mkdir()
rel = str(RUN.relative_to(ROOT))
history = ROOT / 'experiment_history/90_gate_disjoint_five_datasets_r1_r100.md'
files = [RUN / n for n in ['report.md', 'complete.json', 'state.json', 'handoff.md']]
files += [ROOT / n for n in ['summary.md', 'spec.md', 's-target.md', 's-experiment.md']]
files += [history]
for p in files:
    out = backup / p.relative_to(ROOT)
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, out)
shutil.copytree(RUN / 'reviews/docs', backup / 'reviews_docs')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

report = RUN / 'report.md'
s = report.read_text()
head, _, rest = s.partition('\n')
intro = ('2026-09-16：数值、图表与最终身份核验完成。详见[逐数据集分析与 hard/soft 建议](analysis.md)，'
         '其中保留90%/95%/99%召回门槛的实际Recall、QPS、预算以及三次计时波动。'
         '当前没有统一赢家：WebVid的K1支持GT10，GIST的K100更适合完整HNSW；Deep/SIFT的hard与soft很接近。'
         '继续保留hard为预先指定研究主线、soft为固定对照，不自动更换既有默认。')
report.write_text(head + '\n\n' + intro + '\n' + rest +
    '\n## Yandex 前置检查中断与限定修正\n\n'
    '2026-09-15 14:09 前检发现 manifest 声明10000行而路径指向100000行，流水线在正式测试前停止。'
    '随后物化原 query/GT 的固定前10000行，符合E96既定前缀，无结果驱动选样；15:19前检通过、15:20恢复。'
    '约70分钟等待中断不计计算成本。原100K文件、181个原冻结资产和旧E96结果保留，限定修订后最终183个冻结资产核验通过。'
    '见[历史90a](../../experiment_history/90a_yandex_test_prefix_fix.md)、'
    '[修正审计](reviews/yandex_test_prefix_correction_v1/correction.json)。\n')

history.write_text(history.read_text() +
    f'\n2026-09-16最终分析已完成：[逐集分析与门槛表](../{rel}/analysis.md)。'
    'WebVid在90% Recall@1门槛下hard为352.5 QPS（90.73%），NSG为280.9（90.65%）；'
    'Yandex在95% Recall@1门槛下hard为1127.5 QPS（95.02%），soft为906.1（95.77%）。'
    'Deep/SIFT的hard与soft非常接近，GIST的K100更适合完整HNSW。'
    '门槛差异不代表整条曲线支配，GATE未显示跨五集稳定优于GT10；原默认未替换。\n\n'
    '正式阶段15.826小时，结束于2026-09-16 07:09:42；已记录离线阶段4.869小时。'
    '保留[Yandex前缀修正90a](90a_yandex_test_prefix_fix.md)：14:09前检停止、15:20恢复，'
    '约70分钟等待不算计算成本；原100K源文件与旧资产未覆盖。\n')

summary = (f'E97 于2026-09-16完成：WebVid/Yandex/Deep/BIGANN-SIFT/GIST，排除LAION；'
           f'Recall@1/100共800点、2400次单线程端到端计时，四张总图已实际检查，冻结身份核验通过。'
           f'[详细分析]({rel}/analysis.md)、[完整方法与成本]({rel}/report.md)、'
           f'[Recall@1图]({rel}/figures/recall_qps_k1.png)、[Recall@100图]({rel}/figures/recall_qps_k100.png)。\n\n'
           '本轮没有统一赢家。WebVid在90% Recall@1门槛下hard为352.5 QPS/90.73%，'
           'NSG为280.9/90.65%；K100同门槛则完整HNSW为283.0/90.3718%，soft为239.4/90.6868%。'
           'Yandex在95% Recall@1门槛下hard为1127.5/95.02%，soft为906.1/95.77%；'
           '99%门槛的反向差异只由L1250上1个query命中差触发，不作普遍优势。'
           'Deep/SIFT的hard/soft曲线非常接近；GIST的K100以完整HNSW更有竞争力，K1高召回需保留NSG/GT10。'
           'GATE正负冲突归零并重训后，仍未显示跨五集稳定优于GT10。hard继续作预先指定主线、固定soft辅助，Web软/Y硬旧默认不变。\n\n'
           '正式阶段15.826小时，07:09结束；已记录离线阶段4.869小时。三次QPS最大/最小相对范围中位数0.441%，最大15.401%，'
           '微小速度差不作强结论。保留[Yandex输入修正](experiment_history/90a_yandex_test_prefix_fix.md)及约70分钟等待中断，'
           '等待不算计算成本；GIST下载校验缺失、Web/Y历史公开测试曝光与新SIFT来源边界均写入分析。')
spec = (f'E97 实现与验收于2026-09-16完成：metric_id绑定IP/L2，K仅1或100，L/ef>=K；完整HNSW使用原生距离。'
        'GATE先从负集合移除全部正hub，再过滤/配对，新模型与E96隔离。'
        '800点、2400次wall、300项跨K核验通过；跨K首ID的212个差异记录限于原距离核验的HNSW等距候选，严格ID评分不变。'
        'Yandex输入显式物化原100K文件的固定前10K行，原文件保留，修订后的183个冻结资产最终身份通过。'
        f'[协议]({rel}/protocol.md)、[数值验收]({rel}/reviews/raw_results_verified.json)、'
        f'[身份验收]({rel}/reviews/final_integrity.json)。\n\n'
        f'E97输出合同：results/metrics.csv为800点；wall_rounds.csv为2400轮；recall_targets.csv为350个预锁门槛选择。'
        f'后处理analysis_thresholds.csv附三次范围并重算核对全部350项；analysis.md解释结果，不反向改模型或网格。'
        f'figures/manifest.json记录28个PNG/PDF，四张总图的实际视觉检查见reviews/figures_visual_check.json。'
        f'complete.json记录report/analysis/metrics哈希，ops/analysis_done.json记录语义分析完成；根文档及报告修订前快照保留于ops/analysis_closeout_before_*。')
target = (f'E97授权工作已完成：五集修复、GATE重训、Recall@1/100重测、绘图和[逐集分析]({rel}/analysis.md)。'
          '保留hard为预先指定研究主线、固定soft作辅助；不根据这轮公开测试自动更换Web软/Y硬默认或按预算拼赢家。'
          '没有待补的LAION、Recall@10、新网格或后续训练。下一步先根据用户提出的新问题确定独立验证范围；'
          '当前结果不能支持“GATE全面无效”“hard全面最优”或“完整HNSW全面支配”。')
experiment = (f'E97（2026-09-15启动，2026-09-16完成）：GATE disjoint-label修复；'
              'WebVid/Yandex/Deep/BIGANN-SIFT/GIST五方法Recall@1/100，共800点、2400次单线程wall，正式阶段15.826小时。'
              f'[详细复盘](experiment_history/{history.name})、[逐集分析]({rel}/analysis.md)、'
              '[Yandex前缀修正与等待中断](experiment_history/90a_yandex_test_prefix_fix.md)。旧默认不变。')
for name, note in [('summary.md', summary), ('spec.md', spec), ('s-target.md', target), ('s-experiment.md', experiment)]:
    p = ROOT / name
    head, _, tail = p.read_text().partition('\n')
    old_first, _, tail = tail.lstrip('\n').partition('\n\n')
    assert old_first.startswith('E97 ' ) or old_first.startswith('E97（'), (name, old_first)
    new = head + '\n\n' + note + '\n\n' + tail
    if name == 'summary.md':
        new = new.replace('当前执行的是新的E97。', '后继E97现也已完成，当前无待恢复的实验。')
    if name == 's-experiment.md':
        new = new.replace('> 更新截至2026-09-15。', '> 更新截至2026-09-16。')
    p.write_text(new)

handoff = RUN / 'handoff.md'
s = handoff.read_text()
head, _, tail = s.partition('\n')
handoff.write_text(head + '\n\n'
    '2026-09-16 FINAL: All five datasets completed at07:09;800 points/2400 timed rounds passed. '
    'Numeric and actual overview visual review PASS; final integrity PASS for183 frozen assets. '
    'Read analysis.md for actual conclusions and report.md for methods. complete.json/state.json include final hashes. '
    'No default changed; no experiment to resume. ops/analysis_done.json certifies completed interpretation. '
    'The hourly timer is being finalized and disabled after this review; consult ops/hourly_status.json for actual final timer status.\n\n'
    'The following paragraphs are preserved chronological handoff notes, superseded by the final status above.\n' + tail)

for name in ['AGENTS.md', 'summary.md', 'spec.md', 's-target.md', 's-experiment.md']:
    before = (RUN / 'source_before' / name).read_text()
    after = (ROOT / name).read_text()
    (RUN / 'reviews/docs' / name).write_text(after)
    (RUN / 'reviews/docs' / (name + '.diff')).write_text(''.join(difflib.unified_diff(
        before.splitlines(True), after.splitlines(True), fromfile='before/' + name, tofile='after/' + name)))

complete = json.loads((RUN / 'complete.json').read_text())
assert complete['status'] == 'COMPLETE'
assert sha(RUN / 'results/metrics.csv') == complete['metrics_sha256']
complete.update(report_sha256=sha(report), analysis_sha256=sha(RUN / 'analysis.md'),
                analysis_completed_beijing=now.isoformat(),
                interpretation_revision=dict(time=now.isoformat(), reason='Add actual five-dataset interpretation, timing variability and preserved Yandex correction',
                                             before_snapshot=str(backup)))
for name in ['complete.json', 'state.json']:
    (RUN / name).write_text(json.dumps(complete, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(status='INTERPRETATION_ATTACHED', snapshot=str(backup),
                     report_sha256=complete['report_sha256'], analysis_sha256=complete['analysis_sha256']), indent=2))
