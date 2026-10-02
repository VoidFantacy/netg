from pathlib import Path
import json,time,hashlib,os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
TB=Path(__file__).resolve().parents[1];R=TB/'research/net_gain_figure_v1';assert not R.exists();R.mkdir()
start=time.time();p=Path('/data/netg/ACSG/entry_method_exploration/20260920_wfree_frozen_replication_v1/results/primary_L128.json');raw=json.loads(p.read_text());rows=[x for x in raw if x['K']==1];assert len(rows)==2
data=[]
for x in rows:
    n=4096;same=x['same_entries'];rescue=x['rescued'];harm=x['newly_harmed'];neutral=n-same-rescue-harm
    assert neutral>=0 and x['WFree_failed']-x['baseline_failed']==harm-rescue and x['delta_recall_pp']==100*(rescue-harm)/n
    data.append(dict(dataset='WebVid' if x['dataset'].startswith('web') else 'Yandex',n=n,same_entries=same,changed_entries_same_hit=neutral,rescued=rescue,harmed=harm,net_recall_pp=x['delta_recall_pp'],qps_delta_pct=x['delta_qps_pct']))
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False,'axes.titleweight':'bold','savefig.facecolor':'white'})
fig,axes=plt.subplots(1,2,figsize=(12,4.4),gridspec_kw={'width_ratios':[1.7,1]});ax,bx=axes
colors=['#cbd5e1','#64748b','#0072b2','#d55e00'];keys=['same_entries','changed_entries_same_hit','rescued','harmed'];labels=['Same entries','Changed entries, same hit state','Rescued','Newly failed']
for i,x in enumerate(data):
    left=0
    for k,col,lab in zip(keys,colors,labels):
        w=100*x[k]/4096;ax.barh(i,w,left=left,height=.40,color=col,label=lab if i==0 else None,edgecolor='white',linewidth=.8);left+=w
    ax.text(0,i-.31,f"Entries changed: {100*(4096-x['same_entries'])/4096:.2f}%",fontsize=10,color='#334155')
    bx.bar(i-.18,x['rescued'],width=.32,color=colors[2]);bx.bar(i+.18,x['harmed'],width=.32,color=colors[3]);bx.text(i-.18,x['rescued']+3,str(x['rescued']),ha='center');bx.text(i+.18,x['harmed']+3,str(x['harmed']),ha='center')
    bx.text(i,151,f"Net R@1: {x['net_recall_pp']:+.4f} pp",ha='center',fontweight='bold',fontsize=10)
    bx.text(i,139,f"Full QPS: {x['qps_delta_pct']:+.2f}%",ha='center',color='#9a3412',fontsize=10)
ax.set_yticks(range(2),[x['dataset'] for x in data]);ax.invert_yaxis();ax.set_xlim(0,100);ax.xaxis.set_major_formatter(PercentFormatter());ax.set_ylim(1.6,-.65);ax.set_xlabel('Share of all 4,096 queries');ax.set_title('A different entry often leaves correctness unchanged',loc='left',pad=16);ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
bx.set_xticks(range(2),[x['dataset'] for x in data]);bx.set_ylim(0,160);bx.set_ylabel('Number of queries');bx.set_title('Rescues and new failures cancel',loc='left',pad=16);bx.grid(axis='y',alpha=.18);bx.set_axisbelow(True)
handles,labs=ax.get_legend_handles_labels();fig.legend(handles,labs,loc='lower center',bbox_to_anchor=(.49,.083),ncol=4,frameon=False,fontsize=9)
fig.suptitle('Frozen WFree replication: action changes are not net gains',x=.07,y=.98,ha='left',fontsize=15,fontweight='bold')
fig.text(.07,.015,'E105 existing exposed development data | K=1, L=128 | No new search or timing | Full curves and uncertainty: E105 report',fontsize=9,color='#475569')
fig.subplots_adjust(left=.08,right=.98,top=.78,bottom=.24,wspace=.28)
fig.savefig(R/'net_gain.png',dpi=180);fig.savefig(R/'net_gain.pdf');plt.close(fig)
def ident(p):p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
(R/'data.json').write_text(json.dumps(data,indent=2)+'\n');(R/'complete.json').write_text(json.dumps(dict(status='PLOTTED_PENDING_VISUAL_REVIEW',pid=os.getpid(),seconds=time.time()-start,source=ident(p),plot_source=ident(__file__),outputs=[ident(R/n) for n in ['data.json','net_gain.png','net_gain.pdf']],NSG_calls=0,ANN_calls=0,new_training=0,new_QPS=False),indent=2)+'\n');print(str(R/'net_gain.png'))
