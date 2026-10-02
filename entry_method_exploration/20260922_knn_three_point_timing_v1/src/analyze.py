"""Score actual outputs and report the small repeated complete-wall comparison."""
from common import *
import csv

assert read(RUN/'state.json')['status']=='MEASUREMENTS_COMPLETE'
assert not (RUN/'analysis.json').exists()
start=time.monotonic()
lock=read(RUN/'config.locked.json')
old=read(OLD/'config.locked.json')
old_info=read(OLD/'analysis/information.json')
metrics=[]
comparisons=[]
restored=0
reference_inputs={}
for ds,cfg in lock['datasets'].items():
    native=cfg['native']
    gt=np.fromfile(native['GT'],'<i4').reshape(4096,100)
    info=np.load(OLD/'analysis'/f'{ds}.information.npz')
    assert read(RUN/'results'/ds/'selector_parity.json')['all_neighbors_actions_entries']
    for k,K in enumerate([1,100]):
        members=[set(map(int,g[:K])) for g in gt]
        target_entries=np.fromfile(Path(cfg['model'])/f'expected_entries_k{K}.i32','<i4').reshape(4096,3)
        for L in cfg['grid'][str(K)]:
            point_metrics=[]
            point_hits=[]
            for method in lock['methods']:
                path=RUN/'results'/ds/f'{method}_k{K}_L{L}'
                complete=read(path/'complete.json')
                assert complete['status']=='PASS' and complete['threads']==1 and len(complete['seconds'])==3
                ids=np.fromfile(path/'ids.i32','<i4').reshape(4096,K)
                dist=np.fromfile(path/'distances.f32','<f4').reshape(4096,K)
                entries=np.fromfile(path/'entry_ids.i32','<i4').reshape(4096,3)
                assert np.all((ids>=0)&(ids<native['base_n'])) and np.isfinite(dist).all()
                assert K==1 or np.all(np.diff(np.sort(ids,axis=1),axis=1)>0)
                assert np.all(np.diff(dist,axis=1)>=0)
                hit=np.array([sum(int(v) in valid for v in row) for row,valid in zip(ids,members)],'i2')
                expected_entries=target_entries if method=='TargetKNN' else np.fromfile(Path(cfg['model'])/'default_entries.i32','<i4').reshape(4096,3)
                assert np.array_equal(entries,expected_entries)
                point_hits.append(hit)
                if method=='TargetKNN':
                    previous=old['datasets'][ds]
                    exists=L in previous['old_K_L'][str(K)]+previous['missing'][str(K)]
                    if exists:
                        origin=OLD if L in previous['missing'][str(K)] else E107
                        for a,action in enumerate(old['actions']):
                            ref=origin/'results'/('main_'+ds)/action/f'k{K}_L{L}'
                            for filename in ['ids.i32','distances.f32']:
                                reference_inputs[str(ref/filename)]=identity(ref/filename)
                            ref_ids=np.fromfile(ref/'ids.i32','<i4').reshape(4096,K)
                            ref_dist=np.fromfile(ref/'distances.f32','<f4').reshape(4096,K)
                            mask=info['TargetKNN_actions'][:,k]==a
                            assert np.array_equal(ids[mask],ref_ids[mask])
                            assert np.array_equal(dist[mask].view('u4'),ref_dist[mask].view('u4'))
                        restored+=1
                qs=4096/np.array(complete['seconds'])
                item=dict(dataset=ds,method=method,K=K,L=L,recall=float(hit.mean()/K),
                    qps_median=float(np.median(qs)),qps_min=float(qs.min()),qps_max=float(qs.max()),
                    qps_1=float(qs[0]),qps_2=float(qs[1]),qps_3=float(qs[2]),
                    complete_query_wall=True,formal_evaluation=False)
                metrics.append(item);point_metrics.append(item)
            delta=point_hits[1].astype('i4')-point_hits[0]
            baseline,candidate=point_metrics
            record=dict(dataset=ds,K=K,L=L,baseline=baseline,candidate=candidate,
                recall_delta_pp=float(100*delta.mean()/K),
                qps_change_pct=100*(candidate['qps_median']/baseline['qps_median']-1),
                timing_ranges_overlap=not(candidate['qps_max']<baseline['qps_min'] or candidate['qps_min']>baseline['qps_max']),
                rescued_queries=int((delta>0).sum()),harmed_queries=int((delta<0).sum()))
            if L==old['datasets'][ds]['target'][str(K)][1]:
                expected=old_info['results'][ds]['methods']['TargetKNN']['K_mean_gain_pp'][k]
                assert abs(record['recall_delta_pp']-expected)<1e-10
            comparisons.append(record)

