from common import *
import csv
threads(cpu=15);resources();started=time.monotonic()
E66=C/'stage7_multimode_index_v1';E67=C/'stage8_multimode_wall_v1'
points=list(csv.DictReader((O/'results/points.csv').open()))
groups=list(csv.DictReader((O/'results/groups.csv').open()))
occupancy=list(csv.DictReader((O/'results/occupancy.csv').open()))
v=read(O/'reviews/verification.json');assert v['status']=='PASS'
cases=list(csv.DictReader((E67/'results/failure_query_summary.csv').open()))
annotated=[];checks=[]
for ds in DS:
    c=read(E66/'inputs'/ds/'construction.json');h=c['hub_count'];d=c['dim']
    ids=np.fromfile(c['hub_ids'],np.int32)
    W=np.fromfile(E66/'models'/ds/'mode3P/W.f32',np.float32).reshape(h,3,d)
    for split in ['fit','aux']:
        z=np.load(O/'results'/ds/(split+'.npz'));n=len(z['source_rows'])
        cfg=read(E66/'inputs'/ds/(split+'.json'))
        q=np.fromfile(cfg['queries_file'],np.float32,count=n*d).reshape(n,d)
        assert np.array_equal(z['source_rows'],np.fromfile(cfg['row_ids'],np.int64)[:n])
        count=0
        for i in range(0,n,4096):
            # Different implementation: Python scalar inner products, max per hub,
            # and Python tuple sorting by (-score, real ID).
            scores=[max(sum(float(x)*float(y) for x,y in zip(q[i],p)) for p in hub) for hub in W]
            ranking=sorted(range(h),key=lambda j:(-scores[j],int(ids[j])))[:3]
            if not z['near_tie_mode'][i]:
                assert np.array_equal(ids[ranking],z['exact_mode_hubs'][i]);count+=1
        for m in ['baseline','duplicate3P','mode3P']:
            entry=np.fromfile(E66/'results'/ds/split/(m+'_L128/entry_ids.i32'),np.int32).reshape(n,3)
            exact=z['exact_mode_hubs' if m=='mode3P' else 'exact_P_hubs']
            agreement=np.array([len(set(map(int,a))&set(map(int,b))) for a,b in zip(entry,exact)],np.uint8)
            assert np.array_equal(agreement,z[m+'_agreement'])
            row=next(r for r in points if r['dataset']==ds and r['split']==split and r['model']==m)
            assert abs(float(row['exact_hub_set_fraction'])-float((agreement==3).mean()))<1e-12
        checks.append(dict(dataset=ds,split=split,agreement_rows=3*n,scalar_mode_replays=count))
        if split=='aux':
            for row in cases:
                if row['dataset']!=ds:continue
                i=int(np.flatnonzero(z['source_rows']==int(row['source_row']))[0])
                r=dict(row)
                for m in ['baseline','duplicate3P','mode3P']:
                    r[m+'_full_score_overlap']=int(z[m+'_agreement'][i])
                    r[m+'_score_regret']=float(z[m+'_score_regret'][i])
                for label in ['P','mode']:
                    r['full_score_'+label+'_hubs']=' '.join(map(str,z['exact_'+label+'_hubs'][i]))
                    r['near_tie_'+label]=bool(z['near_tie_'+label][i])
                r['mode_seven_slots_unique_hubs']=int(z['mode3P_candidate_unique_hubs'][i])
                assert set(map(int,r['baseline_entries'].split()))==set(np.fromfile(E66/'results'/ds/'aux/baseline_L128/entry_ids.i32',np.int32).reshape(n,3)[i])
                assert set(map(int,r['new_entries'].split()))==set(np.fromfile(E66/'results'/ds/'aux/mode3P_L128/entry_ids.i32',np.int32).reshape(n,3)[i])
                annotated.append(r)
assert len(annotated)==93
with (O/'results/failure_ranking_annotation.csv').open('x',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(annotated[0]));w.writeheader();w.writerows(annotated)
numerical_seconds=time.monotonic()-started
dump(O/'reviews/independent_review.json',dict(status='PASS',checks=checks,aligned_failure_queries=len(annotated),seconds=numerical_seconds,new_NSG=0,new_HNSW=0))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,ax=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
colors=['#52657c','#c36b3e','#187f7c'];labels=['Original P','Duplicate 3P','P + two modes']
for j,ds in enumerate(DS):
    for k,m in enumerate(['baseline','duplicate3P','mode3P']):
        yy=[100*float(next(r['exact_hub_set_fraction'] for r in points if r['dataset']==ds and r['split']==sp and r['model']==m)) for sp in ['fit','aux']]
        ax[j].bar(np.arange(2)+(k-1)*.24,yy,.23,color=colors[k],label=labels[k])
        for x,y in zip(np.arange(2)+(k-1)*.24,yy):ax[j].text(x,y+1,f'{y:.1f}',ha='center',fontsize=9)
    ax[j].set(xticks=[0,1],xticklabels=['Historical fit 20K','Exposed aux 7,952'],ylim=(0,105),ylabel='Full profile-score top-3 set agreement (%)',title=['WebVid','Yandex'][j])
    ax[j].grid(axis='y',alpha=.2);ax[j].set_axisbelow(True)
