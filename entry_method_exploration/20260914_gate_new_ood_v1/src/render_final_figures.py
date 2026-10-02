"""Presentation-only plots from frozen metrics; preserves initial figures."""
from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    rows=list(csv.DictReader((RUN/'results/metrics.csv').open()))
    colors=dict(NSG='#777777',GT10='#167dba',GATE='#d97816',HNSW='#249257')
    labels=dict(NSG='NSG',GT10='GT10 (ours)',GATE='GATE (adapted)',HNSW='HNSW')
    titles=['WebVid 2.505M','Yandex 10M','LAION 10.004M']
    outputs=[]
    for failure in [False,True]:
        fig,axes=plt.subplots(1,3,figsize=(16,4.8))
        for ax,ds,title in zip(axes,DATASETS,titles):
            for method in colors:
                rr=sorted([r for r in rows if r['dataset']==ds and r['method']==method],key=lambda r:int(r['L']))
                x=[int(r['L']) if failure else float(r['recall_at10'])*100 for r in rr]
                y=[float(r['failed_query_rate'])*100 if failure else float(r['qps_mean']) for r in rr]
                ax.plot(x,y,'o-',ms=4,label=labels[method],color=colors[method])
                if not failure:ax.fill_between(x,[float(r['qps_min']) for r in rr],[float(r['qps_max']) for r in rr],alpha=.12,color=colors[method])
            ax.set_title(title);ax.grid(alpha=.2);ax.legend(fontsize=9)
            if failure:
                ax.set_xlabel('Search budget (L / HNSW efSearch)');ax.set_ylabel('Zero-hit queries (%)');ax.set_xscale('log')
            else:
                ax.set_xlabel('Recall@10 (%)');ax.set_ylabel('Queries / second');ax.set_yscale('log')
        if failure:
            title='Failed query = returned top-10 has no intersection with exact top-10'
            caption='Same budget is not equal work. Rates: metrics.csv. Paired rescue/new-failure counts: paired_queries.csv.'
            stem='failed_query_rate.final'
        else:
            title='Full search: one CPU thread, 10,000 queries, mean of 3 runs'
            caption='16 budgets from 32 to 1500. Shading: observed timing range. WebVid and LAION share the public query source.'
            stem='recall_qps.final'
        fig.suptitle(title,fontsize=13);fig.text(.5,.01,caption,ha='center',fontsize=9);fig.tight_layout(rect=[0,.035,1,.94])
        for ext in ['png','pdf']:
            p=RUN/'figures'/f'{stem}.{ext}';fig.savefig(p,dpi=190);outputs.append(p)
        plt.close(fig)
    dump(RUN/'reviews/final_figures.json',dict(status='PASS',presentation_only=True,metrics_sha256=sha(RUN/'results/metrics.csv'),initial_figures_preserved=True,changes=['GT10 explicitly labeled ours','Paired counts caption corrected to paired_queries.csv'],files={str(p.relative_to(RUN)):sha(p) for p in outputs},script_sha256=sha(Path(__file__))))
    print('Four final PNG/PDF figures generated from unchanged metrics.')

if __name__=='__main__':main()
