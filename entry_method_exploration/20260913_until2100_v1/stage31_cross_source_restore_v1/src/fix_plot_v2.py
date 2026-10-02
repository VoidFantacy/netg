from common import *
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threads();resources();pairs=list(csv.DictReader((O/'results/paired.csv').open()));fail=list(csv.DictReader((O/'results/failure_queries.csv').open()));cost=read(O/'results/cost.json');gate=read(O/'results/gate.json');figdir=O/'figures';figdir.mkdir(exist_ok=True)
fig,axes=plt.subplots(2,3,figsize=(13,7),layout='constrained')
for di,ds in enumerate(DS):
 rr=[r for r in pairs if r['dataset']==ds and r['split']=='accept' and r['candidate']=='supported10']
 for ax,key,title in zip(axes[di],['net_hits','failure_change','total_NDC_change_pct'],['Net GT10 hits','Zero-hit failure change','Total NDC change (%)']):
  v=[float(r[key]) for r in rr];bars=ax.bar(['P','compact','E89','random'],v,color='#267f96');ax.axhline(0,color='black',lw=.7);ax.margins(y=.3);ax.bar_label(bars,fmt='%.3f' if key.endswith('pct') else '%+.0f',padding=4);ax.set_ylim(min(v+[0])-(max(v+[0])-min(v+[0]) or 1)*.3,max(v+[0])+(max(v+[0])-min(v+[0]) or 1)*.35);ax.set_title(('WebVid' if di==0 else 'Yandex')+' — '+title);ax.set_xlabel('E90 minus reference');ax.grid(axis='y',alpha=.2)
fig.suptitle('E90 cross-source restoration | exposed acceptance suffix 3,976 | L128 | no QPS')
fig.savefig(figdir/'acceptance_v2.png',dpi=170);fig.savefig(figdir/'acceptance_v2.svg');plt.close(fig)
shutil.copy2(O/'report.md',O/'report_v1.md');p=O/'report.md';p.write_text(p.read_text().replace('figures/acceptance.png','figures/acceptance_v2.png'));dump(O/'reviews/figure_layout_correction.json',dict(reason='Zero labels touched title in original Y failure panel; original retained, only y margins changed.',new_ANN=0))
