#!/usr/bin/env python3
"""Write Chinese E176 delivery from actual audited metrics and actual receipts.
Source creation does not execute this file. No GT/raw/vector/distance/CI access.
"""
import argparse
import hashlib
import json
import math
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATASETS=('webvid2_5m_light_v1','yandex_t2i_official10M_ip_v1')
LABELS=dict(zip(DATASETS,('WebVid2.5M','YandexT2I')))
def require(ok,msg):
    if not ok:raise ValueError(msg)
def load(path):
    p=Path(path);require(p.stat().st_size<64*1024*1024,'bounded metadata only');return json.loads(p.read_text())
def stat4(path):
    s=Path(path).stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]
def sha(path):
    p=Path(path);before=stat4(p);require(before[2]<64*1024*1024,'small metadata/source hash only');h=hashlib.sha256(p.read_bytes()).hexdigest();require(stat4(p)==before,'stable small hash');return h
def link(name,path):return f'[{name}]({Path(path).resolve()})'
def fmt(x,n=4,signed=False):return format(x,('+' if signed else '')+f'.{n}f')
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join('---' for _ in headers)+' |']+['| '+' | '.join(str(x) for x in r)+' |' for r in rows])
def trend(rows,field):return '/'.join(str(sum((r[field]>0,r[field]==0,r[field]<0)[i] for r in rows)) for i in range(3))
def ranges(rows,field):return f"[{fmt(min(r[field] for r in rows),signed=True)}, {fmt(max(r[field] for r in rows),signed=True)}]" if rows else '未冻结此对照'
def pk(p):return p['dataset'],p['K'],p['L'],p['method']
def ck(c):return c['dataset'],c['K'],c['L'],c['method'],c['reference_L'],c['reference']
def select(rows,a,b,same=True):return [r for r in rows if r['method']==a and r['reference']==b and ((r['L']==r['reference_L']) is same)]
def elapsed(record):
    # Missing/unmeasured administrative failures remain None, never invented0.
    for key in ('elapsed_seconds','actual_elapsed_seconds','total_elapsed_seconds'):
        if key in record:return record[key]
    return None

