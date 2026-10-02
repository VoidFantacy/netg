from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();assert read(O/'reviews/verification.json')['status']=='PASS'
points=list(csv.DictReader((O/'results/points.csv').open()));paired=list(csv.DictReader((O/'results/paired.csv').open()));interp=list(csv.DictReader((O/'results/frontier_interpolation.csv').open()));cost=read(O/'results/cost.json')
selection=read(O/'results/frozen_selection.json')['datasets'];(O/'figures').mkdir(exist_ok=True)
colors={'nsg':'#697386','fast30k':'#1673b8','gt10_hard':'#e39125','baseline_soft':'#30946e','best_new':'#ac3c85'}
base_labels={'nsg':'NSG','fast30k':'Fast30K (GT1)','gt10_hard':'FastGT10-hard','baseline_soft':'GT10-soft (matched)'}
def pp(ds,name):return sorted([p for p in points if p['dataset']==ds and p['model']==name],key=lambda x:int(x['L']))
def names(ds):return ['nsg','fast30k','gt10_hard']+(['baseline_soft'] if ds==DS[0] else [])+['best_new']
def label(ds,name):return base_labels.get(name,'New: '+selection[ds]['best_new'])
def export(fig,name):
    for ext in ['png','svg','pdf']:fig.savefig(O/'figures'/f'{name}.{ext}',dpi=180)
    plt.close(fig)
foot='Historical development 2,048 queries already used for selection • CPU15 / 1 thread • Five full batch walls • Not final validation'
for key,xlabel,file in [('recall_pct','Recall@10 (%)','recall_qps'),('failure_rate_pct','GT10 zero-hit failure rate (%)','failure_qps')]:
    fig,axes=plt.subplots(1,2,figsize=(13,5.5))
    for ax,ds,title in zip(axes,DS,['WebVid','Yandex']):
        for name in names(ds):
            ps=pp(ds,name);x=[float(p[key]) for p in ps];q=np.array([float(p['QPS']) for p in ps]);low=np.array([float(p['QPS_min']) for p in ps]);high=np.array([float(p['QPS_max']) for p in ps])
            ax.plot(x,q,'o-',label=label(ds,name),color=colors[name],markersize=4,lw=1.4);ax.fill_between(x,low,high,color=colors[name],alpha=.13)
        ax.set(title=title,xlabel=xlabel,ylabel='QPS (median; shade = five-run range)');ax.set_yscale('log');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('E65 — '+('Recall–QPS' if key=='recall_pct' else 'Failure rate–QPS'),fontsize=15);fig.text(.5,.014,foot,ha='center',fontsize=9);fig.tight_layout(rect=(0,.05,1,.94));export(fig,file)
fig,axes=plt.subplots(2,3,figsize=(14,8))
for row,(ds,title) in enumerate(zip(DS,['WebVid','Yandex'])):
    for name in names(ds):
        ps=pp(ds,name);x=np.arange(5)
        for col,(key,ylabel) in enumerate([('recall_pct','Recall@10 (%)'),('QPS','QPS (median)'),('failure_rate_pct','Zero-hit failures (%)')]):
            ax=axes[row,col];ax.plot(x,[float(p[key]) for p in ps],'o-',color=colors[name],label=label(ds,name),markersize=4,lw=1.3);ax.set_xticks(x,[64,128,256,400,800]);ax.set(xlabel='Search L',ylabel=ylabel,title=title+' — '+ylabel);ax.grid(alpha=.2)
            if col==1:ax.set_yscale('log')
    axes[row,0].legend(fontsize=8)
fig.suptitle('E65 — all three measured metrics by L',fontsize=15);fig.text(.5,.01,foot,ha='center',fontsize=9);fig.tight_layout(rect=(0,.04,1,.94));export(fig,'three_metrics_by_L')
fig,axes=plt.subplots(2,2,figsize=(12,7))
for row,(ds,title) in enumerate(zip(DS,['WebVid','Yandex'])):
    comparator='baseline_soft' if ds==DS[0] else 'gt10_hard'
    vals=sorted([p for p in paired if p['dataset']==ds and p['comparator']==comparator],key=lambda p:int(p['L']));x=np.arange(5)
    recall=np.array([float(p['delta_recall_pp']) for p in vals]);qps=np.array([float(p['QPS_change_pct']) for p in vals])
    axes[row,0].plot(x,recall,'o-',color='#ac3c85');axes[row,0].fill_between(x,[float(p['descriptive_query_bootstrap_low_pp']) for p in vals],[float(p['descriptive_query_bootstrap_high_pp']) for p in vals],color='#ac3c85',alpha=.12)
    axes[row,1].plot(x,qps,'o-',color='#ac3c85');axes[row,1].fill_between(x,[float(p['all_range_low_pct']) for p in vals],[float(p['all_range_high_pct']) for p in vals],color='#ac3c85',alpha=.12)
    for col,yl in enumerate(['Recall change (pp)','QPS change (%)']):
        ax=axes[row,col];ax.axhline(0,color='gray',lw=.8);ax.set_xticks(x,[64,128,256,400,800]);ax.set(title=title+' new vs matched GT10',xlabel='Search L',ylabel=yl);ax.grid(alpha=.2)
