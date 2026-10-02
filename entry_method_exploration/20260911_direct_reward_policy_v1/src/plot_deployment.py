from common import *
import sys
sys.dont_write_bytecode=True;sys.path.insert(0,str(E28/'src/vendor'))
from openpyxl import Workbook
from openpyxl.styles import Font,PatternFill
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

assert read(O/'state.json')['status']=='DEPLOYMENT_ANALYSIS_COMPLETE'
real=read(O/'results/deployment_tables.json');training=read(O/'results/analysis_tables.json')
names={DS[0]:'WebVid2.5M',DS[1]:'Yandex10M IP'};colors=['#7c96a8','#d7792d']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
fig,axs=plt.subplots(2,2,figsize=(14.5,9.6))
for j,ds in enumerate(DS):
    default='gt10_soft' if ds==DS[0] else 'gt10_hard'
    for k,reference in enumerate([default,'teacher']):
        rows=[next(x for x in real['real_paired'] if x['dataset']==ds and x['split']==stage and x['method']=='reward' and x['reference']==reference) for stage in ['fit','cal','audit']]
        xs=np.arange(3)+(k-.5)*.25;ys=np.array([r['delta_recall_pp'] for r in rows]);lo=np.array([r['ci95_low_pp'] for r in rows]);hi=np.array([r['ci95_high_pp'] for r in rows])
        axs[0,j].errorbar(xs,ys,yerr=[ys-lo,hi-ys],fmt='o',capsize=4,color=colors[k],label='Reward vs '+('current default' if k==0 else 'teacher C8'),markersize=6)
        for x,y in zip(xs,ys):axs[0,j].annotate(f'{y:+.3f}',(x,y),xytext=(0,10 if k==0 else -20),textcoords='offset points',ha='center',fontsize=9,color=colors[k])
    axs[0,j].axhline(0,color='#566878',lw=.8);axs[0,j].set_xticks(range(3),['Fit (20K)','Cal (1,024)','Audit (1,024)'])
    axs[0,j].set_title(names[ds]+' — real L128 retrieval');axs[0,j].set_ylabel('Recall@10 change (pp)');axs[0,j].grid(axis='y',alpha=.16)
    methods=[default,'teacher','reward'];rows=[next(x for x in real['real_points'] if x['dataset']==ds and x['split']=='audit' and x['method']==m) for m in methods]
    routing=np.array([r['route_ndc'] for r in rows]);graph=np.array([r['graph_ndc'] for r in rows])
    axs[1,j].bar(range(3),graph,color='#7c96a8',label='NSG graph distances')
    axs[1,j].bar(range(3),routing,bottom=graph,color='#d7792d',label='Full route distances')
    for i,amount in enumerate(graph+routing):axs[1,j].text(i,amount+30,f'{amount:,.0f}',ha='center',fontsize=10)
    axs[1,j].set_ylim(0,max(graph+routing)*1.15);axs[1,j].set_xticks(range(3),['Current default','Teacher C8','Reward C8'])
    axs[1,j].set_ylabel('Mean distance computations per query');axs[1,j].set_title('Audit: candidate generation is included in routing');axs[1,j].grid(axis='y',alpha=.16)
fig.suptitle('Fit gains shrink outside training; C8 adds routing work',fontsize=18,y=.98)
axs[0,0].legend(loc='upper right',frameon=False,fontsize=9);axs[1,0].legend(loc='upper left',frameon=False,fontsize=9)
fig.text(.5,.048,'Whiskers: descriptive paired-query bootstrap 95% intervals. All splits have historical use; no fresh blind test.',ha='center',fontsize=10,color='#556776')
fig.text(.5,.019,'The WebVid cal point misses the prelocked default-improvement gate. No validation / QPS run; NDC does not determine latency.',ha='center',fontsize=10,color='#556776')
fig.subplots_adjust(left=.08,right=.98,top=.91,bottom=.13,hspace=.32,wspace=.23)
for ext in ['png','svg']:fig.savefig(O/'figures'/('development_and_cost.'+ext),dpi=160,facecolor='white')
plt.close(fig)

tables={**training,'reward_support':read(O/'results/reward_support.json'),**{k:v for k,v in real.items() if v}}
dump(O/'results/report_tables.json',tables)
shutil.copy2(O/'chart_data.xlsx',O/'source_before/chart_data_training_only.xlsx')
wb=Workbook();wb.remove(wb.active)
for name,rows in tables.items():
    ws=wb.create_sheet(name);fields=list(rows[0]);ws.append(fields)
    for row in rows:ws.append([row.get(k) for k in fields])
    for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='263C50')
    ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
    for col in ws.columns:ws.column_dimensions[col[0].column_letter].width=min(42,max(14,len(str(col[0].value))+2))
    for row in ws.iter_rows(min_row=2):
        for c in row:
            if isinstance(c.value,float):c.number_format='0.000000'
sources=[('Protocol',str(O/'protocol.md')),('Deployment plan',str(O/'deployment_plan.md')),('Configuration repair',str(O/'configuration_repair.md')),
    ('Complete-action labels',str(E28/'labels')),('Frozen reward scales',str(O/'reviews/reward_scales.json')),('Report',str(O/'report.md')),
    ('Expected reward','Exact softmax expectation over 56 complete C8 triples; not stochastic online evaluation'),
    ('Cached utility','Frozen float32 model selects C8 action, then reads existing real L128/K10 labels'),
    ('Real retrieval','Fit20K/cal1024/audit1024: full candidate routing and original NSG; raw IDs independently rescored'),
    ('Cost','route NDC includes two HNSW proposals, H anchor scores and 8 model scores; graph NDC separate'),
    ('No QPS','Prelocked development gate failed; validation and wall repetitions were not run'),
    ('Limits','Historical split use; one H/seed/lambda/temperature; new reward has larger displacement than teacher')]
ws=wb.create_sheet('Sources');ws.append(['Item','Definition / file'])
for row in sources:ws.append(row)
ws.column_dimensions['A'].width=30;ws.column_dimensions['B'].width=130
wb.save(O/'chart_data.xlsx')
dump(O/'reviews/final_plots_generated.json',dict(status='PASS',figures=3,formats=['png','svg'],workbook_sheets=len(tables)+1,sources=sources))
print('DEPLOYMENT_PLOTS_AND_WORKBOOK_COMPLETE',flush=True)