def main():
    started=time.monotonic();parser=argparse.ArgumentParser();parser.add_argument('--metrics',type=Path,default=ROOT/'analysis/final_v1/metrics.json');parser.add_argument('--out',type=Path,default=ROOT/'analysis/final_v1/report.md');args=parser.parse_args()
    require(args.metrics.is_absolute() and args.out.is_absolute() and not args.out.exists(),'fresh absolute report')
    state=load(ROOT/'run_state.json');require(state['status']=='NATIVE_COMPLETE_PENDING_INDEPENDENT_GT_EVALUATION' and state.get('active') is None and len(state['completed'])==2 and all(j['exit_code']==0 for j in state['completed']),'actual all-native completion')
    audit_path=ROOT/'reviews/independent_result_audit/report.json';audit=load(audit_path);require(audit['status']=='PASS_E176_INDEPENDENT_DYNAMIC_INTEGER_WALL_TRACE_AUDIT','actual independent audit PASS')
    binding=audit['source_sha256_and_stat4'][str(args.metrics)];require(binding['sha256']==sha(args.metrics) and binding['stat4']==stat4(args.metrics),'audited metrics byte binding')
    for path,record in audit['source_sha256_and_stat4'].items():require(stat4(path)==record['stat4'],'current audited sources')
    plot_path=ROOT/'reviews/plot_curves_execution.json';plot=load(plot_path);require(plot['status']=='PASS_E176_PRECOMPUTED_DYNAMIC_BUDGET_CURVES' and plot['metrics']==str(args.metrics) and plot['metrics_audited_sha256_and_stat4']==binding and plot['saved_point_fields_exactly_equal'] is True,'actual audited curves completed')
    for path,digest in plot['output_sha256'].items():require(sha(path)==digest,'actual figure bytes')
    data=load(args.metrics);lock=load(ROOT/'parameter_lock.json');require(data['status']=='COMPLETE_E176_DYNAMIC_FROZEN_EVALUATION' and data['default_replacement'] is False and data['test_no_training'] is True and data['primary_method']==lock['primary_method'],'final scientific scope and default retained')
    require(len(data['points'])==audit['point_count'] and len(data['comparisons'])==audit['comparison_count'] and len(data['mechanisms'])==audit['mechanism_count'],'exact audited dimensions')
    points={pk(p):p for p in data['points']};comparisons=data['comparisons'];mechanisms=data['mechanisms'];names=list(dict.fromkeys(p['method'] for p in data['points']))
    configs=[load(p) for p in lock['jobs']];expected={(c['dataset'],K,L,m['name']) for c in configs for K in c['K_values'] for L in c['L'] for m in c['methods']};require(set(points)==expected,'dynamic frozen full point matrix')
    required=[ROOT/'protocol.md',ROOT/'parameter_lock.json',ROOT/'execution_lock.json',args.metrics,audit_path,plot_path]+[ROOT/f'analysis/final_v1/{x}.csv' for x in ('points','comparisons','mechanisms')]
    before={str(p):stat4(p) for p in required};before.update({p:record['stat4'] for p,record in audit['source_sha256_and_stat4'].items()})
    lines=['# E176：残差条件补全与完整 wall 曲线','',f"本轮实际完成 {audit['point_count']} 点、{audit['formal_timed_batches']} 个计时批次、{audit['comparison_count']} 个事先固定比较、{audit['mechanism_count']} 个完整候选机制记录，独立整数、原始返回、wall 与 trace 审计已通过。保持 GT10 默认，保留原 M5 研究基线。公共测试为既有已曝光 10K 单角色，不能称为新的可靠确认。",'',f"方法：{', '.join(names)}。两数据集均继承原 raw-IP、K=1/100、L=200/400/800/1000/1200；串行 CPU15 单线程，每点三轮完整正常 Batch 生命周期。新 FIT 是用户授权的独立实际阶段；formal test 不训练。split 的 source/role tuple 继承历史登记，本次只核 frozen TRAIN/public 窗口 exact-byte 查询去重与源行身份，不构成对全部历史角色语义独立性的重新证明。所有数值来自 {link('metrics.json',args.metrics)}，全部实测点见 {link('points.csv',ROOT/'analysis/final_v1/points.csv')}。",'', '## 曲线与判定范围','']
    for stem,label in [('recall_qps_budget_curves','主方法曲线'),('mechanism_budget_curves','优化与等预算补全对照')]:
        png=ROOT/f'analysis/final_v1/figures/{stem}.png';svg=png.with_suffix('.svg');csv=png.with_suffix('.csv')
        if png.exists():lines += [f"![{label}]({png})",'',f"{link('SVG',svg)} · {link('精确绘图字段CSV',csv)}",'']
    lines += ['横轴 Recall，纵轴完整 wall QPS 中位数，误差线为三轮实际 [min,max]。线段只引导阅读五个实测 L；没有曲线拟合或中间 L 承诺。同 L Recall 增长仍需检查 QPS，严格同时增长才计 observed joint gain。样本 paired bootstrap 仅描述性，非语义 IID 或全比较同时显著性保证。','','## 同 L：原 M5、成本优化与新增补全','']
    pairs=[('M5','GT'),('M5REG96','M5'),('M5OPT','M5'),('REGOPT96','M5REG96'),('M5RES12','M5'),('M5RES12','M5OPT'),('M5RES12','M5REG96'),('M5RES12','WIDE12'),('WIDE12','M5OPT')]
    rows=[]
    for a,b in pairs:
        selected=select(comparisons,a,b)
        if not selected:continue
        rows.append([f'{a}−{b}',len(selected),trend(selected,'recall_delta_pp'),ranges(selected,'recall_delta_pp'),trend(selected,'paired_qps_change_pct'),ranges(selected,'paired_qps_change_pct'),sum(r['rescue_members'] for r in selected),sum(r['damage_members'] for r in selected),sum(r['observed_joint_gain'] for r in selected)])
    lines += [table(['比较','点数','R 升/平/降','ΔR pp范围','QPS 升/平/降','paired QPS %范围','救回成员','损伤成员','双升点'],rows),'','缓存优化的效果以 M5OPT/M5、REGOPT96/M5REG96 同一轮返回 ID/score word 的严格身份为前件。新 residual 表的增量同时对原 M5 和同成本基础 M5OPT 报告，不能把缓存节约全算为补全监督的质量贡献。WIDE12 与 M5RES12 在线额外上限都为12，实际到达 X 个数可能不同；PAIR/WIDE 离线条件键数、键目标对数、模型字节与resident字节未强制匹配，差异不能全部归因于 winner 条件化。','']
    main=lock['primary_method'];lines+=['四个 dataset/K 分组的主方法同 L 对照：','']
    rows=[]
    for ds in DATASETS:
        for K in (1,100):
            for ref in ('M5','M5OPT','GT','WIDE12'):
                selected=[r for r in select(comparisons,main,ref) if r['dataset']==ds and r['K']==K]
                if selected:rows.append([LABELS[ds],K,f'{main}−{ref}',trend(selected,'recall_delta_pp'),ranges(selected,'recall_delta_pp'),trend(selected,'paired_qps_change_pct'),ranges(selected,'paired_qps_change_pct'),sum(r['rescue_members'] for r in selected),sum(r['damage_members'] for r in selected)])
    lines += [table(['数据集','K','比较','R 升/平/降','ΔR pp','QPS 升/平/降','QPS %','救回','损伤'],rows),'','## 跨 L：逐个原始工作点的实际双升','']
    cross=[r for r in comparisons if r['L']!=r['reference_L']];joint=[r for r in cross if r['observed_joint_gain']]
    lines += [f'预锁跨 L 比较 {len(cross)} 个，实际 observed joint gain {len(joint)} 个。所有都是较小预算候选方法对较大预算 GT；以下保留两端真实方法和预算身份，不插值。','']
    rows=[];index={ck(r):r for r in comparisons}
    for r in joint:
        old=index.get((r['dataset'],r['K'],r['L'],'M5',r['reference_L'],'GT'));existing=bool(old and old['observed_joint_gain'])
        rows.append([LABELS[r['dataset']],r['K'],f"{r['method']} L{r['L']}",f"GT L{r['reference_L']}",fmt(r['recall_delta_pp'],signed=True),fmt(r['paired_qps_change_pct'],signed=True),r['rescue_members'],r['damage_members'],'原M5此预算已双升' if existing else '本轮候选新增双升'])
    lines += [table(['数据集','K','候选','原始参照','ΔR pp','paired QPS %','救回','损伤','贡献归属'],rows) if rows else '无实际跨预算双升。','',f"完整全部比较（含非双升、损伤与描述性区间）：{link('comparisons.csv',ROOT/'analysis/final_v1/comparisons.csv')}。新增双升分类只表示当前公开工作点的观察，不表示新 held-out confirmation 或默认替换。",'','## 候选机制与 U 外真实救回、损伤','']
    rows=[]
    for name in dict.fromkeys(m['method'] for m in mechanisms):
        for ds in DATASETS:
            for K in (1,100):
                ms=[m for m in mechanisms if (m['method'],m['dataset'],m['K'])==(name,ds,K)]
                if not ms:continue
                rows.append([name,LABELS[ds],K,fmt(sum(m['C_total'] for m in ms)/sum(m['n'] for m in ms)),fmt(sum(m['X_total'] for m in ms)/sum(m['n'] for m in ms)),sum(m['new_rescues_vs_M5'] for m in ms),sum(m['new_damage_vs_M5'] for m in ms),sum(m['new_rescues_outside_original_M5_U'] for m in ms),sum(m['new_damage_outside_original_M5_U'] for m in ms),sum(m['new_rescues_outside_original_TRAIN_GT100_U'] for m in ms),sum(m['new_damage_outside_original_TRAIN_GT100_U'] for m in ms)])
    lines += [table(['方法','数据集','K','C均值','X均值','救回vsM5','损伤vsM5','M5U外救','M5U外损','旧TRAINU外救','旧TRAINU外损'],rows),'',f"逐 K/L 机制见 {link('mechanisms.csv',ROOT/'analysis/final_v1/mechanisms.csv')}，完整已保存 trace 的独立成员诊断见 {link('independent_mechanisms.csv',ROOT/'reviews/independent_result_audit/independent_mechanisms.csv')}。U 外损伤直接由 (原M5返回−实际返回)∩GT_K 无条件累加，未假定为0。",'', 'pair 表按 (route,原C逐行winner) 条件，route 表按 route；同一 winner 可重复出现在多个路由行。每行最多4目标、三行合计最多12；去原R/全部C/已出现X，pair miss 空，不回退 route。训练残差是 GT_K−原 M5_final_K，使用合法冻结 TRAIN，条件键要求至少两个 distinct TRAIN query 支持；表由实际残差目标的整数联合覆盖编译。旧 REG 扩展普通图邻接，与此目标支持机制不同。表质量观察只能支持本轮实际冻结模型，不能声称泛化定理。','','## 实际费用、资源与身份','']
    receipt_names=('reviews/build.json','reviews/fit_build.json','reviews/fit_preflight.json','reviews/data_preflight.json','reviews/native_qualification.json','reviews/smoke_regression.json','reviews/fit_campaign_execution.json','reviews/FIT_execution.json','reviews/fit_execution.json','reviews/evaluation_execution.json','reviews/independent_audit_execution.json','reviews/plot_curves_wrapper_execution.json','reviews/plot_curves_execution.json','reviews/administrative_failure_1.json')+tuple(f'reviews/fit_execution.{ds}.json' for ds in DATASETS)
    costs=[];sources={str(args.metrics):sha(args.metrics),str(audit_path):sha(audit_path),str(plot_path):sha(plot_path)}
    for name in receipt_names:
        path=ROOT/name
        if not path.exists():continue
        r=load(path);costs.append([name,r.get('status','未声明'),r.get('exit_code','—'),'未计量/None' if elapsed(r) is None else fmt(elapsed(r),6),link('receipt',path)]);sources[str(path)]=sha(path)
    lines += [table(['阶段收据','实际状态','exit','实际 elapsed 秒','来源'],costs),'','native 单线程阶段：','']
    rows=[];setup=[];model_capacity=[]
    for j in state['completed']:
        rows.append([LABELS[j['dataset']],j['role'],fmt(elapsed(j),6) if elapsed(j) is not None else '未计量/None',j['exit_code'],j.get('max_threads_observed','未登记'),j.get('peak_rss_bytes_observed',j.get('peak_VmRSS_bytes',j.get('peak_rss_bytes','查看原run_state')))])
    for c in configs:
        ep=Path(c['out'])/'native_environment.json';env=load(ep)
        resident={(x['K'],x['L'],x['family']):x['resident_bytes'] for x in env.get('completion_tables',[])}
        manifest_path=Path(c.get('completion_manifest',ROOT/'models'/c['dataset']/'compile_manifest.json'))
        if manifest_path.exists():
            manifest=load(manifest_path);require(manifest['status']=='FROZEN_TRAIN_ONLY_POST_M5_RESIDUAL_COMPLETION_ALL_10_POINTS','actual compiler qualification');sources[str(manifest_path)]=sha(manifest_path)
            for key,pair in manifest['models'].items():
                for family,record in pair.items():model_capacity.append([LABELS[c['dataset']],record['K'],record['L'],family,record['eligible_key_count'],record['populated_key_count'],record['selected_key_target_pairs'],record['bytes'],resident.get((record['K'],record['L'],family),'未登记'),record['support_min_distinct_queries']])
            setup.append({'dataset':c['dataset'],'new_FIT_and_compiler_actual_fields':{k:manifest.get(k) for k in ('compiler_elapsed_seconds','native_response_generation_elapsed_seconds','compiler_max_seconds_remainder','source_hash_seconds','label_decode_seconds')},'manifest':str(manifest_path)})
        ep=Path(c['out'])/'native_environment.json';env=load(ep)
        setup.append({'dataset':c['dataset'],'startup_fields':{k:v for k,v in env.items() if 'startup' in k or 'resident' in k},'optimized_layouts':env.get('optimized_layouts',[])});sources[str(ep)]=sha(ep)
    fit=load(ROOT/'fit_state.json');sources[str(ROOT/'fit_state.json')]=sha(ROOT/'fit_state.json')
    require(fit['status']=='FIT_COMPLETE_ALL_MODELS_FROZEN' and fit.get('active') is None and len(fit['completed'])==2,'actual eligible FIT phase complete')
    fit_rows=[]
    for record in fit['completed']:
        require(record['status']=='PASS_ADDITIONAL_FIT_COMPLETE_WITHIN_900S' and record['model_eligible'] and record['historical_cost_reset'] is False and record['cap_seconds']==900 and record['elapsed_seconds']<=900,'actual FIT per-dataset budget')
        stage=record['stages'];fit_rows.append([LABELS[record['dataset']],fmt(record['historical_TRAIN_seconds'],6),fmt(record['elapsed_seconds'],6),record['cap_seconds'],fmt(record['cumulative_TRAIN_with_this_increment_seconds'],6),fmt(stage[0]['elapsed_seconds'],6),fmt(stage[1]['elapsed_seconds'],6)])
    lines += ['每数据集实际新增 FIT wholewall 与历史债：','',table(['数据集','历史TRAIN秒','本次增量秒','本次cap秒','累计TRAIN秒','native subprocess秒','compiler subprocess秒'],fit_rows),'']
    lines += [table(['数据集','role','整job wall秒','exit','观测线程','sampled峰RSS bytes'],rows),'',f"run_state.training_increment_seconds = {json.dumps(state.get('training_increment_seconds'))}；与 formal test no_training 分开。whole FIT budget费用含 native/compiler 子进程的完整生命周期，不包含其后收尾 manifest hash 与行政收据写入；该边界按实际阶段收据保留。没有记录 elapsed 的失败项保留 None，不当0。建表、compiler、预检、smoke、native、评价、独审、绘图按各实际阶段列账；wrapper 与 inner 图 receipt 是同一阶段包含关系，不重复相加。旧 TRAIN、原模型和既有构图费用是历史债；本轮完整 new FIT 与 startup layout/setup 成本不能归为零或隐藏。",'', '实际模型容量（直接保存的 compiler 字段；在线12上限不等于离线容量相等）：','',table(['数据集','K','L','family','eligible keys','populated keys','key-target pairs','bytes','resident bytes','support≥queries'],model_capacity),'','优化布局初始化登记：','', '```json',json.dumps(setup,ensure_ascii=False,indent=2),'```','',f"资源冻结上限：产物累计1536MiB、最小free1GiB、RSS64GiB、每formal dataset job10800秒；实际占用与采样边界以冻结 {link('protocol.md',ROOT/'protocol.md')} 与 {link('run_state.json',ROOT/'run_state.json')} 原始资源收据为准；所有产物保留，不用删除失败数据使费用或磁盘账变小。报告生成耗时由独立 wrapper 后续落账，本报告生成时不伪造自身最终 elapsed。",'', '## 限界与停止/保留','', '全量保存的 normal untimed plain 已在同一 pass 完成独立 fresh scalar/linear oracle 与 GT main packet word 校验；本轮没有第二次整批 native replay。OPT 分支另外与相应原方法的完整 packet word 身份核对，缓存 R 在 untimed qualifier 检查 n×K words。固定256 count 查询的 post/region计数不能写为全10K NDC；完整 oldREG trace 与两种 completion trace 分开，REGOPT 不另存 trace，依其完整原方法输出身份与 native oracle 限界。三轮 timed packet 不保存，不能声称逐 query timed bit parity。','', '仍保留默认 GT10、原 M5 与同步计时对照。结果仅是当前公开已曝光两数据集、单一10K角色、五档L、冻结模型上的实际信号；没有新 confirmation、没有多模态几何因果证明、没有跨数据集或未测预算推广保证。未过严格 Recall/QPS 双升的点记为取舍；即使通过公开点 observed joint gain，也不自动替换生产默认。','',f"独审来源：{link('independent audit',audit_path)}；科学点/比较/候选整数来自其绑定 metrics SHA `{binding['sha256']}`。图与报告只呈现这些保存字段，无新 ANN、fit、distance、GT 或 bootstrap。",'']
    require(all(stat4(p)==s for p,s in before.items()),'report preserved scientific sources')
    args.out.write_text('\n'.join(lines),encoding='utf-8');receipt=ROOT/'reviews/report_generation.json';require(not receipt.exists(),'preserve report receipt')
    record=dict(status='PASS_E176_AUDITED_CHINESE_REPORT',report=str(args.out),report_sha256=sha(args.out),metrics=str(args.metrics),metrics_audited_sha256_and_stat4=binding,point_count=len(points),comparison_count=len(comparisons),mechanism_count=len(mechanisms),cross_L_comparisons=len(cross),cross_L_observed_joint=len(joint),source_sha256=sources,writer_source_sha256=sha(__file__),elapsed_seconds=time.monotonic()-started,default_replacement=False,no_new_query_GT_distance_fit_bootstrap=True,actual_stage_unknown_elapsed_preserved_None=True)
    receipt.write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n');print(json.dumps({k:record[k] for k in ('status','point_count','comparison_count','mechanism_count','cross_L_observed_joint')}))
if __name__=='__main__':main()
