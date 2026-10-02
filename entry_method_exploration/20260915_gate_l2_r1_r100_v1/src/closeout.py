from common import *
import csv, difflib
from datetime import datetime
from zoneinfo import ZoneInfo

def readrows(name):
    with (RUN/'results'/name).open() as f:return list(csv.DictReader(f))

def closeout():
    assert json.loads((RUN/'reviews/raw_results_verified.json').read_text())['status']=='PASS'
    assert (RUN/'reviews/figures_visual_check.json').exists(),'inspect generated figures before closeout'
    frozen=json.loads((RUN/'reviews/frozen_models.json').read_text());t=time.time();checked=0
    for p,h in frozen['sources'].items():assert sha(p)==h,('frozen source changed',p)
    for p,r in frozen['protected'].items():
        f=Path(p);assert f.stat().st_size==r['bytes'] and sha(f)==r['sha256'],('frozen model/base changed',p);checked+=1
    for rec in json.loads((RUN/'reviews/preflight.json').read_text())['datasets']:
        c=json.loads((RUN/'inputs'/rec['dataset']/'manifest.json').read_text())
        assert sha(c['paths']['query_path'])==rec['query_sha256'] and sha(c['paths']['gt_path'])==rec['gt_sha256'],'test identity changed after preflight'
    for ds in ['webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1']:
        reused=json.loads((RUN/'inputs'/ds/'reuse.complete.json').read_text())
        for p,r in reused['protected'].items():assert Path(p).stat().st_size==r['bytes'] and sha(p)==r['sha256'],('historical reused asset changed',p)
    dump(RUN/'reviews/final_integrity.json',dict(status='PASS',frozen_artifacts_checked=checked,seconds=time.time()-t,historical_reused_assets_unchanged=True))
    from analyze import ORDER,LABELS,DISPLAY
    rows=readrows('metrics.csv');targets=readrows('recall_targets.csv')
    model_rows=frozen['datasets'];costs=json.loads((RUN/'results/offline_and_evaluation_costs.json').read_text())
    offline=sum(x['seconds'] for x in costs if not x['stage'].startswith('formal_'))
    evaluation=sum(x['seconds'] for x in costs if x['stage'].startswith('formal_'))
    text=['# E97：修正 GATE 后的五集 Recall@1/100 重测','',
      '已完成 WebVid、Yandex、Deep、BIGANN-SIFT、GIST 五集，排除 LAION。五方法 × 两种 K × 16 档搜索预算，共800个正式点、2400次单线程端到端计时。所有结论来自新返回与新计时，旧 Recall@10 不参与。','',
      'GATE 负集合现在先移除同一 query 的全部正 hub，再筛选和配对。五集实际 triplet 均无正负冲突、无同一 query 同时作正负；选中 checkpoint 与导出画像已核对。WebVid/Yandex 复用身份兼容的底图、hub/子图特征、hop 缓存及完整 HNSW，GATE 模型重新训练。','',
      '新 L2 数据保留原始向量。SIFT 使用公开 BIGANN 首10M与独立公开 query/learn，替代旧本地非标准11.16M及从base抽query的版本；不能拼接旧 SIFT 数值。GIST 使用现有原始标准规模文件，但缺少原下载校验清单，这个来源限制保留。新三集 GT100 都从完整底库精确计算，并用独立 float64 直接距离检查；GT10-hard 为预先指定的主线，soft 仅使用 fit 确定的固定温度。','',
      '所有方法固定CPU15，进程/OMP/BLAS/MKL均单线程，一次warmup、三次普通计时及独立计数，重复ID/距离/入口逐位一致。QPS包含路由、归一化、ID映射、图搜索和写入预分配返回数组；不包含加载、构图、GT评分和磁盘写出。完整 HNSW 与所有 NSG 方法使用相同原生距离与完整底库。','',
      '## 新图','',
      '![Recall@1 与 QPS](figures/recall_qps_k1.png)','',
      '![Recall@100 与 QPS](figures/recall_qps_k100.png)','',
      '阴影为三次QPS的实测范围；连线保留全部16点。零命中图、每集独立图及PDF见 [figures](figures/manifest.json)。','',
      '## 相同召回门槛的实测速度','',
      '下表取达到90%召回门槛的最快实测点，未达到记为“未达到”。不插值、不外推；数值为QPS。门槛和实际Recall可能存在离散预算差异，完整0.5至0.99门槛及L在CSV中。','',
      '| 数据集 | K | NSG | GT10 hard | GT10 soft | GATE修正 | 完整HNSW |','|---|---:|---:|---:|---:|---:|---:|']
    table=[]
    for ds in ORDER:
        for k in [1,100]:
            vals=[]
            for method in ['NSG','GT10-hard','GT10-soft-t1','GATE','HNSW']:
                r=next(r for r in targets if r['dataset']==ds and int(r['K'])==k and r['method']==method and float(r['target_recall'])==.9)
                vals.append(f"{float(r['qps']):,.0f}" if r['achieved']=='True' else '未达到')
            line='| '+LABELS[ds]+' | '+str(k)+' | '+' | '.join(vals)+' |';text.append(line);table.append(line)
    text+=['','这里比较的是五集公开查询的实测曲线。WebVid/Yandex 公共测试在旧实验中已经使用；新 L2 数据结果也不能代表所有查询分布。不凭同L或单个QPS差值宣布部署收益，不自动覆盖旧默认方案。','',
      '## 训练与成本','',
      '| 数据集 | 有效 triplet | 训练轮数 | GATE训练秒 | 导出最大误差 |','|---|---:|---:|---:|---:|']
    for r in model_rows:text.append(f"| {LABELS[r['dataset']]} | {r['train_triplets']:,} | {r['training_epochs']} | {r['training_seconds']:.1f} | {r['checkpoint_export_max_abs']:.2g} |")
    text+=['',f'本轮已记录的离线阶段合计 {offline/3600:.2f} 小时；正式评测阶段总wall {evaluation/3600:.2f} 小时（含加载、warmup、计数及写出，不能倒算为查询QPS）。模型最终核验和图文整理单列于各review；复用资产的旧成本不算新构建成本，也不把未知历史成本记为零。进程峰值内存观察见 [资源记录](reviews/offline_resource_observations.json)。','',
      '新三集GT10流程：独立5000 query按球面聚类选800个真实GT hub；独立fit的20000 query取各自精确GT前10目标，按目标与原hub的cosine硬归属或soft权重分配，每query总权重1；累加单位query方向，加单位raw-hub先验1，最终画像单位化。在线只在Micro-HNSW中选3个真实入口，再查原NSG。','',
      'GATE流程：完整底库32×16 HBKM选512真实hub；每hub按5近5远/最多5跳1000节点抽子图，WL2与Doc2Vec得到结构特征；10000 train与1024独立monitor对每hub执行L64/K1搜索，真实发现深度生成正负标签；修正后cosine triplet训练batch-first网络，Adam1e-5，batch16384，最多200轮、patience20；用monitor选checkpoint、导出512画像。网络不在线运行。1000节点截断、Sinkhorn近似聚类与统一项目kernel属于已披露适配。','',
      '## 可核验产物','',
      '- [800点完整指标](results/metrics.csv)、[2400次wall](results/wall_rounds.csv)、[召回门槛比较](results/recall_targets.csv)。',
      '- [逐query配对](results/paired_queries.csv)、[完整阶段成本](results/offline_and_evaluation_costs.json)；所有原始ID、距离、入口、NDC和hit向量保存在results各数据集目录。',
      '- [合成修复验证](reviews/changes_verified.json)、[模型冻结](reviews/frozen_models.json)、[正式前检查](reviews/preflight.json)、[完整返回核验](reviews/raw_results_verified.json)、[最终身份核验](reviews/final_integrity.json)。',
      '- [锁定配置](config.locked.json)、[协议](protocol.md)、[实现源码](src/evaluate.cpp)。','']
    (RUN/'report.md').write_text('\n'.join(text))
    relative=str(RUN.relative_to(ROOT));history=ROOT/'experiment_history/90_gate_disjoint_five_datasets_r1_r100.md'
    history.write_text('# E97：GATE正负标签修正与五集Recall@1/100\n\n'+f'已完成800点、2400次单线程wall，数据为WebVid、Yandex、Deep、BIGANN-SIFT、GIST，排除LAION。GATE五集新训练，GT10-hard/soft固定对照和NSG、完整HNSW同口径重测。详见[完整复盘](../{relative}/report.md)、[CSV](../{relative}/results/metrics.csv)和[原始配置](../{relative}/config.locked.json)。\n\n底图/向量/模型/GT及E96旧结果保留；新SIFT来源变化、GIST下载校验限制、历史测试曝光、离线成本与指标口径均在复盘中披露。未因本次公开测试自动替换默认方法。\n')
    additions={
      'summary.md':f'E97 已完成：五集 WebVid/Yandex/Deep/BIGANN-SIFT/GIST，排除 LAION；Recall@1/100 共800点、2400次单线程端到端计时，图已重画。GATE正负标签冲突归零并重新训练，GT10-hard、固定soft、NSG及完整HNSW一并重测。旧默认未自动替换。[结果与成本]({relative}/report.md)、[完整指标]({relative}/results/metrics.csv)、[Recall@1图]({relative}/figures/recall_qps_k1.png)、[Recall@100图]({relative}/figures/recall_qps_k100.png)。',
      'spec.md':f'E97 实现与验收已完成：metric_id显式绑定IP/L2、K仅1或100、L/ef>=K；完整HNSW使用原生距离。GATE先从负集合移除全部正hub，再过滤和配对，新模型和旧E96隔离。800点通过线程、plain/count、全部返回评分、跨K首距离/入口及同距tie及冻结身份核验。[实现与接口]({relative}/protocol.md)、[验收]({relative}/reviews/raw_results_verified.json)。',
      's-target.md':f'E97 已完成当前授权的五集修复、重训、Recall@1/100重测与绘图；未启动LAION、新网格或后续训练。当前可据[完整结果]({relative}/report.md)讨论下一步；继续保留GT10-hard为新三集预先指定主线、soft为固定辅助，不根据公开测试自动改旧默认。',
      's-experiment.md':f'E97（2026-09-15，完成）：GATE disjoint-label修复；WebVid/Yandex/Deep/BIGANN-SIFT/GIST的五方法Recall@1/100，共800点、2400次单线程wall。[详细复盘](experiment_history/{history.name})、[新图及结果]({relative}/report.md)。'}
    for name,note in additions.items():
        p=ROOT/name;s=p.read_text();first,sep,rest=s.partition('\n')
        prefixes={'summary.md':'当前执行：E97','spec.md':'E97 接口增量','s-target.md':'当前任务：完成已授权的 E97','s-experiment.md':'E97（2026-09-15，执行中）'}
        parts=rest.lstrip('\n').split('\n\n',1)
        if parts[0].startswith(prefixes[name]):rest=parts[1] if len(parts)>1 else ''
        p.write_text(first+'\n\n'+note+'\n\n'+rest.lstrip('\n'))
    idx=ROOT/'experiment_history/README.md';idx.write_text(idx.read_text()+f'\n- [E97 GATE修复与五集Recall@1/100]({history.name})：800点、2400次wall及重画图。\n')
    docs=RUN/'reviews/docs';docs.mkdir(exist_ok=True)
    for name in ['AGENTS.md','summary.md','spec.md','s-target.md','s-experiment.md']:
        (docs/name).write_text((ROOT/name).read_text())
        before=(RUN/'source_before'/name).read_text();after=(ROOT/name).read_text()
        (docs/(name+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='before/'+name,tofile='after/'+name)))
    complete=dict(status='COMPLETE',datasets=DATASETS,excluded=['laion10m_acsg_v1'],K=[1,100],points=800,wall_rounds=2400,threads=1,unix=time.time(),report_sha256=sha(RUN/'report.md'),metrics_sha256=sha(RUN/'results/metrics.csv'),new_default_adopted=False,completed_beijing=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat())
    dump(RUN/'complete.json',complete);dump(RUN/'state.json',complete);print('E97_COMPLETE',flush=True)

if __name__=='__main__':closeout()
