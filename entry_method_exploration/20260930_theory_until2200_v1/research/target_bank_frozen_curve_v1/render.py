import csv, hashlib, io, json, os
from pathlib import Path
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
R=Path(__file__).resolve().parent

def read(p): return json.loads(Path(p).read_text())
def put(p,x):
    with Path(p).open('x') as f:
        f.write(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def iv(v): return '['+', '.join(f'{x:+.6f}' for x in v)+']'
def short(ds): return 'WebVid' if ds.startswith('web') else 'Yandex'

def main():
    assert read(R/'reviews/independent_audit.json')['status']=='PASS'
    a=read(R/'results/analysis.json')
    full=[];cross=[];r90=[];cost=[];rows=[];crossrows=[]
    for ds,d in a['datasets'].items():
        for point,p in d['points'].items():
            for name,m in p['methods'].items():
                v=m['vs_Default3'];label=f'{short(ds)} R{p["K"]}/L{p["L"]}'
                full.append(f'| {label} | {name} | {m["recall_pct"]:.6f} | {m["qps_pooled"]:.3f} | '+', '.join(f'{x:.3f}' for x in m['qps_each'])+f' | {v["delta_recall_pp"]:+.6f} {iv(v["descriptive_interval_pp"])} | {v["delta_QPS_pct"]:+.4f}% |')
                cost.append(f'| {label} | {name} | {m["route_NDC"]:.3f} | {m["graph_NDC"]:.3f} | {v["extra_us_per_query"]:+.3f} | {v["rescued_queries"]}/{v["damaged_queries"]} | {v["net_positive_hits"]}/{v["net_negative_hits"]} | {v["true_member_added"]}/{v["true_member_lost"]} |')
                rows.append(dict(dataset=ds,K=p['K'],L=p['L'],method=name,Recall_pct=m['recall_pct'],QPS=m['qps_pooled'],QPS0=m['qps_each'][0],QPS1=m['qps_each'][1],QPS2=m['qps_each'][2],seconds0=m['seconds'][0],seconds1=m['seconds'][1],seconds2=m['seconds'][2],route_NDC=m['route_NDC'],graph_NDC=m['graph_NDC'],**{k:v[k] for k in ['delta_recall_pp','delta_QPS_pct','rescued_queries','damaged_queries','net_positive_hits','net_negative_hits','true_member_added','true_member_lost']},CI_lo_pp=v['descriptive_interval_pp'][0],CI_hi_pp=v['descriptive_interval_pp'][1]))
        for v in d['all_TargetBank_cross_budget_comparisons']:
            cross.append(f'| {short(ds)} R{v["K"]} | {v["TargetBank_L"]} | {v["control"]}/{v["control_L"]} | {v["delta_recall_pp"]:+.6f} {iv(v["descriptive_interval_pp"])} | {v["delta_QPS_pct"]:+.4f}% | {v["empirical_dominates"]} | {v["all_three_paired_QPS_faster"]} | {v["QPS_ranges_overlap"]} |')
            crossrows.append({'dataset':ds,**{k:z for k,z in v.items() if not isinstance(z,list)},'CI_lo_pp':v['descriptive_interval_pp'][0],'CI_hi_pp':v['descriptive_interval_pp'][1],'delta_QPS0_pct':v['paired_repeat_delta_QPS_pct'][0],'delta_QPS1_pct':v['paired_repeat_delta_QPS_pct'][1],'delta_QPS2_pct':v['paired_repeat_delta_QPS_pct'][2]})
        for K,methods in d['fastest_measured_R90'].items():
            for name,v in methods.items():
                r90.append(f'| {short(ds)} R{K} | {name} | '+('未达90% | — | — |' if v is None else f'{v["L"]} | {v["recall_pct"]:.6f} | {v["qps_pooled"]:.3f} |'))
    for fn,data in [('metrics.csv',rows),('all_cross_budget_comparisons.csv',crossrows)]:
        s=io.StringIO();w=csv.DictWriter(s,fieldnames=list(data[0]));w.writeheader();w.writerows(data);put(R/'results'/fn,s.getvalue())
    text='''# 全部冻结曲线数据

每集历史4096 query。真实K1/K100；三次完整wall，QPS=3N/sum(time)。95%query-paired bootstrap为历史开发、多重比较下的描述区间。R90只选最快实测达标点；不插值，不把不同实际Recall称为精确同Recall比较。

## 90%阈值

| 组合 | 方法 | L | 实际Recall % | 完整QPS |
|---|---|---:|---:|---:|
'''+ '\n'.join(r90)+'''

## 全部36个点

| 工作点 | 方法 | Recall % | pooled QPS | 三次QPS | 对默认ΔRecall pp及区间 | 对默认ΔQPS |
|---|---|---:|---:|---|---|---:|
'''+ '\n'.join(full)+'''

## 费用与救回/损伤

| 工作点 | 方法 | 路由NDC | 主图NDC | 对默认额外微秒/query | 改善/受损query | 正/负净命中 | 真实成员新增/移除 |
|---|---|---:|---:|---:|---:|---:|---:|
'''+ '\n'.join(cost)+'''

K100在同query内可同时新增和移除正确成员；这与净命中变化不同。

## 全部72个跨预算比较

经验支配只指本样本Recall均值不低且pooled QPS更高；同时列出三轮是否均更快与速度范围是否重叠。此表不是总体支配证明或后选模型依据。同预算TargetBank减rank1也包含在表中。

| 组合 | TargetBank L | 控制/L | ΔRecall pp及区间 | ΔQPS | 经验支配 | 三轮都快 | 速度范围重叠 |
|---|---:|---|---|---:|---|---|---|
'''+ '\n'.join(cross)+'\n'
    put(R/'results/tables.md',text)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(2,2,figsize=(11,8),constrained_layout=True)
    colors={'Default3':'#253b69','DefaultRank1':'#dd9640','TargetBank1':'#188774'}
    markers={'Default3':'o','DefaultRank1':'s','TargetBank1':'^'}
    for row,(ds,d) in enumerate(a['datasets'].items()):
        for col,K in enumerate((1,100)):
            ax=axs[row,col]
            for name in colors:
                ps=sorted((p for p in d['points'].values() if p['K']==K),key=lambda p:p['L'])
                x=[p['methods'][name]['recall_pct'] for p in ps];y=[p['methods'][name]['qps_pooled'] for p in ps]
                lo=[yy-min(p['methods'][name]['qps_each']) for p,yy in zip(ps,y)];hi=[max(p['methods'][name]['qps_each'])-yy for p,yy in zip(ps,y)]
                ax.errorbar(x,y,yerr=[lo,hi],fmt=markers[name],color=colors[name],capsize=3,label=name,markersize=6)
                ax.plot(x,y,color=colors[name],alpha=.3,linewidth=1)
                if name=='TargetBank1':
                    for xx,yy,p in zip(x,y,ps):ax.annotate('L'+str(p['L']),(xx,yy),xytext=(5,5),textcoords='offset points',fontsize=8,color=colors[name])
            ax.axvline(90,color='#888888',linestyle=':',linewidth=1)
            ax.set_title(f'{short(ds)}  Recall@{K}');ax.set_xlabel('Recall (%)');ax.set_ylabel('Full QPS, single thread');ax.grid(alpha=.15)
    axs[0,0].legend(loc='best',frameon=False,fontsize=8)
    fig.suptitle('Frozen target bank: measured local Recall–QPS curves',fontsize=14)
    folder=R/'figures';folder.mkdir(exist_ok=False)
    for ext in ('png','pdf'):fig.savefig(folder/f'curves.{ext}',dpi=180)
    plt.close(fig)
    sources=[R/'results/analysis.json',R/'reviews/independent_audit.json',R/'render.py']
    outputs=[R/'results/tables.md',R/'results/metrics.csv',R/'results/all_cross_budget_comparisons.csv',folder/'curves.png',folder/'curves.pdf']
    put(R/'reviews/render_identity.json',{'source':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'outputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs},'caption':'All 36 measured points. Error bars show three-run QPS range, not confidence intervals. Lines guide the eye only; no interpolated evidence. Historical development queries; unequal L/Recall at R90.', 'new_search':0})
    print('RENDERED',len(rows),len(crossrows),flush=True)
if __name__=='__main__':main()