def interpolated_qps(points,target):
    points=sorted(points,key=lambda p:p['L'])
    if not all(a['recall']<=b['recall'] for a,b in zip(points,points[1:])):
        return None
    for p in points:
        if p['recall']==target:
            return p['qps_median']
    for a,b in zip(points,points[1:]):
        if a['recall']<target<b['recall']:
            weight=(target-a['recall'])/(b['recall']-a['recall'])
            return 1/((1-weight)/a['qps_median']+weight/b['qps_median'])
    return None

matched=[]
for ds in lock['datasets']:
    for K in [1,100]:
        groups={m:[p for p in metrics if p['dataset']==ds and p['K']==K and p['method']==m] for m in lock['methods']}
        # Report one declared target and the middle measured baseline recall, with no extrapolation.
        middle=groups['DefaultGT10'][1]['recall']
        for name,target in [('R90',.9),('middle_baseline_recall',middle)]:
            qps={m:interpolated_qps(points,target) for m,points in groups.items()}
            measured={m:max([p['qps_median'] for p in points if p['recall']>=target],default=None) for m,points in groups.items()}
            change=None if any(v is None for v in qps.values()) else 100*(qps['TargetKNN']/qps['DefaultGT10']-1)
            matched.append(dict(dataset=ds,K=K,target_name=name,recall=target,interpolated_qps=qps,
                interpolated_change_pct=change,best_measured_qps_at_or_above=measured,
                scope='coarse descriptive interpolation in time vs Recall; not exact matched-Recall evidence'))
preserve_check()
for item in reference_inputs.values():
    assert identity(item['path'])==item
dump(RUN/'reviews/reference_returns.json',dict(files=list(reference_inputs.values()),restored_candidate_points=restored))
dump(RUN/'analysis.json',dict(comparisons=comparisons,matched=matched,seconds=time.monotonic()-start,
    status='PASS',default_changed=False,complete_query_wall=True,formal_evaluation=False,
    scope='same exposed queries; frozen four-fold rules; only three budgets and three timing repeats'))
