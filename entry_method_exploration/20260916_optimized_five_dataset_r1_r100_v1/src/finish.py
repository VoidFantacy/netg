from common import *
import csv,datetime,subprocess,shutil
read=lambda p:json.loads(p.read_text());now=datetime.datetime.now().astimezone().isoformat()
a=read(RUN/'reviews/raw_results_verified.json');assert a['status']=='PASS' and a['points']==800 and a['wall_rounds']==2400 and a['reference_raw_files']==4000 and a['actual_batch4_count']
assert read(RUN/'reviews/post_run_identity.json')['status']=='PASS'
done=read(RUN/'results/completed_datasets.json');assert len(done)==5 and sum(x['search_calls'] for x in done)==32800000
for x in read(RUN/'reviews/frozen.json').items():assert sha(x[0])==x[1],x[0]
backup=read(RUN/'reviews/git_backup.json');assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==backup['main_head_unchanged'];assert sha(ROOT/'.git/index')==backup['index_unchanged_sha256']
fig=read(RUN/'figures/manifest.json');assert fig['status']=='PASS'
for n,h in fig['files'].items():assert sha(RUN/'figures'/n)==h
p=RUN/'results/threshold_comparisons.json';comparisons=read(p);valid=[x for x in comparisons if x['mean_fastest']];first=sum(x['gt10_mean_fastest'] for x in valid);group=sum(x['gt10_in_overlap_group'] for x in valid)
rel=str(RUN.relative_to(ROOT));headline=f'E103于{now}完成统一优化后五集完整重测：800配置、2400轮单线程plain、32800000次真实搜索；NSG/hard/soft/GATE同一span+batch4，HNSW同轮重新计时。全部返回/入口/逐query NDC对齐E97，Recall独立重算。90/95/99%门槛中{len(valid)}个组合至少一方法达到，GT10均值最快{first}个、进入三轮范围重叠组{group}个；范围重叠不是显著性判断。图和分析已自动生成，人工图像检查待完成。无训练/新图/GT/默认变更。'
links=f'[报告与新图]({rel}/report.md) · [复盘96](experiment_history/96_optimized_five_dataset_retest.md)。'
card=ROOT/'experiment_history/96_optimized_five_dataset_retest.md'
cardtext='# E103：优化后的五集完整重测\n\n'+headline+'\n\n用户根据E102结果有条件授权重测；条件仅依据已完成四点GT10仍处最好一组，不先声称五集全面第一。复用E97五集公开查询和每K原16档预算，排除LAION与Recall@10，原模型和数据保持。门槛表取达到目标召回的最快实测点，不插值，实际Recall、L、重复范围全部保留；完整分析必须看各集差异。\n\n独立后台流水线依次冻结、测试、全量历史结果和输入身份对照、GT评分、float64距离抽检、跨K核验、画图和分析。单线程CPU15，端到端包含路由/search/output；计数直接转发真实batch4。无自动重试或选最快轮。\n\n本轮优化仅用于独立评测入口，生产仍E99。Git备份cd3a3229；旧资产/main/index保留，原公开query曝光和GIST来源校验限制保留。\n\n[完整报告](../'+rel+'/report.md) · [协议](../'+rel+'/protocol.md) · [数值验收](../'+rel+'/reviews/raw_results_verified.json)\n'
notes={'summary.md':headline+' '+links,'spec.md':'E103完整矩阵数值验收完成；五集metric/shape显式校验、32预算×5方法，四入口共用相同span+batch4，HNSW原生metric同轮。全部warm/plain输出及count逐query NDC对齐E97，4000份raw文件哈希复核及独立GT/float64距离检查通过。生产API/trace/默认保持。'+links,'s-target.md':'E103用户授权的完整优化重测与自动图表分析已完成；当前待人工查看生成图像。'+headline+' 不据公开结果自动换模型、扩预算或部署。'+links,'s-experiment.md':headline+' '+links}
expected=read(RUN/'reviews/root_docs_start.json');unchanged=all(sha(ROOT/n)==h for n,h in expected.items());docstatus='UPDATED' if unchanged else 'SKIPPED_EXTERNAL_EDITS_PRESERVED'
if unchanged:
 snap=RUN/'reviews/docs_before_automatic_closeout';snap.mkdir()
 for n in expected:
  p=ROOT/n;q=snap/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 for n,note in notes.items():
  p=ROOT/n;parts=p.read_text().split('\n\n',2);assert parts[1].startswith('E103');p.write_text(parts[0]+'\n\n'+note+'\n\n'+parts[2])
 card.write_text(cardtext)
else:
 dump(RUN/'reviews/pending_doc_updates.json',dict(notes=notes,history_card=cardtext,reason='Root documents changed since launch; preserve current user work.'))
complete=dict(status='COMPLETE_AUTOMATED_RESULTS_PENDING_VISUAL_REVIEW',completed_at=now,points=800,wall_rounds=2400,real_search_calls=32800000,threads=1,automatic_analysis=True,figures_generated=True,manual_figures_review=False,production_changed=False,default_changed=False,root_docs=docstatus,report_sha256=sha(RUN/'report.md'),metrics_sha256=sha(RUN/'results/metrics.csv'))
dump(RUN/'complete.json',complete);dump(RUN/'state.json',complete);dump(RUN/'reviews/final_numeric_review.json',dict(status='PASS',reviewed_at=now,points=800,raw_files=4000,reference_output_and_ndc_parity=True,all_assets_rehashed_after_search=True,frozen_code_unchanged=True,git_backup_main_index_verified=True,manual_figures_review=False))
print(json.dumps(complete,ensure_ascii=False))