fig.suptitle('E65 — paired changes; bands: query bootstrap / timing ranges',fontsize=15);fig.text(.5,.01,foot,ha='center',fontsize=9);fig.tight_layout(rect=(0,.04,1,.94));export(fig,'paired_deltas')
table=[];differences=[]
for ds,title in zip(DS,['WebVid','Yandex']):
    comparator='baseline_soft' if ds==DS[0] else 'gt10_hard'
    for p in points:
        if p['dataset']==ds:
            table.append(f"| {title} | {label(ds,p['model'])} | {p['L']} | {float(p['recall_pct']):.4f} | {float(p['QPS']):.2f} [{float(p['QPS_min']):.2f}, {float(p['QPS_max']):.2f}] | {float(p['failure_rate_pct']):.4f} ({p['failure_count']}) |")
    a=[p for p in paired if p['dataset']==ds and p['comparator']==comparator];dr='/'.join(f"{float(p['delta_recall_pp']):+.4f}" for p in a);speed='/'.join(f"{float(p['QPS_change_pct']):+.3f}%" for p in a);netfail='/'.join(f"{int(p['new_failures'])-int(p['rescued']):+d}" for p in a)
    range_cross=sum(float(p['all_range_low_pct'])<=0<=float(p['all_range_high_pct']) for p in a)
    ip=[p for p in interp if p['dataset']==ds];ir='/'.join(f"{float(p['change_pct']):+.3f}%" for p in ip)
    differences.append(f"{title}：相对匹配起点，按L64/128/256/400/800的ΔRecall为{dr} pp；QPS中位变化{speed}，{range_cross}/5点的五轮交叉范围含零方向；失败净新增{netfail}条。共同Recall区间三个内部点的描述性log-QPS插值变化为{ir}，它们不是实测同Recall点。")
report=['# E65 今日实际候选的完整开发集QPS–Recall与失败汇报','',
'已完成45个方法点、225轮单线程完整wall；曲线包含今日实际新候选。两个候选均未通过E64完整开发门，默认保持，整日最终目标未完成。本批数据为历史开发且已用于选型，所有正负均只支持开发范围，不能替代晚间E34最终对照。','',
'WebVid的开发局部曲线信号保留：4/5个L的Recall为正，共同Recall区间描述性插值为+0.57%～+0.81%；同时四个L失败各净增1～2条。两数据集各五点的QPS差范围都包含零方向，尚无稳定加速证据；Yandex质量混合，未形成双集稳定新前沿。', '',
'WebVid固定E62_topology（评分P不变、加载遗漏画像构造的图），Yandex固定E63_zero_mass（2倍zero-hit质量画像及普通图）。选型来自E64全部7952辅助query的预锁规则；本轮source[2048:4096]共2048是协议预定子集，没有按结果换query、模型、L或seed。best_all双集仍是原GT10；best_new只是实际新方法诊断展示，非推荐。','']+differences+['',
'所有方法同机同批：原NSG、原Fast30K/GT1/seed100、FastGT10-hard20K，以及WebVid额外匹配soft起点。Fast与FastGT还有训练量/seed差异，其全部差异不能归因GT数量。真实入口H815/821和底层NSG/base/GT/raw-IP保持；新方法在线仍一份Micro-HNSW→三真实入口→原NSG。','',
'| 数据集 | 方法 | L | Recall@10 % | QPS中位数 [五轮范围] | 零命中率 %（条数） |','|---|---|---:|---:|---:|---:|']+table+['',
'失败严格指top10返回与exact GT10集合无交集，hits1不失败；完整paired.csv的gain_hits/loss_hits分别是逐query净命中数变化的正部/负部之和，保存救回/新增以及描述性query bootstrap；GT10成员集合实际找回/丢失另存results/member_deltas.csv。两种记账净值相同，但同一query内成员替换会抵消：Web L128相对匹配P的前者33/28、集合成员50/45；Y为26/26与34/34。timing重复不是独立Recall样本，收益/损伤不以仅失败指标替代。跨方法的QPS差及插值应结合全曲线与五轮范围，不由单次或同L值声称最终改进。','',
f"累计新增{cost['NSG_calls']:,} NSG、{cost['HNSW_calls']:,} HNSW；35静态图加载/复制、70 plain/count加载，0新图构建、梯度或GT。native两job总操作{cost['native_job_seconds']:.3f}秒含加载/count/IO；各纯wall原值另见timings.csv，route-only/graph-only未单测，以null和原因记录。", '',
'CPU15实际进程/OMP/BLAS/MKL1线程，子进程exec前绑核，单个被测方法串行；计时包含完整在线路由/映射/原NSG/预分配输出，GT/count/hash/JSON/build/load在timer外，一次完整warmup加五轮轮换。两native工具terminal实际exit后才做独立分析。92160返回集合和GT10 mask、720原kernel parity、完整plain/count/五轮bits、35图全bytes、五L同图同入口、8192行E64相同query L128逐位回归及225轮顺序/QPS恒等均通过。', '',
'E63原fit正值、E64 WebVid拓扑净正伴随失败损伤分别保留。本轮无E34最终validation输入/反馈，无held-out访问；下一阶段不能把本批开发结果包装为最终泛化成功。最后20:00停训练、20:40停新增查询、21:00交付的整日安排保持。','',
'[协议](protocol.md) · [全部原始点](results/points.csv) · [225轮wall](results/timings.csv) · [配对增损](results/paired.csv) · [失败query](results/failure_cases.csv) · [输入角色](reviews/input_roles.json) · [验收](reviews/verification.json) · [成本](results/cost.json)', '',
'[QPS–Recall](figures/recall_qps.svg) · [QPS–失败率](figures/failure_qps.svg) · [按L三指标](figures/three_metrics_by_L.svg) · [配对小差值及不确定性](figures/paired_deltas.svg)；同名PNG/PDF已保存。']
(O/'report.md').write_text('\n'.join(report)+'\n');print('E65_REPORT_READY')
