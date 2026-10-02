"""Standalone scientific figures and complete numerical tables from analysis.json."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from common import RUN, DATASETS, LS, read, dump
from analyze import LABELS, METHODS, METHOD_LABELS

COLORS = {'nsg':'#7a7f87','fast30k':'#333a46','fast20k':'#3478bf',
          'e24':'#de8b2e','base_gate':'#24947c','dual_gate':'#b14c82'}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'svg.fonttype':'none','figure.dpi':140,'savefig.dpi':180})


def save(fig, name):
    folder = RUN / 'figures';folder.mkdir(exist_ok=True)
    fig.savefig(folder / f'{name}.svg',bbox_inches='tight')
    fig.savefig(folder / f'{name}.png',bbox_inches='tight')
    plt.close(fig)


def main():
    report=read(RUN / 'results/analysis.json')
    fig,axes=plt.subplots(1,2,figsize=(13.4,5.2))
    for ax,ds in zip(axes,DATASETS):
        r=report['datasets'][ds]
        for kind in METHODS:
            p=sorted([m for m in r['measured_points'] if m['kind']==kind],key=lambda m:m['L'])
            y=np.asarray([m['qps'] for m in p]);low=np.asarray([m['qps_min'] for m in p]);high=np.asarray([m['qps_max'] for m in p])
            ax.errorbar([m['recall_at_10']*100 for m in p],y,yerr=[y-low,high-y],fmt='o-',
                        ms=4,lw=1.5,capsize=3,color=COLORS[kind],label=METHOD_LABELS[kind])
            if kind=='fast20k':
                for m in p:
                    ax.annotate(f"L{m['L']}",(m['recall_at_10']*100,m['qps']),xytext=(4,6),textcoords='offset points',fontsize=8)
        ax.set(title=LABELS[ds],xlabel='Recall@10 (%)',ylabel='End-to-end QPS (one thread)')
        ax.grid(alpha=.2);ax.legend(fontsize=8,ncol=2)
    fig.suptitle('E25: fixed methods, historical validation 2,000 queries; median and range of 3 walls')
    fig.text(.5,-.01,'Lines connect the five measured L values; they are not an interpolated equal-Recall performance estimate.',ha='center',fontsize=9)
    fig.tight_layout();save(fig,'recall_qps')

    fig,axes=plt.subplots(2,2,figsize=(11.5,9))
    markers={'cal':'s','audit':'^','validation':'o'}
    for row,(retention,avoidance,title) in enumerate([('R','A','Query x L events'),('Rh','Ah','Hit gain / loss magnitude')]):
        for col,ds in enumerate(DATASETS):
            ax=axes[row,col]
            ax.axvspan(.75,1,color='#dbeee6',alpha=.6);ax.axhspan(0,.25,color='white',alpha=.85)
            ax.axvline(.75,color='#6d7b72',ls='--',lw=1);ax.axhline(.25,color='#6d7b72',ls='--',lw=1)
            for kind in ['base_gate','dual_gate']:
                p=[report['datasets'][ds]['splits'][s]['gates'][kind]['pooled_L64_L128'] for s in markers]
                ax.plot([m[retention] for m in p],[m[avoidance] for m in p],color=COLORS[kind],lw=1,alpha=.6)
                for stage,m in zip(markers,p):
                    ax.scatter(m[retention],m[avoidance],s=65,color=COLORS[kind],marker=markers[stage],
                               label=f'{METHOD_LABELS[kind]} / {stage}',edgecolors='white',linewidths=.6)
            ax.set(xlim=(0,1.02),ylim=(0,1.02),xlabel='Fraction of gains retained',ylabel='Fraction of harm avoided',
                   title=f'{LABELS[ds]} — {title}')
            ax.grid(alpha=.15)
            if row==0:ax.legend(fontsize=7,loc='upper right')
    fig.suptitle('Can a frozen rule retain >=75% of benefit and avoid >=25% of harm?\nPooled L64/L128; net-hit requirement is checked separately in the tables')
    fig.tight_layout();save(fig,'retention_harm')

    fig,axes=plt.subplots(1,2,figsize=(12,4.6))
    stages=['fit','cal','audit','validation']
    for ax,ds in zip(axes,DATASETS):
        x=np.arange(len(stages))
        for offset,kind in [(-.18,'base_gate'),(.18,'dual_gate')]:
            vals=[report['datasets'][ds]['splits'][s]['gates'][kind]['signal']['weighted_AUC'] for s in stages]
            ax.bar(x+offset,vals,width=.34,color=COLORS[kind],label=METHOD_LABELS[kind])
            for i,v in enumerate(vals):ax.text(i+offset,v+.01,f'{v:.3f}',ha='center',fontsize=8)
        ax.axhline(.5,color='black',lw=1,ls='--');ax.set(xticks=x,xticklabels=stages,ylim=(0,1),ylabel='Hit-weighted AUC',title=LABELS[ds]);ax.legend(fontsize=9)
    fig.suptitle('Benefit-versus-harm ranking from the frozen logit; L64/L128\nFit queries were seen by the E24 profiles; other splits are historical development/validation data')
    fig.tight_layout();save(fig,'signal_transfer')

    fig,axes=plt.subplots(2,2,figsize=(12.5,8.7))
    for row,ds in enumerate(DATASETS):
        for offset,kind in [(-.18,'base_gate'),(.18,'dual_gate')]:
            points=sorted([c for c in report['comparisons'] if c['dataset']==ds and c['method']==kind and c['reference']=='e24'],key=lambda c:c['L'])
            x=np.arange(5)+offset
            y=np.asarray([c['delta_recall_pp'] for c in points]);low=np.asarray([c['delta_recall_pp_95']['low'] for c in points]);high=np.asarray([c['delta_recall_pp_95']['high'] for c in points])
            axes[row,0].errorbar(x,y,yerr=[y-low,high-y],fmt='o',capsize=3,color=COLORS[kind],label=METHOD_LABELS[kind])
            q=np.asarray([c['qps_percent_change_medians'] for c in points]);runs=np.asarray([c['qps_percent_change_by_repeat'] for c in points])
            axes[row,1].scatter(x,q,color=COLORS[kind],label=METHOD_LABELS[kind])
            # Paired-repeat ratios can bracket their median-ratio differently, so draw ranges independently.
            axes[row,1].vlines(x,runs.min(axis=1),runs.max(axis=1),color=COLORS[kind],lw=1.5)
        for col in range(2):
            axes[row,col].axhline(0,color='#565656',lw=1)
            axes[row,col].set(xticks=np.arange(5),xticklabels=[str(L) for L in LS],xlabel='L',title=LABELS[ds])
            axes[row,col].grid(axis='y',alpha=.2);axes[row,col].legend(fontsize=9)
        axes[row,0].set_ylabel('Recall difference vs E24 (percentage points)')
        axes[row,1].set_ylabel('QPS difference vs E24 (%)')
    fig.suptitle('Frozen gate versus always using E24\nRecall: descriptive paired-query 95% intervals. QPS: median ratio and 3 paired-repeat range.')
    fig.tight_layout();save(fig,'deltas_vs_e24')

    lines=['# E25 全部原值与配对统计','',
           '所有Recall均保留完整query分母。QPS来自同机单线程独立plain wall，三次计时是同一批query的重复，不增加Recall样本数。','',
           '## 60个正式测量点','',
           '| 数据集 | 方法 | L | Recall % | 零命中 | QPS 1 | QPS 2 | QPS 3 | QPS median | QPS min–max | route NDC | graph NDC |',
           '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for ds in DATASETS:
        for kind in METHODS:
            for p in sorted([m for m in report['datasets'][ds]['measured_points'] if m['kind']==kind],key=lambda p:p['L']):
                q=p['qps_runs']
                lines.append(f"| {LABELS[ds]} | {METHOD_LABELS[kind]} | {p['L']} | {100*p['recall_at_10']:.3f} | {p['failed_queries']} | {q[0]:.2f} | {q[1]:.2f} | {q[2]:.2f} | {p['qps']:.2f} | {p['qps_min']:.2f}–{p['qps_max']:.2f} | {p['mean_route_ndc']:.2f} | {p['mean_graph_ndc']:.2f} |")
    lines += ['', '## 训练到验证：L64/128合并','',
              '| 数据集 | 分段 | 规则 | 改道 % | R % | A % | Rh % | Ah % | 净命中 vs A0 | A1净命中 | 目标 | weighted AUC |',
              '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|']
    for ds in DATASETS:
        for stage in stages:
            for kind in ['base_gate','dual_gate']:
                g=report['datasets'][ds]['splits'][stage]['gates'][kind];m=g['pooled_L64_L128']
                ratios=' | '.join(f'{100*m[k]:.2f}' for k in ['R','A','Rh','Ah'])
                lines.append(f"| {LABELS[ds]} | {stage} | {METHOD_LABELS[kind]} | {100*m['switch_fraction']:.2f} | {ratios} | {m['net_delta_hits']:+d} | {m['always_A1_net_delta_hits']:+d} | {'PASS' if m['target_met'] else 'NOT_MET'} | {g['signal']['weighted_AUC']:.4f} |")
    lines += ['', '## 每L的收益保留与受损避免','',
              '| 数据集 | 规则 | L | R % | A % | Rh % | Ah % | 正事件保留/原有 | 负事件保留/原有 | 净命中 vs A0 | 净命中 vs A1 |',
              '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for ds in DATASETS:
        for kind in ['base_gate','dual_gate']:
            for L in LS:
                m=report['datasets'][ds]['validation_gates'][kind]['per_L'][str(L)]['stats']
                ratios=' | '.join(f'{100*m[k]:.2f}' if m[k] is not None else 'NA' for k in ['R','A','Rh','Ah'])
                lines.append(f"| {LABELS[ds]} | {METHOD_LABELS[kind]} | {L} | {ratios} | {m['positive_events_retained']}/{m['positive_events_available']} | {m['negative_events_retained']}/{m['negative_events_available']} | {m['net_delta_hits']:+d} | {m['net_delta_hits']-m['always_A1_net_delta_hits']:+d} |")
    lines += ['', '## 相对全部必要对照的差值','',
              '| 数据集 | 方法 | 对照 | L | ΔRecall pp | 描述性95%区间 | ΔQPS median % | 三轮ΔQPS % | 更好/受损query | 正/负命中幅度 |',
              '|---|---|---|---:|---:|---:|---:|---|---:|---:|']
    for c in report['comparisons']:
        ci=c['delta_recall_pp_95'];q='/'.join(f'{v:+.2f}' for v in c['qps_percent_change_by_repeat'])
        lines.append(f"| {LABELS[c['dataset']]} | {METHOD_LABELS[c['method']]} | {METHOD_LABELS[c['reference']]} | {c['L']} | {c['delta_recall_pp']:+.3f} | [{ci['low']:+.3f}, {ci['high']:+.3f}] | {c['qps_percent_change_medians']:+.2f} | {q} | {c['improved_queries']}/{c['harmed_queries']} | {c['positive_hits']}/{c['negative_hits']} |")
    (RUN / 'results/tables.md').write_text('\n'.join(lines)+'\n')
    print('FIGURES_AND_ALL_TABLES_WRITTEN',flush=True)


if __name__=='__main__':
    main()