with (RUN/'metrics.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(metrics[0]));writer.writeheader();writer.writerows(metrics)

short=lambda ds:'WebVid' if ds.startswith('web') else 'Yandex'
rows=['# TargetKNN 三点三次轻量速度对比','',
    '用户明确要求的 E120 补测，不是新模型或正式验收。两集各4096条原开发query、K1/K100，各三个固定L点、两方法、每点三次完整单线程计时。所有原选择规则与标签预算保持不变；预测和实际路由在计时段内重算，不使用离线预选动作。','',
    '**结果：12个点召回均值全部提高，但完整QPS全部下降，三次计时范围在各点均不重叠。** Web下降17.58%至26.96%，Y下降27.88%至54.06%。90%召回处的区间内粗略时间插值仍更慢。本次确认当前冻结实现有质量/速度取舍，不能把召回正增益说成没有提升，也没有端到端加速或默认替换。','',
    '## 实测结果','',
    'QPS列为三次中位数[min,max]；Recall为实际返回，三次返回逐位一致。pp表示百分点，不是相对百分比。','',
    '| 数据 | K | L | GT10 Recall % | TargetKNN Recall % | 增益 pp | GT10 QPS | TargetKNN QPS | QPS变化 |',
    '|---|---:|---:|---:|---:|---:|---|---|---:|']
for c in comparisons:
    b,a=c['baseline'],c['candidate']
    rows.append(f"| {short(c['dataset'])} | {c['K']} | {c['L']} | {100*b['recall']:.4f} | {100*a['recall']:.4f} | {c['recall_delta_pp']:+.4f} | {b['qps_median']:.1f} [{b['qps_min']:.1f},{b['qps_max']:.1f}] | {a['qps_median']:.1f} [{a['qps_min']:.1f},{a['qps_max']:.1f}] | {c['qps_change_pct']:+.2f}% |")
rows+=['','## 同召回参考','',
    '只有三点，无法精确定位同召回前沿。下表在相邻点之间线性插值每query时间，再取倒数；仅限实测范围内，不外推。它只是速度/质量取舍的粗略参考。完整JSON还报告达到门槛的最佳已测点和中间基线召回处的插值。','',
    '| 数据 | K | 90% GT10 QPS估计 | 90% TargetKNN QPS估计 | 变化 |',
    '|---|---:|---:|---:|---:|']
for m in matched:
    if m['target_name']=='R90':
        fmt=lambda x:'未覆盖' if x is None else f'{x:.1f}'
        change='未比较' if m['interpolated_change_pct'] is None else f"{m['interpolated_change_pct']:+.2f}%"
        rows.append(f"| {short(m['dataset'])} | {m['K']} | {fmt(m['interpolated_qps']['DefaultGT10'])} | {fmt(m['interpolated_qps']['TargetKNN'])} | {change} |")
jobs=read(RUN/'reviews/jobs.json')
rows+=['','## 口径与验证','',
    '计时包括：每条查询float64归一化、对该折3072个fit向量精确余弦查找、top55选择、七动作标签整数求和、选中动作的精确画像路由或原GT10小图路由、原NSG搜索、写入结果内存。默认只付原GT10路由与主搜索。索引/模型加载、离线fit矩阵物化、磁盘结果保存及GT评分不计入查询wall；双方口径一致。','',
    'CPU15、实际进程1线程，串行；每点双方各128query预热，三次完整4096query计时并轮换先后。四折模型按原query顺序切换，是OOF聚合实现的轻量计时，不是单一部署模型或新盲测。没有把NumPy批处理离线吞吐当在线预测成本。','',
    f'两集全部16384个query/K的邻居集合、动作和入口与冻结E120一致；全部默认返回恢复E105，{restored}个已存在的候选预算点逐query恢复E107/E120。另768次原核/链接E99搜索检查和三重复输出一致性通过。每个主点的召回增益恢复前轮结果。','',
    f"实际NSG {lock['expected_calls']:,} 次（计时294912、预热3072、核验768）。两集进程共 {sum(j['seconds'] for j in jobs if j['name']!='build'):.2f} 秒，编译 {jobs[0]['seconds']:.2f} 秒；含加载/核验的作业wall不可替代上表查询QPS。0重训/新GT/图/新测试payload，旧E120 seal保持。",'',
    '本次回答的是当前冻结规则的完整速度成本，不改原信息门，不据三重复作显著性或替换默认的决定。结果只限两集、这些L、当前实现和历史曝光query，不能外推全部kNN实现或入口学习。','',
    '[协议](protocol.md) · [逐次QPS表](metrics.csv) · [结构化结果](analysis.json) · [作业记录](reviews/jobs.json) · [配置](config.locked.json)','']
(RUN/'report.md').write_text('\n'.join(rows))
dump(RUN/'state.json',dict(status='ANALYZED',completed=False,active_processes=[],pending=['docs','seal'],default_changed=False))
print(json.dumps([dict(dataset=c['dataset'],K=c['K'],L=c['L'],recall_delta_pp=c['recall_delta_pp'],qps_change_pct=c['qps_change_pct']) for c in comparisons],indent=2),flush=True)
