import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import RUN,DATASETS,LS,read
from analyze import LABELS,METHODS,METHOD_LABELS

COLORS={'nsg':'#858991','fast30k':'#353d48','fast20k':'#3478bf','e24':'#d88a2d','shrink':'#248f7b'}
plt.rcParams.update({'font.size':10,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})


def save(fig,name):
    out=RUN/'figures';out.mkdir(exist_ok=True)
    for ext in ['svg','png']:fig.savefig(out/f'{name}.{ext}',bbox_inches='tight')
    plt.close(fig)


def main():
    r=read(RUN/'results/analysis.json')
    fig,axes=plt.subplots(1,2,figsize=(13.5,5.2))
    for ax,ds in zip(axes,DATASETS):
        for method in METHODS:
            points=sorted([p for p in r['datasets'][ds]['measured_points'] if p['family']==method],key=lambda p:p['L'])
            y=np.asarray([p['qps'] for p in points]);lo=np.asarray([p['qps_min'] for p in points]);hi=np.asarray([p['qps_max'] for p in points])
            ax.errorbar([p['recall_at_10']*100 for p in points],y,yerr=[y-lo,hi-y],fmt='o-',ms=4,capsize=3,
                        color=COLORS[method],label=METHOD_LABELS[method],lw=1.5)
            if method=='fast20k':
                for p in points:ax.annotate(f"L{p['L']}",(100*p['recall_at_10'],p['qps']),xytext=(4,6),textcoords='offset points',fontsize=8)
        ax.set(title=f"{LABELS[ds]} / frozen alpha={r['datasets'][ds]['selected_alpha']:.2f}",xlabel='Recall@10 (%)',ylabel='End-to-end QPS (one thread)')
        ax.grid(alpha=.2);ax.legend(fontsize=8,ncol=2)
    fig.suptitle('E26: one profile index per method; historical validation 2,000 queries\nMedian and range of 3 independent warm/plain walls; lines only connect measured L points')
    fig.tight_layout();save(fig,'recall_qps')

    fig,axes=plt.subplots(2,2,figsize=(11.5,8.9))
    for row,(xkey,ykey,title) in enumerate([('R','A_all','Events'),('Rh','Ah_all','Hit magnitude')]):
        for col,ds in enumerate(DATASETS):
            ax=axes[row,col];values=[]
            for stage,color,marker,style in [('cal','#476cad','s','-'),('audit','#9a648c','^','--')]:
                candidates=r['datasets'][ds]['development'][stage]['candidates']
                x=[c['pooled'][xkey] for c in candidates];y=[c['pooled'][ykey] for c in candidates];values+=y
                ax.plot(x,y,marker+style,color=color,label=stage,lw=1.4,ms=6)
                for c,vx,vy in zip(candidates,x,y):ax.annotate(f"{c['alpha']:.2f}",(vx,vy),textcoords='offset points',xytext=(4,5 if stage=='cal' else -13),fontsize=8,color=color)
            selected=r['datasets'][ds]['validation']['pooled_L64_L128']['stats'];values.append(selected[ykey])
            ax.scatter([selected[xkey]],[selected[ykey]],marker='*',s=140,color='#c9822c',label='validation / frozen alpha',zorder=4)
            lower=min(-.03,min(values)-.05)
            ax.fill_between([.75,1],[.25,.25],[1,1],color='#dceee5',alpha=.55,zorder=0)
            ax.axvline(.75,color='#778479',ls=':',lw=1);ax.axhline(.25,color='#778479',ls=':',lw=1)
            ax.set(xlim=(0,1.03),ylim=(lower,1.03),title=f'{LABELS[ds]} — {title}',
                   xlabel='Original benefit retained',ylabel='Total harm reduction, including new harm')
            ax.grid(alpha=.16)
            if row==0:ax.legend(fontsize=8,loc='upper right')
    fig.suptitle('Shrinkage reduces disruption, but does it keep the original benefits?\nThree fixed alpha candidates on cal/audit; only the frozen choice on validation; pooled L64/L128')
    fig.tight_layout();save(fig,'retention_total_harm')

    fig,axes=plt.subplots(2,2,figsize=(12.1,8.4))
    for row,ds in enumerate(DATASETS):
        for col,stage in enumerate(['audit','validation']):
            ax=axes[row,col]
            s=r['datasets'][ds]['development']['audit']['selected']['pooled'] if stage=='audit' else r['datasets'][ds]['validation']['pooled_L64_L128']['stats']
            ax.bar(0,s['original_positive_hits'],color='#338e7a',label='Original gain retained')
            ax.bar(0,-s['original_negative_hits'],color='#b75560',label='Original loss remaining')
            ax.bar(1,s['original_positive_hits_retained'],color='#338e7a')
            ax.bar(1,s['new_or_amplified_positive_hits'],bottom=s['original_positive_hits_retained'],color='#93c5b7',label='New / amplified gain')
            remaining=s['original_negative_hits']-s['original_negative_hits_avoided']
            ax.bar(1,-remaining,color='#b75560')
            ax.bar(1,-s['total_new_or_amplified_negative_hits'],bottom=-remaining,color='#e3a366',label='New / aggravated loss')
            for x,gain,loss in [(0,s['original_positive_hits'],s['original_negative_hits']),(1,s['total_positive_hits'],s['total_negative_hits'])]:
                ax.annotate(f'+{gain}',(x,gain),xytext=(0,4),textcoords='offset points',ha='center',fontsize=9)
                ax.annotate(f'-{loss}',(x,-loss),xytext=(0,-13),textcoords='offset points',ha='center',fontsize=9)
            ax.axhline(0,color='#555',lw=1);ax.set(xticks=[0,1],xticklabels=['E24 / A1','Frozen Shrink'],
                ylabel='Hit changes relative to A0 (pooled L64/L128)',title=f'{LABELS[ds]} / {stage}')
            ax.margins(y=.2);ax.grid(axis='y',alpha=.15)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=2,fontsize=9,bbox_to_anchor=(.5,0))
    fig.suptitle('Separate preserved original effects from newly created effects')
    fig.tight_layout(rect=(0,.07,1,1));save(fig,'gain_loss_decomposition')

    fig,axes=plt.subplots(2,2,figsize=(12.1,8.2))
    for row,ds in enumerate(DATASETS):
        rows=sorted([c for c in r['comparisons'] if c['dataset']==ds and c['method']=='shrink' and c['reference']=='e24'],key=lambda c:c['L'])
        x=np.arange(5);v=np.asarray([c['delta_recall_pp'] for c in rows]);lo=np.asarray([c['delta_recall_pp_95']['low'] for c in rows]);hi=np.asarray([c['delta_recall_pp_95']['high'] for c in rows])
        axes[row,0].errorbar(x,v,yerr=[v-lo,hi-v],fmt='o',capsize=4,color=COLORS['shrink'])
        q=[c['qps_percent_change_medians'] for c in rows];runs=np.asarray([c['qps_percent_change_by_repeat'] for c in rows])
        axes[row,1].scatter(x,q,color=COLORS['shrink']);axes[row,1].vlines(x,runs.min(axis=1),runs.max(axis=1),color=COLORS['shrink'],lw=1.5)
        for ax in axes[row]:ax.axhline(0,color='#555',lw=1);ax.set(xticks=x,xticklabels=[str(L) for L in LS],xlabel='L',title=LABELS[ds]);ax.grid(axis='y',alpha=.2)
        axes[row,0].set_ylabel('Recall difference vs E24 (percentage points)');axes[row,1].set_ylabel('QPS difference vs E24 (%)')
    fig.suptitle('Frozen Shrink versus always using E24\nRecall: descriptive paired-query 95% intervals. QPS: median ratio and 3 paired-repeat range.')
    fig.tight_layout();save(fig,'deltas_vs_e24')

    lines=['# E26 全部原值','', '## 单线程50个正式点','',
        '| 数据集 | 方法 | L | Recall % | 零命中 | QPS 1 | QPS 2 | QPS 3 | QPS median | QPS min–max | route NDC | graph NDC |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for ds in DATASETS:
        for kind in METHODS:
            for p in sorted([v for v in r['datasets'][ds]['measured_points'] if v['family']==kind],key=lambda p:p['L']):
                q=p['qps_runs'];lines.append(f"| {LABELS[ds]} | {METHOD_LABELS[kind]} | {p['L']} | {p['recall_at_10']*100:.3f} | {p['failed_queries']} | {q[0]:.2f} | {q[1]:.2f} | {q[2]:.2f} | {p['qps']:.2f} | {p['qps_min']:.2f}–{p['qps_max']:.2f} | {p['mean_route_ndc']:.2f} | {p['mean_graph_ndc']:.2f} |")
    lines+=['','## 全部alpha开发结果及冻结选择','',
        '| 数据集 | 分段 | alpha | 主选择 | R % | Rh % | A_all % | Ah_all % | 净命中 vs A0 | A1净命中 | 目标 | 原损失避免命中 | 新增/加重损失命中 |',
        '|---|---|---:|---|---:|---:|---:|---:|---:|---:|---|---:|---:|']
    for ds in DATASETS:
        for stage in ['cal','audit']:
            for c in r['datasets'][ds]['development'][stage]['candidates']:
                m=c['pooled'];v=' | '.join(f'{100*m[k]:.2f}' for k in ['R','Rh','A_all','Ah_all'])
                lines.append(f"| {LABELS[ds]} | {stage} | {c['alpha']:.2f} | {'yes' if c['name']==r['datasets'][ds]['selected_name'] else ''} | {v} | {m['net_delta_hits']:+d} | {m['always_A1_net_delta_hits']:+d} | {'PASS' if m['target_met'] else 'NOT_MET'} | {m['original_negative_hits_avoided']} | {m['total_new_or_amplified_negative_hits']} |")
    lines+=['','## validation每L保留与总损失','',
        '| 数据集 | L | R % | Rh % | A_all % | Ah_all % | 原正事件保留/原有 | 全部负事件/原有 | 原负命中避免 | 新增/加重负命中 | 净命中 vs A0 / A1 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for ds in DATASETS:
        for L in LS:
            m=r['datasets'][ds]['validation'][str(L)]['stats'];v=' | '.join(f'{100*m[k]:.2f}' if m[k] is not None else 'NA' for k in ['R','Rh','A_all','Ah_all'])
            lines.append(f"| {LABELS[ds]} | {L} | {v} | {m['original_positive_events_retained']}/{m['original_positive_events']} | {m['total_negative_events']}/{m['original_negative_events']} | {m['original_negative_hits_avoided']} | {m['total_new_or_amplified_negative_hits']} | {m['net_delta_hits']:+d} / {m['net_delta_hits']-m['always_A1_net_delta_hits']:+d} |")
    lines+=['','## 对全部必要基线的配对差','',
        '| 数据集 | 方法 | 对照 | L | ΔRecall pp | 描述性95%区间 | ΔQPS中位数 % | 三轮ΔQPS % | 更好/受损query | 正/负命中幅度 |',
        '|---|---|---|---:|---:|---:|---:|---|---:|---:|']
    for c in r['comparisons']:
        ci=c['delta_recall_pp_95'];q='/'.join(f'{v:+.2f}' for v in c['qps_percent_change_by_repeat'])
        lines.append(f"| {LABELS[c['dataset']]} | {METHOD_LABELS[c['method']]} | {METHOD_LABELS[c['reference']]} | {c['L']} | {c['delta_recall_pp']:+.3f} | [{ci['low']:+.3f},{ci['high']:+.3f}] | {c['qps_percent_change_medians']:+.2f} | {q} | {c['improved_queries']}/{c['harmed_queries']} | {c['positive_hits']}/{c['negative_hits']} |")
    (RUN/'results/tables.md').write_text('\n'.join(lines)+'\n')
    print('E26_FIGURES_AND_TABLES_COMPLETE',flush=True)


if __name__=='__main__':main()
