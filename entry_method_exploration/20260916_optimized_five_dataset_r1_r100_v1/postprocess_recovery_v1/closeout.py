"""Record the completed postprocessing recovery and the actually reviewed figures."""
from pathlib import Path
import datetime, hashlib, json, shutil, subprocess

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[1]
REC = RUN / 'postprocess_recovery_v1'
read = lambda p: json.loads(p.read_text())
def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(16 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()
def dump(p, value):
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

now = datetime.datetime.now().astimezone()
done = read(RUN / 'complete.json')
assert done['status'] == 'COMPLETE_AUTOMATED_RESULTS_PENDING_VISUAL_REVIEW'
assert sha(RUN / 'results/metrics.csv') == done['metrics_sha256']
for name, digest in read(RUN / 'reviews/frozen.json').items():
    assert sha(name) == digest, name
backup = read(RUN / 'reviews/git_backup.json')
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == backup['main_head_unchanged']
assert sha(ROOT / '.git/index') == backup['index_unchanged_sha256']
figures = read(RUN / 'figures/manifest.json')['files']
assert len(figures) == 28
for name, digest in figures.items():
    assert sha(RUN / 'figures' / name) == digest

snapshot = REC / 'before_manual_closeout'
snapshot.mkdir()
names = ['report.md', 'complete.json', 'state.json', 'reviews/final_numeric_review.json', 'results/offline_and_evaluation_costs.json']
for name in names:
    q = snapshot / name
    q.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RUN / name, q)
docs = ['experiment_history/96_optimized_five_dataset_retest.md', 's-experiment.md', 'summary.md', 'spec.md', 's-target.md']
for name in docs:
    q = snapshot / 'root_docs' / name
    q.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / name, q)

interpretation = '''完整曲线支持GT10仍有实际收益，但收益随数据集和K变化：

- WebVid：达到90% Recall@1时，既有默认soft为520.79 QPS、实际Recall 90.75%，NSG为416.68 QPS、90.65%，门槛下吞吐高24.99%；GATE为507.84 QPS、90.34%。Recall@100同门槛soft仅比NSG高0.79%，优势已很小。中低召回区间的曲线分离更清楚。
- Yandex：既有默认hard在90%门槛的Recall@1/100吞吐分别比NSG高9.63%/6.96%；95% Recall@1门槛为1332.80对1029.27 QPS，主要来自hard在L=256达到95.02%，NSG需L=320达到95.39%。99% Recall@1门槛则是soft均值最快，不能把两者逐门槛拼成一个部署方法。
- Deep：90%門槛soft的Recall@1/100吞吐分别比NSG高17.44%/6.22%，但这些点实际Recall已在94.13%/92.60%左右，并非恰好90%；NSG实际Recall略高。高召回下差距收窄。
- BIGANN-SIFT：90%门槛soft的Recall@1/100吞吐分别比NSG高6.01%/3.19%；99% Recall@100门槛只高约1.30%。90%与95%的Recall@1门槛复用了同一个L=32实测点，门槛计数并非独立证据。
- GIST：GT10相对NSG没有稳定收益。95% Recall@1门槛NSG在L=128恰好达到95.0%、966.24 QPS，soft要L=160达到95.8%、805.04 QPS；99% Recall@1和Recall@100门槛也由NSG均值最快。这里不能用优于HNSW/GATE代替优于NSG。

22/25是hard与soft两个固定模型组成的家族在离散门槛上的计数；不是单个模型的胜率，不表示22个独立显著胜出。完整曲线、实际召回和三次计时范围应一起阅读。总体判断是WebVid/Yandex收益较清楚，Deep/SIFT有较小到中等收益，GIST对NSG基本持平或落后。'''.replace('門槛', '门槛')

recovery_note = '''搜索矩阵于2026-09-17清晨完成，原流水线05:30:15在分析阶段因计时记录重复传入K字段而停止。已有搜索、运行后身份检查和原始计时不受影响。08:17起使用独立postprocess_recovery_v1/analyze.py核验K后汇总，重新独立评分并绘图；原冻结源码未修改，新增搜索为0。首次出图的左侧轴标签边界过紧，保留初版图后仅调整导出留白，直接从同一800行CSV重绘。四张总览PNG已实际目视检查，28份PNG/PDF均核验哈希；单集图/PDF未逐张目视验收。失败状态、日志、初版分析器和初版图均保留在恢复目录。'''

p = RUN / 'report.md'
s = p.read_text()
marker = '![Recall@1](figures/recall_qps_k1.png)'
assert s.count(marker) == 1
s = s.replace(marker, '## 完整曲线的结论\n\n' + interpretation + '\n\n' + marker)
old = '图像已自动生成，人工目视检查状态单列于complete.json；自动流水线不声称完成未实际进行的视觉验收。'
assert old in s
s = s.replace(old, '## 收尾修复与验收\n\n' + recovery_note + '\n\n[恢复记录](postprocess_recovery_v1/recovery.json) · [图像检查](reviews/visual_review.json)。')
p.write_text(s)

