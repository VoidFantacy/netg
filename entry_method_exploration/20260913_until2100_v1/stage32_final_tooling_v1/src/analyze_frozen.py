from scoring import *
from plot_results import plots
import argparse

def main():
 ap=argparse.ArgumentParser(description='Verify and report a completed separately frozen final matrix.');ap.add_argument('run_directory');args=ap.parse_args();threads();run=Path(args.run_directory).resolve();lock,budget=validate_frozen(run);jobs=read(run/'logs/jobs.json');assert len(jobs)==2 and [j['dataset'] for j in jobs]==DS and all(j['status']=='COMPLETE' and j['returncode']==0 and j['peak_threads']==1 and j['affinity']==[15] for j in jobs);out=run/'analysis_v1';assert not out.exists();sel=read(run/'selection.json');allrows={k:[] for k in ['points','timings','paired','failures']};verification=[];started=time.monotonic()
 for ds in DS:
  c=read(run/'inputs'/ds/'config.json');roles={k:sel['datasets'][ds][k] for k in ['best_all','best_new']};a=analyze_dataset(c,run/'results'/ds,roles)
  for k in allrows:allrows[k].extend(a[k])
  verification.append(dict(dataset=ds,**a['verification']))
 out.mkdir()
 for k,v in allrows.items():table(out/(k+'.csv'),v)
 assert sum(j['actual_NSG'] for j in jobs)==budget['NSG'];dump(out/'verification.json',dict(status='PASS',datasets=verification,selection_frozen_unchanged=True,new_ANN_during_analysis=0,analysis_seconds=time.monotonic()-started));dump(out/'cost.json',dict(**budget,ordinary_builds=0,new_training=0,new_GT=0,compile_seconds=0,native_operation_seconds=sum(j['seconds'] for j in jobs),complete_wall_seconds=sum(v['pure_wall_seconds'] for v in verification),source_load_seconds=sum(v['source_load_seconds'] for v in verification),count_load_seconds=sum(v['count_load_seconds'] for v in verification),route_only_seconds=None,graph_only_seconds=None,component_reason='Not separately measured; full route+NSG+output wall is recorded.',inherited_training_GT_total_seconds=None,inherited_cost_reason='Historical model/GT costs not remeasured and must be linked in final narrative.'))
 plots(out,'Final E34 historical validation 2,000 | CPU15, one thread | five complete wall batches')
 lines=['# 冻结最终矩阵：数值与失败查询','', '这是预冻模型在E34历史validation2000的最终对照；结果不可回流训练或选型，不称全项目从未观察。完整原NSG/Fast/GT10匹配起点/真实新方法同批五L五轮，计时覆盖路由、原NSG和输出，GT/count/hash/JSON/build/load在外。', '', '| 数据 | 方法 | L | Recall% | QPS中位[范围] | 零命中率% |','|---|---|---:|---:|---|---:|']
 for p in allrows['points']:lines.append(f"| {p['dataset']} | {p['model']} | {p['L']} | {p['recall_pct']:.4f} | {p['QPS']:.2f} [{p['QPS_min']:.2f}, {p['QPS_max']:.2f}] | {p['failure_rate_pct']:.4f} |")
 lines+=['', 'QPS范围是五轮实测范围，不是置信区间；同LRecall增量不是前沿性能GO。最终方法判断仍需根据此同批完整曲线及配对损益写出，不从单点或计数宣称胜出。', '', f"{budget['points']}点/{budget['wall_batches']}完整wall，{budget['NSG']} NSG/{budget['HNSW']} HNSW；0训练/新GT/普通构图。组件wall未分测，历史离线成本缺项保留。", '', '[所有点](points.csv) · [每轮wall](timings.csv) · [配对救回/新增与成员损益](paired.csv) · [全部零命中query×L×method](failures.csv) · [核验](verification.json) · [成本](cost.json)', '', '![QPS–Recall](figures/recall_qps.png)', '', '![QPS–失败](figures/failure_qps.png)', '', '![按L三指标](figures/three_metrics_by_L.png)']
 (out/'report.md').write_text('\n'.join(lines)+'\n');check(run/'reviews/prequery_freeze.json');print('FINAL_ANALYSIS_VERIFIED',budget)
if __name__=='__main__':main()