ax[1].legend(loc='lower right')
fig.suptitle('E68 | Fixed profiles and stored routing traces\nRanking agreement is not NSG utility; zero new ANN queries',fontsize=12)
(O/'figures').mkdir(exist_ok=True)
for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/('profile_ranking_agreement.'+ext),dpi=170)
plt.close(fig)

lines=['# E68 冻结画像完整排序诊断','',
'在完整分数排序相同的条件下，重复三份P明显降低了实际三入口的排序一致率。这确认物理索引与近似检索组合存在损失，值得下一阶段检验；它没有证明提高ef会提升原NSG Recall或完整QPS。新增mode在Yandex有局部收益，而部分严重失败即使已经选中完整画像前三仍发生，不能把全部损伤归因近似误差。','',
'本阶段复用E66的55,904条历史fit/aux和实际返回，计算111,808次原P/mode完整分数参照，duplicate另55,904逻辑alias。0新HNSW、0新NSG、0新GT、0模型/图更新，无QPS。float64 raw-query内积、每hub最高slot分数、按真实ID稳定平局；近tie单列，不声称原SIMD逐位等价。','',
'| 数据/角色 | 原P三hub完全一致 | duplicate3P | mode3P | mode原已测净命中/失败变化 |',
'|---|---:|---:|---:|---:|']
for ds in DS:
    for split in ['fit','aux']:
        rr=[next(r for r in points if r['dataset']==ds and r['split']==split and r['model']==m) for m in ['baseline','duplicate3P','mode3P']]
        lines.append('| '+('WebVid' if ds==DS[0] else 'Yandex')+' '+split+' | '+' | '.join(f"{100*float(r['exact_hub_set_fraction']):.2f}%" for r in rr)+f" | {int(rr[2]['observed_NSG_net_hits']):+d} / {int(rr[2]['observed_NSG_failure_change']):+d} |")
lines+=['',
'原P/duplicate使用同一个完整分数参照；mode列使用自己的完整画像分数前三，三列不能解释为同一个检索效用目标。排除近tie后各一致率变化小于0.04个百分点。duplicate全部55,904条trace的七个返回slot恰好只含3个真实hub；mode含3–7个。这只是返回候选占用，未测内部visited/expanded独立hub数。源码的ef10维护物理节点，而非10个不同真实hub；不能换算为固定ef/3。','',
'Web aux中，mode选中自身完整前三的6,181条净命中−1、救回27/新增27；其余1,771条净−105、救回17/新增30。Y aux对应6,869条净+108、救回32/新增22；其余1,083条净−59、救回10/新增16。分组是事后相关性，查询难度/表示变化同时存在；未实际运行完整前三的NSG，不能把组差相加成反事实收益。','',
'E67全部93条独立失败转换query已连接排序诊断，465个五L已测命中保持原值。以下是具体案例；原数据namespace见CSV，行号是router_train源row。','',
'| 数据/source row | 五L原命中 → mode命中 | 原P/mode完整前三重合数 | mode近tie |',
'|---|---|---:|---|']
for ds,rid in [(DS[1],3846),(DS[0],3849)]:
    r=next(r for r in annotated if r['dataset']==ds and int(r['source_row'])==rid)
    lines.append(f"| {'WebVid' if ds==DS[0] else 'Yandex'} / {rid} | {r['baseline_hits_by_L']} → {r['new_hits_by_L']} | {r['baseline_full_score_overlap']}/3、{r['mode3P_full_score_overlap']}/3 | {r['near_tie_mode']} |")
lines+=['',
'Yandex 3846的mode已经完整命中画像前三，五L却从10命中降为0；WebVid 3849恰好相反，mode与其画像前三0重合，却在五L从0救回10。前者说明提高同一评分排名的近似一致性未必能救回所有损伤；后者说明逼近画像排名也可能改变已有救回。都未测新入口反事实，不能预报ef30结果。若实际mode三入口已与完整画像前三一致，进一步逼近同一个排名不会改变这条query的三入口集合；这只约束该固定评分函数与三入口合同，不推出其它评分/图/搜索预算也无法救回。排序分数不是NSG效用，不能当GT oracle。','',
f"主分析{v['seconds']:.3f}秒；独立审查{numerical_seconds:.3f}秒，另计绘图。112次原P标量完整排序复核、14次mode标量排序复核、167,712行三方法入口集合重算及93条失败连接通过；抽样原生距离最大误差{max(r['max_sampled_native_distance_error'] for r in v['records']):.3g}。均CPU15、进程与库线程1，E67两native实际退出后执行。操作耗时不作QPS。",
'',
'P-fit包含旧train/monitor；aux7952已历史暴露且用于E64/E66辅助选择，本诊断继续是开发反馈。E34最终validation与held-out未读取。原E66双集门失败和E67局部曲线保持，未因此选择新ef或部署候选。下一步优先另建完整P/mode前三的真实NSG回放诊断；若有实际效用再考虑有控制的物理搜索宽度修正，本阶段均未运行。','',
'[前瞻协议](protocol.md) · [排序统计](results/points.csv) · [事后关联](results/groups.csv) · [返回slot占用](results/occupancy.csv) · [93条失败排序注释](results/failure_ranking_annotation.csv) · [主验收](reviews/verification.json) · [独立复核](reviews/independent_review.json)','',
'![完整画像排序一致率](figures/profile_ranking_agreement.png)','']
(O/'report.md').write_text('\n'.join(lines))
resources();print('REPORT_AND_REVIEW_PASS',checks,numerical_seconds,flush=True)
