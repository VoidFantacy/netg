from verify_candidates import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();jobs=read(O/'logs/jobs.json');assert len(jobs)==4 and all(j['status']=='COMPLETE' for j in jobs)
with (O/'results/paired.csv').open() as f:paired=list(csv.DictReader(f))
gate=read(O/'results/gate.json');cost=read(O/'results/cost.json');offline=read(O/'results/offline.json');ret=read(O/'results/gain_retention.json')
allpairs=[r for r in paired if r['split']=='all'];fig,axs=plt.subplots(2,3,figsize=(13,7),layout='constrained')
for di,ds in enumerate(DS):
 rr=[r for r in allpairs if r['dataset']==ds];x=np.arange(len(rr));labels=[r['candidate'].replace('10','')+'\nvs '+r['reference'].replace('10','').replace('baseline','P') for r in rr]
 for j,(key,title) in enumerate([('net_hits','Net GT10 hits'),('failure_change','Zero-hit failure change'),('total_NDC_change_pct','Total distance-count change (%)')]):
  a=axs[di,j];vals=[float(r[key]) for r in rr];a.bar(x,vals,color=['#267f70' if (v>=0 if j==0 else v<=0) else '#be5d4d' for v in vals]);a.axhline(0,color='#555',lw=.8);a.margins(y=.22);a.set_xticks(x,labels,fontsize=7);a.set_title(('WebVid' if di==0 else 'Yandex')+' · '+title,fontsize=10)
  for i,v in enumerate(vals):a.annotate(f'{v:+.0f}' if j<2 else f'{v:+.2f}',(i,v),xytext=(0,4 if v>=0 else -11),textcoords='offset points',ha='center',fontsize=8)
fig.suptitle('E79 target-space profiles | historical aux 7,952 per dataset | L128 | no QPS measurement',fontsize=12)
fig.savefig(O/'figures/target_modes_v2.png',dpi=170);fig.savefig(O/'figures/target_modes_v2.svg');plt.close(fig)