# Keep detailed history and overview synchronized before updating current summary.
p = ROOT / docs[0]
s = p.read_text().replace('图和分析已自动生成，人工图像检查待完成。', '图表、分析与四张总览图的目视检查已完成。')
p.write_text(s + '\n## 完整矩阵结论\n\n' + interpretation + '\n\n## 收尾修复\n\n' + recovery_note + '\n')
rel = str(RUN.relative_to(ROOT))
links = f'[报告与新图]({rel}/report.md) · [复盘96](experiment_history/96_optimized_five_dataset_retest.md)。'
conclusion = '可达的25个90/95/99%门槛组合中，GT10-hard/soft家族平均QPS最快22个；不是单一模型胜率或显著性结论。WebVid/Yandex收益较清楚，Deep/SIFT较小到中等，GIST相对NSG基本持平或落后。'
headlines = {
    's-experiment.md': 'E103五集优化重测已完成：800配置、2400轮单线程计时、3280万次搜索，约13小时；Recall@1/100、排除LAION。' + conclusion + ' 搜索完成后汇总K字段冲突已通过独立后处理修复，无重跑；评分、图表和总览目视检查完成，旧源码/结果保留。' + links,
    'summary.md': 'E103已完成统一优化后的WebVid、Yandex、Deep、BIGANN-SIFT、GIST五集Recall@1/100重测：800配置、2400轮单线程plain、3280万次搜索，约13小时。四种NSG入口共用span+batch4，HNSW同轮计时；4000份原始输出/入口/距离计数与E97一致，Recall独立重算通过。' + conclusion + ' WebVid默认soft在90%门槛下R1/R100吞吐比NSG高24.99%/0.79%，Yandex默认hard高9.63%/6.96%。图表分析和总览目视检查均完成；收尾汇总错误已修复，无新搜索。优化仅在独立评测入口，生产保持E99，默认Web soft/Yandex hard未变。' + links,
    'spec.md': 'E103完整矩阵数值与图表验收完成；五集metric/shape显式校验、32预算×5方法，四入口共用span+batch4，HNSW原生metric同轮。全部warm/plain输出及count逐query NDC对齐E97，4000份raw文件哈希及独立GT/float64距离检查通过。原src/analyze.py存在重复K关键词兼容错误，独立postprocess_recovery_v1/analyze.py校验K后合并字段；仅修后处理与绘图导出留白，无新查询、kernel/数据/模型变更。该恢复路径生成metrics、图和报告，不能重跑旧run.py以修汇总。生产API/trace/默认保持。' + links,
    's-target.md': 'E103用户授权的完整五集优化重测、分析和图表检查均已完成，没有待运行的E103测试。' + conclusion + ' 当前结果支持继续整理GT10的适用范围和论文证据，不支持宣称全部数据集全面支配NSG。没有自动授权额外训练、扩预算、换默认或部署；生产仍E99，Web soft/Yandex hard保持。' + links,
}
for name in docs[1:]:
    p = ROOT / name
    parts = p.read_text().split('\n\n', 2)
    assert parts[1].startswith('E103')
    p.write_text(parts[0] + '\n\n' + headlines[name] + '\n\n' + parts[2])

reviewed = ['recall_qps_k1.png', 'recall_qps_k100.png', 'failed_query_rate_k1.png', 'failed_query_rate_k100.png']
dump(RUN / 'reviews/visual_review.json', dict(status='PASS', reviewed_at=now.isoformat(), reviewer='Codex visual inspection via view_image', files={name: figures[name] for name in reviewed}, checks=['All five datasets and methods labeled; K1/K100 distinguished.', 'Axes, titles, footer, legends and full left Y labels visible after margin fix.', 'Curves agree with threshold tables; overlapping curves retained.', 'Deep/SIFT/GIST near-zero K100 failure rates preserved, not treated as recall parity.'], other_figure_scope='10 individual PNGs and all PDFs hash-verified, not individually visually reviewed.'))
recovery = read(REC / 'recovery.json')
recovery.update(status='COMPLETE', completed_at=now.isoformat(), wall_seconds_including_review=(now - datetime.datetime.fromisoformat(recovery['started_at'])).total_seconds(), new_search_calls=0, metrics_sha256=sha(RUN / 'results/metrics.csv'), figures_manifest_sha256=sha(RUN / 'figures/manifest.json'), report_sha256=sha(RUN / 'report.md'))
dump(REC / 'recovery.json', recovery)
costs = read(RUN / 'results/offline_and_evaluation_costs.json')
costs.append(dict(stage='postprocess_recovery_including_manual_review', seconds=recovery['wall_seconds_including_review'], status='PASS', log=str(REC / 'analyze.log'), new_search_calls=0, scope='Wall time includes operator review, not only analyzer execution.'))
dump(RUN / 'results/offline_and_evaluation_costs.json', costs)
done.update(status='COMPLETE', automated_closeout_at=done['completed_at'], completed_at=now.isoformat(), manual_figures_review=True, visual_review_scope='Four overview PNGs; all 28 image/PDF file hashes verified.', postprocess_recovery='postprocess_recovery_v1/recovery.json', report_sha256=sha(RUN / 'report.md'), figures_manifest_sha256=sha(RUN / 'figures/manifest.json'), new_search_calls_during_recovery=0)
dump(RUN / 'complete.json', done)
dump(RUN / 'state.json', done)
numeric = read(RUN / 'reviews/final_numeric_review.json')
numeric.update(final_closeout_at=now.isoformat(), manual_figures_review=True, visual_review='reviews/visual_review.json', frozen_sources_still_unchanged=True, plots_reexported_without_new_search=True)
dump(RUN / 'reviews/final_numeric_review.json', numeric)
dump(REC / 'closeout_manifest.json', dict(status='PASS', completed_at=now.isoformat(), code_sha256=sha(__file__), root_docs={name: sha(ROOT / name) for name in docs}, final_files={name: sha(RUN / name) for name in ['report.md', 'state.json', 'complete.json', 'results/metrics.csv', 'figures/manifest.json', 'reviews/visual_review.json', 'reviews/final_numeric_review.json']}))
print(json.dumps(done, ensure_ascii=False))
